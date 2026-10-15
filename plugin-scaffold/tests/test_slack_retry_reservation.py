"""Deterministic same-workspace Tier 3 retry admission races; no provider calls."""

from concurrent.futures import ThreadPoolExecutor
from email.message import Message
import hashlib
import io
import json
import os
import threading
import time
import urllib.error
from urllib.parse import urlsplit
import uuid

import pytest

import connectors
from security_store import SecurityStore


@pytest.fixture(params=["sqlite", "postgres"])
def rate_repository(request, monkeypatch, tmp_path):
    if request.param == "postgres":
        url = os.environ.get("WISDOMTWIN_TEST_DATABASE_URL", "").strip()
        if not url:
            pytest.skip("Requires explicitly configured isolated synthetic PostgreSQL")
        if urlsplit(url).hostname not in {"localhost", "127.0.0.1", "::1"} or not urlsplit(url).path.endswith("_test"):
            pytest.fail("Retry tests require an isolated loopback *_test database")
        options = {"database_url": url}
    else:
        options = {"sqlite_path": str(tmp_path / "retry-pacing.sqlite3")}
    db = SecurityStore(**options)
    monkeypatch.setattr("security_store.security_store", lambda: SecurityStore(**options))
    team = "SYNTHETIC_TEAM_" + uuid.uuid4().hex
    key = json.dumps(["SYNTHETIC_APP", team, "conversations.history"])
    try:
        yield team
    finally:
        with db.connection() as connection:
            db.execute(connection, "DELETE FROM security_entries WHERE kind='provider_rate' AND key_hash=?",
                       (hashlib.sha256(key.encode()).hexdigest(),))


@pytest.mark.parametrize("winner", ["retry", "competitor"])
def test_tier3_short_retry_and_competing_user_share_one_atomic_admission(monkeypatch, rate_repository, winner):
    monkeypatch.setenv("SLACK_HISTORY_RATE_CLASS", "tier3")
    clock = [1700000000.0]
    guard = threading.Lock()
    slept, retry_dispatched, competitor_dispatched = (threading.Event() for _ in range(3))
    first_done, second_done = threading.Event(), threading.Event()
    calls, waits = [], []
    monkeypatch.setattr(time, "time", lambda: clock[0])
    url = "https://slack.com/api/conversations.history?channel=C1"
    headers = Message()
    headers["Retry-After"] = "2"

    def wait(delay):
        assert delay == 2
        waits.append(delay)
        clock[0] += delay
        slept.set()
        if winner == "competitor":
            assert competitor_dispatched.wait(5), "Competing request never reached the mocked provider"

    monkeypatch.setattr(time, "sleep", wait)

    def urlopen(request, **kwargs):
        assert request.full_url == url and kwargs["timeout"] == 30
        caller = request.get_header("Authorization")
        with guard:
            calls.append((caller, clock[0]))
            ordinal = sum(1 for token, _ in calls if token == caller)
        if caller == "Bearer synthetic-first" and ordinal == 1:
            raise urllib.error.HTTPError(url, 429, "private-provider-detail", headers, None)
        if caller == "Bearer synthetic-first":
            retry_dispatched.set()
            if winner == "retry":
                assert second_done.wait(5), "Competing admission check did not finish"
        else:
            assert caller == "Bearer synthetic-second"
            competitor_dispatched.set()
            if winner == "competitor":
                assert first_done.wait(5), "Retry admission check did not finish"
        return io.BytesIO(b'{"ok":true}')

    monkeypatch.setattr("urllib.request.urlopen", urlopen)

    def invoke(caller):
        try:
            if caller == "second":
                ready = retry_dispatched if winner == "retry" else slept
                assert ready.wait(5), "First request never reached its bounded retry"
            with connectors.slack_rate_context(team_id=rate_repository, app_id="SYNTHETIC_APP"):
                try:
                    return connectors._request_json(url, "synthetic-" + caller)
                except connectors.SourceRateLimited as exc:
                    return exc
        finally:
            (first_done if caller == "first" else second_done).set()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(invoke, caller) for caller in ("first", "second")]
        results = [future.result(timeout=8) for future in futures]
    expected_winner = 0 if winner == "retry" else 1
    assert results[expected_winner] == {"ok": True}
    losing = results[1 - expected_winner]
    assert isinstance(losing, connectors.SourceRateLimited), "The retry and another user both dispatched at the cooldown boundary"
    assert losing.retry_after_seconds == pytest.approx(1.2)
    assert len(calls) == 2 and sum(at == 1700000002.0 for _, at in calls) == 1
    assert waits == [2]
    assert "private-provider-detail" not in str(losing)
