"""Hybrid retrieval. Role namespace filtering happens inside the store queries."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from store import ChunkRecord, Store


_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "what",
    "who",
    "how",
    "why",
    "when",
    "where",
    "which",
    "are",
    "was",
    "were",
    "does",
    "did",
    "about",
    "into",
    "over",
    "than",
    "then",
    "its",
    "been",
    "being",
}


def _terms(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in _STOPWORDS
    ]


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
    right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
    return dot / (left_norm * right_norm)


@dataclass
class RankedChunk:
    chunk: ChunkRecord
    score: float


def hybrid_search(
    store: Store,
    *,
    role_id: str,
    question: str,
    embedding: list[float],
    limit: int,
) -> list[RankedChunk]:
    vector_hits = store.vector_search(role_id, embedding, 10)
    keyword_hits = store.keyword_search(role_id, _terms(question), 10)
    scores: dict[str, float] = {}
    chunks: dict[str, ChunkRecord] = {}
    for rank, chunk in enumerate(vector_hits, start=1):
        chunks[chunk.id] = chunk
        scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (60 + rank)
    for rank, chunk in enumerate(keyword_hits, start=1):
        chunks[chunk.id] = chunk
        scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (60 + rank)

    question_terms = set(_terms(question))
    ranked: list[RankedChunk] = []
    for chunk_id, fused in scores.items():
        chunk = chunks[chunk_id]
        overlap = 0.0
        if question_terms:
            excerpt_terms = set(_terms(chunk.excerpt))
            overlap = len(question_terms & excerpt_terms) / len(question_terms)
        vector_score = _cosine(embedding, chunk.embedding)
        rerank = (0.5 * fused) + (0.3 * vector_score) + (0.2 * overlap)
        ranked.append(RankedChunk(chunk=chunk, score=rerank))
    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:limit]
