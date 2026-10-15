"""Worker exclusion and tenure invariants; also run with a real test database."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
import threading

import ingest
import service
from store import current_store


def role_and_job():
    connected = service.connect_business_account("slack", "example-corp.com", "CRO")
    store = current_store()
    role = store.get_role(connected["role_id"])
    job = store.create_job(role.id, "slack", "pipeline", 10)
    return store, role, job


def test_duplicate_worker_delivery_fetches_once(monkeypatch):
    store, role, job = role_and_job()
    original = ingest.fetch_slack
    entered, finish = threading.Event(), threading.Event()
    calls = []

    def fetch(*args):
        calls.append(1)
        entered.set()
        assert finish.wait(5)
        return original(*args)

    monkeypatch.setattr(ingest, "fetch_slack", fetch)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(ingest.run_job, job.id, "local")
        assert entered.wait(5)
        second = pool.submit(ingest.run_job, job.id, "local")
        assert second.result(timeout=5).status == "running"
        finish.set()
        assert first.result(timeout=10).status == "completed"
    assert calls == [1]
    assert len(store.chunks_for_role(role.id)) == 10


def test_simultaneous_open_tenure_has_one_officeholder():
    store, role, _ = role_and_job()
    person = store.ensure_officeholder(role.organization_id)
    with ThreadPoolExecutor(max_workers=6) as pool:
        tenures = list(pool.map(lambda _: store.open_tenure(role.id, person.id, date.today()), range(12)))
    assert len({tenure.id for tenure in tenures}) == 1
    assert store.open_tenure_count(role.id) == 1


def test_worker_lock_releases_after_failure(monkeypatch):
    import pytest
    from errors import CodedToolError

    store, role, job = role_and_job()
    original = ingest.fetch_slack
    monkeypatch.setattr(ingest, "fetch_slack", lambda *args: (_ for _ in ()).throw(RuntimeError("synthetic outage")))
    with pytest.raises(CodedToolError, match="CONNECTOR_FAILED"):
        ingest.run_job(job.id)
    monkeypatch.setattr(ingest, "fetch_slack", original)
    assert ingest.run_job(job.id).status == "completed"


def test_source_author_never_becomes_officeholder():
    store = current_store()
    organization = store.upsert_organization("example-corp.com")
    author = store.ensure_source_author(organization.id, "slack", "U_OTHER_AUTHOR")
    officeholder = store.ensure_officeholder(organization.id)
    assert officeholder.id != author.id
    assert officeholder.id == store.ensure_officeholder(organization.id).id


def test_restricted_search_query_creates_no_persistent_job():
    import pytest
    from mcp.server.mcpserver.exceptions import ToolError

    store, role, _ = role_and_job()
    before = len(store.jobs_for_role(role.id))
    with pytest.raises(ToolError):
        service.ingest_data("slack", "credit card 4111111111111111", 10)
    assert len(store.jobs_for_role(role.id)) == before
    assert store.audits()[-1].tool_name == "ingest_data"
