"""Explicit opt-in integration cases for an isolated synthetic PostgreSQL DB."""

import os
import hashlib
import uuid
from datetime import date

import pytest

from errors import AUTHORIZATION_REQUIRED, CodedToolError
from security_store import SecurityStore
from store import actor_subject, current_store

pytestmark = pytest.mark.skipif(not os.environ.get("WISDOMTWIN_TEST_DATABASE_URL"), reason="Requires isolated pgvector test database")


def membership(db, roles):
    return db.provision(issuer="https://synthetic-idp.example", provider_subject=uuid.uuid4().hex,
                        email="reviewer@example-corp.com", domain="example-corp.com", roles=roles)


def test_postgres_durable_encrypted_grants_and_revocation():
    database_url = os.environ["WISDOMTWIN_TEST_DATABASE_URL"]
    db = SecurityStore(database_url=database_url)
    subject = membership(db, ["CRO"])
    key, family = uuid.uuid4().hex, uuid.uuid4().hex
    db.put("access", key, {"subject": subject, "private": "synthetic grant"}, ttl=60, subject=subject, family=family)
    other_process = SecurityStore(database_url=database_url)
    assert other_process.get("access", key)["private"] == "synthetic grant"
    with db.connection() as connection:
        payload = db.execute(connection, "SELECT payload FROM security_entries WHERE key_hash=?", (hashlib.sha256(key.encode()).hexdigest(),)).fetchone()[0]
        assert "synthetic grant" not in payload
    other_process.revoke_family(family)
    assert db.get("access", key) is None


def test_postgres_subject_and_entitlement_checks_on_direct_store_access(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", os.environ["WISDOMTWIN_TEST_DATABASE_URL"])
    monkeypatch.setenv("WISDOMTWIN_AUTH_DISABLED", "0")
    db = SecurityStore(database_url=os.environ["DATABASE_URL"])
    first, second = membership(db, ["CRO"]), membership(db, ["CRO"])
    store = current_store()
    actor = actor_subject.set(first)
    organization = store.upsert_organization("example-corp.com")
    role = store.create_role(organization.id, "CRO")
    person = store.ensure_officeholder(organization.id)
    store.open_tenure(role.id, person.id, date.today())
    job = store.create_job(role.id, "slack", "pipeline", 10)
    actor_subject.set(second)
    assert store.get_role(role.id) is None
    assert store.get_organization(organization.id) is None
    assert store.get_job(job.id) is None
    assert store.chunks_for_role(role.id) == []
    with pytest.raises(CodedToolError, match=AUTHORIZATION_REQUIRED):
        store.save_credential(role.id, "slack", "synthetic encrypted token")
    actor_subject.set(first)
    db.remove_member(first)
    assert store.get_role(role.id) is None
    actor_subject.reset(actor)


def test_postgres_complete_namespace_deletion():
    import service
    import ingest
    store = current_store()
    connected = service.connect_business_account("slack", "example-corp.com", "CRO")
    role_id = connected["role_id"]
    store.save_credential(role_id, "slack", "synthetic encrypted token")
    job = store.create_job(role_id, "slack", "pipeline", 10)
    ingest.run_job(job.id)
    assert service.request_namespace_deletion(role_id) == 10
    assert store.get_role(role_id) is None
    assert store.get_job(job.id) is None
    assert store.connections() == []
    with store._connect() as connection:
        for table in ("chunks", "tenures", "connections", "connector_credentials", "ingestion_jobs", "oauth_transactions"):
            assert connection.execute(f"SELECT count(*) FROM {table} WHERE role_id=%s", (role_id,)).fetchone()[0] == 0
