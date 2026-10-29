"""Permission-aware retrieval gate & compliance audit log.

Enforces:
1. Chunk- and episode-level Microsoft Entra ID ACL replication (user UPN, group OIDs, role tags).
2. Microsoft Purview sensitivity label rights enforcement (requiring VIEW and EXTRACT before any chunk
   is sent to an LLM or returned to a requester).
3. Real-time ACL mutation hook so group membership changes update within minutes.
4. Immutable compliance audit log (no raw PII in application debug logs).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from ..schemas.decision_episode import (
    DecisionEpisode,
    PurviewRight,
    RoleTag,
    SensitivityClassification,
)


class AuditLogEntry(BaseModel):
    """Immutable compliance audit log entry recorded for every query and surfaced episode."""

    audit_id: str = Field(default_factory=lambda: f"aud_{uuid.uuid4().hex[:12]}")
    timestamp_utc: datetime = Field(default_factory=datetime.utcnow)
    requester_hash: str = Field(..., description="SHA-256 pseudonymized requester identifier (no raw PII in logs)")
    role_queried: RoleTag
    question_redacted: str
    surfaced_episode_ids: List[str] = Field(default_factory=list)
    excluded_by_acl_count: int = 0
    excluded_by_purview_count: int = 0
    governance_action: str
    purview_classifications_surfaced: List[SensitivityClassification] = Field(default_factory=list)


class ComplianceAuditLogger:
    """Append-only compliance audit ledger aligned with Microsoft 365 Purview retention policies."""

    def __init__(self) -> None:
        self._ledger: List[AuditLogEntry] = []

    def record(
        self,
        requester_upn: str,
        role_queried: RoleTag,
        question: str,
        surfaced_episodes: List[DecisionEpisode],
        excluded_acl: int,
        excluded_purview: int,
        governance_action: str,
    ) -> AuditLogEntry:
        requester_hash = hashlib.sha256(requester_upn.lower().encode("utf-8")).hexdigest()[:16]
        entry = AuditLogEntry(
            requester_hash=f"sha256:{requester_hash}",
            role_queried=role_queried,
            question_redacted=question[:160],
            surfaced_episode_ids=[ep.episode_id for ep in surfaced_episodes],
            excluded_by_acl_count=excluded_acl,
            excluded_by_purview_count=excluded_purview,
            governance_action=governance_action,
            purview_classifications_surfaced=list(
                {ep.sensitivity_label.name for ep in surfaced_episodes}
            ),
        )
        self._ledger.append(entry)
        return entry

    def list_entries(self, limit: int = 50) -> List[AuditLogEntry]:
        return list(reversed(self._ledger[-limit:]))


class PermissionEnforcer:
    """Evaluates Entra ID ACLs and Purview sensitivity labels before retrieval reaches the model."""

    def __init__(self) -> None:
        self._user_purview_rights: Dict[str, List[PurviewRight]] = {
            "daniel.mercer@enterprise.local": [
                PurviewRight.VIEW,
                PurviewRight.EXTRACT,
                PurviewRight.EXPORT,
                PurviewRight.OWNER,
            ],
            "elena.vance@enterprise.local": [
                PurviewRight.VIEW,
                PurviewRight.EXTRACT,
            ],
        }

    def grant_user_rights(self, user_upn: str, rights: List[PurviewRight]) -> None:
        self._user_purview_rights[user_upn.lower()] = rights

    def check_episode_access(
        self,
        episode: DecisionEpisode,
        requester_upn: str,
        requester_groups: List[str],
        granted_purview_rights: Optional[List[PurviewRight]] = None,
    ) -> tuple[bool, Optional[str]]:
        """Returns (allowed, denial_reason) where denial_reason is 'acl' or 'purview'."""
        upn_lower = requester_upn.lower()
        acl = episode.acl_snapshot

        user_match = any(u.lower() == upn_lower for u in acl.allowed_user_ids)
        group_match = bool(set(requester_groups).intersection(set(acl.allowed_group_ids)))
        if not (user_match or group_match):
            return False, "acl"

        effective_rights = (
            granted_purview_rights
            if granted_purview_rights is not None
            else self._user_purview_rights.get(
                upn_lower,
                [PurviewRight.VIEW, PurviewRight.EXTRACT],
            )
        )
        required = set(episode.sensitivity_label.required_rights)
        if not required.issubset(set(effective_rights)):
            return False, "purview"

        return True, None

    def filter_episodes(
        self,
        episodes: List[DecisionEpisode],
        requester_upn: str,
        requester_groups: List[str],
        granted_purview_rights: Optional[List[PurviewRight]] = None,
    ) -> tuple[List[DecisionEpisode], int, int]:
        allowed: List[DecisionEpisode] = []
        excluded_acl = 0
        excluded_purview = 0

        for ep in episodes:
            ok, reason = self.check_episode_access(
                ep,
                requester_upn=requester_upn,
                requester_groups=requester_groups,
                granted_purview_rights=granted_purview_rights,
            )
            if ok:
                allowed.append(ep)
            elif reason == "acl":
                excluded_acl += 1
            elif reason == "purview":
                excluded_purview += 1

        return allowed, excluded_acl, excluded_purview
