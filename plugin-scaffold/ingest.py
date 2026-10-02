"""Durable, role-bound Celery ingestion and daily namespace retention."""

from __future__ import annotations

import logging
import os
from collections import Counter

from celery import Celery

from connectors import GrantRevoked, fetch_drive, fetch_gmail, fetch_slack
from errors import JOB_NOT_FOUND, CodedToolError
from mcp.server.mcpserver.exceptions import ToolError
from safety import IDENTIFIER_OR_INJECTION, RESTRICTED_TOPIC

logger = logging.getLogger("wisdomtwin")

celery_app = Celery(
    "wisdomtwin",
    broker=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
)
celery_app.conf.update(
    task_ignore_result=True, task_serializer="json", accept_content=["json"],
    result_serializer="json", broker_connection_retry_on_startup=True,
    task_default_queue=os.environ.get("WISDOMTWIN_TASK_QUEUE", "wisdomtwin"),
    beat_schedule={"daily-role-retention": {"task": "wisdomtwin.retention", "schedule": 86400.0}},
)


def run_job(job_id: str, subject: str | None = None):
    from store import current_store, actor_subject, current_actor

    context = actor_subject.set(subject or current_actor())
    store = current_store()
    try:
        job = store.get_job(job_id)
        if job is None:
            raise CodedToolError(JOB_NOT_FOUND, "Ingestion job was not found.")
        with store.job_lock(job_id) as claimed:
            job = store.get_job(job_id)
            if job is None:
                raise CodedToolError(JOB_NOT_FOUND, "Ingestion job was not found.")
            if not claimed or job.status == "completed":
                return job
            return _run_claimed_job(store, job)
    finally:
        actor_subject.reset(context)


def _run_claimed_job(store, job):
    from service import GrantUnavailable, build_indexed_chunks, connector_token, reconnect_error
    from domain import connector_enabled, MONTHLY_CHUNK_QUOTA
    from errors import OAUTH_PENDING, CONNECTOR_FAILED

    try:
        role = store.get_role(job.role_id)
        tenure = store.find_open_tenure(role.id) if role else None
        if role is None or tenure is None:
            raise CodedToolError(JOB_NOT_FOUND, "Ingestion job was not found.")
        if not connector_enabled(job.service):
            raise CodedToolError(OAUTH_PENDING, "The source connector is unavailable.")
        store.update_job(job.id, status="running", progress=10, chunks_ingested=0)
        try:
            token = connector_token(role.id, job.service)
        except GrantUnavailable:
            # A lapsed grant needs the user, not a retry: OAUTH_PENDING is never retried below.
            raise reconnect_error([job.service], "before ingesting again") from None
        fetcher = {"slack": fetch_slack, "gmail": fetch_gmail, "drive": fetch_drive}.get(job.service)
        if fetcher is None:
            raise CodedToolError(CONNECTOR_FAILED, "Unsupported source provider.")
        try:
            items = fetcher(token, job.query, job.max_items)
        except GrantRevoked:
            # The provider revoked or expired the grant itself: like a lapsed grant, never retried.
            raise reconnect_error([job.service], "before ingesting again") from None
        store.update_job(job.id, status="running", progress=40, chunks_ingested=0)
        remaining = MONTHLY_CHUNK_QUOTA - store.monthly_chunk_count(role.organization_id)
        skipped = Counter()
        records = build_indexed_chunks(role.id, tenure.id, tenure.person_id, job.service,
                                       items[:job.max_items], remaining_chunks=remaining, skipped=skipped)
        if skipped:
            # Counts only: skipped text is never stored or logged, and tool outputs are unchanged.
            logger.info("Ingestion job %s skipped %d source items: %d restricted topic, %d identifier or injection",
                        job.id, sum(skipped.values()), skipped[RESTRICTED_TOPIC], skipped[IDENTIFIER_OR_INJECTION])
        store.update_job(job.id, status="running", progress=70, chunks_ingested=0)
        written = store.upsert_chunks(records, job_id=job.id)
        store.touch_role(role.id)
        return store.update_job(job.id, status="completed", progress=100, chunks_ingested=written)
    except Exception as exc:
        if store.get_job(job.id):
            store.update_job(job.id, status="failed", progress=0, chunks_ingested=0)
        if isinstance(exc, CodedToolError):
            raise
        raise CodedToolError(CONNECTOR_FAILED, "Ingestion failed. Retry after source or service recovery.") from None


@celery_app.task(name="wisdomtwin.ingest", bind=True, max_retries=2)
def ingest_job(task, job_id: str, subject: str) -> str:
    from errors import CONNECTOR_FAILED
    try:
        return run_job(job_id, subject).id
    except CodedToolError as exc:
        if exc.code == CONNECTOR_FAILED:
            raise task.retry(exc=RuntimeError(CONNECTOR_FAILED), countdown=30)
        raise


@celery_app.task(name="wisdomtwin.retention")
def retention_job() -> int:
    from service import sweep_expired

    return sweep_expired()
