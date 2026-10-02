"""Synthetic provider lifetime/rotation tests with opt-in isolated PostgreSQL.

Only this test's namespace is erased. No provider requests or real credentials
are used; every HTTP response is supplied by an offline Slack fixture.
"""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import date, datetime, timezone
import io
import json
import os
import threading
import time
from types import SimpleNamespace
import urllib.error
from urllib.parse import parse_qs, urlsplit
import uuid

from cryptography.fernet import Fernet
import pytest

import corporate_login
from errors import AUTHORIZATION_REQUIRED, CONNECTOR_FAILED, OAUTH_PENDING, CodedToolError
from oauth_connectors import SLACK_USER_SCOPES
import provider_binding
from security_store import security_store
import service
from store import MemoryStore, PostgresStore, actor_subject, reset_store
from tokens import decrypt_token, encrypt_token


NOW = datetime(2026, 10, 1, 12, tzinfo=timezone.utc).timestamp()
OLD_ACCESS = "synthetic-old-access"
OLD_REFRESH = "synthetic-old-refresh"
NEW_ACCESS = "synthetic-rotated-access"
NEW_REFRESH = "synthetic-rotated-refresh"
LOGIN_ACCESS = "synthetic-concurrent-login-access"
TEAM = "SYNTHETIC_TEAM"
USER = "SYNTHETIC_USER"
EMAIL = "reviewer@example-corp.com"


@pytest.fixture(autouse=True)
def isolated_security_state(tmp_path, monkeypatch):
    """Override the global truncating fixture for this namespace-only suite."""
    monkeypatch.setenv("WISDOMTWIN_AUTH_DB", str(tmp_path / "provider-lifetime-auth.sqlite3"))
    monkeypatch.setenv("CONNECTOR_TOKEN_KEY", Fernet.generate_key().decode())
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SLACK_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("SLACK_TOKEN_REFRESH_ENABLED", raising=False)
    monkeypatch.delenv("WISDOMTWIN_ALLOW_PAID_MODEL_APIS", raising=False)
    actor = actor_subject.set("local")
    reset_store(MemoryStore())

    def forbidden(*args, **kwargs):
        pytest.fail("Provider lifetime regressions must never use the network")

    monkeypatch.setattr("urllib.request.urlopen", forbidden)
    monkeypatch.setattr(corporate_login, "urlopen", forbidden)
    yield
    reset_store(MemoryStore())
    actor_subject.reset(actor)


class OfflineSlack:
    def __init__(self):
        self.calls = []
        self.refresh_calls = []
        self.guard = threading.Lock()
        self.refresh_body = {
            "ok": True, "token_type": "user", "access_token": NEW_ACCESS,
            "refresh_token": NEW_REFRESH, "expires_in": 43200,
            "scope": ",".join(SLACK_USER_SCOPES),
        }
        self.refresh_hook = None
        self.identity = {"ok": True, "team_id": TEAM, "user_id": USER}
        self.profile = {"ok": True, "user": {"id": USER, "profile": {"email": EMAIL}}}

    def urlopen(self, request, timeout):
        parsed = urlsplit(request.full_url)
        assert parsed.scheme == "https" and parsed.hostname == "slack.com"
        assert 0 < timeout <= 30
        with self.guard:
            self.calls.append(parsed.path)
        if parsed.path == "/api/oauth.v2.access":
            assert request.get_method() == "POST"
            body = parse_qs(request.data.decode())
            assert body["grant_type"] == ["refresh_token"]
            assert body["refresh_token"] == [OLD_REFRESH]
            assert "code_verifier" not in body and "code_challenge" not in body
            with self.guard:
                self.refresh_calls.append(body)
            if self.refresh_hook:
                self.refresh_hook()
            response = self.refresh_body
            if isinstance(response, Exception):
                raise response
        elif parsed.path == "/api/auth.test":
            assert request.get_header("Authorization", "").startswith("Bearer synthetic-")
            response = self.identity
        elif parsed.path == "/api/users.info":
            assert parse_qs(parsed.query)["user"] == [USER]
            response = self.profile
        else:
            pytest.fail(f"Unexpected offline provider endpoint: {parsed.path}")
        return io.BytesIO(json.dumps(response).encode())

    def clear_calls(self):
        self.calls.clear()
        self.refresh_calls.clear()


@pytest.fixture(params=["memory", "postgres"])
def grant_harness(request, monkeypatch):
    if request.param == "postgres":
        database_url = os.environ.get("WISDOMTWIN_TEST_DATABASE_URL", "").strip()
        if not database_url:
            pytest.skip("Requires explicitly configured isolated synthetic PostgreSQL")
        store = PostgresStore(database_url)
    else:
        store = MemoryStore()
    reset_store(store)
    now = [NOW]
    monkeypatch.setattr(time, "time", lambda: now[0])
    subject = security_store().provision(issuer="https://synthetic-provider-lifetime.test", provider_subject=uuid.uuid4().hex,
        email=EMAIL, domain="example-corp.com", roles=["CRO"], slack_team_id=TEAM, slack_user_id=USER)
    actor = actor_subject.set(subject)
    member = security_store().membership(subject)
    org = store.upsert_organization(member["domain"])
    person = store.ensure_officeholder(org.id)
    role = store.create_role(org.id, "CRO")
    store.open_tenure(role.id, person.id, date.today())
    store.record_connection(role.id, "slack", org.domain, role.title)
    pending = {"subject": subject, "role_id": role.id, "domain": org.domain,
        "role_title": role.title, "service": "slack"}
    http = OfflineSlack()
    monkeypatch.setattr("urllib.request.urlopen", http.urlopen)
    monkeypatch.setattr(corporate_login, "urlopen", http.urlopen)
    monkeypatch.setattr(service, "use_fixtures", lambda: False)
    monkeypatch.setenv("SLACK_POLICY_APPROVED", "true")
    harness = SimpleNamespace(store=store, role=role, member=member, subject=subject, pending=pending,
        clock=now, http=http, backend=request.param)
    try:
        yield harness
    finally:
        # This is never a shared-table reset or truncation.
        if store.get_role(role.id) is not None:
            store.delete_namespace(role.id)
        security_store().remove_member(subject)
        actor_subject.reset(actor)


def initial_grant(harness, *, expiry=None, refresh=None):
    user = {"id": USER, "access_token": OLD_ACCESS, "token_type": "user", "scope": ",".join(SLACK_USER_SCOPES)}
    if expiry is not None:
        user["expires_in"] = expiry
    if refresh is not None:
        user["refresh_token"] = refresh
    provider_binding.bind_slack(harness.pending, harness.member, {"ok": True, "team": {"id": TEAM}, "authed_user": user})
    harness.http.clear_calls()
    return harness.store.get_credential(harness.role.id, "slack")


def payload(harness):
    return json.loads(decrypt_token(harness.store.get_credential(harness.role.id, "slack")))


def rotating_grant(harness, monkeypatch):
    ciphertext = initial_grant(harness, expiry=1, refresh=OLD_REFRESH)
    harness.clock[0] += 2
    monkeypatch.setenv("SLACK_TOKEN_REFRESH_ENABLED", "true")
    monkeypatch.setenv("SLACK_CLIENT_ID", "synthetic-refresh-client")
    monkeypatch.setenv("SLACK_CLIENT_SECRET", "synthetic-refresh-client-secret")
    return ciphertext


def token(harness):
    return service.connector_token(harness.role.id, "slack")


def reconnect_error(action):
    with pytest.raises(CodedToolError) as caught:
        action()
    assert caught.value.code == OAUTH_PENDING
    assert "reconnect" in str(caught.value).lower()
    return caught.value


def test_nonrotating_slack_grant_has_no_invented_expiry(grant_harness):
    harness = grant_harness
    ciphertext = initial_grant(harness)
    assert payload(harness).get("expires_at") is None
    harness.clock[0] += 2 * 86400
    assert token(harness) == OLD_ACCESS
    assert harness.store.get_credential(harness.role.id, "slack") == ciphertext
    assert harness.http.calls == []


@pytest.mark.parametrize("expires_in", [60, 43200, 172800])
def test_rotating_slack_grant_preserves_provider_lifetime_and_encrypted_refresh(grant_harness, expires_in):
    harness = grant_harness
    ciphertext = initial_grant(harness, expiry=expires_in, refresh=OLD_REFRESH)
    saved = payload(harness)
    assert saved["expires_at"] == pytest.approx(NOW + expires_in, rel=0, abs=0.001)
    assert saved["refresh_token"] == OLD_REFRESH
    assert saved["subject"] == harness.subject and saved["role_id"] == harness.role.id
    assert saved["service"] == "slack" and saved["team_id"] == TEAM and saved["user_id"] == USER
    assert set(saved["scopes"]) == set(SLACK_USER_SCOPES)
    assert NOW < saved["refresh_expires_at"] <= NOW + 30 * 86400
    assert OLD_ACCESS not in ciphertext and OLD_REFRESH not in ciphertext


def test_legacy_expired_nonrefresh_grant_requires_explicit_reconnect(grant_harness):
    harness = grant_harness
    initial_grant(harness)
    legacy = {**payload(harness), "expires_at": NOW - 1}
    legacy.pop("refresh_token", None)
    ciphertext = encrypt_token(json.dumps(legacy))
    harness.store.save_credential(harness.role.id, "slack", ciphertext)
    reconnect_error(lambda: token(harness))
    assert harness.http.calls == []
    assert harness.store.get_credential(harness.role.id, "slack") == ciphertext


def test_disabled_refresh_is_explicit_and_never_calls_provider(grant_harness, monkeypatch):
    harness = grant_harness
    ciphertext = rotating_grant(harness, monkeypatch)
    monkeypatch.delenv("SLACK_TOKEN_REFRESH_ENABLED")
    reconnect_error(lambda: token(harness))
    assert harness.http.calls == []
    assert harness.store.get_credential(harness.role.id, "slack") == ciphertext


@pytest.mark.parametrize("missing", ["SLACK_CLIENT_ID", "SLACK_CLIENT_SECRET"])
def test_server_refresh_without_client_auth_requires_reconnect(grant_harness, monkeypatch, missing):
    harness = grant_harness
    ciphertext = rotating_grant(harness, monkeypatch)
    monkeypatch.delenv(missing)
    reconnect_error(lambda: token(harness))
    assert harness.http.calls == []
    assert harness.store.get_credential(harness.role.id, "slack") == ciphertext


def test_expired_pkce_refresh_token_is_not_redeemed(grant_harness, monkeypatch):
    harness = grant_harness
    ciphertext = rotating_grant(harness, monkeypatch)
    harness.clock[0] = NOW + 30 * 86400 + 1
    reconnect_error(lambda: token(harness))
    assert harness.http.calls == []
    assert harness.store.get_credential(harness.role.id, "slack") == ciphertext


def test_successful_user_refresh_reverifies_identity_and_replaces_refresh_atomically(grant_harness, monkeypatch):
    harness = grant_harness
    old = rotating_grant(harness, monkeypatch)
    assert token(harness) == NEW_ACCESS
    saved = payload(harness)
    ciphertext = harness.store.get_credential(harness.role.id, "slack")
    assert ciphertext != old
    assert saved["access_token"] == NEW_ACCESS and saved["refresh_token"] == NEW_REFRESH
    assert saved["expires_at"] == pytest.approx(harness.clock[0] + 43200, rel=0, abs=0.001)
    assert saved["subject"] == harness.subject and saved["role_id"] == harness.role.id
    assert saved["team_id"] == TEAM and saved["user_id"] == USER
    assert set(saved["scopes"]) == set(SLACK_USER_SCOPES)
    assert NEW_ACCESS not in ciphertext and NEW_REFRESH not in ciphertext
    assert len(harness.http.refresh_calls) == 1
    assert "/api/auth.test" in harness.http.calls and "/api/users.info" in harness.http.calls
    harness.http.clear_calls()
    assert token(harness) == NEW_ACCESS
    assert harness.http.calls == []


def test_transient_refresh_failure_preserves_existing_ciphertext(grant_harness, monkeypatch):
    harness = grant_harness
    ciphertext = rotating_grant(harness, monkeypatch)
    harness.http.refresh_body = urllib.error.HTTPError("https://slack.com/api/oauth.v2.access", 503,
        "synthetic provider failure", {}, None)
    with pytest.raises(CodedToolError) as caught:
        token(harness)
    assert caught.value.code == CONNECTOR_FAILED
    assert 1 <= len(harness.http.refresh_calls) <= 2
    assert harness.store.get_credential(harness.role.id, "slack") == ciphertext
    assert OLD_ACCESS not in str(caught.value) and OLD_REFRESH not in str(caught.value)


def test_uncertain_refresh_outcome_is_not_redeemed_again(grant_harness, monkeypatch):
    harness = grant_harness
    ciphertext = rotating_grant(harness, monkeypatch)
    harness.http.refresh_body = urllib.error.HTTPError("https://slack.com/api/oauth.v2.access", 503,
        "synthetic uncertain outcome", {}, None)
    with pytest.raises(CodedToolError) as caught:
        token(harness)
    assert caught.value.code == CONNECTOR_FAILED
    attempts = len(harness.http.refresh_calls)
    assert 1 <= attempts <= 2
    harness.http.refresh_body = {"ok": True}
    reconnect_error(lambda: token(harness))
    assert len(harness.http.refresh_calls) == attempts
    assert harness.store.get_credential(harness.role.id, "slack") == ciphertext


@pytest.mark.parametrize("body", [None, [], "not-an-object"], ids=["null", "array", "string"])
def test_nonobject_refresh_response_fails_without_identity_lookup_or_overwrite(grant_harness, monkeypatch, body):
    harness = grant_harness
    ciphertext = rotating_grant(harness, monkeypatch)
    harness.http.refresh_body = body
    with pytest.raises(CodedToolError):
        token(harness)
    assert harness.http.calls == ["/api/oauth.v2.access"]
    assert harness.store.get_credential(harness.role.id, "slack") == ciphertext


@pytest.mark.parametrize("expiry", [0, -1, True, 1.5, "43200", None],
    ids=["zero", "negative", "boolean", "fractional", "string", "rotating-missing-expiry"])
def test_invalid_initial_provider_lifetime_is_never_saved(grant_harness, expiry):
    harness = grant_harness
    with pytest.raises(ValueError):
        initial_grant(harness, expiry=expiry, refresh=OLD_REFRESH)
    assert harness.store.get_credential(harness.role.id, "slack") is None


@pytest.mark.parametrize("change", [
    {"expires_in": 0}, {"refresh_token": None}, {"token_type": "bot"},
    {"scope": ",".join([*SLACK_USER_SCOPES, "chat:write"])}, {"access_token": None},
], ids=["bad-expiry", "missing-refresh", "bot-token", "extra-scope", "missing-access"])
def test_malformed_refresh_response_never_overwrites_old_grant(grant_harness, monkeypatch, change):
    harness = grant_harness
    ciphertext = rotating_grant(harness, monkeypatch)
    harness.http.refresh_body = {**harness.http.refresh_body, **change}
    with pytest.raises(CodedToolError):
        token(harness)
    assert 1 <= len(harness.http.refresh_calls) <= 2
    assert harness.store.get_credential(harness.role.id, "slack") == ciphertext


@pytest.mark.parametrize("substitution", ["team", "user", "email"])
def test_refresh_identity_substitution_never_overwrites_old_grant(grant_harness, monkeypatch, substitution):
    harness = grant_harness
    ciphertext = rotating_grant(harness, monkeypatch)
    if substitution == "team":
        harness.http.identity = {**harness.http.identity, "team_id": "DIFFERENT_TEAM"}
    elif substitution == "user":
        harness.http.identity = {**harness.http.identity, "user_id": "DIFFERENT_USER"}
    else:
        harness.http.profile = {"ok": True, "user": {"id": USER, "profile": {"email": "different@example-corp.com"}}}
    with pytest.raises(CodedToolError):
        token(harness)
    assert harness.store.get_credential(harness.role.id, "slack") == ciphertext


@pytest.mark.parametrize("field,value", [("subject", "different-subject"), ("role_id", str(uuid.UUID(int=42))),
    ("team_id", "DIFFERENT_TEAM"), ("user_id", "DIFFERENT_USER")])
def test_substituted_stored_refresh_binding_is_never_redeemed(grant_harness, monkeypatch, field, value):
    harness = grant_harness
    rotating_grant(harness, monkeypatch)
    substituted = {**payload(harness), field: value}
    ciphertext = encrypt_token(json.dumps(substituted))
    harness.store.save_credential(harness.role.id, "slack", ciphertext)
    with pytest.raises(CodedToolError):
        token(harness)
    assert harness.http.calls == []
    assert harness.store.get_credential(harness.role.id, "slack") == ciphertext


def test_concurrent_reauthorization_wins_over_stale_refresh_response(grant_harness, monkeypatch):
    harness = grant_harness
    rotating_grant(harness, monkeypatch)
    replacement = {**payload(harness), "access_token": LOGIN_ACCESS, "expires_at": NOW + 43200,
        "refresh_token": "synthetic-concurrent-login-refresh"}
    replacement_ciphertext = encrypt_token(json.dumps(replacement))

    def reauthorize():
        harness.store.save_credential(harness.role.id, "slack", replacement_ciphertext)

    harness.http.refresh_hook = reauthorize
    try:
        returned = token(harness)
    except CodedToolError:
        returned = None
    assert len(harness.http.refresh_calls) == 1
    assert returned in {None, LOGIN_ACCESS}
    assert harness.store.get_credential(harness.role.id, "slack") == replacement_ciphertext


def test_deletion_during_refresh_prevents_credential_resurrection(grant_harness, monkeypatch):
    harness = grant_harness
    rotating_grant(harness, monkeypatch)
    harness.http.refresh_hook = lambda: harness.store.delete_namespace(harness.role.id)
    with pytest.raises(CodedToolError):
        token(harness)
    assert len(harness.http.refresh_calls) == 1
    assert harness.store.get_role(harness.role.id) is None
    if harness.backend == "memory":
        assert (harness.role.id, "slack") not in harness.store.credentials
    else:
        with harness.store._connect() as connection:
            assert connection.execute("SELECT count(*) FROM connector_credentials WHERE role_id=%s", (harness.role.id,)).fetchone()[0] == 0


def test_revocation_during_refresh_preserves_old_ciphertext_and_denies_new_token(grant_harness, monkeypatch):
    harness = grant_harness
    ciphertext = rotating_grant(harness, monkeypatch)
    harness.http.refresh_hook = lambda: security_store().revoke_subject(harness.subject)
    with pytest.raises(CodedToolError) as caught:
        token(harness)
    assert caught.value.code in {AUTHORIZATION_REQUIRED, OAUTH_PENDING}
    assert len(harness.http.refresh_calls) == 1
    assert harness.store.get_credential(harness.role.id, "slack") == ciphertext


def test_concurrent_expired_grant_readers_redeem_refresh_only_once(grant_harness, monkeypatch):
    harness = grant_harness
    rotating_grant(harness, monkeypatch)
    first_in_exchange = threading.Event()
    release_exchange = threading.Event()
    second_checked_lock = threading.Event()
    worker_number = threading.local()
    original_lock = getattr(harness.store, "credential_lock", None)
    if original_lock is not None:
        @contextmanager
        def observed_lock(role_id, provider):
            with original_lock(role_id, provider) as acquired:
                if getattr(worker_number, "value", None) == 2:
                    second_checked_lock.set()
                yield acquired

        monkeypatch.setattr(harness.store, "credential_lock", observed_lock)

    def exchange():
        first_in_exchange.set()
        assert release_exchange.wait(5), "Concurrent fixture did not release its mocked exchange"

    harness.http.refresh_hook = exchange

    def read(index):
        worker_number.value = index
        actor = actor_subject.set(harness.subject)
        try:
            try:
                return token(harness)
            except CodedToolError as exc:
                return exc
        finally:
            actor_subject.reset(actor)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(read, 1)
        try:
            assert first_in_exchange.wait(2), "Expired rotating grant was never refreshed"
            second = executor.submit(read, 2)
            assert second_checked_lock.wait(2), "Second caller did not check the nonblocking credential lock"
        finally:
            release_exchange.set()
        outcomes = [first.result(timeout=5), second.result(timeout=5)]
    assert len(harness.http.refresh_calls) == 1
    assert any(result == NEW_ACCESS for result in outcomes)
    assert all(result == NEW_ACCESS or isinstance(result, CodedToolError) and result.code == CONNECTOR_FAILED for result in outcomes)
    assert payload(harness)["refresh_token"] == NEW_REFRESH
