"""Grounded answers. The live model is the Responses API at temperature 0.3."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from store import ChunkRecord

EMPTY_CONTEXT = "I have nothing ingested on that."
NON_BUSINESS_REFUSAL = "I only answer questions about this role's business record."

_NON_BUSINESS = (
    "joke",
    "poem",
    "recipe",
    "horoscope",
    "dating",
    "lyrics",
    "homework",
    "weather",
    "sports score",
    "movie plot",
)
_BUSINESS = (
    "customer",
    "revenue",
    "pipeline",
    "contract",
    "board",
    "forecast",
    "quota",
    "deal",
    "account",
    "vendor",
    "hiring",
    "security",
    "pricing",
    "legal",
    "procurement",
    "sales",
    "renewal",
    "budget",
    "role",
    "slack",
)


def is_non_business(question: str) -> bool:
    lowered = question.lower()
    if any(phrase in lowered for phrase in _BUSINESS):
        return False
    return any(phrase in lowered for phrase in _NON_BUSINESS)


def _trim(text: str, max_tokens: int) -> str:
    words = text.split()
    if len(words) <= max_tokens:
        return text
    return " ".join(words[:max_tokens])


def _local_answer(question: str, chunks: list[ChunkRecord], max_tokens: int) -> str:
    excerpts = " ".join(chunk.excerpt for chunk in chunks[:3])
    answer = f"From the role record: {excerpts}"
    if question.strip():
        answer = f"From the role record, regarding {question.strip()}: {excerpts}"
    return _trim(answer, max_tokens)


def _responses_answer(question: str, chunks: list[ChunkRecord], max_tokens: int) -> str:
    context = "\n".join(f"[{index}] {chunk.excerpt}" for index, chunk in enumerate(chunks, start=1))
    payload = json.dumps(
        {
            "model": os.environ.get("OPENAI_GENERATION_MODEL", "gpt-6.1-sol"),
            "temperature": 0.3,
            "max_output_tokens": max_tokens,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "Answer only from the supplied business excerpts. "
                        "If they do not contain the answer, reply exactly: "
                        f"{EMPTY_CONTEXT} "
                        "Do not add outside knowledge."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nExcerpts:\n{context}",
                },
            ],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=payload,
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Generation request failed with status {exc.code}") from None
    output_text = body.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return _trim(output_text.strip(), max_tokens)
    chunks_out = body.get("output") or []
    collected: list[str] = []
    for item in chunks_out:
        for content in item.get("content") or []:
            text = content.get("text")
            if text:
                collected.append(text)
    if not collected:
        raise RuntimeError("Generation response did not include text")
    return _trim(" ".join(collected).strip(), max_tokens)


def answer_from_context(question: str, chunks: list[ChunkRecord], max_tokens: int) -> str:
    if not chunks:
        return EMPTY_CONTEXT
    if os.environ.get("OPENAI_API_KEY"):
        try:
            return _responses_answer(question, chunks, max_tokens)
        except RuntimeError:
            return _local_answer(question, chunks, max_tokens)
    return _local_answer(question, chunks, max_tokens)
