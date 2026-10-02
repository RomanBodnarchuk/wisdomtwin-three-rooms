"""Role-namespace storage. Postgres when DATABASE_URL is set, memory otherwise."""

from __future__ import annotations

import contextvars
import json
import math
import os
import uuid
import threading
from functools import wraps
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

from domain import EMBEDDING_DIMENSIONS, RETENTION_DAYS


def _require_organization(store, organization_id: str) -> Organization:
    from errors import AUTHORIZATION_REQUIRED, CodedToolError

    org = store.get_organization(organization_id)
    if org is None:
        raise CodedToolError(AUTHORIZATION_REQUIRED, "Organization access is not authorized.")
    return org


def _require_role(store, role_id: str) -> Role:
    from errors import AUTHORIZATION_REQUIRED, CodedToolError

    role = store.get_role(role_id)
    if role is None:
        raise CodedToolError(AUTHORIZATION_REQUIRED, "Role access is not authorized.")
    return role


def _entitled(subject: str, domain: str, title: str | None = None) -> bool:
    from auth_provider import auth_is_required

    if _maintenance.get() or not auth_is_required():
        return True
    from security_store import security_store

    member = security_store().membership(subject, domain)
    return bool(member and (title is None or title in member["roles"]))


actor_subject: contextvars.ContextVar[str] = contextvars.ContextVar("wisdomtwin_actor", default="local")
_maintenance: contextvars.ContextVar[bool] = contextvars.ContextVar("wisdomtwin_maintenance", default=False)


def current_actor() -> str:
    return actor_subject.get()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _id() -> str:
    return str(uuid.uuid4())


@dataclass
class Organization:
    id: str
    domain: str
    created_at: datetime
    subject: str = "local"


@dataclass
class Person:
    id: str
    organization_id: str
    display_name: str
    created_at: datetime


@dataclass
class Role:
    id: str
    organization_id: str
    title: str
    created_at: datetime
    last_activity_at: datetime


@dataclass
class Tenure:
    id: str
    role_id: str
    person_id: str
    started_on: date
    ended_on: date | None


@dataclass
class ChunkRecord:
    id: str
    role_id: str
    tenure_id: str
    author_person_id: str
    service: str
    uri: str
    excerpt: str
    embedding: list[float]
    created_at: datetime
    source_uri: str = ""
    source_hash: str = ""
    chunk_index: int = 0
    keyword_hashes: list[str] = field(default_factory=list)


@dataclass
class JobRecord:
    id: str
    role_id: str
    service: str
    query: str
    max_items: int
    status: str
    progress: int
    chunks_ingested: int


@dataclass
class AuditRecord:
    id: str
    tool_name: str
    error_code: str | None
    organization_id: str | None
    role_id: str | None
    created_at: datetime


@dataclass
class Connection:
    role_id: str
    service: str
    domain: str
    role_title: str
    connected_at: datetime
    subject: str = "local"


class Store(Protocol):
    def upsert_organization(self, domain: str) -> Organization: ...
    def get_organization_by_domain(self, domain: str) -> Organization | None: ...
    def ensure_officeholder(self, organization_id: str) -> Person: ...
    def find_role(self, organization_id: str, title: str) -> Role | None: ...
    def create_role(self, organization_id: str, title: str) -> Role: ...
    def find_open_tenure(self, role_id: str) -> Tenure | None: ...
    def open_tenure(self, role_id: str, person_id: str, started_on: date) -> Tenure: ...
    def set_active_role(self, role_id: str) -> None: ...
    def get_active_role_id(self) -> str | None: ...
    def get_role(self, role_id: str) -> Role | None: ...
    def get_organization(self, organization_id: str) -> Organization | None: ...
    def record_connection(self, role_id: str, service: str, domain: str, role_title: str) -> None: ...
    def connections(self) -> list[Connection]: ...
    def monthly_chunk_count(self, organization_id: str, when: datetime | None = None) -> int: ...
    def upsert_chunks(self, chunks: list[ChunkRecord]) -> int: ...
    def chunks_for_role(self, role_id: str) -> list[ChunkRecord]: ...
    def delete_namespace(self, role_id: str) -> int: ...
    def vector_search(self, role_id: str, embedding: list[float], limit: int) -> list[ChunkRecord]: ...
    def keyword_search(self, role_id: str, terms: list[str], limit: int) -> list[ChunkRecord]: ...
    def touch_role(self, role_id: str, when: datetime | None = None) -> None: ...
    def roles_inactive_before(self, cutoff: datetime) -> list[Role]: ...
    def write_audit(
        self,
        tool_name: str,
        *,
        error_code: str | None = None,
        organization_id: str | None = None,
        role_id: str | None = None,
    ) -> AuditRecord: ...
    def audits(self) -> list[AuditRecord]: ...
    def create_job(self, role_id: str, service: str, query: str, max_items: int) -> JobRecord: ...
    def get_job(self, job_id: str) -> JobRecord | None: ...
    def update_job(self, job_id: str, *, status: str, progress: int, chunks_ingested: int) -> JobRecord: ...
    def save_secret(self, key: str, payload: dict) -> None: ...
    def pop_secret(self, key: str) -> dict | None: ...
    def save_credential(self, role_id: str, service: str, ciphertext: str) -> None: ...
    def get_credential(self, role_id: str, service: str) -> str | None: ...
    def role_count_for_domain(self, domain: str) -> int: ...
    def open_tenure_count(self, role_id: str) -> int: ...


def _sql_statements(script: str) -> list[str]:
    """Split a schema script into single statements psycopg can execute."""
    kept: list[str] = []
    for line in script.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        kept.append(line)
    return [part.strip() for part in "\n".join(kept).split(";") if part.strip()]


def _vector_param(embedding: list[float]):
    from pgvector import Vector

    return Vector(embedding)


def _vector_list(value) -> list[float]:
    if value is None:
        return []
    if hasattr(value, "to_list"):
        return [float(item) for item in value.to_list()]
    return [float(item) for item in value]


def _cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
    right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
    return dot / (left_norm * right_norm)


@dataclass
class MemoryStore:
    organizations: dict[str, Organization] = field(default_factory=dict)
    persons: dict[str, Person] = field(default_factory=dict)
    roles: dict[str, Role] = field(default_factory=dict)
    tenures: dict[str, Tenure] = field(default_factory=dict)
    chunks: dict[str, ChunkRecord] = field(default_factory=dict)
    jobs: dict[str, JobRecord] = field(default_factory=dict)
    audit_rows: list[AuditRecord] = field(default_factory=list)
    connection_rows: list[Connection] = field(default_factory=list)
    secrets: dict[str, dict] = field(default_factory=dict)
    credentials: dict[tuple[str, str], str] = field(default_factory=dict)
    active_roles: dict[str, str] = field(default_factory=dict)
    lock: threading.RLock = field(default_factory=threading.RLock)

    def upsert_organization(self, domain: str) -> Organization:
        subject = current_actor()
        if not _entitled(subject, domain):
            from errors import AUTHORIZATION_REQUIRED, CodedToolError
            raise CodedToolError(AUTHORIZATION_REQUIRED, "Corporate membership is required.")
        for org in self.organizations.values():
            if org.domain == domain and org.subject == subject:
                return org
        org = Organization(id=_id(), domain=domain, created_at=_now(), subject=subject)
        self.organizations[org.id] = org
        return org

    def get_organization_by_domain(self, domain: str) -> Organization | None:
        subject = current_actor()
        for org in self.organizations.values():
            if org.domain == domain and org.subject == subject:
                return org
        return None

    def ensure_officeholder(self, organization_id: str) -> Person:
        person_id = str(uuid.uuid5(uuid.UUID(organization_id), f"officeholder:{current_actor()}"))
        if person_id in self.persons:
            return self.persons[person_id]
        person = Person(
            id=person_id,
            organization_id=organization_id,
            display_name="Current officeholder",
            created_at=_now(),
        )
        self.persons[person.id] = person
        return person

    def ensure_source_author(self, organization_id: str, service: str, provider_id: str) -> Person:
        _require_organization(self, organization_id)
        person_id = str(uuid.uuid5(uuid.UUID(organization_id), f"{service}:{provider_id}"))
        if person_id not in self.persons:
            self.persons[person_id] = Person(person_id, organization_id, f"{service} source author", _now())
        return self.persons[person_id]

    def find_role(self, organization_id: str, title: str) -> Role | None:
        org = _require_organization(self, organization_id)
        if not _entitled(current_actor(), org.domain, title):
            return None
        for role in self.roles.values():
            if role.organization_id == organization_id and role.title == title:
                return role
        return None

    def create_role(self, organization_id: str, title: str) -> Role:
        org = _require_organization(self, organization_id)
        if not _entitled(current_actor(), org.domain, title):
            from errors import AUTHORIZATION_REQUIRED, CodedToolError
            raise CodedToolError(AUTHORIZATION_REQUIRED, "Role entitlement is required.")
        existing = self.find_role(organization_id, title)
        if existing:
            return existing
        role = Role(
            id=_id(),
            organization_id=organization_id,
            title=title,
            created_at=_now(),
            last_activity_at=_now(),
        )
        self.roles[role.id] = role
        return role

    def find_open_tenure(self, role_id: str) -> Tenure | None:
        for tenure in self.tenures.values():
            if tenure.role_id == role_id and tenure.ended_on is None:
                return tenure
        return None

    def open_tenure(self, role_id: str, person_id: str, started_on: date) -> Tenure:
        with self.lock:
            return self._open_tenure(role_id, person_id, started_on)

    def _open_tenure(self, role_id: str, person_id: str, started_on: date) -> Tenure:
        role = _require_role(self, role_id)
        person = self.persons.get(person_id)
        if not person or person.organization_id != role.organization_id:
            from errors import AUTHORIZATION_REQUIRED, CodedToolError
            raise CodedToolError(AUTHORIZATION_REQUIRED, "Officeholder does not belong to this organization.")
        existing = self.find_open_tenure(role_id)
        if existing:
            return existing
        tenure = Tenure(
            id=_id(),
            role_id=role_id,
            person_id=person_id,
            started_on=started_on,
            ended_on=None,
        )
        self.tenures[tenure.id] = tenure
        return tenure

    def set_active_role(self, role_id: str) -> None:
        self.active_roles[current_actor()] = role_id

    def get_active_role_id(self) -> str | None:
        return self.active_roles.get(current_actor())

    def get_role(self, role_id: str) -> Role | None:
        role = self.roles.get(role_id)
        org = self.get_organization(role.organization_id) if role else None
        return role if org and _entitled(current_actor(), org.domain, role.title) else None

    def get_organization(self, organization_id: str) -> Organization | None:
        org = self.organizations.get(organization_id)
        return org if org and org.subject == current_actor() and _entitled(current_actor(), org.domain) else None

    def record_connection(self, role_id: str, service: str, domain: str, role_title: str) -> None:
        self.connection_rows = [
            row for row in self.connection_rows if not (row.role_id == role_id and row.service == service)
        ]
        subject = current_actor()
        self.connection_rows.append(
            Connection(
                role_id=role_id,
                service=service,
                domain=domain,
                role_title=role_title,
                connected_at=_now(),
                subject=subject,
            )
        )

    def connections(self) -> list[Connection]:
        subject = current_actor()
        return [row for row in self.connection_rows if row.subject == subject and self.get_role(row.role_id)]

    def monthly_chunk_count(self, organization_id: str, when: datetime | None = None) -> int:
        moment = when or _now()
        role_ids = {role.id for role in self.roles.values() if role.organization_id == organization_id}
        return sum(
            1
            for chunk in self.chunks.values()
            if chunk.role_id in role_ids
            and chunk.created_at.year == moment.year
            and chunk.created_at.month == moment.month
        )

    def upsert_chunks(self, chunks: list[ChunkRecord], *, job_id: str | None = None) -> int:
        from errors import QUOTA_EXCEEDED, JOB_NOT_FOUND, CodedToolError
        from domain import MONTHLY_CHUNK_QUOTA

        with self.lock:
            job = self.get_job(job_id) if job_id else None
            if job_id and (not job or any(chunk.role_id != job.role_id for chunk in chunks)):
                raise CodedToolError(JOB_NOT_FOUND, "Ingestion was deleted.")
            for chunk in chunks:
                role = _require_role(self, chunk.role_id)
                tenure = self.find_open_tenure(role.id)
                author = self.persons.get(chunk.author_person_id)
                if not tenure or chunk.tenure_id != tenure.id or not author or author.organization_id != role.organization_id:
                    raise ValueError("Chunk tenure does not belong to the role")
                if len(chunk.embedding) != EMBEDDING_DIMENSIONS:
                    raise ValueError("Chunk embedding has the wrong dimensionality")
            organizations = {self.get_role(chunk.role_id).organization_id for chunk in chunks}
            for organization_id in organizations:
                now = _now()
                existing_keys = {(chunk.role_id, chunk.uri) for chunk in self.chunks.values() if chunk.created_at.year == now.year and chunk.created_at.month == now.month}
                added = {(chunk.role_id, chunk.uri) for chunk in chunks if self.get_role(chunk.role_id).organization_id == organization_id} - existing_keys
                if self.monthly_chunk_count(organization_id) + len(added) > MONTHLY_CHUNK_QUOTA:
                    raise CodedToolError(QUOTA_EXCEEDED, "Expanded chunks exceed the monthly quota.")
            return self._write_chunks(chunks)

    def _write_chunks(self, chunks: list[ChunkRecord]) -> int:
        written = 0
        for chunk in chunks:
            if len(chunk.embedding) != EMBEDDING_DIMENSIONS:
                raise ValueError("Chunk embedding has the wrong dimensionality")
            existing = next(
                (
                    current
                    for current in self.chunks.values()
                    if current.role_id == chunk.role_id and current.uri == chunk.uri
                ),
                None,
            )
            if existing:
                self.chunks.pop(existing.id, None)
            self.chunks[chunk.id] = chunk
            written += 1
        return written

    def chunks_for_role(self, role_id: str) -> list[ChunkRecord]:
        if self.get_role(role_id) is None:
            return []
        return [chunk for chunk in self.chunks.values() if chunk.role_id == role_id]

    def delete_namespace(self, role_id: str, *, if_inactive_before: datetime | None = None) -> int:
        with self.lock:
            role = _require_role(self, role_id)
            if if_inactive_before is not None and role.last_activity_at >= if_inactive_before:
                return 0
            return self._delete_namespace(role_id)

    def _delete_namespace(self, role_id: str) -> int:
        _require_role(self, role_id)
        doomed = [chunk.id for chunk in self.chunks.values() if chunk.role_id == role_id]
        for chunk_id in doomed:
            self.chunks.pop(chunk_id, None)
        self.credentials = {key: value for key, value in self.credentials.items() if key[0] != role_id}
        self.jobs = {key: value for key, value in self.jobs.items() if value.role_id != role_id}
        self.connection_rows = [row for row in self.connection_rows if row.role_id != role_id]
        self.active_roles = {key: value for key, value in self.active_roles.items() if value != role_id}
        self.secrets = {key: value for key, value in self.secrets.items() if value.get("role_id") != role_id}
        organization_id = self.roles.pop(role_id).organization_id
        self.tenures = {key: value for key, value in self.tenures.items() if value.role_id != role_id}
        used_persons = {tenure.person_id for tenure in self.tenures.values()} | {chunk.author_person_id for chunk in self.chunks.values()}
        self.persons = {key: value for key, value in self.persons.items() if value.organization_id != organization_id or key in used_persons}
        if not any(role.organization_id == organization_id for role in self.roles.values()):
            self.organizations.pop(organization_id, None)
        return len(doomed)

    def vector_search(self, role_id: str, embedding: list[float], limit: int) -> list[ChunkRecord]:
        scoped = self.chunks_for_role(role_id)
        scoped.sort(key=lambda chunk: _cosine(embedding, chunk.embedding), reverse=True)
        return scoped[:limit]

    def keyword_search(self, role_id: str, terms: list[str], limit: int) -> list[ChunkRecord]:
        from tokens import keyword_hash

        scoped = self.chunks_for_role(role_id)
        if not terms:
            return []
        hashed = {term: keyword_hash(term) for term in terms}

        def score(chunk: ChunkRecord) -> int:
            excerpt = chunk.excerpt.lower()
            return sum(1 for term in terms if term in excerpt or hashed[term] in chunk.keyword_hashes)

        ranked = [chunk for chunk in scoped if score(chunk) > 0]
        ranked.sort(key=score, reverse=True)
        return ranked[:limit]

    def touch_role(self, role_id: str, when: datetime | None = None) -> None:
        with self.lock:
            role = self.roles.get(role_id)
            if role:
                role.last_activity_at = when or _now()

    def roles_inactive_before(self, cutoff: datetime) -> list[Role]:
        return [role for role in self.roles.values() if role.last_activity_at < cutoff]

    def write_audit(
        self,
        tool_name: str,
        *,
        error_code: str | None = None,
        organization_id: str | None = None,
        role_id: str | None = None,
    ) -> AuditRecord:
        row = AuditRecord(
            id=_id(),
            tool_name=tool_name,
            error_code=error_code,
            organization_id=organization_id,
            role_id=role_id,
            created_at=_now(),
        )
        self.audit_rows.append(row)
        return row

    def audits(self) -> list[AuditRecord]:
        return list(self.audit_rows)

    def create_job(self, role_id: str, service: str, query: str, max_items: int) -> JobRecord:
        job = JobRecord(
            id=_id(),
            role_id=role_id,
            service=service,
            query=query,
            max_items=max_items,
            status="queued",
            progress=0,
            chunks_ingested=0,
        )
        self.jobs[job.id] = job
        return job

    def get_job(self, job_id: str) -> JobRecord | None:
        job = self.jobs.get(job_id)
        return job if job and self.get_role(job.role_id) else None

    @contextmanager
    def job_lock(self, job_id: str):
        # Synthetic local workers share the same exclusion semantics as Postgres.
        with self.lock:
            locks = self.__dict__.setdefault("_job_locks", {})
            lock = locks.setdefault(job_id, threading.Lock())
        acquired = lock.acquire(blocking=False)
        try:
            yield acquired
        finally:
            if acquired:
                lock.release()

    def update_job(self, job_id: str, *, status: str, progress: int, chunks_ingested: int) -> JobRecord:
        if self.get_job(job_id) is None:
            from errors import JOB_NOT_FOUND, CodedToolError
            raise CodedToolError(JOB_NOT_FOUND, "Ingestion job was not found.")
        job = self.jobs[job_id]
        job.status = status
        job.progress = progress
        job.chunks_ingested = chunks_ingested
        return job

    def save_secret(self, key: str, payload: dict) -> None:
        import time

        self.secrets[key] = {**payload, "expires_at": time.time() + 300}

    def pop_secret(self, key: str) -> dict | None:
        import time

        payload = self.secrets.pop(key, None)
        return payload if payload and payload.get("expires_at", 0) > time.time() else None

    def jobs_for_role(self, role_id: str) -> list[JobRecord]:
        _require_role(self, role_id)
        return [job for job in self.jobs.values() if job.role_id == role_id]

    def save_credential(self, role_id: str, service: str, ciphertext: str) -> None:
        self.credentials[(role_id, service)] = ciphertext

    def get_credential(self, role_id: str, service: str) -> str | None:
        return self.credentials.get((role_id, service))

    def role_count_for_domain(self, domain: str) -> int:
        org = self.get_organization_by_domain(domain)
        if not org:
            return 0
        return sum(1 for role in self.roles.values() if role.organization_id == org.id)

    def open_tenure_count(self, role_id: str) -> int:
        return sum(1 for tenure in self.tenures.values() if tenure.role_id == role_id and tenure.ended_on is None)

    def owner_for_retention(self, role_id: str) -> str:
        return self.organizations[self.roles[role_id].organization_id].subject

    def cleanup_transients(self, cutoff: datetime) -> None:
        import time
        self.audit_rows = [row for row in self.audit_rows if row.created_at >= cutoff]
        self.secrets = {key: value for key, value in self.secrets.items() if value.get("expires_at", 0) > time.time()}


class PostgresStore:
    """pgvector-backed store. Role filters are SQL predicates."""

    def __init__(self, database_url: str) -> None:
        import psycopg
        from pgvector.psycopg import register_vector

        self._psycopg = psycopg
        self._register_vector = register_vector
        self._database_url = database_url
        self._active_roles: dict[str, str] = {}
        self._ensure_schema()

    def _connect(self):
        connection = self._psycopg.connect(self._database_url)
        self._register_vector(connection)
        return connection

    def _ensure_schema(self) -> None:
        schema = (Path(__file__).resolve().parent / "schema.sql").read_text(encoding="utf-8")
        connection = self._psycopg.connect(self._database_url)
        try:
            connection.autocommit = True
            for statement in _sql_statements(schema):
                connection.execute(statement)
            self._migrate_actor_scope(connection)
        finally:
            connection.close()

    def _migrate_actor_scope(self, connection) -> None:
        connection.execute(
            "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS subject TEXT NOT NULL DEFAULT 'local'"
        )
        connection.execute("ALTER TABLE organizations DROP CONSTRAINT IF EXISTS organizations_domain_key")
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS organizations_subject_domain_key
            ON organizations (subject, domain)
            """
        )
        connection.execute(
            "ALTER TABLE connections ADD COLUMN IF NOT EXISTS subject TEXT NOT NULL DEFAULT 'local'"
        )
        connection.execute("ALTER TABLE oauth_transactions ADD COLUMN IF NOT EXISTS role_id UUID")
        for column, definition in (("source_uri", "TEXT NOT NULL DEFAULT ''"), ("source_hash", "TEXT NOT NULL DEFAULT ''"),
                                   ("chunk_index", "INTEGER NOT NULL DEFAULT 0"), ("keyword_hashes", "JSONB NOT NULL DEFAULT '[]'")):
            connection.execute(f"ALTER TABLE chunks ADD COLUMN IF NOT EXISTS {column} {definition}")
        has_subject = connection.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'active_role' AND column_name = 'subject'
            """
        ).fetchone()
        if not has_subject:
            connection.execute("DROP TABLE active_role")
            connection.execute(
                """
                CREATE TABLE active_role (
                    subject TEXT PRIMARY KEY,
                    role_id UUID NOT NULL REFERENCES roles (id)
                )
                """
            )

    def truncate_all(self) -> None:
        self._active_roles = {}
        with self._connect() as connection:
            connection.execute(
                """
                TRUNCATE TABLE
                    connector_credentials,
                    oauth_transactions,
                    active_role,
                    connections,
                    ingestion_jobs,
                    audit_log,
                    chunks,
                    judgment_seeds,
                    tenures,
                    roles,
                    persons,
                    organizations
                RESTART IDENTITY CASCADE
                """
            )

    def upsert_organization(self, domain: str) -> Organization:
        if not _entitled(current_actor(), domain):
            from errors import AUTHORIZATION_REQUIRED, CodedToolError
            raise CodedToolError(AUTHORIZATION_REQUIRED, "Corporate membership is required.")
        with self._connect() as connection:
            row = connection.execute(
                """
                INSERT INTO organizations (id, subject, domain)
                VALUES (%s, %s, %s)
                ON CONFLICT (subject, domain) DO UPDATE SET domain = EXCLUDED.domain
                RETURNING id, domain, created_at, subject
                """,
                (_id(), current_actor(), domain),
            ).fetchone()
            connection.commit()
        return Organization(id=str(row[0]), domain=row[1], created_at=row[2], subject=row[3])

    def get_organization_by_domain(self, domain: str) -> Organization | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, domain, created_at, subject
                FROM organizations WHERE domain = %s AND subject = %s
                """,
                (domain, current_actor()),
            ).fetchone()
        if not row:
            return None
        return Organization(id=str(row[0]), domain=row[1], created_at=row[2], subject=row[3])

    def ensure_officeholder(self, organization_id: str) -> Person:
        person_id = str(uuid.uuid5(uuid.UUID(organization_id), f"officeholder:{current_actor()}"))
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO persons (id, organization_id, display_name) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",
                (person_id, organization_id, "Current officeholder"),
            )
            connection.commit()
            created = connection.execute(
                "SELECT id, organization_id, display_name, created_at FROM persons WHERE id = %s",
                (person_id,),
            ).fetchone()
        return Person(id=str(created[0]), organization_id=str(created[1]), display_name=created[2], created_at=created[3])

    def ensure_source_author(self, organization_id: str, service: str, provider_id: str) -> Person:
        _require_organization(self, organization_id)
        person_id = str(uuid.uuid5(uuid.UUID(organization_id), f"{service}:{provider_id}"))
        with self._connect() as connection:
            connection.execute("INSERT INTO persons (id,organization_id,display_name) VALUES (%s,%s,%s) ON CONFLICT (id) DO NOTHING", (person_id, organization_id, f"{service} source author"))
        return Person(person_id, organization_id, f"{service} source author", _now())

    def find_role(self, organization_id: str, title: str) -> Role | None:
        org = _require_organization(self, organization_id)
        if not _entitled(current_actor(), org.domain, title):
            return None
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, organization_id, title, created_at, last_activity_at
                FROM roles WHERE organization_id = %s AND title = %s
                """,
                (organization_id, title),
            ).fetchone()
        if not row:
            return None
        return Role(id=str(row[0]), organization_id=str(row[1]), title=row[2], created_at=row[3], last_activity_at=row[4])

    def create_role(self, organization_id: str, title: str) -> Role:
        org = _require_organization(self, organization_id)
        if not _entitled(current_actor(), org.domain, title):
            from errors import AUTHORIZATION_REQUIRED, CodedToolError
            raise CodedToolError(AUTHORIZATION_REQUIRED, "Role entitlement is required.")
        existing = self.find_role(organization_id, title)
        if existing:
            return existing
        role_id = _id()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO roles (id, organization_id, title) VALUES (%s, %s, %s)",
                (role_id, organization_id, title),
            )
            connection.commit()
        role = self.find_role(organization_id, title)
        if role is None:
            raise RuntimeError("Role insert did not persist")
        return role

    def find_open_tenure(self, role_id: str) -> Tenure | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, role_id, person_id, started_on, ended_on
                FROM tenures WHERE role_id = %s AND ended_on IS NULL
                LIMIT 1
                """,
                (role_id,),
            ).fetchone()
        if not row:
            return None
        return Tenure(id=str(row[0]), role_id=str(row[1]), person_id=str(row[2]), started_on=row[3], ended_on=row[4])

    def open_tenure(self, role_id: str, person_id: str, started_on: date) -> Tenure:
        role = _require_role(self, role_id)
        with self._connect() as connection:
            # Serialize officeholder creation without repairing legacy history.
            # A legacy namespace with multiple open tenures requires an operator
            # decision; do not silently end or reassign any existing tenure.
            connection.execute("SELECT id FROM roles WHERE id=%s FOR UPDATE", (role_id,))
            person = connection.execute("SELECT 1 FROM persons WHERE id=%s AND organization_id=%s", (person_id, role.organization_id)).fetchone()
            if not person:
                from errors import AUTHORIZATION_REQUIRED, CodedToolError
                raise CodedToolError(AUTHORIZATION_REQUIRED, "Officeholder does not belong to this organization.")
            rows = connection.execute("SELECT id,role_id,person_id,started_on,ended_on FROM tenures WHERE role_id=%s AND ended_on IS NULL", (role_id,)).fetchall()
            if len(rows) > 1:
                raise RuntimeError("Multiple open tenures require operator reconciliation")
            row = rows[0] if rows else connection.execute(
                "INSERT INTO tenures (id,role_id,person_id,started_on,ended_on) VALUES (%s,%s,%s,%s,NULL) RETURNING id,role_id,person_id,started_on,ended_on",
                (_id(), role_id, person_id, started_on),
            ).fetchone()
        return Tenure(str(row[0]), str(row[1]), str(row[2]), row[3], row[4])

    def set_active_role(self, role_id: str) -> None:
        subject = current_actor()
        self._active_roles[subject] = role_id
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO active_role (subject, role_id) VALUES (%s, %s)
                ON CONFLICT (subject) DO UPDATE SET role_id = EXCLUDED.role_id
                """,
                (subject, role_id),
            )
            connection.commit()

    def get_active_role_id(self) -> str | None:
        subject = current_actor()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT role_id FROM active_role WHERE subject = %s",
                (subject,),
            ).fetchone()
        if not row:
            return None
        self._active_roles[subject] = str(row[0])
        return self._active_roles[subject]

    def get_role(self, role_id: str) -> Role | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, organization_id, title, created_at, last_activity_at
                FROM roles WHERE id = %s AND organization_id IN (
                    SELECT id FROM organizations WHERE subject = %s)
                """,
                (role_id, current_actor()),
            ).fetchone()
        if not row:
            return None
        org = self.get_organization(str(row[1]))
        return Role(id=str(row[0]), organization_id=str(row[1]), title=row[2], created_at=row[3], last_activity_at=row[4]) if org and _entitled(current_actor(), org.domain, row[2]) else None

    def get_organization(self, organization_id: str) -> Organization | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, domain, created_at, subject FROM organizations WHERE id = %s AND subject = %s",
                (organization_id, current_actor()),
            ).fetchone()
        if not row:
            return None
        return Organization(id=str(row[0]), domain=row[1], created_at=row[2], subject=row[3]) if _entitled(current_actor(), row[1]) else None

    def record_connection(self, role_id: str, service: str, domain: str, role_title: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO connections (id, role_id, service, domain, role_title, subject)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (role_id, service) DO UPDATE
                SET domain = EXCLUDED.domain,
                    role_title = EXCLUDED.role_title,
                    subject = EXCLUDED.subject,
                    connected_at = now()
                """,
                (_id(), role_id, service, domain, role_title, current_actor()),
            )
            connection.commit()

    def connections(self) -> list[Connection]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role_id, service, domain, role_title, connected_at, subject
                FROM connections WHERE subject = %s ORDER BY connected_at
                """,
                (current_actor(),),
            ).fetchall()
        return [
            Connection(
                role_id=str(row[0]),
                service=row[1],
                domain=row[2],
                role_title=row[3],
                connected_at=row[4],
                subject=row[5],
            )
            for row in rows if self.get_role(str(row[0]))
        ]

    def monthly_chunk_count(self, organization_id: str, when: datetime | None = None) -> int:
        moment = when or _now()
        start = moment.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT count(*) FROM chunks c
                JOIN roles r ON r.id = c.role_id
                WHERE r.organization_id = %s AND c.created_at >= %s AND c.created_at < %s
                """,
                (organization_id, start, end),
            ).fetchone()
        return int(row[0])

    def upsert_chunks(self, chunks: list[ChunkRecord], *, job_id: str | None = None) -> int:
        from errors import QUOTA_EXCEEDED, JOB_NOT_FOUND, CodedToolError
        from domain import MONTHLY_CHUNK_QUOTA

        roles = {chunk.role_id: _require_role(self, chunk.role_id) for chunk in chunks}
        for chunk in chunks:
            tenure = self.find_open_tenure(chunk.role_id)
            role = roles[chunk.role_id]
            with self._connect() as connection:
                author = connection.execute("SELECT 1 FROM persons WHERE id=%s AND organization_id=%s", (chunk.author_person_id, role.organization_id)).fetchone()
            if not tenure or chunk.tenure_id != tenure.id or not author:
                raise ValueError("Chunk tenure does not belong to the role")
            if len(chunk.embedding) != EMBEDDING_DIMENSIONS:
                raise ValueError("Chunk embedding has the wrong dimensionality")
        with self._connect() as connection:
            for organization_id in sorted({role.organization_id for role in roles.values()}):
                # Serialize quota checks per organization across workers.
                connection.execute("SELECT id FROM organizations WHERE id=%s FOR UPDATE", (organization_id,))
                start = _now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                used = connection.execute("SELECT count(*) FROM chunks c JOIN roles r ON c.role_id=r.id WHERE r.organization_id=%s AND c.created_at>=%s", (organization_id, start)).fetchone()[0]
                added = 0
                for role_id, uri in {(chunk.role_id, chunk.uri) for chunk in chunks if roles[chunk.role_id].organization_id == organization_id}:
                    if not connection.execute("SELECT 1 FROM chunks WHERE role_id=%s AND uri=%s AND created_at>=%s", (role_id, uri, start)).fetchone():
                        added += 1
                if used + added > MONTHLY_CHUNK_QUOTA:
                    raise CodedToolError(QUOTA_EXCEEDED, "Expanded chunks exceed the monthly quota.")
            for role_id in sorted(roles):
                connection.execute("SELECT id FROM roles WHERE id=%s FOR UPDATE", (role_id,))
            if job_id:
                job = connection.execute("SELECT role_id FROM ingestion_jobs WHERE id=%s", (job_id,)).fetchone()
                if not job or any(chunk.role_id != str(job[0]) for chunk in chunks):
                    raise CodedToolError(JOB_NOT_FOUND, "Ingestion was deleted or its role was substituted.")
            for chunk in chunks:
                connection.execute(
                    """
                    INSERT INTO chunks (
                        id, role_id, tenure_id, author_person_id, service, uri, excerpt, embedding,
                        source_uri, source_hash, chunk_index, keyword_hashes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (role_id, uri) DO UPDATE SET
                        tenure_id = EXCLUDED.tenure_id,
                        author_person_id = EXCLUDED.author_person_id,
                        excerpt = EXCLUDED.excerpt,
                        embedding = EXCLUDED.embedding,
                        source_uri = EXCLUDED.source_uri, source_hash = EXCLUDED.source_hash,
                        chunk_index = EXCLUDED.chunk_index, keyword_hashes = EXCLUDED.keyword_hashes,
                        created_at = now()
                    """,
                    (
                        chunk.id,
                        chunk.role_id,
                        chunk.tenure_id,
                        chunk.author_person_id,
                        chunk.service,
                        chunk.uri,
                        chunk.excerpt,
                        _vector_param(chunk.embedding),
                        chunk.source_uri, chunk.source_hash, chunk.chunk_index, json.dumps(chunk.keyword_hashes),
                    ),
                )
            connection.commit()
        return len(chunks)

    def chunks_for_role(self, role_id: str) -> list[ChunkRecord]:
        if self.get_role(role_id) is None:
            return []
        return self._load_chunks("WHERE role_id = %s", (role_id,))

    def delete_namespace(self, role_id: str, *, if_inactive_before: datetime | None = None) -> int:
        role = _require_role(self, role_id)
        with self._connect() as connection:
            connection.execute("SELECT id FROM organizations WHERE id=%s FOR UPDATE", (role.organization_id,))
            current = connection.execute("SELECT last_activity_at FROM roles WHERE id = %s FOR UPDATE", (role_id,)).fetchone()
            if not current or (if_inactive_before is not None and current[0] >= if_inactive_before):
                return 0
            row = connection.execute("DELETE FROM chunks WHERE role_id = %s", (role_id,)).rowcount
            for table in ("connector_credentials", "connections", "active_role", "ingestion_jobs", "judgment_seeds"):
                connection.execute(f"DELETE FROM {table} WHERE role_id = %s", (role_id,))
            connection.execute("DELETE FROM oauth_transactions WHERE role_id = %s", (role_id,))
            connection.execute("DELETE FROM tenures WHERE role_id=%s", (role_id,))
            connection.execute("DELETE FROM roles WHERE id=%s", (role_id,))
            connection.execute("DELETE FROM persons WHERE organization_id=%s AND id NOT IN (SELECT person_id FROM tenures) AND id NOT IN (SELECT author_person_id FROM chunks)", (role.organization_id,))
            connection.execute("DELETE FROM organizations WHERE id=%s AND NOT EXISTS (SELECT 1 FROM roles WHERE organization_id=%s)", (role.organization_id, role.organization_id))
            connection.commit()
        self._active_roles = {key: value for key, value in self._active_roles.items() if value != role_id}
        return int(row or 0)

    def _load_chunks(self, where_sql: str, params: tuple) -> list[ChunkRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT id, role_id, tenure_id, author_person_id, service, uri, excerpt, embedding, created_at, source_uri, source_hash, chunk_index, keyword_hashes
                FROM chunks {where_sql}
                """,
                params,
            ).fetchall()
        loaded: list[ChunkRecord] = []
        for row in rows:
            embedding = _vector_list(row[7])
            loaded.append(
                ChunkRecord(
                    id=str(row[0]),
                    role_id=str(row[1]),
                    tenure_id=str(row[2]),
                    author_person_id=str(row[3]),
                    service=row[4],
                    uri=row[5],
                    excerpt=row[6],
                    embedding=embedding,
                    created_at=row[8],
                    source_uri=row[9], source_hash=row[10], chunk_index=row[11], keyword_hashes=row[12],
                )
            )
        return loaded

    def vector_search(self, role_id: str, embedding: list[float], limit: int) -> list[ChunkRecord]:
        _require_role(self, role_id)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, role_id, tenure_id, author_person_id, service, uri, excerpt, embedding, created_at, source_uri, source_hash, chunk_index, keyword_hashes
                FROM chunks
                WHERE role_id = %s
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (role_id, _vector_param(embedding), limit),
            ).fetchall()
        return [
            ChunkRecord(
                id=str(row[0]),
                role_id=str(row[1]),
                tenure_id=str(row[2]),
                author_person_id=str(row[3]),
                service=row[4],
                uri=row[5],
                excerpt=row[6],
                embedding=_vector_list(row[7]),
                created_at=row[8],
                    source_uri=row[9], source_hash=row[10], chunk_index=row[11], keyword_hashes=row[12],
            )
            for row in rows
        ]

    def keyword_search(self, role_id: str, terms: list[str], limit: int) -> list[ChunkRecord]:
        _require_role(self, role_id)
        if not terms:
            return []
        from tokens import keyword_hash

        clauses = " OR ".join(["excerpt ILIKE %s" for _ in terms])
        params: list = [role_id, *[f"%{term}%" for term in terms], [keyword_hash(term) for term in terms], limit]
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT id, role_id, tenure_id, author_person_id, service, uri, excerpt, embedding, created_at, source_uri, source_hash, chunk_index, keyword_hashes
                FROM chunks
                WHERE role_id = %s AND ({clauses} OR keyword_hashes ?| %s)
                LIMIT %s
                """,
                params,
            ).fetchall()
        return [
            ChunkRecord(
                id=str(row[0]),
                role_id=str(row[1]),
                tenure_id=str(row[2]),
                author_person_id=str(row[3]),
                service=row[4],
                uri=row[5],
                excerpt=row[6],
                embedding=_vector_list(row[7]),
                created_at=row[8],
                    source_uri=row[9], source_hash=row[10], chunk_index=row[11], keyword_hashes=row[12],
            )
            for row in rows
        ]

    def touch_role(self, role_id: str, when: datetime | None = None) -> None:
        moment = when or _now()
        with self._connect() as connection:
            connection.execute("UPDATE roles SET last_activity_at = %s WHERE id = %s", (moment, role_id))
            connection.commit()

    def roles_inactive_before(self, cutoff: datetime) -> list[Role]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, organization_id, title, created_at, last_activity_at
                FROM roles WHERE last_activity_at < %s
                """,
                (cutoff,),
            ).fetchall()
        return [
            Role(id=str(row[0]), organization_id=str(row[1]), title=row[2], created_at=row[3], last_activity_at=row[4])
            for row in rows
        ]

    def write_audit(
        self,
        tool_name: str,
        *,
        error_code: str | None = None,
        organization_id: str | None = None,
        role_id: str | None = None,
    ) -> AuditRecord:
        audit_id = _id()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_log (id, tool_name, error_code, organization_id, role_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (audit_id, tool_name, error_code, organization_id, role_id),
            )
            connection.commit()
            row = connection.execute(
                "SELECT id, tool_name, error_code, organization_id, role_id, created_at FROM audit_log WHERE id = %s",
                (audit_id,),
            ).fetchone()
        return AuditRecord(
            id=str(row[0]),
            tool_name=row[1],
            error_code=row[2],
            organization_id=str(row[3]) if row[3] else None,
            role_id=str(row[4]) if row[4] else None,
            created_at=row[5],
        )

    def audits(self) -> list[AuditRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, tool_name, error_code, organization_id, role_id, created_at FROM audit_log ORDER BY created_at"
            ).fetchall()
        return [
            AuditRecord(
                id=str(row[0]),
                tool_name=row[1],
                error_code=row[2],
                organization_id=str(row[3]) if row[3] else None,
                role_id=str(row[4]) if row[4] else None,
                created_at=row[5],
            )
            for row in rows
        ]

    def create_job(self, role_id: str, service: str, query: str, max_items: int) -> JobRecord:
        job_id = _id()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO ingestion_jobs (id, role_id, service, query, max_items, status, progress, chunks_ingested)
                VALUES (%s, %s, %s, %s, %s, 'queued', 0, 0)
                """,
                (job_id, role_id, service, query, max_items),
            )
            connection.commit()
        job = self.get_job(job_id)
        if job is None:
            raise RuntimeError("Job insert did not persist")
        return job

    def get_job(self, job_id: str) -> JobRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, role_id, service, query, max_items, status, progress, chunks_ingested
                FROM ingestion_jobs WHERE id = %s
                """,
                (job_id,),
            ).fetchone()
        if not row:
            return None
        if self.get_role(str(row[1])) is None:
            return None
        return JobRecord(
            id=str(row[0]),
            role_id=str(row[1]),
            service=row[2],
            query=row[3],
            max_items=row[4],
            status=row[5],
            progress=row[6],
            chunks_ingested=row[7],
        )

    @contextmanager
    def job_lock(self, job_id: str):
        # Session advisory locks cover fetch/embed/commit across worker processes.
        # They release on connection close or worker death, so retries can resume.
        with self._connect() as connection:
            acquired = connection.execute("SELECT pg_try_advisory_lock(hashtextextended(%s,0))", (job_id,)).fetchone()[0]
            try:
                yield bool(acquired)
            finally:
                if acquired:
                    connection.execute("SELECT pg_advisory_unlock(hashtextextended(%s,0))", (job_id,))

    def update_job(self, job_id: str, *, status: str, progress: int, chunks_ingested: int) -> JobRecord:
        if self.get_job(job_id) is None:
            from errors import JOB_NOT_FOUND, CodedToolError
            raise CodedToolError(JOB_NOT_FOUND, "Ingestion job was not found.")
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE ingestion_jobs
                SET status = %s, progress = %s, chunks_ingested = %s
                WHERE id = %s
                """,
                (status, progress, chunks_ingested, job_id),
            )
            connection.commit()
        job = self.get_job(job_id)
        if job is None:
            raise RuntimeError("Job update lost the row")
        return job

    def save_secret(self, key: str, payload: dict) -> None:
        import time

        from tokens import encrypt_token
        payload = {**payload, "expires_at": time.time() + 300}
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO oauth_transactions (id, payload_json, role_id) VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET payload_json = EXCLUDED.payload_json
                """,
                (key, encrypt_token(json.dumps(payload)), payload.get("role_id")),
            )
            connection.commit()

    def pop_secret(self, key: str) -> dict | None:
        import time
        from tokens import decrypt_token
        with self._connect() as connection:
            row = connection.execute(
                "DELETE FROM oauth_transactions WHERE id = %s RETURNING payload_json",
                (key,),
            ).fetchone()
            connection.commit()
        if not row:
            return None
        try:
            payload = json.loads(decrypt_token(row[0]))
        except Exception:
            # Pre-hardening plaintext transactions cannot authorize a new grant.
            return None
        return payload if payload.get("expires_at", 0) > time.time() else None

    def jobs_for_role(self, role_id: str) -> list[JobRecord]:
        _require_role(self, role_id)
        with self._connect() as connection:
            ids = connection.execute("SELECT id FROM ingestion_jobs WHERE role_id=%s ORDER BY created_at DESC LIMIT 20", (role_id,)).fetchall()
        return [job for row in ids if (job := self.get_job(str(row[0]))) is not None]

    def save_credential(self, role_id: str, service: str, ciphertext: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO connector_credentials (id, role_id, service, token_ciphertext)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (role_id, service) DO UPDATE SET token_ciphertext = EXCLUDED.token_ciphertext
                """,
                (_id(), role_id, service, ciphertext),
            )
            connection.commit()

    def get_credential(self, role_id: str, service: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT token_ciphertext FROM connector_credentials WHERE role_id = %s AND service = %s",
                (role_id, service),
            ).fetchone()
        if not row:
            return None
        return row[0]

    def role_count_for_domain(self, domain: str) -> int:
        org = self.get_organization_by_domain(domain)
        if not org:
            return 0
        with self._connect() as connection:
            row = connection.execute(
                "SELECT count(*) FROM roles WHERE organization_id = %s",
                (org.id,),
            ).fetchone()
        return int(row[0])

    def open_tenure_count(self, role_id: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT count(*) FROM tenures WHERE role_id = %s AND ended_on IS NULL",
                (role_id,),
            ).fetchone()
        return int(row[0])

    def owner_for_retention(self, role_id: str) -> str:
        with self._connect() as connection:
            row = connection.execute("SELECT o.subject FROM roles r JOIN organizations o ON r.organization_id=o.id WHERE r.id=%s", (role_id,)).fetchone()
        return row[0] if row else ""

    def cleanup_transients(self, cutoff: datetime) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM audit_log WHERE created_at<%s", (cutoff,))
            connection.execute("DELETE FROM oauth_transactions WHERE created_at<now()-interval '5 minutes'")


def _guard_scope(method, resource: str):
    @wraps(method)
    def checked(self, identifier, *args, **kwargs):
        if resource == "role":
            _require_role(self, identifier)
        else:
            _require_organization(self, identifier)
        return method(self, identifier, *args, **kwargs)
    return checked


# All store reads/writes that take an arbitrary resource id enforce ownership,
# including direct service calls, callbacks, and workers.
for _store_type in (MemoryStore, PostgresStore):
    for _name in ("ensure_officeholder", "find_role", "create_role", "monthly_chunk_count"):
        setattr(_store_type, _name, _guard_scope(getattr(_store_type, _name), "organization"))
    for _name in ("find_open_tenure", "open_tenure", "set_active_role", "record_connection",
                  "touch_role", "delete_namespace", "save_credential", "get_credential",
                  "create_job", "open_tenure_count"):
        setattr(_store_type, _name, _guard_scope(getattr(_store_type, _name), "role"))


_store: Store | None = None


def build_store() -> Store:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        return PostgresStore(database_url)
    from runtime import local_test_mode
    if not local_test_mode():
        raise RuntimeError("Production requires DATABASE_URL; memory storage is restricted to local tests")
    return MemoryStore()


def current_store() -> Store:
    global _store
    if _store is None:
        _store = build_store()
    return _store


def reset_store(store: Store | None = None) -> Store:
    global _store
    if store is not None:
        _store = store
        return _store
    test_url = os.environ.get("WISDOMTWIN_TEST_DATABASE_URL", "").strip()
    if test_url:
        postgres = PostgresStore(test_url)
        postgres.truncate_all()
        _store = postgres
        return _store
    _store = MemoryStore()
    return _store


def retention_cutoff(now: datetime | None = None) -> datetime:
    moment = now or _now()
    return moment - timedelta(days=RETENTION_DAYS)
