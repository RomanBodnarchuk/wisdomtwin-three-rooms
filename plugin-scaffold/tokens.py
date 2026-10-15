"""Encrypt connector tokens at rest. The key arrives only as an environment variable."""

from __future__ import annotations

import os

from cryptography.fernet import Fernet


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
