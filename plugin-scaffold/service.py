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
from collections import Counter
from functools import wraps
from datetime import date, datetime, timezone

from cryptography.fernet import InvalidToken

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
from runtime import max_source_fetches
from store import ChunkRecord, actor_subject, current_actor, current_store, retention_cutoff
from tokens import decrypt_token, keyword_hash
from safety import identifier_or_injection, restricted_topic, skip_reason, unsafe_text

_call_audited = contextvars.ContextVar("wisdomtwin_call_audited", default=False)

# query_twin never cites more than this many chunks, so it never verifies more.
MAX_CITED_CHUNKS = 3
_SERVICE_NAMES = {"slack": "Slack", "gmail": "Gmail", "drive": "Google Drive"}


class GrantUnavailable(Exception):
    """The caller has no current source grant: missing, expired or bound to another identity."""

    def __init__(self, service: str) -> None:
        self.service = service
        super().__init__(f"No current {service} grant")


def _service_names(services: list[str]) -> str:
    names = list(dict.fromkeys(_SERVICE_NAMES.get(service, service) for service in services))
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def reconnect_error(services: list[str], purpose: str) -> CodedToolError:
    return CodedToolError(OAUTH_PENDING, f"Reconnect {_service_names(services)} with connect_business_account {purpose}.")


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
    if not query.strip() or len(query) > 1024 or identifier_or_injection(query):
        raise ToolError("Use a short business search query without secrets or restricted identifiers.")
    if restricted_topic(query):
        raise ToolError("This search query names a restricted topic (for example patient or credit card); "
                        "items on these topics are not indexed.")
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
    # Queued job status carries no error code, so a lapsed grant is reported
    # here; the worker re-checks it in case the grant lapses while queued.
    try:
        connector_token(role.id, service)
    except GrantUnavailable:
        _audit("ingest_data", error_code=OAUTH_PENDING, organization_id=role.organization_id, role_id=role.id)
        raise reconnect_error([service], "before ingesting again") from None
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
    question_terms = set(_terms(question))

    def supports(chunk: ChunkRecord) -> bool:
        return bool(question_terms & set(_terms(chunk.excerpt))) and not unsafe_text(chunk.excerpt)

    if use_fixtures():
        chunks = [chunk for chunk in chunks if supports(chunk)]
    else:
        # A chunk whose stored keyword hashes share no question term cannot pass
        # `supports`, so it must not spend the per-query fetch budget first.
        # Demote, do not drop: rows hashed under another key still verify.
        # Bare SHA-256 hashes are pre-HMAC rows awaiting re-indexing.
        wanted = ({keyword_hash(term) for term in question_terms}
                  | {hashlib.sha256(term.encode()).hexdigest() for term in question_terms})
        # sorted is stable, so rank order is kept within each group.
        chunks = sorted(chunks, key=lambda chunk: not (wanted & set(chunk.keyword_hashes)))
        # Verify lazily in that order and stop once enough support exists to cite.
        chunks = hydrate_sources(chunks, keep=supports, limit=MAX_CITED_CHUNKS)
    if not chunks:
        _audit("query_twin", organization_id=organization_id, role_id=role.id)
        return {"answer": EMPTY_CONTEXT, "citations": []}
    chunks = chunks[:MAX_CITED_CHUNKS]
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
    """Return the caller's current grant, or raise GrantUnavailable so callers can ask for a reconnect.

    Fixture Slack needs no token and returns an empty string.
    """
    if use_fixtures() and service == "slack":
        return ""
    ciphertext = current_store().get_credential(role_id, service)
    if not ciphertext:
        raise GrantUnavailable(service)
    # A grant stored under a rotated CONNECTOR_TOKEN_KEY, or a corrupted one, needs a
    # reconnect, which overwrites it under the current key. A malformed key still fails loudly.
    try:
        plaintext = decrypt_token(ciphertext)
    except (InvalidToken, UnicodeDecodeError):
        raise GrantUnavailable(service) from None
    try:
        payload = json.loads(plaintext)
    except ValueError:
        raise GrantUnavailable(service) from None
    if not isinstance(payload, dict):
        raise GrantUnavailable(service)
    # None means the provider set no lifetime; a missing key fails closed.
    expires_at = payload.get("expires_at", 0)
    if payload.get("subject") != current_actor() or payload.get("role_id") != role_id or payload.get("service") != service or (expires_at is not None and expires_at <= time.time()):
        raise GrantUnavailable(service)
    from security_store import require_membership
    role = current_store().get_role(role_id)
    if role is None:
        raise CodedToolError(AUTHORIZATION_REQUIRED, "Role access is not authorized.")
    org = current_store().get_organization(role.organization_id)
    member = require_membership(current_actor(), org.domain, role.title)
    if service == "slack" and (payload.get("team_id") != member["slack_team_id"] or payload.get("user_id") != member["slack_user_id"]):
        raise GrantUnavailable(service)
    if service in {"gmail", "drive"} and payload.get("provider_subject") != member["google_subject"]:
        raise GrantUnavailable(service)
    if not payload.get("access_token"):
        raise GrantUnavailable(service)
    return payload["access_token"]


def build_indexed_chunks(role_id: str, tenure_id: str, author_person_id: str, service: str,
                         items: list[dict[str, str]], *, metadata_only: bool | None = None,
                         remaining_chunks: int | None = None, skipped: Counter | None = None) -> list[ChunkRecord]:
    """Embed and hash source items for the role index.

    Items with restricted identifiers, instruction injection or restricted topic
    words are not indexed. ``skipped`` counts them by fixed reason label; their
    text is never kept.
    """
    metadata_only = not use_fixtures() if metadata_only is None else metadata_only
    store = current_store()
    role = store.get_role(role_id)
    if role is None:
        raise CodedToolError(AUTHORIZATION_REQUIRED, "Role access is not authorized.")
    pieces = []
    for item in items:
        reason = skip_reason(item["text"])
        if reason:
            if skipped is not None:
                skipped[reason] += 1
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
            keyword_hashes=sorted({keyword_hash(term) for term in _terms(excerpt)}),
        ))
    return records


def hydrate_sources(records: list[ChunkRecord], *, keep=None, limit: int | None = None) -> list[ChunkRecord]:
    """Re-fetch text with the current user's token and discard changed/inaccessible sources.

    Records are verified lazily in the given order. Fetching stops once ``limit``
    verified chunks pass ``keep``, and at most WISDOMTWIN_MAX_SOURCE_FETCHES
    distinct sources are requested per call. A rate limit or provider failure
    after some evidence verified stops fetching and keeps that evidence; with
    nothing verified it is a coded failure. If nothing verified and a service
    grant was missing, expired or rejected by the provider, the caller is asked
    to reconnect. If nothing verified while the budget left sources unchecked,
    it is a coded failure too, never the empty-context answer.
    """
    from connectors import refetch_slack, refetch_google, GrantRevoked, SourceUnavailable, SourceRateLimited
    from errors import CONNECTOR_FAILED

    hydrated = []
    cache: dict[tuple[str, str], dict | None] = {}
    grants: dict[str, str] = {}
    missing_grants: list[str] = []
    budget = max_source_fetches()
    fetched = 0
    unchecked = False
    for record in records:
        if limit is not None and len(hydrated) >= limit:
            break
        # Legacy records containing raw excerpts are never returned in production.
        if record.excerpt or not record.source_uri or not record.source_hash or not connector_enabled(record.service):
            continue
        if record.service in missing_grants:
            continue
        key = (record.service, record.source_uri)
        if key not in cache:
            # Resolved once per service, before the budget check. connector_token makes
            # no provider call, so a lapsed grant is still reported after the budget is spent.
            if record.service not in grants:
                try:
                    grants[record.service] = connector_token(record.role_id, record.service)
                except GrantUnavailable:
                    grants[record.service] = ""
            token = grants[record.service]
            if not token:
                missing_grants.append(record.service)
                continue
            if fetched >= budget:
                unchecked = True
                continue
            fetched += 1
            try:
                cache[key] = refetch_slack(token, record.source_uri) if record.service == "slack" else refetch_google(token, record.service, record.source_uri)
            except SourceUnavailable:
                cache[key] = None
            except GrantRevoked:
                # The provider rejected the grant itself, so every source of this service is unreadable.
                missing_grants.append(record.service)
                continue
            except SourceRateLimited as exc:
                if hydrated:
                    budget = fetched  # Keep the verified evidence and stop fetching.
                    continue
                import math

                _audit("query_twin", error_code=CONNECTOR_FAILED, role_id=record.role_id)
                guidance = (f"Retry after at least {math.ceil(exc.retry_after_seconds)} seconds."
                            if exc.retry_after_seconds is not None else "Retry after the provider's rate limit clears.")
                raise CodedToolError(CONNECTOR_FAILED, f"Source provider is rate limited. {guidance}") from None
            except Exception:
                if hydrated:
                    budget = fetched  # Keep the verified evidence and stop fetching.
                    continue
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
        verified = replace(record, excerpt=excerpt)
        if keep is None or keep(verified):
            hydrated.append(verified)
    if not hydrated and missing_grants:
        # The index is intact; only the grant lapsed, so "nothing ingested" would be false.
        _audit("query_twin", error_code=OAUTH_PENDING, role_id=records[0].role_id)
        raise reconnect_error(missing_grants, "to restore cited answers")
    if not hydrated and unchecked:
        # Candidates remain that were never fetched, so "nothing ingested" would be false too.
        _audit("query_twin", error_code=CONNECTOR_FAILED, role_id=records[0].role_id)
        raise CodedToolError(CONNECTOR_FAILED, "No supporting source verified within this query's source-check limit. "
                             "Ask a narrower question or retry.")
    return hydrated
