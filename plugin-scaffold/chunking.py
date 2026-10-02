"""Chunk source text at about 500 tokens with 20 percent overlap."""

from __future__ import annotations

from domain import CHUNK_OVERLAP_RATIO, CHUNK_TOKENS


def _tokens(text: str) -> list[str]:
    return text.split()


def chunk_text(text: str, *, tokens: int = CHUNK_TOKENS, overlap_ratio: float = CHUNK_OVERLAP_RATIO) -> list[str]:
    words = _tokens(text.strip())
    if not words:
        return []
    if len(words) <= tokens:
        return [" ".join(words)]
    overlap = int(tokens * overlap_ratio)
    step = max(tokens - overlap, 1)
    pieces: list[str] = []
    start = 0
    while start < len(words):
        piece = words[start : start + tokens]
        if not piece:
            break
        pieces.append(" ".join(piece))
        if start + tokens >= len(words):
            break
        start += step
    return pieces
