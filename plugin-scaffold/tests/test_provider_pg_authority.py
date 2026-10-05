"""Offline connector refresh with credentials and membership on real PostgreSQL.

The explicit test database must be on loopback and named *_test. Each fixture
owns one synthetic subject/role; cleanup never resets or truncates shared tables.
Bounded PostgreSQL timeouts expose a nested epoch/membership lock regression.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
import hashlib
import io
import ipaddress
import json
import os
import threading
import time
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit
import uuid

from cryptography.fernet import Fernet
import pytest

import corporate_login
from errors import AUTHORIZATION_REQUIRED, CodedToolError
from oauth_connectors import SLACK_USER_SCOPES
import provider_binding
from provider_lifecycle import resolve_connector_token
from security_store import SecurityStore, security_store
from store import MemoryStore, PostgresStore, actor_subject, reset_store
from tokens import decrypt_token


def isolated_postgres_dsn():
    value = os.environ.get("WISDOMTWIN_TEST_DATABASE_URL", "").strip()
    if not value:
        pytest.skip("Requires an explicitly configured loopback *_test PostgreSQL database")
    from psycopg.conninfo import conninfo_to_dict, make_conninfo

    params = conninfo_to_dict(value)
    host = params.get("host", "")
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host == "localhost"
    assert loopback and params.get("dbname", "").endswith("_test"), "Refusing a non-loopback or non-test database"
    assert not params.get("service"), "Service aliases are not allowed in this isolated test"
    if params.get("hostaddr"):
        assert ipaddress.ip_address(params["hostaddr"]).is_loopback
    return make_conninfo(value, connect_timeout=3,
        options="-c statement_timeout=3000 -c lock_timeout=2500",
        application_name="wisdomtwin-provider-pg-authority-review")


@pytest.fixture(autouse=True)
def isolated_security_state(tmp_path, monkeypatch):
    """Override conftest's opt-in truncating reset with explicit memory resets."""
    monkeypatch.setenv("WISDOMTWIN_AUTH_DB", str(tmp_path / "unused-authority.sqlite3"))
    monkeypatch.setenv("CONNECTOR_TOKEN_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("WISDOMTWIN_AUTH_DISABLED", "0")
    monkeypatch.setenv("SLACK_TOKEN_REFRESH_ENABLED", "true")
    monkeypatch.setenv("SLACK_CLIENT_ID", "synthetic-pg-refresh-client")
    monkeypatch.setenv("SLACK_CLIENT_SECRET", "synthetic-pg-refresh-secret")
    monkeypatch.delenv("WISDOMTWIN_ALLOW_PAID_MODEL_APIS", raising=False)
    reset_store(MemoryStore())
    actor = actor_subject.set("local")

    def forbidden(*args, **kwargs):
        pytest.fail("PostgreSQL authority tests must never call a real provider or paid API")

    monkeypatch.setattr("urllib.request.urlopen", forbidden)
    monkeypatch.setattr(corporate_login, "urlopen", forbidden)
    yield
    reset_store(MemoryStore())
    actor_subject.reset(actor)


class OfflineSlack:
    def __init__(self, identity, old_access, old_refresh, new_access, new_refresh):
        self.identity = identity
        self.old_access, self.old_refresh = old_access, old_refresh
        self.new_access, self.new_refresh = new_access, new_refresh
        self.calls = []
        self.refresh_hook = None

    def urlopen(self, request, timeout):
        url = urlsplit(request.full_url)
        assert url.scheme == "https" and url.hostname == "slack.com"
        assert 0 < timeout <= 30
        self.calls.append(url.path)
        if url.path == "/api/oauth.v2.access":
            body = parse_qs(request.data.decode())
            assert request.get_method() == "POST"
            assert body == {"grant_type": ["refresh_token"], "refresh_token": [self.old_refresh],
                "client_id": ["synthetic-pg-refresh-client"], "client_secret": ["synthetic-pg-refresh-secret"]}
            if self.refresh_hook:
                self.refresh_hook()
            response = {"ok": True, "token_type": "user", "access_token": self.new_access,
                "refresh_token": self.new_refresh, "expires_in": 43200, "scope": ",".join(SLACK_USER_SCOPES)}
        elif url.path == "/api/auth.test":
            assert request.get_header("Authorization") in {f"Bearer {self.old_access}", f"Bearer {self.new_access}"}
            response = {"ok": True, "team_id": self.identity["slack_team_id"], "user_id": self.identity["slack_user_id"]}
        elif url.path == "/api/users.info":
            assert parse_qs(url.query)["user"] == [self.identity["slack_user_id"]]
            response = {"ok": True, "user": {"id": self.identity["slack_user_id"],
                "profile": {"email": self.identity["email"]}}}
        else:
            pytest.fail(f"Unexpected offline Slack endpoint: {url.path}")
        return io.BytesIO(json.dumps(response).encode())


@pytest.fixture
def pg_authority(monkeypatch):
    dsn = isolated_postgres_dsn()
    monkeypatch.setenv("DATABASE_URL", dsn)
    repository = security_store()
    assert repository.database_url == dsn
    store = PostgresStore(dsn)
    reset_store(store)
    unique = uuid.uuid4().hex
    identity = {"issuer": "https://synthetic-pg-provider-authority.test", "provider_subject": unique,
        "email": "reviewer@example-corp.com", "domain": "example-corp.com", "roles": ["CRO"],
        "slack_team_id": f"SYNTHETIC_TEAM_{unique}", "slack_user_id": f"SYNTHETIC_USER_{unique}"}
    subject = repository.provision(**identity)
    actor = actor_subject.set(subject)
    org = store.upsert_organization(identity["domain"])
    role = store.create_role(org.id, "CRO")
    store.open_tenure(role.id, store.ensure_officeholder(org.id).id, date.today())
    store.record_connection(role.id, "slack", org.domain, role.title)
    http = OfflineSlack(identity, f"synthetic-old-access-{unique}", f"synthetic-old-refresh-{unique}",
        f"synthetic-new-access-{unique}", f"synthetic-new-refresh-{unique}")
    monkeypatch.setattr("urllib.request.urlopen", http.urlopen)
    monkeypatch.setattr(corporate_login, "urlopen", http.urlopen)
    harness = SimpleNamespace(dsn=dsn, repository=repository, store=store, identity=identity,
        subject=subject, role=role, http=http, attempt_hashes=set(), pending={"subject": subject,
        "role_id": role.id, "domain": org.domain, "role_title": role.title, "service": "slack"})
    try:
        yield harness
    finally:
        # Re-establish only this synthetic member if the race removed it, solely
        # to authorize the normal namespace cleanup with auth still enabled.
        if repository.membership(subject) is None:
            repository.provision(**identity)
        if store.get_role(role.id) is not None:
            store.delete_namespace(role.id)
        repository.remove_member(subject)
        with repository.connection() as connection:
            repository.execute(connection, "DELETE FROM security_subject_epochs WHERE subject=?", (subject,))
            for digest in harness.attempt_hashes:
                repository.execute(connection, "DELETE FROM security_entries WHERE kind='provider_refresh_attempt' AND key_hash=?", (digest,))
        actor_subject.reset(actor)


def save_grant(harness, *, expired):
    http = harness.http
    token = http.old_access if expired else http.new_access
    refresh = http.old_refresh if expired else http.new_refresh
    body = {"ok": True, "team": {"id": harness.identity["slack_team_id"]}, "authed_user": {
        "id": harness.identity["slack_user_id"], "access_token": token, "refresh_token": refresh,
        "token_type": "user", "expires_in": 43200, "scope": ",".join(SLACK_USER_SCOPES)}}
    provider_binding.bind_slack(harness.pending, harness.repository.membership(harness.subject), body)
    ciphertext = harness.store.get_credential(harness.role.id, "slack")
    if expired:
        # Backdate only our encrypted synthetic grant; no global clock changes.
        from tokens import encrypt_token

        payload = json.loads(decrypt_token(ciphertext))
        payload["expires_at"] = time.time() - 1
        ciphertext = encrypt_token(json.dumps(payload))
        harness.store.save_credential(harness.role.id, "slack", ciphertext)
        attempt_key = hashlib.sha256(ciphertext.encode()).hexdigest()
        harness.attempt_hashes.add(hashlib.sha256(attempt_key.encode()).hexdigest())
    http.calls.clear()
    return ciphertext


def raw_credential(harness):
    with harness.store._connect() as connection:
        row = connection.execute("SELECT token_ciphertext FROM connector_credentials WHERE role_id=%s AND service='slack'",
                                 (harness.role.id,)).fetchone()
    return row[0] if row else None


def resolve_as_subject(harness):
    actor = actor_subject.set(harness.subject)
    try:
        return resolve_connector_token(harness.role.id, "slack")
    finally:
        actor_subject.reset(actor)


def test_pg_epoch_guard_nested_membership_and_constructor_complete_successful_refresh(pg_authority):
    harness = pg_authority
    old = save_grant(harness, expired=True)
    epoch = harness.repository.subject_epoch(harness.subject)
    # Auth is enabled, so the real guard performs nested _bound_payload role
    # checks, SecurityStore constructors and PostgreSQL membership reads.
    assert resolve_as_subject(harness) == harness.http.new_access
    ciphertext = raw_credential(harness)
    assert ciphertext != old and harness.http.new_access not in ciphertext and harness.http.new_refresh not in ciphertext
    saved = json.loads(decrypt_token(ciphertext))
    assert saved["access_token"] == harness.http.new_access and saved["refresh_token"] == harness.http.new_refresh
    assert saved["subject"] == harness.subject and saved["role_id"] == harness.role.id
    assert set(saved["scopes"]) == set(SLACK_USER_SCOPES)
    assert harness.repository.subject_epoch(harness.subject) == epoch
    assert harness.http.calls == ["/api/oauth.v2.access", "/api/auth.test", "/api/users.info"]
    harness.http.calls.clear()
    assert resolve_as_subject(harness) == harness.http.new_access
    assert harness.http.calls == []


@pytest.mark.parametrize("mutation", ["revoke_subject", "reprovision", "remove_and_reprovision", "remove_member"])
def test_pg_membership_epoch_change_during_refresh_blocks_replacement(pg_authority, mutation):
    harness = pg_authority
    old = save_grant(harness, expired=True)
    epoch = harness.repository.subject_epoch(harness.subject)
    entered, release = threading.Event(), threading.Event()

    def pause():
        entered.set()
        assert release.wait(8), "Synthetic refresh response was not released"

    harness.http.refresh_hook = pause
    with ThreadPoolExecutor(max_workers=1) as executor:
        result = executor.submit(resolve_as_subject, harness)
        try:
            assert entered.wait(8), "Refresh never reached the offline provider"
            other = SecurityStore(database_url=harness.dsn)
            if mutation == "revoke_subject":
                other.revoke_subject(harness.subject)
            elif mutation == "remove_member":
                other.remove_member(harness.subject)
            else:
                if mutation == "remove_and_reprovision":
                    other.remove_member(harness.subject)
                assert other.provision(**harness.identity) == harness.subject
            assert other.subject_epoch(harness.subject) > epoch
        finally:
            release.set()
        with pytest.raises(CodedToolError) as caught:
            result.result(timeout=8)
    assert caught.value.code == AUTHORIZATION_REQUIRED
    assert raw_credential(harness) == old
    assert harness.http.calls.count("/api/oauth.v2.access") == 1
    # A fresh provider authorization is usable after the epoch change.
    harness.http.refresh_hook = None
    if harness.repository.membership(harness.subject) is None:
        harness.repository.provision(**harness.identity)
    save_grant(harness, expired=False)
    assert resolve_as_subject(harness) == harness.http.new_access
    assert harness.http.calls == []


def test_pg_namespace_deletion_during_refresh_never_restores_credentials(pg_authority):
    harness = pg_authority
    save_grant(harness, expired=True)
    entered, release = threading.Event(), threading.Event()

    def pause():
        entered.set()
        assert release.wait(8), "Synthetic refresh response was not released"

    harness.http.refresh_hook = pause
    with ThreadPoolExecutor(max_workers=1) as executor:
        result = executor.submit(resolve_as_subject, harness)
        try:
            assert entered.wait(8), "Refresh never reached the offline provider"
            harness.store.delete_namespace(harness.role.id)
        finally:
            release.set()
        with pytest.raises(CodedToolError) as caught:
            result.result(timeout=8)
    assert caught.value.code == AUTHORIZATION_REQUIRED
    assert harness.store.get_role(harness.role.id) is None
    assert raw_credential(harness) is None
    assert harness.http.calls.count("/api/oauth.v2.access") == 1


def test_session_locks_are_not_held_inside_an_open_transaction(pg_authority):
    store = pg_authority.store
    probe = store._psycopg.connect(store._database_url, autocommit=True)
    try:
        holders = (
            store.job_lock("synthetic-job-lock"),
            store.credential_lock(pg_authority.role.id, "slack"),
        )
        for holder in holders:
            with holder as acquired:
                assert acquired
                rows = probe.execute(
                    """
                    SELECT state FROM pg_stat_activity
                    WHERE application_name = 'wisdomtwin-session-lock'
                      AND pid <> pg_backend_pid()
                    """
                ).fetchall()
                assert rows
                assert all(row[0] == "idle" for row in rows)
    finally:
        probe.close()
