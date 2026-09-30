"""Encrypt connector tokens at rest. The key arrives only as an environment variable."""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet


def _fernet() -> Fernet:
    raw = os.environ.get("CONNECTOR_TOKEN_KEY", "").strip()
    if not raw:
        raise RuntimeError("CONNECTOR_TOKEN_KEY is required before a connector token can be stored")
    try:
        return Fernet(raw.encode("utf-8"))
    except Exception:
        derived = base64.urlsafe_b64encode(hashlib.sha256(raw.encode("utf-8")).digest())
        return Fernet(derived)


def encrypt_token(token: str) -> str:
    return _fernet().encrypt(token.encode("utf-8")).decode("utf-8")


def decrypt_token(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
