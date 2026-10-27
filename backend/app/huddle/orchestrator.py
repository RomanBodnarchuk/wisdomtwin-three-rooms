"""Multi-Twin Audio Executive Huddle Orchestrator.

Manages the Three Rooms flow (DREAM -> STRESS-TEST -> BUILD -> COMPLETE), routes CEO questions
to the appropriate role twin(s), queries each twin's TemporalContextGraph, enforces the
Safe-Decline governance gate, updates the Blocker Register, and generates the Thursday Board Package.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..graph.context_graph import TemporalContextGraph
from ..schemas.decision_episode import (
    HuddleParticipantPersona,
    HuddleStartRequest,
    HuddleStartResponse,
    HuddleTurnRequest,
    HuddleTurnResponse,
    QueryTwinRequest,
    RoleTag,
)
from .voice_interface import VoiceSessionHandle, get_voice_adapter


CANONICAL_BLOCKERS: List[Dict[str, str]] = [
    {
        "id": "blk_public_cloud",
        "title": "Public cloud PHI restriction",
        "category": "legal",
        "policy": "Patient data cannot touch a public cloud model",
        "precedent": "Governance memos + external model rejection rationale (prior year)",
        "owner": "Chief Legal Officer Twin",
        "decision": "Private deployment only",
        "status": "resolved",
    },
    {
        "id": "blk_budget_cap",
        "title": "New-program spending cap",
        "category": "financial",
        "policy": "Board-capped new programs at $11M this fiscal year",
        "precedent": "March motion, vote 7–2, dissent preserved",
        "owner": "CFO Twin",
        "decision": "Phase one at $7.4M under cap",
        "status": "resolved",
    },
    {
        "id": "blk_scale_precedent",
        "title": "Peak-load throughput precedent",
        "category": "technical",
        "policy": "Confidence must meet governance threshold",
        "precedent": "No reliable peak-load precedent at proposed volume",
        "owner": "VP, Clinical Operations (human)",
        "decision": "Escalate; measure 90 days before expand",
        "status": "escalated",
    },
    {
        "id": "blk_human_denial",
        "title": "Named-human denial sign-off",
        "category": "regulatory",
        "policy": "Four state-records regimes require human sign-off on denials",
        "precedent": "State compliance requirements",
        "owner": "Chief Legal Officer Twin",
        "decision": "Route 9% clinical cases to named clinicians",
        "status": "resolved",
    },
    {
        "id": "blk_securities",
        "title": "Material revenue disclosure timing",
        "category": "legal",
        "policy": "Material revenue program triggers securities disclosure rules",
        "precedent": "Disclosure governance practice",
        "owner": "Chief Legal Officer Twin",
        "decision": "Announce correctly or not at all",
        "status": "mitigated",
    },
]

CANONICAL_BOARD_ARTIFACTS: List[Dict[str, str]] = [
    {
        "id": "art_slide14",
        "title": "Slide 14 updated",
        "detail": "Board sequence reframed: risk, governance, human control, then revenue",
        "status": "ready",
    },
    {
        "id": "art_financial",
        "title": "Financial appendix regenerated",
        "detail": "Phase-one $7.4M plan under March spending cap",
        "status": "ready",
    },
    {
        "id": "art_legal",
        "title": "Legal citations attached",
        "detail": "Public-cloud prohibition + four-market human denial requirements",
        "status": "ready",
    },
    {
        "id": "art_dissent",
        "title": "Dissent preserved",
        "detail": "March 7–2 dissent notes retained in board package",
        "status": "ready",
    },
    {
        "id": "art_objections",
        "title": "Three anticipated objections",
        "detail": "Prepared responses for board Q&A",
        "status": "ready",
    },
    {
        "id": "art_notes",
        "title": "Speaking notes generated",
        "detail": "CEO talking points sequenced for Thursday session",
        "status": "ready",
    },
    {
        "id": "art_memo",
        "title": "Board memo ready",
        "detail": "Governed launch plan with precedent attached",
        "status": "ready",
    },
]


class AudioHuddleOrchestrator:
    """Coordinates multi-twin executive huddles across voice adapters and the TemporalContextGraph."""

    def __init__(self, graph: TemporalContextGraph) -> None:
        self.graph = graph
        self._sessions: Dict[str, VoiceSessionHandle] = {}
        self._session_providers: Dict[str, str] = {}

    def start_huddle(self, request: HuddleStartRequest) -> HuddleStartResponse:
        adapter = get_voice_adapter(request.voice_provider)
        personas = [
            HuddleParticipantPersona(
                role=role,
                display_name=f"{role.value} Twin",
                voice_id=f"{adapter.provider_name}-{role.value.lower()}",
                voice_provider=adapter.provider_name,
                speaking_style="Direct, evidence-grounded executive cadence",
            )
            for role in request.roles
        ]
        handle = adapter.start_session(twin_ids=request.roles, personas=personas)
        self._sessions[handle.session_id] = handle
        self._session_providers[handle.session_id] = adapter.provider_name

        return HuddleStartResponse(
            session_id=handle.session_id,
            topic=request.topic,
            join_url=f"https://wisdomtwin.ai/?mode=live&session={handle.session_id}",
            voice_provider=adapter.provider_name,
            active_roles=request.roles,
            room_mode="stress-test",
            initial_confidence=62,
            status="live",
        )

    def process_turn(self, request: HuddleTurnRequest) -> HuddleTurnResponse:
        provider_name = self._session_providers.get(request.session_id, "grok_voice_3")
        adapter = get_voice_adapter(provider_name)

        routed_roles = (
            [request.target_role]
            if request.target_role is not None
            else self._route_roles_for_prompt(request.prompt)
        )

        turns: List[Dict[str, Any]] = []
        any_safe_decline = False
        escalation_payload: Optional[Dict[str, Any]] = None
        last_audit_id = "aud_huddle_default"

        for role in routed_roles:
            query_res = self.graph.query_precedent(
                QueryTwinRequest(
                    question=request.prompt,
                    role=role,
                    top_k=2,
                )
            )
            last_audit_id = query_res.audit_log_id
            voice_packet = adapter.stream_audio(
                session_id=request.session_id,
                speaker_role=role,
                text_to_speak=query_res.answer,
            )
            if query_res.safe_decline_active:
                any_safe_decline = True
                escalation_payload = {
                    "id": "esc_vp_clinical",
                    "title": "Peak-load throughput review",
                    "reason": "Confidence below governance threshold; no sufficient precedent",
                    "reviewer": query_res.escalation_reviewer or "Vice President of Clinical Operations",
                    "estimatedMinutes": query_res.estimated_review_minutes or 38,
                    "status": "pending-human",
                    "auditRecorded": True,
                }

            turns.append(
                {
                    "role": role.value,
                    "speaker_label": voice_packet.speaker_label,
                    "text": query_res.answer,
                    "confidence": query_res.confidence,
                    "governance_action": query_res.governance_action.value,
                    "audio_asset_url": voice_packet.audio_asset_url,
                    "latency_ms": voice_packet.latency_ms,
                    "judgments": [j.model_dump() for j in query_res.judgments],
                    "citations": [c.model_dump() for c in query_res.citations],
                }
            )

        room_mode = request.room_mode or ("stress-test" if any_safe_decline else "build")
        consensus_confidence = 62 if any_safe_decline else 91

        return HuddleTurnResponse(
            session_id=request.session_id,
            room_mode=room_mode,
            routed_roles=routed_roles,
            turns=turns,
            safe_decline_active=any_safe_decline,
            escalation=escalation_payload,
            blockers=CANONICAL_BLOCKERS,
            consensus_confidence=consensus_confidence,
            board_artifacts=CANONICAL_BOARD_ARTIFACTS,
            audit_log_id=last_audit_id,
        )

    @staticmethod
    def _route_roles_for_prompt(prompt: str) -> List[RoleTag]:
        p = prompt.lower()
        routed: List[RoleTag] = []
        if any(k in p for k in ("budget", "cap", "$11m", "$7.4m", "spend", "cfo", "dissent", "fx")):
            routed.append(RoleTag.CFO)
        if any(k in p for k in ("cloud", "legal", "phi", "denial", "securities", "disclosure", "gate")):
            routed.append(RoleTag.LEGAL)
        if any(k in p for k in ("scale", "cto", "throughput", "peak", "12,400", "91%", "architecture")):
            routed.append(RoleTag.CTO)
        if any(k in p for k in ("account", "renewal", "cro", "revenue", "payer", "speed")):
            routed.append(RoleTag.CRO)
        if any(k in p for k in ("board", "sequence", "cybersecurity", "cmo", "slide 14", "pattern")):
            routed.append(RoleTag.CMO)

        if not routed:
            return [RoleTag.LEGAL, RoleTag.CFO, RoleTag.CTO]
        return routed
