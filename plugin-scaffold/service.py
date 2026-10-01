"""The four WisdomTwin tools, plus namespace deletion and retention."""

from __future__ import annotations

import os
import secrets
import uuid
from datetime import date, datetime, timezone

from chunking import chunk_text
from connectors import fetch_drive, fetch_gmail, fetch_slack, use_fixtures
from domain import (
    COMING_SOON,
    MONTHLY_CHUNK_QUOTA,
    connector_enabled,
    domain_rejection_reason,
    normalize_domain,
    normalize_title,
)
from embeddings import embed_texts
from mcp.server.mcpserver.exceptions import ToolError

from errors import (
    DOMAIN_REJECTED,
    OAUTH_PENDING,
    QUOTA_EXCEEDED,
    CodedToolError,
)
from generation import EMPTY_CONTEXT, NON_BUSINESS_REFUSAL, answer_from_context, is_non_business
from oauth_connectors import google_authorize_url, new_pkce, slack_authorize_url
from retrieval import _terms, hybrid_search
from store import ChunkRecord, actor_subject, current_actor, current_store, retention_cutoff
from tokens import decrypt_token


def bind_actor() -> str:
    from auth_provider import auth_is_required

    if auth_is_required():
        from mcp.server.auth.middleware.auth_context import get_access_token

        token = get_access_token()
        subject = token.subject if token is not None and token.subject else "local"
        actor_subject.set(subject)
    return current_actor()


def _audit(tool_name: str, *, error_code: str | None = None, organization_id: str | None = None, role_id: str | None = None) -> None:
    current_store().write_audit(
        tool_name,
        error_code=error_code,
        organization_id=organization_id,
        role_id=role_id,
    )


def connect_business_account(service: str, domain: str, role_title: str) -> dict:
    bind_actor()
    store = current_store()
    normalized = normalize_domain(domain)
    reason = domain_rejection_reason(normalized)
    if reason:
        _audit("connect_business_account", error_code=DOMAIN_REJECTED)
        raise CodedToolError(DOMAIN_REJECTED, reason)
    title = normalize_title(role_title)
    if not title:
        _audit("connect_business_account")
        raise ToolError("A role title is required.")
    if service in {"gmail", "drive"} and not connector_enabled(service):
        _audit("connect_business_account", error_code=OAUTH_PENDING)
        raise CodedToolError(OAUTH_PENDING, COMING_SOON[service])
    if service == "slack" and not connector_enabled("slack"):
        _audit("connect_business_account", error_code=OAUTH_PENDING)
        raise CodedToolError(OAUTH_PENDING, "Slack is turned off by configuration.")

    organization = store.upsert_organization(normalized)
    person = store.ensure_officeholder(organization.id)
    role = store.create_role(organization.id, title)
    tenure = store.open_tenure(role.id, person.id, date.today())
    store.set_active_role(role.id)
    store.touch_role(role.id)
    store.record_connection(role.id, service, normalized, title)
    verifier, challenge = new_pkce()
    state = secrets.token_urlsafe(24)
    store.save_secret(
        state,
        {
            "verifier": verifier,
            "service": service,
            "role_id": role.id,
            "tenure_id": tenure.id,
        },
    )
    if service == "slack":
        oauth_url = slack_authorize_url(state=state, code_challenge=challenge)
    else:
        oauth_url = google_authorize_url(service=service, state=state, code_challenge=challenge)
    _audit("connect_business_account", organization_id=organization.id, role_id=role.id)
    return {"oauth_url": oauth_url, "status": "authorization_required", "role_id": role.id}


def _require_active_role():
    store = current_store()
    role_id = store.get_active_role_id()
    if not role_id:
        raise ToolError("Connect a role before ingesting.")
    role = store.get_role(role_id)
    if role is None:
        raise ToolError("The active role is no longer available.")
    return role


def ingest_data(service: str, query: str, max_items: int = 1000) -> dict:
    bind_actor()
    store = current_store()
    if service in {"gmail", "drive"} and not connector_enabled(service):
        _audit("ingest_data", error_code=OAUTH_PENDING)
        raise CodedToolError(OAUTH_PENDING, COMING_SOON[service])
    if service == "slack" and not connector_enabled("slack"):
        _audit("ingest_data", error_code=OAUTH_PENDING)
        raise CodedToolError(OAUTH_PENDING, "Slack is turned off by configuration.")
    if max_items < 1 or max_items > MONTHLY_CHUNK_QUOTA:
        _audit("ingest_data", error_code=QUOTA_EXCEEDED)
        raise CodedToolError(
            QUOTA_EXCEEDED,
            f"max_items is outside the free-tier monthly quota of {MONTHLY_CHUNK_QUOTA} chunks.",
        )

    role = _require_active_role()
    organization = store.get_organization(role.organization_id)
    used = store.monthly_chunk_count(role.organization_id)
    remaining = MONTHLY_CHUNK_QUOTA - used
    if max_items > remaining:
        _audit("ingest_data", error_code=QUOTA_EXCEEDED, organization_id=role.organization_id, role_id=role.id)
        raise CodedToolError(
            QUOTA_EXCEEDED,
            f"max_items exceeds the free-tier monthly quota of {MONTHLY_CHUNK_QUOTA} chunks.",
        )
    job = store.create_job(role.id, service, query, max_items)
    _audit("ingest_data", organization_id=role.organization_id, role_id=role.id)
    if os.environ.get("REDIS_URL", "").strip():
        from ingest import ingest_job

        ingest_job.delay(job.id)
        return {"job_id": job.id, "progress": job.progress, "chunks_ingested": job.chunks_ingested}
    from ingest import run_job

    finished = run_job(job.id)
    if organization:
        store.touch_role(role.id)
    return {
        "job_id": finished.id,
        "progress": finished.progress,
        "chunks_ingested": finished.chunks_ingested,
    }


def query_twin(question: str, max_results: int = 10, max_tokens: int = 512) -> dict:
    bind_actor()
    store = current_store()
    role_id = store.get_active_role_id()
    role = store.get_role(role_id) if role_id else None
    organization_id = role.organization_id if role else None
    if is_non_business(question):
        _audit("query_twin", organization_id=organization_id, role_id=role_id)
        return {"answer": NON_BUSINESS_REFUSAL, "citations": []}
    if role is None or not store.chunks_for_role(role.id):
        _audit("query_twin", organization_id=organization_id, role_id=role_id)
        return {"answer": EMPTY_CONTEXT, "citations": []}
    embedding = embed_texts([question])[0]
    ranked = hybrid_search(
        store,
        role_id=role.id,
        question=question,
        embedding=embedding,
        limit=max(1, min(max_results, 10)),
    )
    chunks = [item.chunk for item in ranked]
    question_terms = set(_terms(question))
    supporting = [chunk for chunk in chunks if question_terms & set(_terms(chunk.excerpt))]
    chunks = supporting or chunks[:1]
    if not chunks:
        _audit("query_twin", organization_id=organization_id, role_id=role.id)
        return {"answer": EMPTY_CONTEXT, "citations": []}
    answer = answer_from_context(question, chunks, max_tokens)
    citations = [{"uri": chunk.uri, "snippet": chunk.excerpt[:240]} for chunk in chunks]
    store.touch_role(role.id)
    _audit("query_twin", organization_id=organization_id, role_id=role.id)
    return {"answer": answer, "citations": citations}


def list_twins_status() -> list[dict]:
    bind_actor()
    store = current_store()
    rows = []
    for connection in store.connections():
        chunks = store.chunks_for_role(connection.role_id)
        last_update = None
        if chunks:
            last_update = max(chunk.created_at for chunk in chunks).isoformat()
        else:
            last_update = connection.connected_at.isoformat()
        rows.append(
            {
                "service": connection.service,
                "role_title": connection.role_title,
                "ingested_chunks": len(chunks),
                "last_update": last_update,
                "domain": connection.domain,
            }
        )
    role_id = store.get_active_role_id()
    _audit("list_twins_status", role_id=role_id)
    return rows


def request_namespace_deletion(role_id: str) -> int:
    store = current_store()
    removed = store.delete_namespace(role_id)
    _audit("namespace_deletion", role_id=role_id)
    return removed


def sweep_expired(now: datetime | None = None) -> int:
    store = current_store()
    moment = now or datetime.now(timezone.utc)
    removed = 0
    for role in store.roles_inactive_before(retention_cutoff(moment)):
        removed += store.delete_namespace(role.id)
        _audit("retention_sweep", organization_id=role.organization_id, role_id=role.id)
    return removed


def connector_token(role_id: str, service: str) -> str:
    if use_fixtures() and service == "slack":
        return ""
    ciphertext = current_store().get_credential(role_id, service)
    if not ciphertext:
        return ""
    return decrypt_token(ciphertext)


def build_indexed_chunks(role_id: str, tenure_id: str, author_person_id: str, service: str, items: list[dict[str, str]]) -> list[ChunkRecord]:
    pieces: list[tuple[str, str]] = []
    for item in items:
        for excerpt in chunk_text(item["text"]):
            pieces.append((item["uri"], excerpt))
    if not pieces:
        return []
    vectors = embed_texts([excerpt for _, excerpt in pieces])
    created = datetime.now(timezone.utc)
    records: list[ChunkRecord] = []
    seen_uris: dict[str, int] = {}
    for (uri, excerpt), vector in zip(pieces, vectors):
        seen_uris[uri] = seen_uris.get(uri, 0) + 1
        chunk_uri = uri if seen_uris[uri] == 1 else f"{uri}#chunk-{seen_uris[uri]}"
        records.append(
            ChunkRecord(
                id=str(uuid.uuid4()),
                role_id=role_id,
                tenure_id=tenure_id,
                author_person_id=author_person_id,
                service=service,
                uri=chunk_uri,
                excerpt=excerpt,
                embedding=vector,
                created_at=created,
            )
        )
    return records
