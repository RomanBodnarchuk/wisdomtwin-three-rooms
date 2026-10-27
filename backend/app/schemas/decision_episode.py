"""Canonical schemas for NormalizedDocument, DecisionEpisode, TemporalContextGraph, and Purview/Entra ACLs.

Every field is designed to model role-level institutional judgment over time while enforcing
Microsoft Entra ID access control lists and Microsoft Purview sensitivity labels at the chunk level.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class RoleTag(str, Enum):
    """Canonical enterprise executive roles modeled as Wisdom Twins."""

    CEO = "CEO"
    CFO = "CFO"
    CTO = "CTO"
    CRO = "CRO"
    CMO = "CMO"
    LEGAL = "LEGAL"
    CCO = "CCO"
    BOARD = "BOARD"


class SourceSystem(str, Enum):
    """Supported enterprise ingestion connectors."""

    MS_GRAPH_MAIL = "ms_graph_mail"
    MS_GRAPH_SHAREPOINT = "ms_graph_sharepoint"
    MS_GRAPH_ONEDRIVE = "ms_graph_onedrive"
    MS_GRAPH_TEAMS_CHAT = "ms_graph_teams_chat"
    MS_GRAPH_TEAMS_TRANSCRIPT = "ms_graph_teams_transcript"
    MS_GRAPH_CALENDAR = "ms_graph_calendar"
    SLACK = "slack"
    ZOOM = "zoom"
    GOOGLE_DRIVE = "google_drive"
    GOOGLE_MEET = "google_meet"
    GRANOLA = "granola"
    FIREFLY = "firefly"


class DocumentType(str, Enum):
    """Normalized document types across Microsoft 365 and third-party sources."""

    EMAIL = "email"
    WORD_DOC = "word_doc"
    EXCEL_SHEET = "excel_sheet"
    POWERPOINT_DECK = "powerpoint_deck"
    PDF_MEMO = "pdf_memo"
    TEAMS_MESSAGE = "teams_message"
    TEAMS_TRANSCRIPT = "teams_transcript"
    SLACK_THREAD = "slack_thread"
    MEETING_TRANSCRIPT = "meeting_transcript"
    MEETING_NOTES = "meeting_notes"
    BOARD_MINUTES = "board_minutes"


class SensitivityClassification(str, Enum):
    """Microsoft Purview sensitivity label classifications."""

    PUBLIC = "Public"
    GENERAL = "General"
    CONFIDENTIAL = "Confidential"
    HIGHLY_CONFIDENTIAL = "Highly Confidential"
    BOARD_RESTRICTED = "Board Restricted"


class PurviewRight(str, Enum):
    """Usage rights evaluated from Microsoft Purview Information Protection labels."""

    VIEW = "VIEW"
    EXTRACT = "EXTRACT"
    EDIT = "EDIT"
    EXPORT = "EXPORT"
    OWNER = "OWNER"


class DecisionType(str, Enum):
    """Categorization of institutional decision episodes."""

    POLICY_GATE = "policy_gate"
    BUDGET_CAP_OR_EXCEPTION = "budget_cap_or_exception"
    RISK_OR_COMPLIANCE_SIGNOFF = "risk_or_compliance_signoff"
    ARCHITECTURE_OR_VENDOR = "architecture_or_vendor"
    DISCLOSURE_DETERMINATION = "disclosure_determination"
    COMMERCIAL_PRICING_OR_TERMS = "commercial_pricing_or_terms"
    CLINICAL_OR_OPERATIONAL_ESCALATION = "clinical_or_operational_escalation"
    BOARD_SEQUENCE_STRATEGY = "board_sequence_strategy"


class GovernanceAction(str, Enum):
    """The three governed outcomes supported by WisdomTwin."""

    RECOMMEND = "recommend"
    ESCALATE = "escalate"
    SAFE_DECLINE = "safe_decline"


class EdgeType(str, Enum):
    """Typed temporal edges in the Cognee / Neo4j context graph."""

    DEPENDS_ON = "DEPENDS_ON"
    SUPERSEDES = "SUPERSEDES"
    PRECEDENT_FOR = "PRECEDENT_FOR"
    CONTRADICTS = "CONTRADICTS"
    EVIDENCE_FROM = "EVIDENCE_FROM"
    DECIDED_BY = "DECIDED_BY"
    GOVERNED_BY = "GOVERNED_BY"


class TimeRangeFilter(str, Enum):
    """Supported time range filters for Copilot and Huddle queries."""

    LAST_QUARTER = "last_quarter"
    LAST_YEAR = "last_year"
    FIVE_YEARS = "five_years"
    ALL_TIME = "all_time"


class SensitivityLabel(BaseModel):
    """Microsoft Purview sensitivity label attached to a document, chunk, or episode."""

    label_id: str = Field(..., description="GUID of the Microsoft Purview sensitivity label")
    name: SensitivityClassification = Field(
        default=SensitivityClassification.CONFIDENTIAL,
        description="Display classification of the Purview label",
    )
    is_encrypted: bool = Field(
        default=False,
        description="Whether Purview Rights Management encryption is applied",
    )
    required_rights: List[PurviewRight] = Field(
        default_factory=lambda: [PurviewRight.VIEW, PurviewRight.EXTRACT],
        description="Purview usage rights required for LLM extraction and retrieval synthesis",
    )
    markings_text: Optional[str] = Field(
        default=None,
        description="Watermark/header marking required on surfaced citations",
    )


class AclSnapshot(BaseModel):
    """Chunk-level snapshot of Microsoft Entra ID and SharePoint permissions."""

    tenant_id: str = Field(..., description="Microsoft Entra tenant GUID")
    allowed_user_ids: List[str] = Field(
        default_factory=list,
        description="Entra object IDs (OIDs) or UPNs granted direct read access",
    )
    allowed_group_ids: List[str] = Field(
        default_factory=list,
        description="Entra security/M365 group IDs granted read access",
    )
    allowed_roles: List[RoleTag] = Field(
        default_factory=list,
        description="Resolved executive roles authorized to query this chunk",
    )
    sharepoint_site_id: Optional[str] = Field(
        default=None,
        description="Source SharePoint site ID for inherited permission delta updates",
    )
    synced_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when ACL was last verified via Graph delta",
    )


class RoleHolderIdentity(BaseModel):
    """Resolved identity of a current or historical executive role holder."""

    entra_object_id: str = Field(..., description="Canonical Entra ID user object GUID or historical anchor ID")
    display_name: str = Field(..., description="Full name of the executive")
    primary_email: str = Field(..., description="Primary corporate email / UPN")
    known_aliases: List[str] = Field(
        default_factory=list,
        description="Historical email aliases, Slack handles, and transcript display names",
    )
    role: RoleTag = Field(..., description="Executive role held at the time of the decision")
    title: str = Field(..., description="Formal title during tenure")
    tenure_start: datetime = Field(..., description="Start date in the role")
    tenure_end: Optional[datetime] = Field(
        default=None,
        description="End date in the role (None if current role holder)",
    )


class ProvenanceMetadata(BaseModel):
    """Source lineage and delta-sync tracking metadata."""

    native_id: str = Field(..., description="Source-system native item or message ID")
    thread_or_conversation_id: Optional[str] = Field(
        default=None,
        description="Email conversationId, Slack thread_ts, or Teams thread ID",
    )
    meeting_id: Optional[str] = Field(
        default=None,
        description="Teams onlineMeeting ID, Zoom meeting UUID, or Granola note ID",
    )
    deep_link_url: str = Field(..., description="Direct URI back to the original M365 email, deck, or transcript")
    delta_token_ref: Optional[str] = Field(
        default=None,
        description="Graph deltaLink token checkpoint reference",
    )
    change_type: str = Field(default="created", description="created | updated | deleted")
    structural_location: Optional[str] = Field(
        default=None,
        description="Heading path (Word), slide number/title (PPTX), or sheet/column header (XLSX)",
    )


class NormalizedDocument(BaseModel):
    """Canonical normalized document emitted by all ingestion connectors."""

    id: str = Field(..., description="Globally unique ID formatted as '{source_system}:{native_id}'")
    title: str = Field(..., description="Document title, email subject, or meeting topic")
    author_identity: RoleHolderIdentity = Field(
        ...,
        description="Resolved Entra identity of the primary author or speaker",
    )
    role_tag: RoleTag = Field(..., description="Primary role lens associated with this document")
    participants: List[str] = Field(
        default_factory=list,
        description="All resolved display names or UPNs involved in the thread/meeting",
    )
    timestamp_utc: datetime = Field(..., description="Creation or meeting timestamp in UTC")
    source_system: SourceSystem = Field(..., description="Origin connector")
    document_type: DocumentType = Field(..., description="Normalized document classification")
    body_text: str = Field(
        ...,
        description="Structure-preserved clean text (speaker turns, headings, slide titles, or sheet headers)",
    )
    sensitivity_label: SensitivityLabel = Field(
        ...,
        description="First-class Microsoft Purview sensitivity classification",
    )
    acl_snapshot: AclSnapshot = Field(
        ...,
        description="Source access control list replicated for chunk-level filtering",
    )
    provenance: ProvenanceMetadata = Field(
        ...,
        description="Lineage, thread context, and deep link metadata",
    )

    @field_validator("id")
    @classmethod
    def validate_global_id(cls, value: str) -> str:
        if ":" not in value:
            raise ValueError("NormalizedDocument.id must be formatted as '{source}:{native_id}'")
        return value


class NormalizedChunk(BaseModel):
    """512-token overlapping temporal chunk with inherited ACL and Purview label."""

    chunk_id: str = Field(..., description="Unique chunk ID '{document_id}#chunk-{index}'")
    document_id: str = Field(..., description="Parent NormalizedDocument.id")
    role_tag: RoleTag = Field(..., description="Inherited role tag")
    timestamp_utc: datetime = Field(..., description="Inherited temporal anchor for recency weighting")
    token_count: int = Field(..., ge=1, le=1024, description="Token count (~512 target)")
    text: str = Field(..., description="Chunk text with structural header prefix")
    embedding: Optional[List[float]] = Field(
        default=None,
        description="Vector embedding for hybrid similarity search",
    )
    sensitivity_label: SensitivityLabel = Field(..., description="Inherited Purview sensitivity label")
    acl_snapshot: AclSnapshot = Field(..., description="Inherited Entra/SharePoint ACL snapshot")
    provenance: ProvenanceMetadata = Field(..., description="Inherited provenance and deep link")


class EvidenceQuote(BaseModel):
    """Verbatim evidence quote and quantitative metric extracted from source chunks."""

    source_document_id: str = Field(..., description="Origin NormalizedDocument.id")
    source_title: str = Field(..., description="Human-readable title (e.g., 'March Board Motion')")
    source_system: SourceSystem = Field(..., description="Origin system")
    deep_link_url: str = Field(..., description="Clickable deep link to source")
    verbatim_quote: str = Field(..., description="Exact verbatim excerpt from the source document")
    metrics: Dict[str, str] = Field(
        default_factory=dict,
        description="Key metrics cited in the evidence (e.g., {'Cap': '$11M', 'Vote': '7-2'})",
    )


class ConstraintOrThreshold(BaseModel):
    """Explicit numerical threshold, policy gate, or counterfactual 'never-do' boundary."""

    constraint_id: str = Field(..., description="Unique identifier for the constraint")
    category: str = Field(..., description="financial | legal | technical | regulatory | clinical")
    rule_statement: str = Field(..., description="Clear statement of the threshold or rule")
    threshold_value: Optional[str] = Field(
        default=None,
        description="Quantified limit (e.g., '$11M', '91%', '4 markets')",
    )
    is_counterfactual_boundary: bool = Field(
        default=False,
        description="True if this is an explicit refusal / 'never-do' boundary",
    )


class AuthorityRecord(BaseModel):
    """Captures who held authority to release the decision, vote tallies, and preserved dissent."""

    deciding_authority: str = Field(
        ...,
        description="Role holder, committee, or Board of Directors that made the call",
    )
    vote_tally: Optional[str] = Field(
        default=None,
        description="Recorded vote if committee/board decision (e.g., '7-2')",
    )
    dissent_preserved: bool = Field(
        default=False,
        description="Whether minority dissent notes were recorded and preserved",
    )
    dissent_summary: Optional[str] = Field(
        default=None,
        description="Summary of the dissenting position and conditions",
    )
    named_human_reviewer: Optional[str] = Field(
        default=None,
        description="Named human role required for exception sign-off or escalation",
    )
    estimated_review_minutes: Optional[int] = Field(
        default=None,
        description="Estimated human review duration in minutes when escalated",
    )


class TemporalValidity(BaseModel):
    """Temporal window and threshold drift annotation across role holders."""

    decided_at: datetime = Field(..., description="When the decision episode occurred")
    valid_from: datetime = Field(..., description="Start of policy/precedent applicability")
    valid_until: Optional[datetime] = Field(
        default=None,
        description="When superseded (None if still active precedent)",
    )
    era_label: str = Field(default="FY2026", description="Fiscal era or macro regime label")
    drift_annotation: Optional[str] = Field(
        default=None,
        description="Explanation of how judgment thresholds shifted relative to prior episodes/role holders",
    )


class EntityReference(BaseModel):
    """Canonical entity linked to a DecisionEpisode."""

    entity_id: str
    name: str
    entity_type: str = Field(..., description="person | committee | system | regulation | account | program")


class DecisionEpisode(BaseModel):
    """Canonical Decision-Episode node in the WisdomTwin Temporal Context Graph."""

    episode_id: str = Field(..., description="Unique decision episode identifier (e.g., 'ep_cfo_cap_2026')")
    role: RoleTag = Field(..., description="Executive role twin owning this judgment episode")
    role_holder: RoleHolderIdentity = Field(
        ...,
        description="Identity of the executive who made or articulated the decision",
    )
    decision_type: DecisionType = Field(..., description="Classification of the decision episode")
    title: str = Field(..., description="Concise headline of the decision episode")
    question_asked: str = Field(
        ...,
        description="The underlying decision question, proposal, or exception request",
    )
    decision_statement: str = Field(
        ...,
        description="Single-sentence statement of the decision, stance, or refusal",
    )
    reasoning: str = Field(
        ...,
        description="Detailed rationale explaining why the leader chose what they chose",
    )
    evidence_considered: List[EvidenceQuote] = Field(
        default_factory=list,
        description="Verbatim evidence chains and quantitative metrics supporting the decision",
    )
    constraints_and_thresholds: List[ConstraintOrThreshold] = Field(
        default_factory=list,
        description="Policy gates, budget caps, and counterfactual 'never-do' boundaries",
    )
    alternatives_rejected: List[str] = Field(
        default_factory=list,
        description="Alternative options considered and explicitly rejected with rationale",
    )
    authority: AuthorityRecord = Field(
        ...,
        description="Authority that decided, vote count, preserved dissent, and human escalation path",
    )
    outcome: str = Field(..., description="Observed or governed outcome of the decision")
    temporal_validity: TemporalValidity = Field(
        ...,
        description="Temporal validity window and threshold drift notes",
    )
    entities_involved: List[EntityReference] = Field(
        default_factory=list,
        description="Resolved people, committees, systems, or accounts involved",
    )
    sensitivity_label: SensitivityLabel = Field(
        ...,
        description="Highest water-mark Purview sensitivity label across source chunks",
    )
    acl_snapshot: AclSnapshot = Field(
        ...,
        description="Intersection ACL snapshot governing who can retrieve this episode",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Calibrated confidence score (0.0 to 1.0)",
    )
    field_confidence: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-field extraction confidence scores",
    )
    governance_action: GovernanceAction = Field(
        default=GovernanceAction.RECOMMEND,
        description="recommend | escalate | safe_decline",
    )
    verified_by_human: bool = Field(
        default=False,
        description="True once validated by the current role holder in the validation loop",
    )


class TemporalGraphEdge(BaseModel):
    """Typed temporal edge connecting two nodes in the Cognee / Neo4j context graph."""

    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: EdgeType
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    rationale: str = Field(..., description="Why these two episodes/entities are linked")
    valid_from: datetime
    valid_until: Optional[datetime] = None


# ── API Request / Response Contracts (OpenAPI 3.1 / Copilot Plugin aligned) ──


class QueryTwinRequest(BaseModel):
    """Request payload for POST /twin/query (operationId: queryTwin)."""

    question: str = Field(..., min_length=3, description="The natural language question about past decisions or precedent")
    role: RoleTag = Field(..., description="Target role twin (CFO, CTO, CRO, CMO, LEGAL, CCO, CEO)")
    time_range: TimeRangeFilter = Field(
        default=TimeRangeFilter.ALL_TIME,
        description="Optional temporal filter (last_quarter, last_year, five_years, all_time)",
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum number of precedent judgments to return")
    requester_upn: str = Field(
        default="daniel.mercer@enterprise.local",
        description="Signed-in Entra ID UPN (populated from OBO bearer token in production)",
    )
    requester_groups: List[str] = Field(
        default_factory=lambda: ["grp-exec-officers", "grp-board-packet-readers"],
        description="Entra ID group memberships for ACL filtering",
    )


class CitationRecord(BaseModel):
    """Inline citation with source deep link and Microsoft Purview sensitivity label."""

    document_id: str
    title: str
    source_type: str
    deep_link_url: str
    sensitivity_label: SensitivityClassification
    verbatim_excerpt: str


class JudgmentSummary(BaseModel):
    """Structured judgment item returned to Microsoft 365 Copilot and the Huddle UI."""

    judgment_id: str
    role: RoleTag
    role_holder_name: str
    title: str
    decision: str
    reasoning: str
    alternatives_rejected: List[str]
    counterfactual_boundaries: List[str]
    dissent_notes: Optional[str] = None
    decided_date: str
    confidence: float
    governance_action: GovernanceAction
    metrics: Dict[str, str] = Field(default_factory=dict)
    source: Dict[str, str]


class QueryTwinResponse(BaseModel):
    """Response payload for POST /twin/query."""

    answer: str
    role: RoleTag
    governance_action: GovernanceAction
    confidence: float = Field(..., ge=0.0, le=1.0)
    safe_decline_active: bool = False
    escalation_reviewer: Optional[str] = None
    estimated_review_minutes: Optional[int] = None
    judgments: List[JudgmentSummary]
    citations: List[CitationRecord]
    audit_log_id: str


class RoleSummary(BaseModel):
    """Summary of an available role twin returned by GET /twin/roles."""

    role: RoleTag
    label: str
    title: str
    role_holders_count: int
    episode_count: int
    document_count: int
    date_range_covered: str
    never_do_rules: List[str]


class HuddleParticipantPersona(BaseModel):
    """Voice and persona configuration for a twin in an Audio Executive Huddle."""

    role: RoleTag
    display_name: str
    voice_id: str
    voice_provider: str = Field(default="grok_voice_3", description="grok_voice_3 | openai_realtime | azure_speech | dessa")
    speaking_style: str


class HuddleStartRequest(BaseModel):
    """Request payload for POST /twin/huddle (operationId: startHuddle)."""

    roles: List[RoleTag] = Field(
        default_factory=lambda: [RoleTag.CFO, RoleTag.CTO, RoleTag.CRO, RoleTag.CMO, RoleTag.LEGAL],
        description="Executive role twins to convene in the audio huddle",
    )
    topic: str = Field(
        default="Prior-Authorization AI Strategy & Thursday Board Packet",
        description="Decision topic for the Executive Huddle",
    )
    voice_provider: str = Field(
        default="grok_voice_3",
        description="Voice abstraction adapter: grok_voice_3 | openai_realtime | azure_speech",
    )
    requester_upn: str = Field(default="daniel.mercer@enterprise.local")


class HuddleStartResponse(BaseModel):
    """Response payload for POST /twin/huddle."""

    session_id: str
    topic: str
    join_url: str
    voice_provider: str
    active_roles: List[RoleTag]
    room_mode: str
    initial_confidence: int
    status: str


class HuddleTurnRequest(BaseModel):
    """Interactive turn inside a live Audio Executive Huddle session."""

    session_id: str
    prompt: str = Field(..., min_length=2, description="CEO spoken or typed prompt to the huddle")
    target_role: Optional[RoleTag] = Field(
        default=None,
        description="Optional explicit role twin target; if omitted, orchestrator routes automatically",
    )
    room_mode: Optional[str] = Field(default=None, description="dream | stress-test | build")


class HuddleTurnResponse(BaseModel):
    """Multi-twin turn response with audio metadata, evidence cards, blockers, and confidence."""

    session_id: str
    room_mode: str
    routed_roles: List[RoleTag]
    turns: List[Dict[str, Any]]
    safe_decline_active: bool
    escalation: Optional[Dict[str, Any]] = None
    blockers: List[Dict[str, Any]]
    consensus_confidence: int
    board_artifacts: List[Dict[str, Any]]
    audit_log_id: str
