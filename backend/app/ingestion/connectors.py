"""Secondary enterprise connectors (Slack Events/Threads, Zoom Cloud Transcripts, Granola/Firefly Notes)
mapping into the canonical NormalizedDocument schema.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List

from ..schemas.decision_episode import (
    AclSnapshot,
    DocumentType,
    NormalizedDocument,
    ProvenanceMetadata,
    RoleHolderIdentity,
    RoleTag,
    SensitivityClassification,
    SensitivityLabel,
    SourceSystem,
)


class BaseIngestionConnector(ABC):
    """Abstract base interface for all non-Graph enterprise connectors."""

    source_system: SourceSystem

    @abstractmethod
    def normalize_payload(self, payload: Dict[str, Any], tenant_id: str) -> NormalizedDocument:
        """Maps a source-specific event or transcript into a canonical NormalizedDocument."""


class SlackEventsConnector(BaseIngestionConnector):
    """Ingests Slack threads as cohesive conversation units rather than isolated messages."""

    source_system = SourceSystem.SLACK

    def normalize_payload(self, payload: Dict[str, Any], tenant_id: str) -> NormalizedDocument:
        thread_ts = str(payload.get("thread_ts") or payload.get("ts", "1710000000.000100"))
        channel_id = str(payload.get("channel", "C01EXECFIN"))
        messages: List[Dict[str, Any]] = payload.get("messages", [payload])

        formatted_turns: List[str] = []
        participants: List[str] = []
        for msg in messages:
            user = str(msg.get("user_email") or msg.get("user", "exec@enterprise.local"))
            if user not in participants:
                participants.append(user)
            text = str(msg.get("text", "")).strip()
            formatted_turns.append(f"[{user}]: {text}")

        role_tag = RoleTag(payload.get("role_tag", "CFO"))
        author_email = participants[0] if participants else "cfo@enterprise.local"

        return NormalizedDocument(
            id=f"{self.source_system.value}:{channel_id}_{thread_ts}",
            title=str(payload.get("title", f"Slack Thread in #{channel_id}")),
            author_identity=RoleHolderIdentity(
                entra_object_id=str(payload.get("entra_object_id", "entra-cfo-001")),
                display_name=str(payload.get("author_name", "Executive Speaker")),
                primary_email=author_email,
                known_aliases=[str(payload.get("slack_user_id", "U01CFO"))],
                role=role_tag,
                title=f"Chief {role_tag.value} Officer",
                tenure_start=datetime(2020, 1, 1),
            ),
            role_tag=role_tag,
            participants=participants,
            timestamp_utc=datetime.utcnow(),
            source_system=self.source_system,
            document_type=DocumentType.SLACK_THREAD,
            body_text="\n".join(formatted_turns),
            sensitivity_label=SensitivityLabel(
                label_id="purview-slack-confidential",
                name=SensitivityClassification.CONFIDENTIAL,
            ),
            acl_snapshot=AclSnapshot(
                tenant_id=tenant_id,
                allowed_user_ids=participants,
                allowed_group_ids=payload.get("allowed_groups", ["grp-exec-officers"]),
                allowed_roles=[role_tag, RoleTag.CEO],
            ),
            provenance=ProvenanceMetadata(
                native_id=f"{channel_id}_{thread_ts}",
                thread_or_conversation_id=thread_ts,
                deep_link_url=f"https://app.slack.com/client/{tenant_id}/{channel_id}/thread/{thread_ts}",
            ),
        )


class ZoomTranscriptConnector(BaseIngestionConnector):
    """Ingests Zoom cloud recording transcripts with speaker diarization preserved."""

    source_system = SourceSystem.ZOOM

    def normalize_payload(self, payload: Dict[str, Any], tenant_id: str) -> NormalizedDocument:
        meeting_uuid = str(payload.get("uuid", "zoom-mtg-001"))
        topic = str(payload.get("topic", "Executive Decision Review"))
        role_tag = RoleTag(payload.get("role_tag", "CRO"))

        utterances = payload.get("transcript_utterances", [])
        if utterances:
            body_text = "\n".join(
                f"[{u.get('speaker', 'Speaker')}]: {u.get('text', '')}" for u in utterances
            )
        else:
            body_text = str(payload.get("transcript_text", ""))

        return NormalizedDocument(
            id=f"{self.source_system.value}:{meeting_uuid}",
            title=topic,
            author_identity=RoleHolderIdentity(
                entra_object_id=str(payload.get("host_entra_id", "entra-cro-001")),
                display_name=str(payload.get("host_name", "Chief Revenue Officer")),
                primary_email=str(payload.get("host_email", "cro@enterprise.local")),
                role=role_tag,
                title=f"Chief {role_tag.value} Officer",
                tenure_start=datetime(2021, 6, 1),
            ),
            role_tag=role_tag,
            participants=payload.get("participants", ["cro@enterprise.local", "daniel.mercer@enterprise.local"]),
            timestamp_utc=datetime.utcnow(),
            source_system=self.source_system,
            document_type=DocumentType.MEETING_TRANSCRIPT,
            body_text=body_text,
            sensitivity_label=SensitivityLabel(
                label_id="purview-meeting-confidential",
                name=SensitivityClassification.CONFIDENTIAL,
            ),
            acl_snapshot=AclSnapshot(
                tenant_id=tenant_id,
                allowed_user_ids=payload.get("participants", ["daniel.mercer@enterprise.local"]),
                allowed_group_ids=["grp-exec-officers"],
                allowed_roles=[role_tag, RoleTag.CEO],
            ),
            provenance=ProvenanceMetadata(
                native_id=meeting_uuid,
                meeting_id=meeting_uuid,
                deep_link_url=str(payload.get("recording_url", f"https://zoom.us/rec/play/{meeting_uuid}")),
            ),
        )


class GranolaNotesConnector(BaseIngestionConnector):
    """Ingests structured executive meeting notes from Granola / Firefly."""

    source_system = SourceSystem.GRANOLA

    def normalize_payload(self, payload: Dict[str, Any], tenant_id: str) -> NormalizedDocument:
        note_id = str(payload.get("id", "granola-note-001"))
        role_tag = RoleTag(payload.get("role_tag", "LEGAL"))

        return NormalizedDocument(
            id=f"{self.source_system.value}:{note_id}",
            title=str(payload.get("title", "Governance & Policy Gate Note")),
            author_identity=RoleHolderIdentity(
                entra_object_id=str(payload.get("author_entra_id", "entra-legal-001")),
                display_name=str(payload.get("author_name", "Chief Legal Officer")),
                primary_email=str(payload.get("author_email", "legal@enterprise.local")),
                role=role_tag,
                title="Chief Legal Officer",
                tenure_start=datetime(2019, 3, 1),
            ),
            role_tag=role_tag,
            participants=payload.get("attendees", ["legal@enterprise.local", "daniel.mercer@enterprise.local"]),
            timestamp_utc=datetime.utcnow(),
            source_system=self.source_system,
            document_type=DocumentType.MEETING_NOTES,
            body_text=str(payload.get("markdown_body", "")),
            sensitivity_label=SensitivityLabel(
                label_id="purview-legal-confidential",
                name=SensitivityClassification.HIGHLY_CONFIDENTIAL,
                is_encrypted=True,
            ),
            acl_snapshot=AclSnapshot(
                tenant_id=tenant_id,
                allowed_user_ids=payload.get("attendees", ["daniel.mercer@enterprise.local"]),
                allowed_group_ids=["grp-exec-officers", "grp-legal-counsel"],
                allowed_roles=[role_tag, RoleTag.CEO],
            ),
            provenance=ProvenanceMetadata(
                native_id=note_id,
                meeting_id=payload.get("calendar_event_id"),
                deep_link_url=str(payload.get("note_url", f"https://notes.granola.ai/d/{note_id}")),
            ),
        )
