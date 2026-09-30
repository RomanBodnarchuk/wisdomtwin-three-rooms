"""Celery ingestion tasks. Slack is production. Gmail and Drive run only when enabled."""

from __future__ import annotations

import os

from celery import Celery

from connectors import fetch_drive, fetch_gmail, fetch_slack
from errors import JOB_NOT_FOUND, CodedToolError

celery_app = Celery(
    "wisdomtwin",
    broker=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
)
celery_app.conf.task_ignore_result = True


def run_job(job_id: str):
    from service import build_indexed_chunks, connector_token
    from store import current_store

    store = current_store()
    job = store.get_job(job_id)
    if job is None:
        raise CodedToolError(JOB_NOT_FOUND, "Ingestion job was not found.")
    role = store.get_role(job.role_id)
    if role is None:
        raise CodedToolError(JOB_NOT_FOUND, "Ingestion job was not found.")
    tenure = store.find_open_tenure(role.id)
    if tenure is None:
        raise CodedToolError(JOB_NOT_FOUND, "Ingestion job was not found.")

    store.update_job(job.id, status="running", progress=10, chunks_ingested=0)
    token = connector_token(role.id, job.service)
    if job.service == "slack":
        items = fetch_slack(token, job.query, job.max_items)
    elif job.service == "gmail":
        items = fetch_gmail(token, job.query, job.max_items)
    elif job.service == "drive":
        items = fetch_drive(token, job.query, job.max_items)
    else:
        items = []
    store.update_job(job.id, status="running", progress=40, chunks_ingested=0)
    records = build_indexed_chunks(
        role.id,
        tenure.id,
        tenure.person_id,
        job.service,
        items[: job.max_items],
    )
    store.update_job(job.id, status="running", progress=70, chunks_ingested=0)
    written = store.upsert_chunks(records)
    store.touch_role(role.id)
    return store.update_job(job.id, status="completed", progress=100, chunks_ingested=written)


@celery_app.task(name="wisdomtwin.ingest")
def ingest_job(job_id: str) -> str:
    finished = run_job(job_id)
    return finished.id


@celery_app.task(name="wisdomtwin.retention")
def retention_job() -> int:
    from service import sweep_expired

    return sweep_expired()
