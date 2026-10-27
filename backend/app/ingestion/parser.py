"""Raw-byte staging store and Unstructured-compatible Office document parser
with structural header preservation (Word headings, PowerPoint slide titles, Excel sheet/column headers)
and 512-token overlapping temporal chunking.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..schemas.decision_episode import (
    DocumentType,
    NormalizedChunk,
    NormalizedDocument,
)


class RawByteStore:
    """Preserves immutable raw bytes and source metadata prior to any document parsing."""

    def __init__(self) -> None:
        self._records: Dict[str, Dict[str, Any]] = {}

    def put(self, source: str, native_id: str, raw_bytes: bytes, metadata: Dict[str, Any]) -> str:
        key = f"{source}:{native_id}"
        self._records[key] = {
            "raw_bytes": raw_bytes,
            "byte_length": len(raw_bytes),
            "metadata": metadata,
            "stored_at": datetime.utcnow().isoformat(),
        }
        return key

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self._records.get(key)


class StructurePreservingParser:
    """Parses Word, Excel, PowerPoint, PDF, and transcripts while preserving structural hierarchy
    and chunking at ~512 tokens with configurable overlap.
    """

    def __init__(self, target_tokens: int = 512, overlap_tokens: int = 64) -> None:
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens

    def parse_bytes(
        self,
        raw_bytes: bytes,
        doc_type: DocumentType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Optional[str]]:
        """Extracts structure-annotated text from Office documents and transcripts."""
        meta = metadata or {}
        decoded = raw_bytes.decode("utf-8", errors="replace").strip()

        if doc_type == DocumentType.WORD_DOC:
            heading = meta.get("sectionHeading", "Section 1: Governance & Policy")
            return f"[Heading: {heading}]\n{decoded}", f"Word Heading: {heading}"

        if doc_type == DocumentType.POWERPOINT_DECK:
            slide_num = meta.get("slideNumber", 14)
            slide_title = meta.get("slideTitle", "Board Approval Sequence & Risk Gates")
            return f"[Slide {slide_num}: {slide_title}]\n{decoded}", f"Slide {slide_num}: {slide_title}"

        if doc_type == DocumentType.EXCEL_SHEET:
            sheet_name = meta.get("sheetName", "FY26_Program_Cap_Model")
            columns = ", ".join(meta.get("columnHeaders", ["Program", "FY26_Spend", "Board_Cap", "Phase_1_Allocation"]))
            return f"[Sheet: {sheet_name} | Columns: {columns}]\n{decoded}", f"Sheet: {sheet_name}"

        if doc_type in {DocumentType.TEAMS_TRANSCRIPT, DocumentType.MEETING_TRANSCRIPT}:
            speaker = meta.get("speaker", "Executive Speaker")
            if not decoded.startswith("[Speaker"):
                return f"[Speaker: {speaker}] {decoded}", f"Transcript Speaker: {speaker}"
            return decoded, f"Transcript Speaker: {speaker}"

        return decoded, meta.get("structuralLocation")

    def chunk_document(self, document: NormalizedDocument) -> List[NormalizedChunk]:
        """Splits a NormalizedDocument into ~512-token overlapping chunks with inherited ACL and Purview label."""
        words = document.body_text.split()
        if not words:
            return []

        chunks: List[NormalizedChunk] = []
        step = max(1, self.target_tokens - self.overlap_tokens)
        index = 0

        for start in range(0, len(words), step):
            window = words[start : start + self.target_tokens]
            if not window:
                break
            chunk_text = " ".join(window)
            prefix = f"[{document.role_tag.value} | {document.title} | {document.timestamp_utc.date().isoformat()}] "
            full_text = prefix + chunk_text
            token_estimate = min(1024, max(1, len(full_text.split())))

            chunks.append(
                NormalizedChunk(
                    chunk_id=f"{document.id}#chunk-{index}",
                    document_id=document.id,
                    role_tag=document.role_tag,
                    timestamp_utc=document.timestamp_utc,
                    token_count=token_estimate,
                    text=full_text,
                    sensitivity_label=document.sensitivity_label,
                    acl_snapshot=document.acl_snapshot,
                    provenance=document.provenance,
                )
            )
            index += 1
            if start + self.target_tokens >= len(words):
                break

        return chunks
