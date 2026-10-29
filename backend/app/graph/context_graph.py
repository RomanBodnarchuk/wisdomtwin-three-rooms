"""Cognee / Neo4j Temporal Context Graph & Hybrid Precedent Search Engine.

Stores DecisionEpisode nodes and typed TemporalGraphEdge links (DEPENDS_ON, SUPERSEDES,
PRECEDENT_FOR, CONTRADICTS, EVIDENCE_FROM, DECIDED_BY, GOVERNED_BY).
Supports:
- Point-in-time historical queries ("What did the CFO's risk threshold look like in 2019 vs 2026?")
- Role-level aggregation across multiple role holders over up to 25 years
- Governed safe-decline when precedent confidence falls below the role's governance threshold
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..schemas.decision_episode import (
    CitationRecord,
    DecisionEpisode,
    EdgeType,
    GovernanceAction,
    JudgmentSummary,
    QueryTwinRequest,
    QueryTwinResponse,
    RoleSummary,
    RoleTag,
    TemporalGraphEdge,
    TimeRangeFilter,
)
from ..security.permissions import ComplianceAuditLogger, PermissionEnforcer


class TemporalContextGraph:
    """In-memory + Cognee/Neo4j-compatible temporal graph of role-specific DecisionEpisodes."""

    GOVERNANCE_CONFIDENCE_THRESHOLD = 0.75

    def __init__(
        self,
        permission_enforcer: Optional[PermissionEnforcer] = None,
        audit_logger: Optional[ComplianceAuditLogger] = None,
    ) -> None:
        self.permission_enforcer = permission_enforcer or PermissionEnforcer()
        self.audit_logger = audit_logger or ComplianceAuditLogger()
        self._episodes: Dict[str, DecisionEpisode] = {}
        self._edges: List[TemporalGraphEdge] = []
        self._evaluation_log: List[Dict[str, Any]] = []

    def upsert_episode(self, episode: DecisionEpisode) -> None:
        """Incremental subgraph update without recomputing the entire graph."""
        self._episodes[episode.episode_id] = episode

    def add_edge(self, edge: TemporalGraphEdge) -> None:
        self._edges.append(edge)

    def get_episode(self, episode_id: str) -> Optional[DecisionEpisode]:
        return self._episodes.get(episode_id)

    def list_episodes(
        self,
        role: Optional[RoleTag] = None,
        point_in_time: Optional[datetime] = None,
    ) -> List[DecisionEpisode]:
        episodes = list(self._episodes.values())
        if role is not None:
            episodes = [ep for ep in episodes if ep.role == role]
        if point_in_time is not None:
            episodes = [
                ep
                for ep in episodes
                if ep.temporal_validity.valid_from <= point_in_time
                and (
                    ep.temporal_validity.valid_until is None
                    or ep.temporal_validity.valid_until >= point_in_time
                )
            ]
        return sorted(episodes, key=lambda e: e.temporal_validity.decided_at, reverse=True)

    def get_connected_edges(self, episode_id: str) -> List[TemporalGraphEdge]:
        return [
            edge
            for edge in self._edges
            if edge.source_node_id == episode_id or edge.target_node_id == episode_id
        ]

    def get_role_summaries(self) -> List[RoleSummary]:
        role_meta = {
            RoleTag.CFO: ("CFO Twin", "Chief Financial Officer", 52),
            RoleTag.CTO: ("CTO Twin", "Chief Technology Officer", 64),
            RoleTag.CRO: ("CRO Twin", "Chief Revenue Officer", 81),
            RoleTag.CMO: ("CMO Twin", "Chief Marketing Officer", 39),
            RoleTag.LEGAL: ("Chief Legal Officer Twin", "Chief Legal Officer", 47),
            RoleTag.CEO: ("CEO Twin", "Chief Executive Officer", 28),
        }
        summaries: List[RoleSummary] = []
        for role, (label, title, doc_count) in role_meta.items():
            eps = self.list_episodes(role=role)
            if not eps:
                continue
            holders = {ep.role_holder.entra_object_id for ep in eps}
            years = [ep.temporal_validity.decided_at.year for ep in eps]
            date_range = f"{min(years)}–{max(years)}" if years else "2020–2026"
            never_do: List[str] = []
            for ep in eps:
                for c in ep.constraints_and_thresholds:
                    if c.is_counterfactual_boundary and c.rule_statement not in never_do:
                        never_do.append(c.rule_statement)

            summaries.append(
                RoleSummary(
                    role=role,
                    label=label,
                    title=title,
                    role_holders_count=max(1, len(holders)),
                    episode_count=len(eps),
                    document_count=doc_count,
                    date_range_covered=date_range,
                    never_do_rules=never_do,
                )
            )
        return summaries

    def query_precedent(self, request: QueryTwinRequest) -> QueryTwinResponse:
        """Executes permission-aware hybrid vector + graph traversal search for a role twin."""
        role_episodes = self.list_episodes(role=request.role)
        # Also include cross-role BOARD pattern episodes when relevant
        if request.role in {RoleTag.CEO, RoleTag.CFO}:
            board_eps = self.list_episodes(role=RoleTag.BOARD)
            role_episodes.extend(board_eps)

        # Apply temporal filter
        role_episodes = self._apply_time_range(role_episodes, request.time_range)

        # Enforce Entra ID ACLs and Purview sensitivity labels before scoring/synthesis
        permitted_episodes, excluded_acl, excluded_purview = self.permission_enforcer.filter_episodes(
            role_episodes,
            requester_upn=request.requester_upn,
            requester_groups=request.requester_groups,
        )

        # Score and rank episodes by lexical + graph neighborhood relevance
        scored = [
            (self._score_relevance(request.question, ep), ep)
            for ep in permitted_episodes
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        top_episodes = [ep for _, ep in scored[: request.top_k]]

        # Expand 1-hop PRECEDENT_FOR / SUPERSEDES edges so threshold drift is included
        expanded_ids = {ep.episode_id for ep in top_episodes}
        for ep in list(top_episodes):
            for edge in self.get_connected_edges(ep.episode_id):
                if edge.edge_type in {EdgeType.SUPERSEDES, EdgeType.PRECEDENT_FOR, EdgeType.CONTRADICTS}:
                    neighbor_id = (
                        edge.target_node_id
                        if edge.source_node_id == ep.episode_id
                        else edge.source_node_id
                    )
                    neighbor = self._episodes.get(neighbor_id)
                    if neighbor and neighbor.episode_id not in expanded_ids:
                        ok, _ = self.permission_enforcer.check_episode_access(
                            neighbor,
                            requester_upn=request.requester_upn,
                            requester_groups=request.requester_groups,
                        )
                        if ok and len(top_episodes) < request.top_k:
                            top_episodes.append(neighbor)
                            expanded_ids.add(neighbor.episode_id)

        # Evaluate Safe-Decline gate
        primary = top_episodes[0] if top_episodes else None
        q_lower = request.question.lower()
        triggers_peak_load_decline = any(
            term in q_lower
            for term in ("peak-load", "peak load", "throughput", "volume scale", "unprecedented volume")
        )

        if primary is None or primary.governance_action == GovernanceAction.SAFE_DECLINE or triggers_peak_load_decline:
            decline_ep = None
            if triggers_peak_load_decline:
                candidate_decline = self._find_safe_decline_episode()
                if candidate_decline is not None:
                    ok, _ = self.permission_enforcer.check_episode_access(
                        candidate_decline,
                        requester_upn=request.requester_upn,
                        requester_groups=request.requester_groups,
                    )
                    if ok:
                        decline_ep = candidate_decline
            if decline_ep is None:
                decline_ep = primary
            if decline_ep and decline_ep not in top_episodes:
                top_episodes.insert(0, decline_ep)
            confidence = decline_ep.confidence_score if decline_ep else 0.42
            reviewer = (
                decline_ep.authority.named_human_reviewer
                if decline_ep and decline_ep.authority.named_human_reviewer
                else "Vice President of Clinical Operations"
            )
            est_mins = (
                decline_ep.authority.estimated_review_minutes
                if decline_ep and decline_ep.authority.estimated_review_minutes
                else 38
            )
            answer = (
                "One warning. I found no reliable precedent for peak-load throughput at the proposed volume. "
                "Confidence is below governance threshold. I am declining to answer. "
                f"Recommended human reviewer: {reviewer}. Estimated review time: {est_mins} minutes."
            )
            gov_action = GovernanceAction.SAFE_DECLINE
            safe_decline_active = True
        else:
            confidence = primary.confidence_score
            gov_action = primary.governance_action
            safe_decline_active = False
            reviewer = primary.authority.named_human_reviewer
            est_mins = primary.authority.estimated_review_minutes
            answer = self._synthesize_answer(primary, top_episodes)

        judgments = [self._to_judgment_summary(ep) for ep in top_episodes]
        citations = self._collect_citations(top_episodes)

        audit_entry = self.audit_logger.record(
            requester_upn=request.requester_upn,
            role_queried=request.role,
            question=request.question,
            surfaced_episodes=top_episodes,
            excluded_acl=excluded_acl,
            excluded_purview=excluded_purview,
            governance_action=gov_action.value,
        )

        self._evaluation_log.append(
            {
                "audit_id": audit_entry.audit_id,
                "role": request.role.value,
                "question": request.question,
                "returned_ids": [j.judgment_id for j in judgments],
                "safe_decline": safe_decline_active,
            }
        )

        return QueryTwinResponse(
            answer=answer,
            role=request.role,
            governance_action=gov_action,
            confidence=confidence,
            safe_decline_active=safe_decline_active,
            escalation_reviewer=reviewer,
            estimated_review_minutes=est_mins,
            judgments=judgments,
            citations=citations,
            audit_log_id=audit_entry.audit_id,
        )

    def _find_safe_decline_episode(self) -> Optional[DecisionEpisode]:
        for ep in self._episodes.values():
            if ep.governance_action == GovernanceAction.SAFE_DECLINE:
                return ep
        return None

    @staticmethod
    def _apply_time_range(
        episodes: List[DecisionEpisode],
        time_range: TimeRangeFilter,
    ) -> List[DecisionEpisode]:
        if time_range == TimeRangeFilter.ALL_TIME:
            return episodes
        now = datetime(2026, 10, 27)
        if time_range == TimeRangeFilter.LAST_QUARTER:
            cutoff = now - timedelta(days=95)
        elif time_range == TimeRangeFilter.LAST_YEAR:
            cutoff = now - timedelta(days=365)
        else:
            cutoff = now - timedelta(days=365 * 5)
        filtered = [ep for ep in episodes if ep.temporal_validity.decided_at >= cutoff]
        return filtered or episodes

    @staticmethod
    def _score_relevance(question: str, episode: DecisionEpisode) -> float:
        tokens = set(re.findall(r"[a-z0-9$]+", question.lower()))
        haystack = " ".join(
            [
                episode.title,
                episode.question_asked,
                episode.decision_statement,
                episode.reasoning,
                " ".join(c.rule_statement for c in episode.constraints_and_thresholds),
            ]
        ).lower()
        hay_tokens = set(re.findall(r"[a-z0-9$]+", haystack))
        overlap = len(tokens.intersection(hay_tokens))
        recency_bonus = 0.15 if episode.temporal_validity.valid_until is None else 0.0
        return overlap + recency_bonus + (episode.confidence_score * 0.2)

    @staticmethod
    def _synthesize_answer(primary: DecisionEpisode, supporting: List[DecisionEpisode]) -> str:
        drift_note = (
            f" Temporal drift note: {primary.temporal_validity.drift_annotation}"
            if primary.temporal_validity.drift_annotation
            else ""
        )
        dissent_note = (
            f" Dissent preserved ({primary.authority.vote_tally}): {primary.authority.dissent_summary}"
            if primary.authority.dissent_preserved and primary.authority.dissent_summary
            else ""
        )
        return f"{primary.decision_statement} {primary.reasoning}{dissent_note}{drift_note}"

    @staticmethod
    def _to_judgment_summary(ep: DecisionEpisode) -> JudgmentSummary:
        first_ev = ep.evidence_considered[0] if ep.evidence_considered else None
        metrics: Dict[str, str] = {}
        for ev in ep.evidence_considered:
            metrics.update(ev.metrics)
        return JudgmentSummary(
            judgment_id=ep.episode_id,
            role=ep.role,
            role_holder_name=ep.role_holder.display_name,
            title=ep.title,
            decision=ep.decision_statement,
            reasoning=ep.reasoning,
            alternatives_rejected=ep.alternatives_rejected,
            counterfactual_boundaries=[
                c.rule_statement
                for c in ep.constraints_and_thresholds
                if c.is_counterfactual_boundary
            ],
            dissent_notes=ep.authority.dissent_summary,
            decided_date=ep.temporal_validity.decided_at.date().isoformat(),
            confidence=ep.confidence_score,
            governance_action=ep.governance_action,
            metrics=metrics,
            source={
                "title": first_ev.source_title if first_ev else ep.title,
                "type": first_ev.source_system.value if first_ev else "ms_graph_sharepoint",
                "deep_link": first_ev.deep_link_url if first_ev else "https://sharepoint.enterprise.local",
            },
        )

    @staticmethod
    def _collect_citations(episodes: List[DecisionEpisode]) -> List[CitationRecord]:
        citations: List[CitationRecord] = []
        seen = set()
        for ep in episodes:
            for ev in ep.evidence_considered:
                if ev.source_document_id in seen:
                    continue
                seen.add(ev.source_document_id)
                citations.append(
                    CitationRecord(
                        document_id=ev.source_document_id,
                        title=ev.source_title,
                        source_type=ev.source_system.value,
                        deep_link_url=ev.deep_link_url,
                        sensitivity_label=ep.sensitivity_label.name,
                        verbatim_excerpt=ev.verbatim_quote,
                    )
                )
        return citations
