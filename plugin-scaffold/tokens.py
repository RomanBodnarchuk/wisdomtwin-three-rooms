"""Encrypt connector tokens at rest and key stored keyword hashes. The key arrives only as an environment variable."""

from __future__ import annotations

import base64
from functools import lru_cache
import hashlib
import hmac
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

_KEYWORD_HASH_INFO = b"wisdomtwin/keyword-hash/v1"
# Public and fixed: used only in explicit local/test mode when CONNECTOR_TOKEN_KEY is unset.
_LOCAL_KEYWORD_HASH_KEY = b"wisdomtwin local-only keyword hash key, never for real data"


def _fernet() -> Fernet:
    raw = os.environ.get("CONNECTOR_TOKEN_KEY", "").strip()
    if not raw:
        raise RuntimeError("CONNECTOR_TOKEN_KEY is required before a connector token can be stored")
    # Reject passwords or malformed keys instead of silently deriving a weak key.
    return Fernet(raw.encode("utf-8"))


def encrypt_token(token: str) -> str:
    return _fernet().encrypt(token.encode("utf-8")).decode("utf-8")


def decrypt_token(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")


@lru_cache(maxsize=4)
def _derived_keyword_key(raw: str) -> bytes:
    Fernet(raw.encode("utf-8"))  # Same validation as token encryption: no weak or malformed keys.
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                info=_KEYWORD_HASH_INFO).derive(base64.urlsafe_b64decode(raw.encode("utf-8")))


def keyword_hash_key() -> bytes:
    """The HMAC key for stored keyword hashes, derived with HKDF-SHA256 from CONNECTOR_TOKEN_KEY."""
    raw = os.environ.get("CONNECTOR_TOKEN_KEY", "").strip()
    if raw:
        return _derived_keyword_key(raw)
    from runtime import local_test_mode

    if local_test_mode():
        return _LOCAL_KEYWORD_HASH_KEY
    raise RuntimeError("CONNECTOR_TOKEN_KEY is required before keywords can be indexed or searched")


def keyword_hash(term: str) -> str:
    """HMAC-SHA256 of one keyword term. Indexing and retrieval both use this function.

    Without the server-held key, a database reader cannot recover a chunk's
    vocabulary with a dictionary pass. Rotating CONNECTOR_TOKEN_KEY changes every
    hash, so keyword matching on existing rows stops until the role is re-indexed.
    """
    return hmac.new(keyword_hash_key(), term.encode("utf-8"), hashlib.sha256).hexdigest()
