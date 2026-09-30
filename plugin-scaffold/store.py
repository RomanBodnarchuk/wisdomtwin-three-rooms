"""Role-namespace storage. Postgres when DATABASE_URL is set, memory otherwise."""

from __future__ import annotations

import json
import math
import os
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

from domain import EMBEDDING_DIMENSIONS, RETENTION_DAYS


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _id() -> str:
    return str(uuid.uuid4())


@dataclass
class Organization:
    id: str
    domain: str
    created_at: datetime


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
    active_role_id: str | None = None

    def upsert_organization(self, domain: str) -> Organization:
        for org in self.organizations.values():
            if org.domain == domain:
                return org
        org = Organization(id=_id(), domain=domain, created_at=_now())
        self.organizations[org.id] = org
        return org

    def get_organization_by_domain(self, domain: str) -> Organization | None:
        for org in self.organizations.values():
            if org.domain == domain:
                return org
        return None

    def ensure_officeholder(self, organization_id: str) -> Person:
        for person in self.persons.values():
            if person.organization_id == organization_id:
                return person
        person = Person(
            id=_id(),
            organization_id=organization_id,
            display_name="Current officeholder",
            created_at=_now(),
        )
        self.persons[person.id] = person
        return person

    def find_role(self, organization_id: str, title: str) -> Role | None:
        for role in self.roles.values():
            if role.organization_id == organization_id and role.title == title:
                return role
        return None

    def create_role(self, organization_id: str, title: str) -> Role:
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
        self.active_role_id = role_id

    def get_active_role_id(self) -> str | None:
        return self.active_role_id

    def get_role(self, role_id: str) -> Role | None:
        return self.roles.get(role_id)

    def get_organization(self, organization_id: str) -> Organization | None:
        return self.organizations.get(organization_id)

    def record_connection(self, role_id: str, service: str, domain: str, role_title: str) -> None:
        self.connection_rows = [
            row for row in self.connection_rows if not (row.role_id == role_id and row.service == service)
        ]
        self.connection_rows.append(
            Connection(
                role_id=role_id,
                service=service,
                domain=domain,
                role_title=role_title,
                connected_at=_now(),
            )
        )

    def connections(self) -> list[Connection]:
        return list(self.connection_rows)

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

    def upsert_chunks(self, chunks: list[ChunkRecord]) -> int:
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
        return [chunk for chunk in self.chunks.values() if chunk.role_id == role_id]

    def delete_namespace(self, role_id: str) -> int:
        doomed = [chunk.id for chunk in self.chunks.values() if chunk.role_id == role_id]
        for chunk_id in doomed:
            self.chunks.pop(chunk_id, None)
        return len(doomed)

    def vector_search(self, role_id: str, embedding: list[float], limit: int) -> list[ChunkRecord]:
        scoped = [chunk for chunk in self.chunks.values() if chunk.role_id == role_id]
        scoped.sort(key=lambda chunk: _cosine(embedding, chunk.embedding), reverse=True)
        return scoped[:limit]

    def keyword_search(self, role_id: str, terms: list[str], limit: int) -> list[ChunkRecord]:
        scoped = [chunk for chunk in self.chunks.values() if chunk.role_id == role_id]
        if not terms:
            return []

        def score(chunk: ChunkRecord) -> int:
            excerpt = chunk.excerpt.lower()
            return sum(1 for term in terms if term in excerpt)

        ranked = [chunk for chunk in scoped if score(chunk) > 0]
        ranked.sort(key=score, reverse=True)
        return ranked[:limit]

    def touch_role(self, role_id: str, when: datetime | None = None) -> None:
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
        return self.jobs.get(job_id)

    def update_job(self, job_id: str, *, status: str, progress: int, chunks_ingested: int) -> JobRecord:
        job = self.jobs[job_id]
        job.status = status
        job.progress = progress
        job.chunks_ingested = chunks_ingested
        return job

    def save_secret(self, key: str, payload: dict) -> None:
        self.secrets[key] = payload

    def pop_secret(self, key: str) -> dict | None:
        return self.secrets.pop(key, None)

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


class PostgresStore:
    """pgvector-backed store. Role filters are SQL predicates."""

    def __init__(self, database_url: str) -> None:
        import psycopg
        from pgvector.psycopg import register_vector

        self._psycopg = psycopg
        self._register_vector = register_vector
        self._database_url = database_url
        self._active_role_id: str | None = None
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
        finally:
            connection.close()

    def truncate_all(self) -> None:
        self._active_role_id = None
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
        with self._connect() as connection:
            row = connection.execute(
                """
                INSERT INTO organizations (id, domain)
                VALUES (%s, %s)
                ON CONFLICT (domain) DO UPDATE SET domain = EXCLUDED.domain
                RETURNING id, domain, created_at
                """,
                (_id(), domain),
            ).fetchone()
            connection.commit()
        return Organization(id=str(row[0]), domain=row[1], created_at=row[2])

    def get_organization_by_domain(self, domain: str) -> Organization | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, domain, created_at FROM organizations WHERE domain = %s",
                (domain,),
            ).fetchone()
        if not row:
            return None
        return Organization(id=str(row[0]), domain=row[1], created_at=row[2])

    def ensure_officeholder(self, organization_id: str) -> Person:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, organization_id, display_name, created_at FROM persons WHERE organization_id = %s LIMIT 1",
                (organization_id,),
            ).fetchone()
            if row:
                return Person(id=str(row[0]), organization_id=str(row[1]), display_name=row[2], created_at=row[3])
            person_id = _id()
            connection.execute(
                "INSERT INTO persons (id, organization_id, display_name) VALUES (%s, %s, %s)",
                (person_id, organization_id, "Current officeholder"),
            )
            connection.commit()
            created = connection.execute(
                "SELECT id, organization_id, display_name, created_at FROM persons WHERE id = %s",
                (person_id,),
            ).fetchone()
        return Person(id=str(created[0]), organization_id=str(created[1]), display_name=created[2], created_at=created[3])

    def find_role(self, organization_id: str, title: str) -> Role | None:
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
        existing = self.find_open_tenure(role_id)
        if existing:
            return existing
        tenure_id = _id()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tenures (id, role_id, person_id, started_on, ended_on)
                VALUES (%s, %s, %s, %s, NULL)
                """,
                (tenure_id, role_id, person_id, started_on),
            )
            connection.commit()
        tenure = self.find_open_tenure(role_id)
        if tenure is None:
            raise RuntimeError("Tenure insert did not persist")
        return tenure

    def set_active_role(self, role_id: str) -> None:
        self._active_role_id = role_id
        with self._connect() as connection:
            connection.execute("DELETE FROM active_role")
            connection.execute("INSERT INTO active_role (role_id) VALUES (%s)", (role_id,))
            connection.commit()

    def get_active_role_id(self) -> str | None:
        if self._active_role_id:
            return self._active_role_id
        with self._connect() as connection:
            row = connection.execute("SELECT role_id FROM active_role LIMIT 1").fetchone()
        if not row:
            return None
        self._active_role_id = str(row[0])
        return self._active_role_id

    def get_role(self, role_id: str) -> Role | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, organization_id, title, created_at, last_activity_at
                FROM roles WHERE id = %s
                """,
                (role_id,),
            ).fetchone()
        if not row:
            return None
        return Role(id=str(row[0]), organization_id=str(row[1]), title=row[2], created_at=row[3], last_activity_at=row[4])

    def get_organization(self, organization_id: str) -> Organization | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, domain, created_at FROM organizations WHERE id = %s",
                (organization_id,),
            ).fetchone()
        if not row:
            return None
        return Organization(id=str(row[0]), domain=row[1], created_at=row[2])

    def record_connection(self, role_id: str, service: str, domain: str, role_title: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO connections (id, role_id, service, domain, role_title)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (role_id, service) DO UPDATE
                SET domain = EXCLUDED.domain, role_title = EXCLUDED.role_title, connected_at = now()
                """,
                (_id(), role_id, service, domain, role_title),
            )
            connection.commit()

    def connections(self) -> list[Connection]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT role_id, service, domain, role_title, connected_at FROM connections ORDER BY connected_at"
            ).fetchall()
        return [
            Connection(role_id=str(row[0]), service=row[1], domain=row[2], role_title=row[3], connected_at=row[4])
            for row in rows
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

    def upsert_chunks(self, chunks: list[ChunkRecord]) -> int:
        with self._connect() as connection:
            for chunk in chunks:
                connection.execute(
                    """
                    INSERT INTO chunks (
                        id, role_id, tenure_id, author_person_id, service, uri, excerpt, embedding
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (role_id, uri) DO UPDATE SET
                        tenure_id = EXCLUDED.tenure_id,
                        author_person_id = EXCLUDED.author_person_id,
                        excerpt = EXCLUDED.excerpt,
                        embedding = EXCLUDED.embedding,
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
                    ),
                )
            connection.commit()
        return len(chunks)

    def chunks_for_role(self, role_id: str) -> list[ChunkRecord]:
        return self._load_chunks("WHERE role_id = %s", (role_id,))

    def delete_namespace(self, role_id: str) -> int:
        with self._connect() as connection:
            row = connection.execute("DELETE FROM chunks WHERE role_id = %s", (role_id,)).rowcount
            connection.commit()
        return int(row or 0)

    def _load_chunks(self, where_sql: str, params: tuple) -> list[ChunkRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT id, role_id, tenure_id, author_person_id, service, uri, excerpt, embedding, created_at
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
                )
            )
        return loaded

    def vector_search(self, role_id: str, embedding: list[float], limit: int) -> list[ChunkRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, role_id, tenure_id, author_person_id, service, uri, excerpt, embedding, created_at
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
            )
            for row in rows
        ]

    def keyword_search(self, role_id: str, terms: list[str], limit: int) -> list[ChunkRecord]:
        if not terms:
            return []
        clauses = " OR ".join(["excerpt ILIKE %s" for _ in terms])
        params: list = [role_id, *[f"%{term}%" for term in terms], limit]
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT id, role_id, tenure_id, author_person_id, service, uri, excerpt, embedding, created_at
                FROM chunks
                WHERE role_id = %s AND ({clauses})
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

    def update_job(self, job_id: str, *, status: str, progress: int, chunks_ingested: int) -> JobRecord:
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
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO oauth_transactions (id, payload_json) VALUES (%s, %s)
                ON CONFLICT (id) DO UPDATE SET payload_json = EXCLUDED.payload_json
                """,
                (key, json.dumps(payload)),
            )
            connection.commit()

    def pop_secret(self, key: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "DELETE FROM oauth_transactions WHERE id = %s RETURNING payload_json",
                (key,),
            ).fetchone()
            connection.commit()
        if not row:
            return None
        return json.loads(row[0])

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


_store: Store | None = None


def build_store() -> Store:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        return PostgresStore(database_url)
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
