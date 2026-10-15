"""Current-access batching, explicit partial coverage and durable Slack pacing."""

from datetime import date
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from email.message import Message
import hashlib
import io
import json
import os
import threading
import time
import urllib.error
from urllib.parse import parse_qs, urlsplit
import uuid

import pytest

import connectors
from errors import CodedToolError
import service
from store import current_store


def source(channel, ordinal, text):
    ts = f"1700000000.{ordinal:06d}"
    return {"uri": f"https://synthetic.slack.com/archives/{channel}/p1700000000{ordinal:06d}",
            "text": text, "author_provider_id": "SYNTHETIC_AUTHOR", "ts": ts}


def body(rows, *, more=False):
    return {"ok": True, "messages": [{"ts": row["ts"], "text": row["text"],
        "user": row["author_provider_id"]} for row in rows], "has_more": more}


def indexed(monkeypatch, rows):
    store = current_store()
    org = store.upsert_organization("example-corp.com")
    role = store.create_role(org.id, "CRO")
    person = store.ensure_officeholder(org.id)
    tenure = store.open_tenure(role.id, person.id, date.today())
    store.set_active_role(role.id)
    records = service.build_indexed_chunks(role.id, tenure.id, person.id, "slack", rows, metadata_only=True)
    store.upsert_chunks(records)
    monkeypatch.setattr(service, "use_fixtures", lambda: False)
    monkeypatch.setattr(service, "connector_token", lambda *args: "synthetic-grant")
    monkeypatch.setenv("SLACK_POLICY_APPROVED", "true")
    return store, role, records


@pytest.fixture(autouse=True)
def no_real_requests(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: pytest.fail("Only synthetic provider requests allowed"))
    monkeypatch.delenv("WISDOMTWIN_ALLOW_PAID_MODEL_APIS", raising=False)
    monkeypatch.delenv("SLACK_HISTORY_RATE_CLASS", raising=False)


def test_one_history_read_revalidates_multiple_selected_messages(monkeypatch):
    rows = [source("CBATCH", i, f"Acme pipeline phase {i}") for i in (1, 2, 3)]
    store, role, _ = indexed(monkeypatch, rows)
    calls = []

    def request(url, token):
        params = parse_qs(urlsplit(url).query)
        calls.append(params)
        assert token == "synthetic-grant"
        if params["limit"] == ["1"]:
            return body([row for row in rows if row["ts"] == params["oldest"][0]])
        return body(rows)

    monkeypatch.setattr(connectors, "_request_json", request)
    result = service.query_twin("Acme pipeline phase")
    assert len(result["citations"]) == 3
    assert len(calls) == 1, "Selected messages in one channel must share a current-access read"
    assert calls[0]["limit"] == ["15"]
    assert all(row.excerpt == "" for row in store.chunks_for_role(role.id))


@pytest.mark.parametrize("failure", ["outage", "rate-limit"])
def test_verified_evidence_can_answer_with_explicit_partial_coverage(monkeypatch, failure):
    good = source("CVALID", 1, "Acme pipeline approved stage 3")
    bad = source("CFAILED", 2, "Acme pipeline unavailable secret fixture detail")
    store, role, _ = indexed(monkeypatch, [good, bad])

    def refetch(token, uri):
        if uri == good["uri"]:
            return good
        if failure == "rate-limit":
            kind = getattr(connectors, "SourceRateLimited")
            raise kind(60)
        raise RuntimeError("synthetic-private-provider-detail")

    monkeypatch.setattr(connectors, "refetch_slack", refetch)
    result = service.query_twin("Acme pipeline stage")
    assert "approved stage 3" in result["answer"]
    assert "partial source coverage" in result["answer"].lower()
    assert "retry" in result["answer"].lower()
    if failure == "rate-limit":
        assert "60" in result["answer"]
    assert [item["uri"] for item in result["citations"]] == [good["uri"]]
    assert bad["text"] not in result["answer"]
    assert "synthetic-private-provider-detail" not in result["answer"]
    assert all(row.excerpt == "" for row in store.chunks_for_role(role.id))


def test_no_verified_evidence_reports_outage_instead_of_empty_context(monkeypatch):
    indexed(monkeypatch, [source("CFAILED", 1, "Acme pipeline unseen source")])
    monkeypatch.setattr(connectors, "refetch_slack", lambda *a: (_ for _ in ()).throw(RuntimeError("private outage")))
    with pytest.raises(CodedToolError, match="CONNECTOR_FAILED") as caught:
        service.query_twin("Acme pipeline stage")
    assert "retry" in str(caught.value).lower()
    assert "private outage" not in str(caught.value)


def test_failed_relevant_source_is_not_hidden_by_unrelated_verified_content(monkeypatch):
    good = source("CVALID", 1, "Zenith renewal approved")
    bad = source("CFAILED", 2, "Acme pipeline unseen source")
    _, _, records = indexed(monkeypatch, [good, bad])
    from retrieval import RankedChunk
    monkeypatch.setattr(service, "hybrid_search", lambda *a, **k: [RankedChunk(record, 1) for record in records])
    monkeypatch.setattr(connectors, "refetch_slack", lambda token, uri:
        good if uri == good["uri"] else (_ for _ in ()).throw(RuntimeError("private outage")))
    with pytest.raises(CodedToolError, match="CONNECTOR_FAILED"):
        service.query_twin("Acme pipeline stage")


def test_missing_batch_page_is_uncertain_coverage_not_a_deletion_claim(monkeypatch):
    first = source("CBATCH", 1, "Acme pipeline phase alpha")
    later = source("CBATCH", 100, "Acme pipeline phase omega")
    indexed(monkeypatch, [first, later])
    monkeypatch.setattr(connectors, "_request_json", lambda *a: body([first], more=True))
    result = service.query_twin("Acme pipeline phase")
    assert "partial source coverage" in result["answer"].lower()
    assert [item["uri"] for item in result["citations"]] == [first["uri"]]
    assert "phase omega" not in result["answer"]


def test_thread_messages_share_one_current_access_reply_read(monkeypatch):
    rows = [source("CTHREAD", i, f"Acme pipeline phase {i}") for i in (1, 2, 3)]
    for row in rows:
        row["uri"] += "?thread_ts=1699999999.000001"
    indexed(monkeypatch, rows)
    calls = []
    monkeypatch.setattr(connectors, "_request_json", lambda url, token: calls.append(url) or body(rows))
    result = service.query_twin("Acme pipeline phase")
    assert len(result["citations"]) == 3
    assert len(calls) == 1
    assert urlsplit(calls[0]).path == "/api/conversations.replies"


def test_batch_still_withholds_changed_text_and_substituted_authors(monkeypatch):
    rows = [source("CBATCH", i, f"Acme pipeline phase {i}") for i in (1, 2, 3)]
    indexed(monkeypatch, rows)
    changed = body(rows)
    changed["messages"][1]["text"] = "Acme pipeline unexpected changed text"
    changed["messages"][2]["user"] = "SUBSTITUTED_AUTHOR"
    monkeypatch.setattr(connectors, "_request_json", lambda *a: changed)
    result = service.query_twin("Acme pipeline phase")
    assert [item["uri"] for item in result["citations"]] == [rows[0]["uri"]]
    assert "unexpected" not in result["answer"] and "phase 3" not in result["answer"]


def test_legacy_raw_chunk_cannot_piggyback_on_fresh_chunk_of_same_source(monkeypatch):
    row = source("CBATCH", 1, "Acme pipeline phase qualified")
    _, _, records = indexed(monkeypatch, [row])
    legacy = replace(records[0], id=str(uuid.uuid4()), excerpt=row["text"])
    monkeypatch.setattr(connectors, "refetch_slack", lambda *a: row)
    hydrated = service.hydrate_sources([records[0], legacy])
    assert [item.id for item in hydrated] == [records[0].id]


def test_service_uses_verified_workspace_binding_across_members(monkeypatch):
    from security_store import security_store
    from store import actor_subject

    subjects = [security_store().provision(issuer="https://synthetic-pacing.test", provider_subject=uuid.uuid4().hex,
        email="reviewer@example-corp.com", domain="example-corp.com", roles=["CRO"],
        slack_team_id="SHARED_TEAM", slack_user_id="SYNTHETIC_USER") for _ in range(2)]
    monkeypatch.setattr(service, "use_fixtures", lambda: False)
    monkeypatch.setenv("SLACK_CLIENT_ID", "SHARED_APP")
    monkeypatch.setattr(time, "time", lambda: 1700000000.0)
    calls = []
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: calls.append(True) or io.BytesIO(b'{"ok":true}'))
    url = "https://slack.com/api/conversations.history?channel=C1"
    actor = actor_subject.set(subjects[0])
    try:
        with service.source_rate_context("slack"):
            connectors._request_json(url, "synthetic-user-one")
        actor_subject.set(subjects[1])
        with service.source_rate_context("slack"):
            with pytest.raises(connectors.SourceRateLimited) as caught:
                connectors._request_json(url, "synthetic-user-two")
        assert caught.value.retry_after_seconds == 60
        assert len(calls) == 1
    finally:
        actor_subject.reset(actor)


@pytest.mark.parametrize("backend", ["sqlite", "postgres"])
def test_cooldown_reservation_is_atomic_across_independent_stores(monkeypatch, tmp_path, backend):
    from security_store import SecurityStore

    if backend == "postgres":
        url = os.environ.get("WISDOMTWIN_TEST_DATABASE_URL", "").strip()
        if not url:
            pytest.skip("Requires explicitly configured isolated synthetic PostgreSQL")
        if urlsplit(url).hostname not in {"localhost", "127.0.0.1", "::1"} or not urlsplit(url).path.endswith("_test"):
            pytest.fail("Pacing tests require an isolated loopback *_test database")
        options = {"database_url": url}
    else:
        options = {"sqlite_path": str(tmp_path / "pacing.sqlite3")}
    db = SecurityStore(**options)
    key = json.dumps(["SYNTHETIC_APP", uuid.uuid4().hex, "conversations.history"])
    monkeypatch.setattr(time, "time", lambda: 1700000000.0)
    ready = threading.Barrier(4)

    def reserve():
        other = SecurityStore(**options)
        ready.wait(timeout=5)
        return other.reserve_provider_request(key, 60)

    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(lambda _: reserve(), range(4)))
        assert sorted(results) == [0, 60, 60, 60]
        other = SecurityStore(**options)
        other.extend_provider_cooldown(key, 120)
        db.extend_provider_cooldown(key, 30)
        assert db.reserve_provider_request(key, 60) == 120
        with db.connection() as connection:
            stored = db.execute(connection, "SELECT key_hash,payload,subject,family FROM security_entries WHERE kind='provider_rate' AND key_hash=?",
                                (hashlib.sha256(key.encode()).hexdigest(),)).fetchone()
        assert key not in str(stored) and "conversations.history" not in str(stored)
        assert stored[2:] == ("", "")
    finally:
        with db.connection() as connection:
            db.execute(connection, "DELETE FROM security_entries WHERE kind='provider_rate' AND key_hash=?",
                       (hashlib.sha256(key.encode()).hexdigest(),))


def test_restricted_pacing_is_per_app_workspace_method_across_user_tokens(monkeypatch):
    context = getattr(connectors, "slack_rate_context", None)
    assert context is not None, "Current-access reads need a durable provider rate context"
    clock = [1700000000.0]
    monkeypatch.setattr(time, "time", lambda: clock[0])
    calls = []
    monkeypatch.setattr("urllib.request.urlopen", lambda request, **k: calls.append(request.full_url) or io.BytesIO(b'{"ok":true}'))
    history = "https://slack.com/api/conversations.history?channel=C1"
    replies = "https://slack.com/api/conversations.replies?channel=C1&ts=1700000000.000001"
    with context(team_id="SYNTHETIC_TEAM", app_id="SYNTHETIC_APP"):
        assert connectors._request_json(history, "synthetic-user-one")["ok"]
        with pytest.raises(connectors.SourceRateLimited) as caught:
            connectors._request_json(history, "synthetic-user-two")
        assert caught.value.retry_after_seconds == pytest.approx(60)
        assert connectors._request_json(replies, "synthetic-user-two")["ok"]
    with context(team_id="OTHER_TEAM", app_id="SYNTHETIC_APP"):
        assert connectors._request_json(history, "synthetic-user-two")["ok"]
    clock[0] += 60
    with context(team_id="SYNTHETIC_TEAM", app_id="SYNTHETIC_APP"):
        assert connectors._request_json(history, "synthetic-user-two")["ok"]
    assert len(calls) == 4


def test_long_retry_after_is_durable_without_text_or_token_storage(monkeypatch):
    context = getattr(connectors, "slack_rate_context", None)
    assert context is not None
    clock = [1700000000.0]
    monkeypatch.setattr(time, "time", lambda: clock[0])
    calls = []
    url = "https://slack.com/api/conversations.history?channel=C1"
    headers = Message()
    headers["Retry-After"] = "120"

    def limited(request, **kwargs):
        calls.append(request.full_url)
        raise urllib.error.HTTPError(url, 429, "private-provider-detail", headers, None)

    monkeypatch.setattr("urllib.request.urlopen", limited)
    with context(team_id="SYNTHETIC_TEAM", app_id="SYNTHETIC_APP"):
        with pytest.raises(connectors.SourceRateLimited) as first:
            connectors._request_json(url, "synthetic-user-one")
    clock[0] += 1
    with context(team_id="SYNTHETIC_TEAM", app_id="SYNTHETIC_APP"):
        with pytest.raises(connectors.SourceRateLimited) as second:
            connectors._request_json(url, "synthetic-user-two")
    assert first.value.retry_after_seconds == 120
    assert second.value.retry_after_seconds == pytest.approx(119)
    assert len(calls) == 1, "A later process/request must honor the provider's current cooldown"
    assert "private-provider-detail" not in str(second.value)


def test_success_after_bounded_retry_keeps_full_shared_method_interval(monkeypatch):
    clock = [1700000000.0]
    waits, calls = [], []
    monkeypatch.setattr(time, "time", lambda: clock[0])

    def wait(delay):
        waits.append(delay)
        clock[0] += delay

    monkeypatch.setattr(time, "sleep", wait)
    headers = Message()
    headers["Retry-After"] = "1"
    url = "https://slack.com/api/conversations.history?channel=C1"

    def request(*a, **k):
        calls.append(True)
        if len(calls) == 1:
            raise urllib.error.HTTPError(url, 429, "private-provider-detail", headers, None)
        return io.BytesIO(b'{"ok":true}')

    monkeypatch.setattr("urllib.request.urlopen", request)
    with connectors.slack_rate_context(team_id="SYNTHETIC_TEAM", app_id="SYNTHETIC_APP"):
        assert connectors._request_json(url, "synthetic-user-one")["ok"]
        with pytest.raises(connectors.SourceRateLimited) as caught:
            connectors._request_json(url, "synthetic-user-two")
    assert caught.value.retry_after_seconds == 60
    assert calls == [True, True] and waits == [1]
