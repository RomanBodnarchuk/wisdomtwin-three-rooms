"""Embeddings via text-embedding-3-small, with a local stand-in when no key is set."""

from __future__ import annotations

import hashlib
import json
import math
import os
from runtime import flag, local_test_mode
import urllib.error
import urllib.request

from domain import EMBEDDING_DIMENSIONS


def _local_vector(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % EMBEDDING_DIMENSIONS
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _openai_vectors(texts: list[str]) -> list[list[float]]:
    payload = json.dumps(
        {
            "model": os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            "input": texts,
            "dimensions": EMBEDDING_DIMENSIONS,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/embeddings",
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
        raise RuntimeError(f"Embedding request failed with status {exc.code}") from None
    rows = sorted(body.get("data", []), key=lambda item: item.get("index", 0))
    vectors = [row["embedding"] for row in rows]
    if len(vectors) != len(texts):
        raise RuntimeError("Embedding response did not match the input batch")
    for vector in vectors:
        if len(vector) != EMBEDDING_DIMENSIONS:
            raise RuntimeError("Embedding dimensionality does not match the index")
    return vectors


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if flag("WISDOMTWIN_ALLOW_PAID_MODEL_APIS") and os.environ.get("OPENAI_API_KEY"):
        return _openai_vectors(texts)
    if local_test_mode():
        return [_local_vector(text) for text in texts]
    from errors import OAUTH_PENDING, CodedToolError
    raise CodedToolError(OAUTH_PENDING, "The embedding service is not configured or API spending is not authorized.")
