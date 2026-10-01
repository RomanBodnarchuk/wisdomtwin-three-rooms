"""The four WisdomTwin tools, plus namespace deletion and retention."""

from __future__ import annotations

import os
import secrets
import json
import time
import hashlib
from dataclasses import replace
import uuid
import contextvars
from functools import wraps
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
    AUTHORIZATION_REQUIRED,
)
from generation import EMPTY_CONTEXT, NON_BUSINESS_REFUSAL, answer_from_context, is_non_business
from oauth_connectors import google_authorize_url, new_pkce, slack_authorize_url, public_base_url
from retrieval import _terms, hybrid_search
from store import ChunkRecord, actor_subject, current_actor, current_store, retention_cutoff
from tokens import decrypt_token
from safety import unsafe_text

_call_audited = contextvars.ContextVar("wisdomtwin_call_audited", default=False)


def audited_tool(function):
    """Record failures as well as successful branches without logging inputs."""
    @wraps(function)
    def called(*args, **kwargs):
        marker = _call_audited.set(False)
        actor = actor_subject.set(current_actor())
        try:
            result = function(*args, **kwargs)
            if not _call_audited.get():
                _audit(function.__name__)
            return result
        except Exception as exc:
            # An initial queued event is not proof of a successful tool return.
            try:
                from errors import CONNECTOR_FAILED
                _audit(function.__name__, error_code=getattr(exc, "code", CONNECTOR_FAILED))
            except Exception:
                pass  # Preserve the original error if storage itself is down.
            raise
        finally:
            actor_subject.reset(actor)
            _call_audited.reset(marker)
    return called


def bind_actor() -> str:
    from auth_provider import auth_is_required

    if auth_is_required():
        from mcp.server.auth.middleware.auth_context import get_access_token

        token = get_access_token()
        if token is None or not token.subject or token.subject == "local" or token.resource != f"{public_base_url()}/mcp" or "twin:read" not in token.scopes:
            actor_subject.set("unauthenticated")
            raise CodedToolError(AUTHORIZATION_REQUIRED, "A verified corporate login is required.")
        actor_subject.set(token.subject)
    return current_actor()


def _audit(tool_name: str, *, error_code: str | None = None, organization_id: str | None = None, role_id: str | None = None) -> None:
    current_store().write_audit(
        tool_name,
        error_code=error_code,
        organization_id=organization_id,
        role_id=role_id,
    )
    _call_audited.set(True)


@audited_tool
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
    from auth_provider import auth_is_required
    from security_store import require_membership
    if auth_is_required():
        require_membership(current_actor(), normalized, title)
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
            "subject": current_actor(),
            "domain": normalized,
            "role_title": title,
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


@audited_tool
def ingest_data(service: str, query: str, max_items: int = 1000) -> dict:
    bind_actor()
    store = current_store()
    if not query.strip() or len(query) > 1024 or unsafe_text(query):
        raise ToolError("Use a short business search query without secrets or restricted identifiers.")
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

        try:
            ingest_job.delay(job.id, current_actor())
        except Exception:
            store.update_job(job.id, status="failed", progress=0, chunks_ingested=0)
            raise ToolError("The ingestion worker is unavailable. Retry after service recovery.") from None
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


@audited_tool
def query_twin(question: str, max_results: int = 10, max_tokens: int = 512) -> dict:
    bind_actor()
    store = current_store()
    role_id = store.get_active_role_id()
    role = store.get_role(role_id) if role_id else None
    organization_id = role.organization_id if role else None
    if is_non_business(question):
        _audit("query_twin", organization_id=organization_id, role_id=role_id)
        return {"answer": NON_BUSINESS_REFUSAL, "citations": []}
    if role is None:
        _audit("query_twin", organization_id=organization_id, role_id=role_id)
        return {"answer": EMPTY_CONTEXT, "citations": []}
    if not store.chunks_for_role(role.id):
        _audit("query_twin", organization_id=organization_id, role_id=role.id)
        return {"answer": EMPTY_CONTEXT, "citations": []}
    embedding = embed_texts([question])[0]
    ranked = hybrid_search(store, role_id=role.id, question=question, embedding=embedding,
                           limit=max(1, min(max_results, 10)))
    chunks = [item.chunk for item in ranked]
    if not use_fixtures():
        chunks = hydrate_sources(chunks)
    question_terms = set(_terms(question))
    supporting = [chunk for chunk in chunks if question_terms & set(_terms(chunk.excerpt)) and not unsafe_text(chunk.excerpt)]
    chunks = supporting
    if not chunks:
        _audit("query_twin", organization_id=organization_id, role_id=role.id)
        return {"answer": EMPTY_CONTEXT, "citations": []}
    chunks = chunks[:3]
    # Return exact source excerpts; ChatGPT performs synthesis in the conversation.
    # Citation snippets contain every returned excerpt, including chunk offsets.
    answer = answer_from_context(question, chunks, max(32, min(max_tokens, 2048)))
    if answer == EMPTY_CONTEXT:
        chunks = []
    citations = [{"uri": chunk.uri, "snippet": chunk.excerpt, "trust": "untrusted_source_data"} for chunk in chunks]
    store.touch_role(role.id)
    _audit("query_twin", organization_id=organization_id, role_id=role.id)
    return {"answer": answer, "citations": citations}


@audited_tool
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
    role = store.get_role(role_id)
    if role is None:
        raise CodedToolError(AUTHORIZATION_REQUIRED, "Role access is not authorized.")
    removed = store.delete_namespace(role_id)
    _audit("namespace_deletion", role_id=role_id)
    from auth_provider import auth_is_required
    if auth_is_required():
        from security_store import security_store
        security_store().revoke_subject(current_actor())
    return removed


def sweep_expired(now: datetime | None = None) -> int:
    store = current_store()
    moment = now or datetime.now(timezone.utc)
    removed = 0
    from store import _maintenance
    for role in store.roles_inactive_before(retention_cutoff(moment)):
        actor = actor_subject.set(store.owner_for_retention(role.id))
        maintenance = _maintenance.set(True)
        try:
            removed += store.delete_namespace(role.id, if_inactive_before=retention_cutoff(moment))
            if store.get_role(role.id) is not None:
                continue
            _audit("retention_sweep", organization_id=role.organization_id, role_id=role.id)
            from security_store import security_store
            if os.environ.get("DATABASE_URL") or os.environ.get("WISDOMTWIN_AUTH_DB"):
                security_store().revoke_subject(current_actor())
        finally:
            _maintenance.reset(maintenance)
            actor_subject.reset(actor)
    if os.environ.get("DATABASE_URL") or os.environ.get("WISDOMTWIN_AUTH_DB"):
        from security_store import security_store
        security_store().sweep()
    store.cleanup_transients(retention_cutoff(moment))
    return removed


def connector_token(role_id: str, service: str) -> str:
    if use_fixtures() and service == "slack":
        return ""
    ciphertext = current_store().get_credential(role_id, service)
    if not ciphertext:
        return ""
    payload = json.loads(decrypt_token(ciphertext))
    if payload.get("subject") != current_actor() or payload.get("role_id") != role_id or payload.get("service") != service or payload.get("expires_at", 0) <= time.time():
        return ""
    from security_store import require_membership
    role = current_store().get_role(role_id)
    org = current_store().get_organization(role.organization_id)
    member = require_membership(current_actor(), org.domain, role.title)
    if service == "slack" and (payload.get("team_id") != member["slack_team_id"] or payload.get("user_id") != member["slack_user_id"]):
        return ""
    if service in {"gmail", "drive"} and payload.get("provider_subject") != member["google_subject"]:
        return ""
    return payload["access_token"]


def build_indexed_chunks(role_id: str, tenure_id: str, author_person_id: str, service: str,
                         items: list[dict[str, str]], *, metadata_only: bool | None = None,
                         remaining_chunks: int | None = None) -> list[ChunkRecord]:
    metadata_only = not use_fixtures() if metadata_only is None else metadata_only
    store = current_store()
    role = store.get_role(role_id)
    if role is None:
        raise CodedToolError(AUTHORIZATION_REQUIRED, "Role access is not authorized.")
    pieces = []
    for item in items:
        if unsafe_text(item["text"]):
            continue
        provider_author = item.get("author_provider_id", "")
        if metadata_only and not provider_author:
            raise ToolError("The provider did not supply source authorship; ingestion was stopped.")
        source_author = store.ensure_source_author(role.organization_id, service, provider_author).id if provider_author else author_person_id
        for index, excerpt in enumerate(chunk_text(item["text"])):
            pieces.append((item["uri"], excerpt, index, source_author))
    if remaining_chunks is not None and len(pieces) > remaining_chunks:
        raise CodedToolError(QUOTA_EXCEEDED, "Expanded chunks exceed the monthly quota.")
    if not pieces:
        return []
    vectors = embed_texts([excerpt for _, excerpt, _, _ in pieces])
    created = datetime.now(timezone.utc)
    records = []
    for (uri, excerpt, index, source_author), vector in zip(pieces, vectors):
        records.append(ChunkRecord(
            id=str(uuid.uuid4()), role_id=role_id, tenure_id=tenure_id, author_person_id=source_author,
            service=service, uri=uri if index == 0 else f"{uri}#chunk-{index + 1}",
            excerpt="" if metadata_only else excerpt, embedding=vector, created_at=created,
            source_uri=uri, source_hash=hashlib.sha256(excerpt.encode()).hexdigest(), chunk_index=index,
            keyword_hashes=sorted({hashlib.sha256(term.encode()).hexdigest() for term in _terms(excerpt)}),
        ))
    return records


def hydrate_sources(records: list[ChunkRecord]) -> list[ChunkRecord]:
    """Re-fetch text with the current user's token and discard changed/inaccessible sources."""
    from connectors import refetch_slack, refetch_google, SourceUnavailable, SourceRateLimited
    from errors import CONNECTOR_FAILED

    hydrated = []
    cache: dict[tuple[str, str], dict | None] = {}
    for record in records:
        # Legacy records containing raw excerpts are never returned in production.
        if record.excerpt or not record.source_uri or not record.source_hash or not connector_enabled(record.service):
            continue
        key = (record.service, record.source_uri)
        if key not in cache:
            token = connector_token(record.role_id, record.service)
            if not token:
                continue
            try:
                cache[key] = refetch_slack(token, record.source_uri) if record.service == "slack" else refetch_google(token, record.service, record.source_uri)
            except SourceUnavailable:
                cache[key] = None
            except SourceRateLimited as exc:
                import math

                _audit("query_twin", error_code=CONNECTOR_FAILED, role_id=record.role_id)
                guidance = (f"Retry after at least {math.ceil(exc.retry_after_seconds)} seconds."
                            if exc.retry_after_seconds is not None else "Retry after the provider's rate limit clears.")
                raise CodedToolError(CONNECTOR_FAILED, f"Source provider is rate limited. {guidance}") from None
            except Exception:
                _audit("query_twin", error_code=CONNECTOR_FAILED, role_id=record.role_id)
                raise CodedToolError(CONNECTOR_FAILED, "Source revalidation failed. Retry after the provider recovers.") from None
        source = cache.get(key)
        if not source or unsafe_text(source["text"]):
            continue
        role = current_store().get_role(record.role_id)
        if role is None:
            continue
        author_id = str(uuid.uuid5(uuid.UUID(role.organization_id), f"{record.service}:{source.get('author_provider_id', '')}"))
        if author_id != record.author_person_id:
            continue
        excerpts = chunk_text(source["text"])
        if record.chunk_index >= len(excerpts):
            continue
        excerpt = excerpts[record.chunk_index]
        if hashlib.sha256(excerpt.encode()).hexdigest() != record.source_hash:
            continue
        hydrated.append(replace(record, excerpt=excerpt))
    return hydrated
