"""Durable encrypted OAuth state and operator-provisioned role entitlements.

Production uses the project's Postgres. SQLite is an explicit local test adapter.
Opaque credentials are indexed by SHA-256 and encrypted with the connector key.
One-use state is consumed by DELETE RETURNING, including across processes.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from domain import domain_rejection_reason, normalize_domain, normalize_title
from runtime import local_test_mode
from tokens import decrypt_token, encrypt_token


def stable_subject(issuer: str, provider_subject: str) -> str:
    if not issuer or not provider_subject:
        raise ValueError("Verified issuer and subject are required")
    return "oidc:" + hashlib.sha256(json.dumps([issuer, provider_subject]).encode()).hexdigest()


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class GrantInvalidated(PermissionError):
    """The consent's membership epoch or token family is no longer current."""


class SecurityStore:
    def __init__(self, *, database_url: str = "", sqlite_path: str = "") -> None:
        if not database_url and (not sqlite_path or not local_test_mode()):
            raise RuntimeError("Durable Postgres authorization storage is required outside local tests")
        self.database_url = database_url
        self.sqlite_path = sqlite_path
        if sqlite_path:
            Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            self.execute(db, """CREATE TABLE IF NOT EXISTS security_entries (
                kind TEXT NOT NULL, key_hash TEXT NOT NULL, payload TEXT NOT NULL,
                expires DOUBLE PRECISION NOT NULL, subject TEXT NOT NULL, family TEXT NOT NULL,
                PRIMARY KEY (kind, key_hash))""")
            self.execute(db, """CREATE TABLE IF NOT EXISTS security_revocations (
                family TEXT PRIMARY KEY, expires DOUBLE PRECISION NOT NULL)""")
            self.execute(db, """CREATE TABLE IF NOT EXISTS security_memberships (
                subject TEXT NOT NULL, domain TEXT NOT NULL, payload TEXT NOT NULL,
                PRIMARY KEY (subject, domain))""")
            self.execute(db, """CREATE TABLE IF NOT EXISTS security_subject_epochs (
                subject TEXT PRIMARY KEY, epoch BIGINT NOT NULL)""")

    @contextmanager
    def connection(self):
        if self.database_url:
            import psycopg

            with psycopg.connect(self.database_url) as db:
                yield db
        else:
            db = sqlite3.connect(self.sqlite_path, timeout=20)
            try:
                with db:
                    yield db
            finally:
                db.close()

    def execute(self, db, sql: str, params: tuple = ()):
        return db.execute(sql.replace("?", "%s") if self.database_url else sql, params)

    def _lock(self, db, namespace: str, key: str) -> None:
        if self.database_url:
            lock_id = int.from_bytes(hashlib.sha256(f"{namespace}:{key}".encode()).digest()[:8], "big", signed=True)
            self.execute(db, "SELECT pg_advisory_xact_lock(?)", (lock_id,))
        elif not db.in_transaction:
            # SQLite serializes writes; Postgres locks only the affected identity/family.
            self.execute(db, "BEGIN IMMEDIATE")

    def _put(self, db, kind: str, key: str, payload: dict, ttl: int, subject: str, family: str) -> None:
        self.execute(db, """INSERT INTO security_entries (kind,key_hash,payload,expires,subject,family)
            VALUES (?,?,?,?,?,?) ON CONFLICT (kind,key_hash) DO UPDATE SET
            payload=EXCLUDED.payload,expires=EXCLUDED.expires,subject=EXCLUDED.subject,family=EXCLUDED.family""",
            (kind, _digest(key), encrypt_token(json.dumps(payload)), time.time() + ttl, subject, family))

    def put(self, kind: str, key: str, payload: dict, ttl: int, *, subject: str = "", family: str = "") -> None:
        with self.connection() as db:
            self._put(db, kind, key, payload, ttl, subject, family)

    def _subject_epoch(self, db, subject: str) -> int:
        row = self.execute(db, "SELECT epoch FROM security_subject_epochs WHERE subject=?", (subject,)).fetchone()
        return int(row[0]) if row else 0

    def subject_epoch(self, subject: str) -> int:
        with self.connection() as db:
            return self._subject_epoch(db, subject)

    def _check_subject(self, db, subject: str, expected_epoch: int) -> None:
        members = self.execute(db, "SELECT 1 FROM security_memberships WHERE subject=?", (subject,)).fetchall()
        if type(expected_epoch) is not int or self._subject_epoch(db, subject) != expected_epoch or len(members) != 1:
            raise GrantInvalidated("Corporate membership or consent changed")

    def put_subject_entry(self, kind: str, key: str, payload: dict, ttl: int, *, subject: str, expected_epoch: int) -> None:
        with self.connection() as db:
            self._lock(db, "subject", subject)
            self._check_subject(db, subject, expected_epoch)
            self._put(db, kind, key, payload, ttl, subject, "")

    def issue_grants(self, subject: str, expected_epoch: int, family: str, entries: list[tuple[str, str, dict, int]]) -> None:
        """Validate and insert the complete pair atomically with all revocation paths."""
        with self.connection() as db:
            self._lock(db, "subject", subject)
            self._lock(db, "family", family)
            self._check_subject(db, subject, expected_epoch)
            if self.execute(db, "SELECT 1 FROM security_revocations WHERE family=? AND expires>?", (family, time.time())).fetchone():
                raise GrantInvalidated("Token family was revoked")
            for kind, key, payload, ttl in entries:
                self._put(db, kind, key, payload, ttl, subject, family)
            # Keep old refresh relationships for the lifetime of their active successor.
            lineage_ttl = max(ttl for kind, _, _, ttl in entries if kind == "family")
            self.execute(db, "UPDATE security_entries SET expires=? WHERE kind='family' AND family=?",
                         (time.time() + lineage_ttl, family))

    def get(self, kind: str, key: str, *, consume: bool = False) -> dict | None:
        with self.connection() as db:
            if consume:
                row = self.execute(db, "DELETE FROM security_entries WHERE kind=? AND key_hash=? RETURNING payload,expires,family",
                                   (kind, _digest(key))).fetchone()
            else:
                row = self.execute(db, "SELECT payload,expires,family FROM security_entries WHERE kind=? AND key_hash=?",
                                   (kind, _digest(key))).fetchone()
            if not row or row[1] <= time.time():
                return None
            if row[2] and self.execute(db, "SELECT 1 FROM security_revocations WHERE family=? AND expires>?",
                                       (row[2], time.time())).fetchone():
                return None
        return json.loads(decrypt_token(row[0]))

    def revoke_family(self, family: str) -> None:
        with self.connection() as db:
            self._lock(db, "family", family)
            self.execute(db, "INSERT INTO security_revocations (family,expires) VALUES (?,?) ON CONFLICT (family) DO UPDATE SET expires=EXCLUDED.expires",
                         (family, time.time() + 31 * 86400))
            self.execute(db, "DELETE FROM security_entries WHERE family=?", (family,))

    def _invalidate_subject(self, db, subject: str) -> None:
        self.execute(db, """INSERT INTO security_subject_epochs (subject,epoch) VALUES (?,1)
            ON CONFLICT (subject) DO UPDATE SET epoch=security_subject_epochs.epoch+1""", (subject,))
        families = self.execute(db, "SELECT DISTINCT family FROM security_entries WHERE subject=? AND family<>''", (subject,)).fetchall()
        for row in families:
            self.execute(db, "INSERT INTO security_revocations (family,expires) VALUES (?,?) ON CONFLICT (family) DO UPDATE SET expires=EXCLUDED.expires",
                         (row[0], time.time() + 31 * 86400))
        self.execute(db, "DELETE FROM security_entries WHERE subject=?", (subject,))

    def revoke_subject(self, subject: str) -> None:
        with self.connection() as db:
            self._lock(db, "subject", subject)
            self._invalidate_subject(db, subject)

    def provision(self, *, issuer: str, provider_subject: str, email: str, domain: str,
                  roles: list[str], slack_team_id: str = "", slack_user_id: str = "", google_subject: str = "") -> str:
        subject = stable_subject(issuer, provider_subject)
        domain = normalize_domain(domain)
        email = email.strip().lower()
        titles = [normalize_title(title) for title in roles]
        if domain_rejection_reason(domain) or email.rsplit("@", 1)[-1] != domain or not titles or not all(titles):
            raise ValueError("Provision an exact verified corporate email, domain, and role entitlement")
        payload = {"subject": subject, "issuer": issuer, "provider_subject": provider_subject, "email": email,
                   "domain": domain, "roles": titles, "slack_team_id": slack_team_id,
                   "slack_user_id": slack_user_id, "google_subject": google_subject}
        with self.connection() as db:
            self._lock(db, "subject", subject)
            self.execute(db, "INSERT INTO security_memberships (subject,domain,payload) VALUES (?,?,?) ON CONFLICT (subject,domain) DO UPDATE SET payload=EXCLUDED.payload",
                         (subject, domain, encrypt_token(json.dumps(payload))))
            self._invalidate_subject(db, subject)
        return subject

    def membership(self, subject: str, domain: str | None = None) -> dict | None:
        with self.connection() as db:
            if domain is None:
                rows = self.execute(db, "SELECT payload FROM security_memberships WHERE subject=?", (subject,)).fetchall()
                return json.loads(decrypt_token(rows[0][0])) if len(rows) == 1 else None
            row = self.execute(db, "SELECT payload FROM security_memberships WHERE subject=? AND domain=?", (subject, domain)).fetchone()
        return json.loads(decrypt_token(row[0])) if row else None

    def remove_member(self, subject: str) -> None:
        with self.connection() as db:
            self._lock(db, "subject", subject)
            self.execute(db, "DELETE FROM security_memberships WHERE subject=?", (subject,))
            self._invalidate_subject(db, subject)

    def sweep(self) -> None:
        with self.connection() as db:
            self.execute(db, "DELETE FROM security_entries WHERE expires<=?", (time.time(),))
            self.execute(db, "DELETE FROM security_revocations WHERE expires<=?", (time.time(),))


def security_store() -> SecurityStore:
    # No process-only credential cache; every read observes durable revocation.
    return SecurityStore(database_url=os.environ.get("DATABASE_URL", "").strip(),
                         sqlite_path=os.environ.get("WISDOMTWIN_AUTH_DB", "").strip())


def require_membership(subject: str, domain: str, title: str | None = None) -> dict:
    from errors import AUTHORIZATION_REQUIRED, CodedToolError

    member = security_store().membership(subject, domain)
    if not member or (title is not None and title not in member["roles"]):
        raise CodedToolError(AUTHORIZATION_REQUIRED, "A verified corporate identity and assigned role are required.")
    return member
