"""Exercise real Celery/Redis/Postgres using synthetic, loopback-only fixtures.

Requires isolated WISDOMTWIN_TEST_DATABASE_URL and WISDOMTWIN_TEST_REDIS_URL.
Truncates only that explicitly supplied local *_test database. No model/provider
network calls, public server, durable credentials, or source grants are created.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def wait_for(predicate, timeout=40):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        time.sleep(0.2)
    raise AssertionError("Synthetic worker did not reach the expected state")


def main():
    database = os.environ["WISDOMTWIN_TEST_DATABASE_URL"]
    redis = os.environ["WISDOMTWIN_TEST_REDIS_URL"]
    for value in (database, redis):
        if urlsplit(value).hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("Worker verification requires loopback-only test services")
    if not urlsplit(database).path.endswith("_test"):
        raise ValueError("Only an explicitly isolated *_test database may be reset")
    from cryptography.fernet import Fernet
    with tempfile.TemporaryDirectory(prefix="wisdomtwin-worker-") as temporary:
        for name in ("OPENAI_API_KEY", "SLACK_CLIENT_SECRET", "GOOGLE_CLIENT_SECRET", "PUBLIC_BASE_URL", "RAILWAY_PUBLIC_URL"):
            os.environ.pop(name, None)
        os.environ.update({
            "WISDOMTWIN_ENV": "test", "HOST": "127.0.0.1", "WISDOMTWIN_USE_FIXTURES": "1",
            "WISDOMTWIN_AUTH_DISABLED": "1", "SLACK_CONNECTOR_ENABLED": "true",
            "SLACK_CLIENT_ID": "synthetic-worker-client", "DATABASE_URL": database, "REDIS_URL": redis,
            "GMAIL_CONNECTOR_ENABLED": "false", "DRIVE_CONNECTOR_ENABLED": "false",
            "WISDOMTWIN_ALLOW_PAID_MODEL_APIS": "false", "WISDOMTWIN_TASK_QUEUE": "synthetic-" + uuid.uuid4().hex,
            "CONNECTOR_TOKEN_KEY": Fernet.generate_key().decode(),
            "WISDOMTWIN_AUTH_DB": str(Path(temporary) / "synthetic-auth.sqlite3"),
        })
        from runtime import validate_runtime
        validate_runtime()
        import service
        from ingest import celery_app, retention_job
        from store import current_store, reset_store
        reset_store()
        store = current_store()
        log_path = Path(temporary) / "worker.log"
        with log_path.open("w") as log:
            worker = subprocess.Popen([sys.executable, "-m", "celery", "-A", "ingest.celery_app", "worker",
                "--pool=solo", "--concurrency=1", "--loglevel=WARNING", "--without-gossip", "--without-mingle"],
                cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            try:
                connected = service.connect_business_account("slack", "example-corp.com", "CRO")
                queued = service.ingest_data("slack", "pipeline", 10)
                assert queued["progress"] == 0
                job = wait_for(lambda: (job if (job := store.get_job(queued["job_id"])) and job.status == "completed" else None))
                assert job.chunks_ingested == 10
                assert service.query_twin("What is the Acme pipeline stage?")["citations"]
                assert celery_app.conf.beat_schedule["daily-role-retention"]["schedule"] == 86400.0
                store.touch_role(connected["role_id"], datetime.now(timezone.utc) - timedelta(days=31))
                retention_job.delay()
                wait_for(lambda: store.get_role(connected["role_id"]) is None)
                assert store.get_job(job.id) is None and store.connections() == []
                print(json.dumps({"queued_ingestion": "passed", "chunks_ingested": 10,
                    "source_citations": "passed", "queued_retention": "passed", "model_api_calls": 0}))
            except Exception:
                # Fixtures contain no real secrets; keep logs private nonetheless.
                raise AssertionError("Synthetic Celery/Postgres/Redis verification failed; inspect local services") from None
            finally:
                worker.terminate()
                try:
                    worker.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    worker.kill()
                    worker.wait(timeout=5)
                celery_app.control.purge()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
