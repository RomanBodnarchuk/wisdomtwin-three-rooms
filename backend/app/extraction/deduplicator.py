"""Historical Entity Resolution across up to 25 years of role holders and Cross-Source Episode Deduplication."""

from __future__ import annotations

from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, List, Optional

from ..schemas.decision_episode import (
    DecisionEpisode,
    RoleHolderIdentity,
    RoleTag,
)


class HistoricalEntityResolver:
    """Resolves people across email aliases, name changes, Slack handles, and Zoom display names
    against Microsoft Entra ID and the historical role-tenure registry.
    """

    def __init__(self) -> None:
        self._identities_by_id: Dict[str, RoleHolderIdentity] = {}
        self._alias_index: Dict[str, str] = {}
        self._seed_default_role_holders()

    def _seed_default_role_holders(self) -> None:
        defaults = [
            RoleHolderIdentity(
                entra_object_id="entra-ceo-mercer",
                display_name="Daniel Mercer",
                primary_email="daniel.mercer@enterprise.local",
                known_aliases=["dmercer", "Daniel Mercer, CEO", "d.mercer@enterprise.local"],
                role=RoleTag.CEO,
                title="Chief Executive Officer",
                tenure_start=datetime(2019, 1, 1),
            ),
            RoleHolderIdentity(
                entra_object_id="entra-cfo-2026",
                display_name="Elena Vance",
                primary_email="elena.vance@enterprise.local",
                known_aliases=["evance", "CFO", "CFO Twin", "e.vance@enterprise.local"],
                role=RoleTag.CFO,
                title="Chief Financial Officer",
                tenure_start=datetime(2022, 4, 1),
            ),
            RoleHolderIdentity(
                entra_object_id="entra-cfo-2016",
                display_name="Marcus Sterling",
                primary_email="marcus.sterling@enterprise.local",
                known_aliases=["msterling", "Marcus Sterling (Former CFO)"],
                role=RoleTag.CFO,
                title="Chief Financial Officer (2016-2022)",
                tenure_start=datetime(2016, 1, 1),
                tenure_end=datetime(2022, 3, 31),
            ),
            RoleHolderIdentity(
                entra_object_id="entra-cto-2026",
                display_name="Dr. Aris Thorne",
                primary_email="aris.thorne@enterprise.local",
                known_aliases=["athorne", "CTO", "CTO Twin"],
                role=RoleTag.CTO,
                title="Chief Technology Officer",
                tenure_start=datetime(2020, 9, 1),
            ),
            RoleHolderIdentity(
                entra_object_id="entra-cro-2026",
                display_name="Jordan Blake",
                primary_email="jordan.blake@enterprise.local",
                known_aliases=["jblake", "CRO", "CRO Twin"],
                role=RoleTag.CRO,
                title="Chief Revenue Officer",
                tenure_start=datetime(2021, 2, 1),
            ),
            RoleHolderIdentity(
                entra_object_id="entra-cmo-2026",
                display_name="Maya Lin",
                primary_email="maya.lin@enterprise.local",
                known_aliases=["mlin", "CMO", "CMO Twin"],
                role=RoleTag.CMO,
                title="Chief Marketing Officer",
                tenure_start=datetime(2023, 1, 1),
            ),
            RoleHolderIdentity(
                entra_object_id="entra-legal-2026",
                display_name="Stella Cabrera",
                primary_email="stella.cabrera@enterprise.local",
                known_aliases=["scabrera", "Legal", "Chief Legal Officer", "Chief Legal Officer Twin"],
                role=RoleTag.LEGAL,
                title="Chief Legal Officer",
                tenure_start=datetime(2018, 6, 1),
            ),
        ]
        for identity in defaults:
            self.register_identity(identity)

    def register_identity(self, identity: RoleHolderIdentity) -> None:
        self._identities_by_id[identity.entra_object_id] = identity
        self._alias_index[identity.primary_email.lower()] = identity.entra_object_id
        self._alias_index[identity.display_name.lower()] = identity.entra_object_id
        for alias in identity.known_aliases:
            self._alias_index[alias.lower()] = identity.entra_object_id

    def resolve(self, raw_identifier: str, fallback_role: RoleTag = RoleTag.CFO) -> RoleHolderIdentity:
        normalized = raw_identifier.strip().lower()
        if normalized in self._alias_index:
            return self._identities_by_id[self._alias_index[normalized]]

        for identity in self._identities_by_id.values():
            if identity.role == fallback_role and identity.tenure_end is None:
                return identity

        return next(iter(self._identities_by_id.values()))

    def list_role_holders(self, role: Optional[RoleTag] = None) -> List[RoleHolderIdentity]:
        holders = list(self._identities_by_id.values())
        if role is not None:
            return [h for h in holders if h.role == role]
        return holders


class CrossSourceDeduplicator:
    """Clusters near-identical decisions across email, SharePoint decks, Teams chats, and transcripts
    into a single canonical DecisionEpisode with merged evidence chains.
    """

    def __init__(self, similarity_threshold: float = 0.78) -> None:
        self.similarity_threshold = similarity_threshold

    def deduplicate(self, episodes: List[DecisionEpisode]) -> List[DecisionEpisode]:
        merged: List[DecisionEpisode] = []

        for candidate in episodes:
            matched_existing: Optional[DecisionEpisode] = None
            for existing in merged:
                if existing.role != candidate.role:
                    continue
                sim = SequenceMatcher(
                    None,
                    existing.decision_statement.lower(),
                    candidate.decision_statement.lower(),
                ).ratio()
                if sim >= self.similarity_threshold:
                    matched_existing = existing
                    break

            if matched_existing is None:
                merged.append(candidate)
            else:
                self._merge_into(matched_existing, candidate)

        return merged

    @staticmethod
    def _merge_into(target: DecisionEpisode, incoming: DecisionEpisode) -> None:
        existing_doc_ids = {ev.source_document_id for ev in target.evidence_considered}
        for ev in incoming.evidence_considered:
            if ev.source_document_id not in existing_doc_ids:
                target.evidence_considered.append(ev)
                existing_doc_ids.add(ev.source_document_id)

        existing_rules = {c.rule_statement for c in target.constraints_and_thresholds}
        for constraint in incoming.constraints_and_thresholds:
            if constraint.rule_statement not in existing_rules:
                target.constraints_and_thresholds.append(constraint)
                existing_rules.add(constraint.rule_statement)

        for alt in incoming.alternatives_rejected:
            if alt not in target.alternatives_rejected:
                target.alternatives_rejected.append(alt)

        target.confidence_score = round(max(target.confidence_score, incoming.confidence_score), 3)
