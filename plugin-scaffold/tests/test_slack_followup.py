"""Synthetic Slack thread deletion and bounded HTTP 429 retry regressions."""

from datetime import date, datetime, timezone
from email.message import Message
from email.utils import format_datetime
import io
import json
import time
from types import SimpleNamespace
import urllib.error
from urllib.parse import parse_qs, urlsplit

import pytest

import connectors
from errors import CodedToolError
import service
from store import current_store


SLACK_API = "https://slack.com/api/conversations.replies?channel=CDELETED&ts=1700000000.000001"
MESSAGE_TS = "1700000000.000001"
VALID_URI = "https://example.slack.com/archives/CVALID/p1700000000000001"
DELETED_URI = "https://example.slack.com/archives/CDELETED/p1700000000000001"
VALID_SOURCE = {"uri": VALID_URI, "text": "Acme pipeline approved stage 3", "author_provider_id": "AUTHOR_VALID"}
FIXED_NOW = datetime(2026, 10, 1, 12, tzinfo=timezone.utc).timestamp()


@pytest.fixture(autouse=True)
def offline_clock_and_requests(monkeypatch):
    waits = []

    def forbid_network(*args, **kwargs):
        pytest.fail("Slack follow-up tests must never use the network")

    monkeypatch.setattr("urllib.request.urlopen", forbid_network)
    monkeypatch.setattr(time, "time", lambda: FIXED_NOW)
    monkeypatch.setattr(time, "sleep", lambda seconds: waits.append(seconds))
    monkeypatch.delenv("WISDOMTWIN_ALLOW_PAID_MODEL_APIS", raising=False)
    return waits


def deleted_uri(thread_reference):
    return DELETED_URI + ("?thread_ts=1699999999.000002&cid=CDELETED" if thread_reference else "")


def message_body(source):
    return {"ok": True, "messages": [{"ts": MESSAGE_TS, "text": source["text"],
        "user": source["author_provider_id"]}]}


def indexed_sources(monkeypatch, sources):
    store = current_store()
    org = store.upsert_organization("example-corp.com")
    person = store.ensure_officeholder(org.id)
    role = store.create_role(org.id, "CRO")
    tenure = store.open_tenure(role.id, person.id, date.today())
    store.set_active_role(role.id)
    records = service.build_indexed_chunks(role.id, tenure.id, tenure.person_id, "slack", sources, metadata_only=True)
    store.upsert_chunks(records)
    # The real-source query branch is exercised under the synthetic loopback
    # identity; credentials and all provider responses are offline mocks.
    monkeypatch.setattr(service, "use_fixtures", lambda: False)
    monkeypatch.setattr(service, "connector_token", lambda *args: "offline-scoped-grant")
    monkeypatch.setenv("SLACK_POLICY_APPROVED", "true")
    monkeypatch.setattr(service, "hybrid_search", lambda *args, **kwargs:
        [SimpleNamespace(chunk=record) for record in records])
    return store, role, records


def thread_response(provider_error, requested):
    def response(url, token):
        parsed = urlsplit(url)
        channel = parse_qs(parsed.query)["channel"][0]
        requested.append((channel, parsed.path))
        if channel == "CVALID":
            return message_body(VALID_SOURCE)
        if parsed.path.endswith("conversations.history"):
            return {"ok": True, "messages": []}
        assert parsed.path.endswith("conversations.replies")
        return {"ok": False, "error": provider_error}

    return response


@pytest.mark.parametrize("thread_reference", [True, False], ids=["explicit-thread", "history-fallback"])
def test_deleted_slack_thread_does_not_hide_other_valid_sources(monkeypatch, thread_reference):
    failed_uri = deleted_uri(thread_reference)
    deleted = {"uri": failed_uri, "text": "Acme pipeline obsolete thread data", "author_provider_id": "AUTHOR_DELETED"}
    store, role, records = indexed_sources(monkeypatch, [deleted, VALID_SOURCE])
    requested = []
    monkeypatch.setattr(connectors, "_request_json", thread_response("thread_not_found", requested))
    result = service.query_twin("Acme pipeline stage")
    assert "approved stage 3" in result["answer"]
    assert "obsolete thread data" not in result["answer"]
    assert [citation["uri"] for citation in result["citations"]] == [VALID_URI]
    assert ("CDELETED", "/api/conversations.replies") in requested
    if not thread_reference:
        assert ("CDELETED", "/api/conversations.history") in requested
    assert all(record.excerpt == "" for record in store.chunks_for_role(role.id))


@pytest.mark.parametrize("thread_reference", [True, False], ids=["explicit-thread", "history-fallback"])
def test_deleted_slack_thread_alone_abstains_exactly(monkeypatch, thread_reference):
    source = {"uri": deleted_uri(thread_reference), "text": "Acme pipeline obsolete thread data",
        "author_provider_id": "AUTHOR_DELETED"}
    indexed_sources(monkeypatch, [source])
    requested = []
    monkeypatch.setattr(connectors, "_request_json", thread_response("thread_not_found", requested))
    assert service.query_twin("Acme pipeline stage") == {
        "answer": "I have nothing ingested on that.", "citations": []}


@pytest.mark.parametrize("thread_reference", [True, False], ids=["explicit-thread", "history-fallback"])
def test_reply_provider_outage_is_a_coded_failure_without_partial_evidence(monkeypatch, thread_reference):
    failed = {"uri": deleted_uri(thread_reference), "text": "Acme pipeline unavailable thread data",
        "author_provider_id": "AUTHOR_DELETED"}
    # Valid evidence is hydrated first; a later outage must not return it as a
    # partial answer or classify the unavailable thread as permanently deleted.
    indexed_sources(monkeypatch, [VALID_SOURCE, failed])
    requested = []
    monkeypatch.setattr(connectors, "_request_json", thread_response("internal_error", requested))
    monkeypatch.setattr(service, "answer_from_context", lambda *args: pytest.fail("Outage must prevent evidence output"))
    with pytest.raises(CodedToolError, match="CONNECTOR_FAILED") as caught:
        service.query_twin("Acme pipeline stage")
    assert "retry" in str(caught.value).lower()
    assert VALID_SOURCE["text"] not in str(caught.value)
    assert "unavailable thread data" not in str(caught.value)
    assert ("CDELETED", "/api/conversations.replies") in requested


def rate_limited(retry_after):
    headers = Message()
    headers["Retry-After"] = retry_after
    return urllib.error.HTTPError(SLACK_API, 429, "synthetic rate limit", headers, None)


def scripted_urlopen(monkeypatch, steps):
    pending = list(steps)
    calls = []

    def urlopen(request, timeout):
        calls.append((request.full_url, timeout, request.get_header("Authorization")))
        assert timeout == 30
        assert request.get_header("Authorization") == "Bearer offline-scoped-grant"
        assert pending, "Retry exceeded the bounded attempt count"
        step = pending.pop(0)
        if isinstance(step, Exception):
            raise step
        return io.BytesIO(json.dumps(step).encode())

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    return calls, pending


def http_date(seconds):
    return format_datetime(datetime.fromtimestamp(FIXED_NOW + seconds, tz=timezone.utc), usegmt=True)


@pytest.mark.parametrize("seconds", [1, 2])
def test_short_numeric_retry_after_waits_once_then_returns_response(monkeypatch, offline_clock_and_requests, seconds):
    calls, pending = scripted_urlopen(monkeypatch, [rate_limited(str(seconds)), {"ok": True, "messages": []}])
    assert connectors._request_json(SLACK_API, "offline-scoped-grant") == {"ok": True, "messages": []}
    assert offline_clock_and_requests == [seconds]
    assert len(calls) == 2 and not pending


def test_short_http_date_retry_after_uses_the_current_utc_clock(monkeypatch, offline_clock_and_requests):
    calls, pending = scripted_urlopen(monkeypatch, [rate_limited(http_date(1)), {"ok": True}])
    assert connectors._request_json(SLACK_API, "offline-scoped-grant") == {"ok": True}
    assert offline_clock_and_requests == [pytest.approx(1)]
    assert len(calls) == 2 and not pending


@pytest.mark.parametrize("retry_after,seconds", [("3", 3), ("60", 60), (http_date(3), 3), (http_date(60), 60)],
    ids=["numeric-above-bound", "numeric-long", "http-date-above-bound", "http-date-long"])
def test_excessive_retry_after_never_blocks_or_retries(monkeypatch, offline_clock_and_requests, retry_after, seconds):
    calls, pending = scripted_urlopen(monkeypatch, [rate_limited(retry_after), {"ok": True}])
    with pytest.raises(RuntimeError) as caught:
        connectors._request_json(SLACK_API, "offline-scoped-grant")
    expected_type = getattr(connectors, "SourceRateLimited", None)
    assert expected_type is not None and isinstance(caught.value, expected_type)
    assert caught.value.retry_after_seconds == pytest.approx(seconds)
    assert offline_clock_and_requests == []
    assert len(calls) == 1 and len(pending) == 1


@pytest.mark.parametrize("second_delay", [1, 60], ids=["repeated-short", "repeated-long"])
def test_repeated_429_retries_only_once_and_preserves_retry_guidance(monkeypatch, offline_clock_and_requests, second_delay):
    calls, pending = scripted_urlopen(monkeypatch,
        [rate_limited("1"), rate_limited(str(second_delay)), {"ok": True}])
    with pytest.raises(RuntimeError) as caught:
        connectors._request_json(SLACK_API, "offline-scoped-grant")
    expected_type = getattr(connectors, "SourceRateLimited", None)
    assert expected_type is not None and isinstance(caught.value, expected_type)
    assert caught.value.retry_after_seconds == pytest.approx(second_delay)
    assert offline_clock_and_requests == [1]
    assert len(calls) == 2 and len(pending) == 1


@pytest.mark.parametrize("retry_headers,expected_delay,expected_waits", [
    (["60"], 60, []), (["1", "1"], 1, [1]),
], ids=["excessive-delay", "repeated-429"])
def test_rate_limit_failure_has_safe_guidance_and_returns_no_evidence(monkeypatch, offline_clock_and_requests,
    retry_headers, expected_delay, expected_waits):
    failed = {"uri": deleted_uri(True), "text": "Acme pipeline rate-limited thread data",
        "author_provider_id": "AUTHOR_DELETED"}
    store, role, records = indexed_sources(monkeypatch, [VALID_SOURCE, failed])
    pending = [rate_limited(header) for header in retry_headers]
    requested = []

    def urlopen(request, timeout):
        assert timeout == 30
        params = parse_qs(urlsplit(request.full_url).query)
        requested.append(params["channel"][0])
        if params["channel"] == ["CVALID"]:
            return io.BytesIO(json.dumps(message_body(VALID_SOURCE)).encode())
        assert pending, "429 was retried more than once"
        raise pending.pop(0)

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    monkeypatch.setattr(service, "answer_from_context", lambda *args: pytest.fail("429 must prevent evidence output"))
    with pytest.raises(CodedToolError, match="CONNECTOR_FAILED") as caught:
        service.query_twin("Acme pipeline stage")
    error = str(caught.value).lower()
    assert "retry" in error and str(expected_delay) in error
    assert VALID_SOURCE["text"].lower() not in error
    assert failed["text"].lower() not in error
    assert requested[0] == "CVALID" and len(requested) == 1 + len(retry_headers)
    assert offline_clock_and_requests == expected_waits
    assert all(record.excerpt == "" for record in store.chunks_for_role(role.id))
