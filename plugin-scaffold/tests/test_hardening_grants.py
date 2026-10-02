"""Offline grant lifetime, bounded source re-fetch and Gmail link regressions (H1, H2, M5, L3).

Also the review follow-ups: G1 and F1 (the fetch budget goes to candidates that
can support the question, and an exhausted budget is never "nothing ingested"),
G2 (a provider-side grant rejection is a reconnect) and G6 (an unreadable stored
grant is a reconnect).
"""

from dataclasses import replace
from datetime import date
from email.message import Message
import hashlib
import hmac
import io
import json
import socket
import time
from types import SimpleNamespace
import urllib.error
from urllib.parse import parse_qs, urlsplit

import pytest
from cryptography.fernet import Fernet
from mcp.server.auth.provider import AccessToken

import connectors
import ingest
import provider_binding
import runtime
import service
from errors import CodedToolError
from oauth_connectors import GMAIL_SCOPE, SLACK_USER_SCOPES, public_base_url
from retrieval import _terms
from security_store import security_store
from store import actor_subject, current_store
from tokens import decrypt_token, encrypt_token


ISSUER = "https://identity.synthetic.test"
EMAIL = "alice@example-corp.com"
SLACK_TOKEN = "synthetic-slack-token"
GOOGLE_TOKEN = "synthetic-google-token"
MESSAGE_TS = "1700000000.000001"
T0 = 1_790_000_000.0
HOUR = 3600
QUESTION = "What is the Acme pipeline stage?"
SLACK_RECONNECT = "OAUTH_PENDING: Reconnect Slack with connect_business_account to restore cited answers."
GMAIL_RECONNECT = "OAUTH_PENDING: Reconnect Gmail with connect_business_account to restore cited answers."
DRIVE_RECONNECT = "OAUTH_PENDING: Reconnect Google Drive with connect_business_account to restore cited answers."
SOURCE_CHECK_LIMIT = ("CONNECTOR_FAILED: No supporting source verified within this query's source-check limit. "
                      "Ask a narrower question or retry.")
EMPTY_CONTEXT = {"answer": "I have nothing ingested on that.", "citations": []}
GMAIL_URI = "https://mail.google.com/mail/#all/MSG_A"
LEGACY_GMAIL_URI = "https://mail.google.com/mail/u/0/#inbox/MSG_A"
GMAIL_DETAIL = {"id": "MSG_A", "snippet": "Acme pipeline stage 3 budget approved", "labelIds": ["INBOX"],
    "payload": {"headers": [{"name": "From", "value": "Bob <bob@example-corp.com>"}]}}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbid(*args, **kwargs):
        pytest.fail("Grant hardening tests must never use the network")

    monkeypatch.setattr("urllib.request.urlopen", forbid)
    monkeypatch.setattr(socket, "create_connection", forbid)
    monkeypatch.setattr(socket, "getaddrinfo", forbid)
    monkeypatch.setattr(provider_binding, "request_json", forbid)
    monkeypatch.setattr(time, "sleep", lambda seconds: pytest.fail("No test may wait on a provider"))
    monkeypatch.delenv("WISDOMTWIN_ALLOW_PAID_MODEL_APIS", raising=False)
    monkeypatch.delenv("WISDOMTWIN_MAX_SOURCE_FETCHES", raising=False)


@pytest.fixture
def clock(monkeypatch):
    now = SimpleNamespace(value=T0)
    monkeypatch.setattr(time, "time", lambda: now.value)
    return now


@pytest.fixture
def member(monkeypatch):
    """A provisioned corporate member signed in with a real-source (not fixture) namespace."""
    monkeypatch.setenv("WISDOMTWIN_AUTH_DISABLED", "0")
    monkeypatch.setenv("SLACK_POLICY_APPROVED", "true")
    monkeypatch.setattr(service, "use_fixtures", lambda: False)
    subject = security_store().provision(issuer=ISSUER, provider_subject="alice", email=EMAIL,
        domain="example-corp.com", roles=["CRO"], slack_team_id="TEAM_A", slack_user_id="USER_A",
        google_subject="GOOGLE_A")
    token = AccessToken(token="offline-identity", client_id="wisdomtwin-local", scopes=["twin:read"],
        resource=f"{public_base_url()}/mcp", subject=subject)
    monkeypatch.setattr("mcp.server.auth.middleware.auth_context.get_access_token", lambda: token)
    context = actor_subject.set(subject)
    try:
        store = current_store()
        org = store.upsert_organization("example-corp.com")
        person = store.ensure_officeholder(org.id)
        role = store.create_role(org.id, "CRO")
        tenure = store.open_tenure(role.id, person.id, date.today())
        store.set_active_role(role.id)
        yield SimpleNamespace(subject=subject, store=store, org=org, role=role, tenure=tenure,
                              membership=security_store().membership(subject))
    finally:
        actor_subject.reset(context)


def enable_gmail(monkeypatch):
    monkeypatch.setenv("GMAIL_CONNECTOR_ENABLED", "true")
    monkeypatch.setenv("GOOGLE_REVIEW_APPROVED", "true")


def pending(ns, service_name):
    return {"subject": ns.subject, "role_id": ns.role.id, "domain": ns.org.domain,
            "role_title": ns.role.title, "service": service_name}


def slack_body(**user_fields):
    return {"ok": True, "team": {"id": "TEAM_A"}, "authed_user": {"id": "USER_A", "access_token": SLACK_TOKEN,
        "scope": ",".join(SLACK_USER_SCOPES), **user_fields}}


def slack_identity(url, *, token):
    assert token == SLACK_TOKEN
    if url == "https://slack.com/api/auth.test":
        return {"ok": True, "team_id": "TEAM_A", "user_id": "USER_A"}
    assert url.startswith("https://slack.com/api/users.info?")
    return {"ok": True, "user": {"id": "USER_A", "profile": {"email": EMAIL}}}


def bind_slack(ns, monkeypatch, **user_fields):
    monkeypatch.setattr(provider_binding, "request_json", slack_identity)
    provider_binding.bind_slack(pending(ns, "slack"), ns.membership, slack_body(**user_fields))


def bind_gmail(ns, monkeypatch, expires_in=3599):
    def identity(url, *, token):
        assert token == GOOGLE_TOKEN and url == "https://openidconnect.googleapis.com/v1/userinfo"
        return {"sub": "GOOGLE_A", "email": EMAIL, "email_verified": True}

    monkeypatch.setattr(provider_binding, "request_json", identity)
    provider_binding.bind_google(pending(ns, "gmail"), ns.membership, {
        "access_token": GOOGLE_TOKEN, "scope": f"openid email {GMAIL_SCOPE}", "expires_in": expires_in})


def stored_grant(ns, service_name):
    return json.loads(decrypt_token(ns.store.get_credential(ns.role.id, service_name)))


def slack_source(index, text=None):
    channel = f"C{index:02d}"
    return {"uri": f"https://example.slack.com/archives/{channel}/p1700000000000001",
            "text": text or f"Acme pipeline stage {index} approved", "author_provider_id": f"AUTHOR_{index:02d}"}


def index_sources(ns, sources, provider="slack"):
    records = service.build_indexed_chunks(ns.role.id, ns.tenure.id, ns.tenure.person_id, provider, sources,
                                           metadata_only=True)
    ns.store.upsert_chunks(records)
    return records


def rank_in_order(monkeypatch, records):
    monkeypatch.setattr(service, "hybrid_search", lambda *args, **kwargs:
        [SimpleNamespace(chunk=record) for record in records])


def rate_limited(url, retry_after="60"):
    headers = Message()
    headers["Retry-After"] = retry_after
    return urllib.error.HTTPError(url, 429, "synthetic rate limit", headers, None)


class FakeSlack:
    """Offline conversations.history: one message per channel, with scripted denials, limits and outages.

    ``rejected`` maps a channel to the Slack error code its request returns.
    """

    def __init__(self, sources, *, deleted=(), limited=(), broken=(), rejected=None):
        self.sources = {urlsplit(source["uri"]).path.split("/")[2]: source for source in sources}
        self.deleted, self.limited, self.broken = set(deleted), set(limited), set(broken)
        self.rejected = dict(rejected or {})
        self.calls = []

    def urlopen(self, request, timeout):
        parsed = urlsplit(request.full_url)
        assert parsed.netloc == "slack.com" and parsed.path == "/api/conversations.history"
        assert request.get_header("Authorization") == f"Bearer {SLACK_TOKEN}"
        channel = parse_qs(parsed.query)["channel"][0]
        self.calls.append(channel)
        if channel in self.limited:
            raise rate_limited(request.full_url)
        if channel in self.rejected:
            body = {"ok": False, "error": self.rejected[channel]}
        elif channel in self.deleted:
            body = {"ok": False, "error": "channel_not_found"}
        elif channel in self.broken:
            body = {"ok": False, "error": "internal_error"}
        else:
            source = self.sources[channel]
            body = {"ok": True, "messages": [{"ts": MESSAGE_TS, "text": source["text"],
                                              "user": source["author_provider_id"]}]}
        return io.BytesIO(json.dumps(body).encode())


def serve_slack(monkeypatch, sources, **script):
    fake = FakeSlack(sources, **script)
    monkeypatch.setattr("urllib.request.urlopen", fake.urlopen)
    return fake


def serve_gmail(monkeypatch, calls):
    def urlopen(request, timeout):
        assert request.get_header("Authorization") == f"Bearer {GOOGLE_TOKEN}"
        assert request.full_url == "https://gmail.googleapis.com/gmail/v1/users/me/messages/MSG_A?format=metadata"
        calls.append(request.full_url)
        return io.BytesIO(json.dumps(GMAIL_DETAIL).encode())

    monkeypatch.setattr("urllib.request.urlopen", urlopen)


def cited(result):
    return [citation["uri"] for citation in result["citations"]]


# H1: grant lifetime follows the provider, and a lapsed grant asks for a reconnect.

def test_slack_grant_without_expires_in_stays_valid_after_25_hours(member, monkeypatch, clock):
    bind_slack(member, monkeypatch)
    assert stored_grant(member, "slack")["expires_at"] is None
    source = slack_source(1)
    index_sources(member, [source])
    clock.value = T0 + 25 * HOUR
    assert service.connector_token(member.role.id, "slack") == SLACK_TOKEN
    fake = serve_slack(monkeypatch, [source])
    result = service.query_twin(QUESTION)
    assert "stage 1 approved" in result["answer"]
    assert cited(result) == [source["uri"]]
    assert fake.calls == ["C01"]


def test_rotating_slack_grant_honors_the_provider_lifetime(member, monkeypatch, clock):
    bind_slack(member, monkeypatch, expires_in=12 * HOUR)
    assert stored_grant(member, "slack")["expires_at"] == T0 + 12 * HOUR
    index_sources(member, [slack_source(1)])
    clock.value = T0 + 12 * HOUR - 1
    assert service.connector_token(member.role.id, "slack") == SLACK_TOKEN
    clock.value = T0 + 12 * HOUR
    with pytest.raises(service.GrantUnavailable):
        service.connector_token(member.role.id, "slack")
    with pytest.raises(CodedToolError) as caught:
        service.query_twin(QUESTION)
    assert str(caught.value) == SLACK_RECONNECT


@pytest.mark.parametrize("lifetime", ["soon", [3600], {"seconds": 3600}, float("inf")])
def test_malformed_provider_lifetime_stores_no_grant(member, monkeypatch, lifetime):
    with pytest.raises(ValueError):
        bind_slack(member, monkeypatch, expires_in=lifetime)
    assert member.store.get_credential(member.role.id, "slack") is None


def test_google_grant_works_until_its_hour_then_query_asks_for_reconnect(member, monkeypatch, clock):
    enable_gmail(monkeypatch)
    bind_gmail(member, monkeypatch)
    assert stored_grant(member, "gmail")["expires_at"] == T0 + 3599
    index_sources(member, [{"uri": GMAIL_URI, "text": GMAIL_DETAIL["snippet"],
                            "author_provider_id": "bob@example-corp.com"}], provider="gmail")
    calls = []
    serve_gmail(monkeypatch, calls)
    clock.value = T0 + 10 * 60
    result = service.query_twin(QUESTION)
    assert "budget approved" in result["answer"] and cited(result) == [GMAIL_URI]
    assert len(calls) == 1
    clock.value = T0 + HOUR
    with pytest.raises(CodedToolError) as caught:
        service.query_twin(QUESTION)
    assert str(caught.value) == GMAIL_RECONNECT
    assert len(calls) == 1, "An expired grant must never reach the provider"
    assert all(chunk.excerpt == "" for chunk in member.store.chunks_for_role(member.role.id))


def test_expired_google_grant_fails_the_ingest_tool_before_queueing(member, monkeypatch, clock):
    enable_gmail(monkeypatch)
    bind_gmail(member, monkeypatch)
    clock.value = T0 + HOUR
    monkeypatch.setattr(ingest, "fetch_gmail", lambda *args: pytest.fail("No fetch without a current grant"))
    with pytest.raises(CodedToolError) as caught:
        service.ingest_data("gmail", "budget", 10)
    assert str(caught.value) == "OAUTH_PENDING: Reconnect Gmail with connect_business_account before ingesting again."
    assert member.store.jobs_for_role(member.role.id) == []


def test_grant_lapsing_while_queued_fails_the_job_without_a_celery_retry(member, monkeypatch, clock):
    enable_gmail(monkeypatch)
    bind_gmail(member, monkeypatch)
    retries = []

    def retry(**kwargs):
        retries.append(kwargs)
        return RuntimeError("synthetic retry scheduled")

    monkeypatch.setattr(ingest.ingest_job, "retry", retry)
    monkeypatch.setattr(ingest, "fetch_gmail", lambda *args: pytest.fail("No fetch without a current grant"))
    job = member.store.create_job(member.role.id, "gmail", "budget", 10)
    clock.value = T0 + HOUR
    with pytest.raises(CodedToolError) as caught:
        ingest.ingest_job(job.id, member.subject)
    assert caught.value.code == "OAUTH_PENDING"
    assert "Reconnect Gmail with connect_business_account" in str(caught.value)
    assert retries == []
    assert member.store.get_job(job.id).status == "failed"


def test_real_provider_outage_still_retries_with_a_current_grant(member, monkeypatch, clock):
    enable_gmail(monkeypatch)
    bind_gmail(member, monkeypatch)
    retries = []

    def retry(**kwargs):
        retries.append(kwargs)
        return RuntimeError("synthetic retry scheduled")

    def outage(token, query, max_items):
        assert token == GOOGLE_TOKEN
        raise RuntimeError("synthetic provider outage")

    monkeypatch.setattr(ingest.ingest_job, "retry", retry)
    monkeypatch.setattr(ingest, "fetch_gmail", outage)
    job = member.store.create_job(member.role.id, "gmail", "budget", 10)
    with pytest.raises(RuntimeError, match="synthetic retry scheduled"):
        ingest.ingest_job(job.id, member.subject)
    assert len(retries) == 1 and retries[0]["countdown"] == 30
    assert member.store.get_job(job.id).status == "failed"


def credential(ns, service_name, **overrides):
    payload = {"access_token": "synthetic-direct-token", "subject": ns.subject, "role_id": ns.role.id,
               "service": service_name, "expires_at": None, "team_id": "TEAM_A", "user_id": "USER_A",
               "provider_subject": "GOOGLE_A", **overrides}
    payload = {key: value for key, value in payload.items() if value is not ...}
    ns.store.save_credential(ns.role.id, service_name, encrypt_token(json.dumps(payload)))


@pytest.mark.parametrize("service_name,overrides", [
    ("slack", {"team_id": "TEAM_B"}), ("slack", {"user_id": "USER_B"}),
    ("slack", {"subject": "another-subject"}), ("slack", {"role_id": "another-role"}),
    ("slack", {"service": "gmail"}), ("slack", {"access_token": ""}),
    ("slack", {"expires_at": ...}), ("gmail", {"provider_subject": "GOOGLE_B"}),
], ids=["slack-team", "slack-user", "subject", "role", "service", "empty-token", "no-expiry-key", "google-subject"])
def test_identity_mismatch_still_yields_no_token(member, monkeypatch, service_name, overrides):
    enable_gmail(monkeypatch)
    credential(member, service_name)
    assert service.connector_token(member.role.id, service_name) == "synthetic-direct-token"
    credential(member, service_name, **overrides)
    with pytest.raises(service.GrantUnavailable):
        service.connector_token(member.role.id, service_name)


def test_reprovisioned_slack_identity_invalidates_the_stored_grant(member, monkeypatch):
    bind_slack(member, monkeypatch)
    index_sources(member, [slack_source(1)])
    security_store().provision(issuer=ISSUER, provider_subject="alice", email=EMAIL, domain="example-corp.com",
        roles=["CRO"], slack_team_id="TEAM_A", slack_user_id="USER_REPLACED", google_subject="GOOGLE_A")
    with pytest.raises(service.GrantUnavailable):
        service.connector_token(member.role.id, "slack")
    with pytest.raises(CodedToolError) as caught:
        service.query_twin(QUESTION)
    assert str(caught.value) == SLACK_RECONNECT


def test_removed_membership_is_still_an_authorization_failure(member, monkeypatch):
    bind_slack(member, monkeypatch)
    security_store().remove_member(member.subject)
    with pytest.raises(CodedToolError, match="AUTHORIZATION_REQUIRED"):
        service.connector_token(member.role.id, "slack")


def test_membership_revoked_between_grant_reads_is_an_authorization_failure(member, monkeypatch):
    bind_slack(member, monkeypatch)
    read = member.store.get_credential

    def read_then_revoke(role_id, service_name):
        ciphertext = read(role_id, service_name)
        security_store().remove_member(member.subject)
        return ciphertext

    monkeypatch.setattr(member.store, "get_credential", read_then_revoke)
    with pytest.raises(CodedToolError, match="AUTHORIZATION_REQUIRED"):
        service.connector_token(member.role.id, "slack")


def test_missing_grant_does_not_hide_other_verified_evidence(member, monkeypatch, clock):
    enable_gmail(monkeypatch)
    bind_slack(member, monkeypatch)
    gmail = index_sources(member, [{"uri": GMAIL_URI, "text": GMAIL_DETAIL["snippet"],
                                    "author_provider_id": "bob@example-corp.com"}], provider="gmail")
    source = slack_source(1)
    slack = index_sources(member, [source])
    rank_in_order(monkeypatch, gmail + slack)
    fake = serve_slack(monkeypatch, [source])
    result = service.query_twin(QUESTION)
    assert cited(result) == [source["uri"]]
    assert fake.calls == ["C01"]


def test_every_missing_service_is_named_when_nothing_verifies(member, monkeypatch):
    enable_gmail(monkeypatch)
    gmail = index_sources(member, [{"uri": GMAIL_URI, "text": GMAIL_DETAIL["snippet"],
                                    "author_provider_id": "bob@example-corp.com"}], provider="gmail")
    slack = index_sources(member, [slack_source(1)])
    rank_in_order(monkeypatch, slack + gmail)
    with pytest.raises(CodedToolError) as caught:
        service.query_twin(QUESTION)
    assert str(caught.value) == ("OAUTH_PENDING: Reconnect Slack and Gmail with connect_business_account "
                                 "to restore cited answers.")


# H2: verification is lazy, bounded and keeps evidence that verified before a provider failure.

def test_lazy_refetch_makes_at_most_three_successful_fetches_when_ten_chunks_rank(member, monkeypatch):
    bind_slack(member, monkeypatch)
    sources = [slack_source(index) for index in range(1, 11)]
    records = index_sources(member, sources)
    assert len(records) == 10
    rank_in_order(monkeypatch, records)
    fake = serve_slack(monkeypatch, sources)
    result = service.query_twin(QUESTION)
    assert fake.calls == ["C01", "C02", "C03"]
    assert cited(result) == [source["uri"] for source in sources[:3]]


def test_verified_source_that_does_not_support_the_question_is_neither_cited_nor_counted(member, monkeypatch):
    bind_slack(member, monkeypatch)
    sources = [slack_source(1, "Quarterly offsite catering menu"), *(slack_source(index) for index in range(2, 6))]
    records = index_sources(member, sources)
    rank_in_order(monkeypatch, records)
    fake = serve_slack(monkeypatch, sources)
    result = service.query_twin(QUESTION)
    # G1: its keyword hashes share no question term, so it is demoted behind the
    # supporting sources and never fetched. The demoted-but-fetched case is
    # test_rows_hashed_under_an_earlier_key_are_demoted_not_dropped.
    assert fake.calls == ["C02", "C03", "C04"]
    assert cited(result) == [source["uri"] for source in sources[1:4]]
    assert "catering" not in result["answer"]


def test_deleted_source_is_withheld_and_counts_toward_the_fetch_budget(member, monkeypatch):
    bind_slack(member, monkeypatch)
    sources = [slack_source(index) for index in range(1, 11)]
    records = index_sources(member, sources)
    rank_in_order(monkeypatch, records)
    fake = serve_slack(monkeypatch, sources, deleted={"C02"})
    result = service.query_twin(QUESTION)
    assert fake.calls == ["C01", "C02", "C03", "C04"]
    assert cited(result) == [sources[0]["uri"], sources[2]["uri"], sources[3]["uri"]]
    assert "stage 2 approved" not in result["answer"]


@pytest.mark.parametrize("configured,expected_fetches", [(None, 4), ("2", 2), ("6", 6)])
def test_fetch_cap_is_honored(member, monkeypatch, configured, expected_fetches):
    if configured is not None:
        monkeypatch.setenv("WISDOMTWIN_MAX_SOURCE_FETCHES", configured)
    bind_slack(member, monkeypatch)
    sources = [slack_source(index) for index in range(1, 11)]
    records = index_sources(member, sources)
    rank_in_order(monkeypatch, records)
    deleted = {f"C{index:02d}" for index in range(1, 5)}
    fake = serve_slack(monkeypatch, sources, deleted=deleted)
    if expected_fetches <= 4:
        # F1: valid sources were left unchecked, so "nothing ingested" would be false.
        with pytest.raises(CodedToolError) as caught:
            service.query_twin(QUESTION)
        assert str(caught.value) == SOURCE_CHECK_LIMIT
        assert any(row.tool_name == "query_twin" and row.error_code == "CONNECTOR_FAILED"
                   and row.role_id == member.role.id for row in member.store.audits())
    else:
        result = service.query_twin(QUESTION)
        assert cited(result) == [source["uri"] for source in sources[4:expected_fetches]]
    assert fake.calls == [f"C{index:02d}" for index in range(1, expected_fetches + 1)]


def test_fetch_cap_counts_distinct_sources_not_chunks(member, monkeypatch):
    monkeypatch.setenv("WISDOMTWIN_MAX_SOURCE_FETCHES", "1")
    bind_slack(member, monkeypatch)
    long_source = slack_source(1, " ".join(f"stage{index}" for index in range(700)))
    records = index_sources(member, [long_source, slack_source(2)])
    assert len(records) == 3
    fake = serve_slack(monkeypatch, [long_source, slack_source(2)])
    hydrated = service.hydrate_sources(records)
    assert [record.source_uri for record in hydrated] == [long_source["uri"]] * 2
    assert fake.calls == ["C01"]


@pytest.mark.parametrize("value", ["0", "-1", "four", "1.5"])
def test_invalid_fetch_cap_fails_closed_at_startup(monkeypatch, value):
    monkeypatch.setenv("WISDOMTWIN_MAX_SOURCE_FETCHES", value)
    with pytest.raises(RuntimeError, match="WISDOMTWIN_MAX_SOURCE_FETCHES"):
        runtime.validate_runtime()


@pytest.mark.parametrize("failure", ["limited", "broken"])
def test_provider_failure_after_verified_evidence_returns_a_partial_answer(member, monkeypatch, failure):
    bind_slack(member, monkeypatch)
    sources = [slack_source(1), slack_source(2, "Acme pipeline stage 2 withheld text"), slack_source(3)]
    records = index_sources(member, sources)
    rank_in_order(monkeypatch, records)
    fake = serve_slack(monkeypatch, sources, **{failure: {"C02"}})
    result = service.query_twin(QUESTION)
    assert cited(result) == [sources[0]["uri"]]
    assert "stage 1 approved" in result["answer"] and "withheld" not in result["answer"]
    assert fake.calls == ["C01", "C02"], "Fetching stops after the failure"
    assert all(chunk.excerpt == "" for chunk in member.store.chunks_for_role(member.role.id))


@pytest.mark.parametrize("failure,message", [
    ("limited", "CONNECTOR_FAILED: Source provider is rate limited. Retry after at least 60 seconds."),
    ("broken", "CONNECTOR_FAILED: Source revalidation failed. Retry after the provider recovers."),
])
def test_provider_failure_before_any_verification_is_a_coded_failure(member, monkeypatch, failure, message):
    bind_slack(member, monkeypatch)
    sources = [slack_source(1, "Acme pipeline stage 1 withheld text"), slack_source(2)]
    records = index_sources(member, sources)
    rank_in_order(monkeypatch, records)
    fake = serve_slack(monkeypatch, sources, **{failure: {"C01"}})
    monkeypatch.setattr(service, "answer_from_context", lambda *args: pytest.fail("No evidence after the failure"))
    with pytest.raises(CodedToolError) as caught:
        service.query_twin(QUESTION)
    assert str(caught.value) == message
    assert fake.calls == ["C01"]


# G1 and F1: the fetch budget goes to candidates that can support the question first,
# and running out of it with nothing verified is never "nothing ingested".

def off_topic(index):
    return slack_source(index, f"Quarterly offsite catering menu option {index}")


def test_off_topic_sources_ranked_first_do_not_spend_the_fetch_budget(member, monkeypatch):
    bind_slack(member, monkeypatch)
    sources = [*(off_topic(index) for index in range(1, 5)), *(slack_source(index) for index in range(5, 8))]
    records = index_sources(member, sources)
    rank_in_order(monkeypatch, records)
    fake = serve_slack(monkeypatch, sources)
    result = service.query_twin(QUESTION)
    assert fake.calls == ["C05", "C06", "C07"]
    assert cited(result) == [source["uri"] for source in sources[4:]]
    assert "catering" not in result["answer"]


def test_real_ranking_with_off_topic_hits_first_still_cites_the_supporting_sources(member, monkeypatch):
    # The reported case, ranked by the real hybrid_search: the off-topic messages
    # share only stopwords with the question, yet rank ahead of the supporting ones.
    bind_slack(member, monkeypatch)
    topics = ["menu", "venue", "agenda", "budget", "travel"]
    sources = [slack_source(index, f"What is the plan of the offsite {topic}?") for index, topic in enumerate(topics, 1)]
    sources += [slack_source(index, f"Acme renewal signed {index}") for index in range(6, 9)]
    index_sources(member, sources)
    question = "What is the status of the Acme renewal?"
    ranked = service.hybrid_search(member.store, role_id=member.role.id, question=question,
                                   embedding=service.embed_texts([question])[0], limit=10)
    assert [urlsplit(item.chunk.source_uri).path.split("/")[2] for item in ranked][:4] == ["C01", "C02", "C03", "C04"]
    fake = serve_slack(monkeypatch, sources)
    result = service.query_twin(question)
    assert sorted(fake.calls) == ["C06", "C07", "C08"]
    assert sorted(cited(result)) == sorted(source["uri"] for source in sources[5:])


def test_pre_hmac_keyword_hashes_still_rank_as_supporting(member, monkeypatch):
    bind_slack(member, monkeypatch)
    sources = [*(off_topic(index) for index in range(1, 5)), slack_source(5)]
    records = index_sources(member, sources)
    legacy = replace(records[4], keyword_hashes=sorted(hashlib.sha256(term.encode()).hexdigest()
                                                       for term in set(_terms(sources[4]["text"]))))
    rank_in_order(monkeypatch, [*records[:4], legacy])
    fake = serve_slack(monkeypatch, sources)
    result = service.query_twin(QUESTION)
    # The legacy row is fetched first; the demoted rows then use the rest of the budget.
    assert fake.calls == ["C05", "C01", "C02", "C03"]
    assert cited(result) == [sources[4]["uri"]]


def test_rows_hashed_under_an_earlier_key_are_demoted_not_dropped(member, monkeypatch):
    bind_slack(member, monkeypatch)
    sources = [off_topic(1), *(slack_source(index) for index in range(2, 6))]
    records = index_sources(member, sources)
    earlier_key = b"synthetic earlier keyword key"
    earlier = [replace(record, keyword_hashes=sorted(hmac.new(earlier_key, term.encode(), hashlib.sha256).hexdigest()
                                                     for term in set(_terms(source["text"]))))
               for record, source in zip(records, sources)]
    rank_in_order(monkeypatch, earlier)
    fake = serve_slack(monkeypatch, sources)
    result = service.query_twin(QUESTION)
    # No row matches the current key, so rank order holds. The off-topic source
    # verifies but is neither cited nor counted toward the three citations.
    assert fake.calls == ["C01", "C02", "C03", "C04"]
    assert cited(result) == [source["uri"] for source in sources[1:4]]
    assert "catering" not in result["answer"]


def test_lapsed_grant_ranked_after_the_spent_budget_still_asks_for_a_reconnect(member, monkeypatch):
    enable_gmail(monkeypatch)
    bind_slack(member, monkeypatch)
    sources = [slack_source(index) for index in range(1, 5)]
    slack = index_sources(member, sources)
    gmail = index_sources(member, [{"uri": GMAIL_URI, "text": GMAIL_DETAIL["snippet"],
                                    "author_provider_id": "bob@example-corp.com"}], provider="gmail")
    rank_in_order(monkeypatch, slack + gmail)
    fake = serve_slack(monkeypatch, sources, deleted={"C01", "C02", "C03", "C04"})
    with pytest.raises(CodedToolError) as caught:
        service.query_twin(QUESTION)
    assert str(caught.value) == GMAIL_RECONNECT
    assert fake.calls == ["C01", "C02", "C03", "C04"]


def test_grant_is_resolved_once_per_service(member, monkeypatch):
    bind_slack(member, monkeypatch)
    sources = [slack_source(index) for index in range(1, 4)]
    records = index_sources(member, sources)
    rank_in_order(monkeypatch, records)
    serve_slack(monkeypatch, sources)
    resolve = service.connector_token
    resolved = []

    def counted(role_id, service_name):
        resolved.append(service_name)
        return resolve(role_id, service_name)

    monkeypatch.setattr(service, "connector_token", counted)
    assert len(service.query_twin(QUESTION)["citations"]) == 3
    assert resolved == ["slack"]


def test_budget_that_checked_every_candidate_keeps_the_empty_context_answer(member, monkeypatch):
    bind_slack(member, monkeypatch)
    sources = [slack_source(index) for index in range(1, 5)]
    records = index_sources(member, sources)
    rank_in_order(monkeypatch, records)
    fake = serve_slack(monkeypatch, sources, deleted={"C01", "C02", "C03", "C04"})
    assert service.query_twin(QUESTION) == EMPTY_CONTEXT
    assert fake.calls == ["C01", "C02", "C03", "C04"]


# G2: a grant the provider revoked, expired or deactivated asks for a reconnect.

def test_slack_grant_and_per_source_errors_are_separate():
    assert connectors.SLACK_GRANT_ERRORS == {"token_revoked", "invalid_auth", "account_inactive",
                                             "token_expired", "not_authed"}
    assert connectors.SLACK_UNAVAILABLE_ERRORS == {"missing_scope", "access_denied", "message_not_found",
                                                   "thread_not_found", "channel_not_found", "not_in_channel"}


@pytest.mark.parametrize("error", sorted(connectors.SLACK_GRANT_ERRORS))
def test_slack_grant_rejection_asks_for_a_reconnect(member, monkeypatch, error):
    bind_slack(member, monkeypatch)
    sources = [slack_source(1), slack_source(2)]
    records = index_sources(member, sources)
    rank_in_order(monkeypatch, records)
    fake = serve_slack(monkeypatch, sources, rejected={"C01": error, "C02": error})
    with pytest.raises(CodedToolError) as caught:
        service.query_twin(QUESTION)
    assert str(caught.value) == SLACK_RECONNECT
    assert fake.calls == ["C01"], "A rejected grant is not tried again for the next source"


@pytest.mark.parametrize("error", sorted(connectors.SLACK_UNAVAILABLE_ERRORS))
def test_slack_per_source_denial_stays_absent_evidence(member, monkeypatch, error):
    bind_slack(member, monkeypatch)
    sources = [slack_source(1)]
    records = index_sources(member, sources)
    rank_in_order(monkeypatch, records)
    fake = serve_slack(monkeypatch, sources, rejected={"C01": error})
    assert service.query_twin(QUESTION) == EMPTY_CONTEXT
    assert fake.calls == ["C01"]


@pytest.mark.parametrize("error", sorted(connectors.SLACK_GRANT_ERRORS))
@pytest.mark.parametrize("thread_reference", [True, False], ids=["explicit-thread", "history-fallback"])
def test_refetch_slack_raises_grant_revoked_on_every_request(monkeypatch, error, thread_reference):
    uri = slack_source(1)["uri"] + ("?thread_ts=1699999999.000002&cid=C01" if thread_reference else "")
    requested = []

    def response(url, token):
        requested.append(urlsplit(url).path)
        if url.startswith("https://slack.com/api/conversations.history"):
            return {"ok": True, "messages": []}
        return {"ok": False, "error": error}

    monkeypatch.setattr(connectors, "_request_json", response)
    with pytest.raises(connectors.GrantRevoked) as caught:
        connectors.refetch_slack(SLACK_TOKEN, uri)
    assert caught.value.service == "slack"
    assert requested[-1] == "/api/conversations.replies"


def test_revoked_slack_grant_does_not_hide_verified_gmail_evidence(member, monkeypatch, clock):
    enable_gmail(monkeypatch)
    bind_slack(member, monkeypatch)
    bind_gmail(member, monkeypatch)
    slack = index_sources(member, [slack_source(1)])
    gmail = index_sources(member, [{"uri": GMAIL_URI, "text": GMAIL_DETAIL["snippet"],
                                    "author_provider_id": "bob@example-corp.com"}], provider="gmail")
    rank_in_order(monkeypatch, slack + gmail)
    revoked_slack = FakeSlack([slack_source(1)], rejected={"C01": "token_revoked"})
    gmail_calls = []

    def urlopen(request, timeout):
        if urlsplit(request.full_url).netloc == "slack.com":
            return revoked_slack.urlopen(request, timeout)
        gmail_calls.append(request.full_url)
        assert request.get_header("Authorization") == f"Bearer {GOOGLE_TOKEN}"
        return io.BytesIO(json.dumps(GMAIL_DETAIL).encode())

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    result = service.query_twin(QUESTION)
    assert cited(result) == [GMAIL_URI]
    assert revoked_slack.calls == ["C01"] and len(gmail_calls) == 1


def unauthorized(request, timeout):
    raise urllib.error.HTTPError(request.full_url, 401, "synthetic revoked grant", Message(), None)


@pytest.mark.parametrize("provider,uri,reconnect", [
    ("gmail", GMAIL_URI, GMAIL_RECONNECT),
    ("drive", "https://drive.google.com/file/d/FILE_A/view", DRIVE_RECONNECT),
])
def test_google_401_asks_for_a_reconnect(member, monkeypatch, provider, uri, reconnect):
    monkeypatch.setenv("GOOGLE_REVIEW_APPROVED", "true")
    monkeypatch.setenv(f"{provider.upper()}_CONNECTOR_ENABLED", "true")
    credential(member, provider)
    index_sources(member, [{"uri": uri, "text": "Acme pipeline stage 3", "author_provider_id": "PERSON_A"}],
                  provider=provider)
    calls = []

    def revoked(request, timeout):
        calls.append(request.full_url)
        unauthorized(request, timeout)

    monkeypatch.setattr("urllib.request.urlopen", revoked)
    with pytest.raises(CodedToolError) as caught:
        service.query_twin(QUESTION)
    assert str(caught.value) == reconnect
    assert len(calls) == 1


@pytest.mark.parametrize("provider", ["gmail", "drive"])
def test_google_fetchers_raise_grant_revoked_on_401(monkeypatch, provider):
    monkeypatch.setattr("urllib.request.urlopen", unauthorized)
    fetch = {"gmail": connectors.fetch_gmail, "drive": connectors.fetch_drive}[provider]
    with pytest.raises(connectors.GrantRevoked) as caught:
        fetch(GOOGLE_TOKEN, "budget", 10)
    assert caught.value.service == provider


@pytest.mark.parametrize("error", sorted(connectors.SLACK_GRANT_ERRORS))
def test_slack_grant_rejection_fails_the_job_without_a_celery_retry(member, monkeypatch, error):
    bind_slack(member, monkeypatch)
    retries = []

    def retry(**kwargs):
        retries.append(kwargs)
        return RuntimeError("synthetic retry scheduled")

    def search(request, timeout):
        assert request.full_url.startswith("https://slack.com/api/search.messages?")
        return io.BytesIO(json.dumps({"ok": False, "error": error}).encode())

    monkeypatch.setattr(ingest.ingest_job, "retry", retry)
    monkeypatch.setattr(connectors, "use_fixtures", lambda: False)  # The real search, against the offline fake.
    monkeypatch.setattr("urllib.request.urlopen", search)
    job = member.store.create_job(member.role.id, "slack", "pipeline", 10)
    with pytest.raises(CodedToolError) as caught:
        ingest.ingest_job(job.id, member.subject)
    assert str(caught.value) == "OAUTH_PENDING: Reconnect Slack with connect_business_account before ingesting again."
    assert retries == []
    assert member.store.get_job(job.id).status == "failed"


def test_slack_grant_rejection_through_the_ingest_tool_asks_for_a_reconnect(member, monkeypatch):
    bind_slack(member, monkeypatch)
    monkeypatch.setattr(connectors, "use_fixtures", lambda: False)
    monkeypatch.setattr("urllib.request.urlopen", lambda request, timeout: io.BytesIO(
        json.dumps({"ok": False, "error": "token_revoked"}).encode()))
    with pytest.raises(CodedToolError) as caught:
        service.ingest_data("slack", "pipeline", 10)
    assert str(caught.value) == "OAUTH_PENDING: Reconnect Slack with connect_business_account before ingesting again."
    assert [job.status for job in member.store.jobs_for_role(member.role.id)] == ["failed"]


def test_google_401_fails_the_job_without_a_celery_retry(member, monkeypatch, clock):
    enable_gmail(monkeypatch)
    bind_gmail(member, monkeypatch)
    retries = []

    def retry(**kwargs):
        retries.append(kwargs)
        return RuntimeError("synthetic retry scheduled")

    monkeypatch.setattr(ingest.ingest_job, "retry", retry)
    monkeypatch.setattr("urllib.request.urlopen", unauthorized)
    job = member.store.create_job(member.role.id, "gmail", "budget", 10)
    with pytest.raises(CodedToolError) as caught:
        ingest.ingest_job(job.id, member.subject)
    assert str(caught.value) == "OAUTH_PENDING: Reconnect Gmail with connect_business_account before ingesting again."
    assert retries == []
    assert member.store.get_job(job.id).status == "failed"


# G6: a stored grant that cannot be read asks for a reconnect, which replaces it.

@pytest.mark.parametrize("stored", ["rotated-key", "not-a-token", "not-json", "list", "string", "null"])
def test_unreadable_stored_grant_asks_for_a_reconnect(member, monkeypatch, stored):
    bind_slack(member, monkeypatch)
    index_sources(member, [slack_source(1)])
    grant = json.dumps(stored_grant(member, "slack"))
    ciphertext = {
        "rotated-key": lambda: Fernet(Fernet.generate_key()).encrypt(grant.encode()).decode(),
        "not-a-token": lambda: "synthetic-corrupted-ciphertext",
        "not-json": lambda: encrypt_token("synthetic grant that is not JSON"),
        "list": lambda: encrypt_token(json.dumps([SLACK_TOKEN])),
        "string": lambda: encrypt_token(json.dumps(SLACK_TOKEN)),
        "null": lambda: encrypt_token("null"),
    }[stored]()
    member.store.save_credential(member.role.id, "slack", ciphertext)
    with pytest.raises(service.GrantUnavailable):
        service.connector_token(member.role.id, "slack")
    with pytest.raises(CodedToolError) as caught:
        service.query_twin(QUESTION)
    assert str(caught.value) == SLACK_RECONNECT
    with pytest.raises(CodedToolError) as caught:
        service.ingest_data("slack", "pipeline", 10)
    assert str(caught.value) == "OAUTH_PENDING: Reconnect Slack with connect_business_account before ingesting again."
    assert member.store.jobs_for_role(member.role.id) == []
    bind_slack(member, monkeypatch)
    assert service.connector_token(member.role.id, "slack") == SLACK_TOKEN


def test_malformed_connector_key_is_still_a_configuration_error(member, monkeypatch):
    bind_slack(member, monkeypatch)
    monkeypatch.setenv("CONNECTOR_TOKEN_KEY", "not-a-fernet-key")
    with pytest.raises(ValueError):
        service.connector_token(member.role.id, "slack")


# L3: Gmail links no longer assume the first signed-in account.

def test_gmail_ingestion_emits_account_neutral_links(monkeypatch):
    def response(url, token):
        assert token == GOOGLE_TOKEN
        if "/messages?" in url:
            return {"messages": [{"id": "MSG_A"}]}
        assert url.endswith("/messages/MSG_A?format=metadata")
        return GMAIL_DETAIL

    monkeypatch.setattr(connectors, "_request_json", response)
    items = connectors.fetch_gmail(GOOGLE_TOKEN, "budget", 10)
    assert [item["uri"] for item in items] == [GMAIL_URI]
    assert "/u/0/" not in items[0]["uri"]


@pytest.mark.parametrize("uri", [GMAIL_URI, LEGACY_GMAIL_URI], ids=["current", "legacy"])
def test_gmail_current_and_legacy_links_both_refetch(monkeypatch, uri):
    calls = []
    serve_gmail(monkeypatch, calls)
    source = connectors.refetch_google(GOOGLE_TOKEN, "gmail", uri)
    assert source == {"uri": uri, "text": GMAIL_DETAIL["snippet"], "author_provider_id": "bob@example-corp.com"}
    assert len(calls) == 1


@pytest.mark.parametrize("uri", [
    "https://mail.google.com/mail/u/1/#inbox/MSG_A", "https://mail.google.com/mail/#inbox/MSG_A",
    "https://mail.google.com/mail/#all/MSG_A/extra", "https://mail.example.test/mail/#all/MSG_A",
    "https://mail.google.com/mail/#all/MSG A", "http://mail.google.com/mail/#all/MSG_A",
])
def test_other_gmail_link_shapes_are_still_rejected(uri):
    with pytest.raises(ValueError):
        connectors.refetch_google(GOOGLE_TOKEN, "gmail", uri)


def test_legacy_gmail_rows_still_answer_through_the_query_path(member, monkeypatch, clock):
    enable_gmail(monkeypatch)
    bind_gmail(member, monkeypatch)
    index_sources(member, [{"uri": LEGACY_GMAIL_URI, "text": GMAIL_DETAIL["snippet"],
                            "author_provider_id": "bob@example-corp.com"}], provider="gmail")
    calls = []
    serve_gmail(monkeypatch, calls)
    result = service.query_twin(QUESTION)
    assert cited(result) == [LEGACY_GMAIL_URI] and len(calls) == 1
