"""Explicit loopback-only fixture mode and production configuration checks."""

from __future__ import annotations

import os
from urllib.parse import urlsplit


DEFAULT_MAX_SOURCE_FETCHES = 4
DEFAULT_OPENAI_MAX_OUTPUT_TOKENS = 16000
DEFAULT_OPENAI_REASONING_EFFORT = "low"
OPENAI_REASONING_EFFORTS = ("low", "medium", "high", "xhigh", "max")


def flag(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def openai_max_output_tokens() -> int:
    """Responses output budget. It covers reasoning plus visible text, so it is
    separate from query_twin's max_tokens, which caps only the visible answer."""
    raw = os.environ.get("OPENAI_MAX_OUTPUT_TOKENS", "").strip()
    if not raw:
        return DEFAULT_OPENAI_MAX_OUTPUT_TOKENS
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if value < 1:
        raise RuntimeError("OPENAI_MAX_OUTPUT_TOKENS must be a positive integer")
    return value


def openai_reasoning_effort() -> str:
    raw = os.environ.get("OPENAI_REASONING_EFFORT", "").strip().lower()
    if not raw:
        return DEFAULT_OPENAI_REASONING_EFFORT
    if raw not in OPENAI_REASONING_EFFORTS:
        raise RuntimeError("OPENAI_REASONING_EFFORT must be one of " + ", ".join(OPENAI_REASONING_EFFORTS))
    return raw


def max_source_fetches() -> int:
    """Distinct sources one query may re-fetch, bounding provider rate-limit use."""
    raw = os.environ.get("WISDOMTWIN_MAX_SOURCE_FETCHES", "").strip()
    if not raw:
        return DEFAULT_MAX_SOURCE_FETCHES
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if value < 1:
        raise RuntimeError("WISDOMTWIN_MAX_SOURCE_FETCHES must be a positive integer")
    return value


def local_test_mode() -> bool:
    if os.environ.get("WISDOMTWIN_ENV") not in {"local", "test"}:
        return False
    if os.environ.get("HOST", "127.0.0.1") not in {"127.0.0.1", "localhost", "::1"}:
        return False
    for name in ("PUBLIC_BASE_URL", "RAILWAY_PUBLIC_URL"):
        value = os.environ.get(name, "").strip()
        if value:
            url = urlsplit(value)
            if url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost", "::1"} or url.username:
                return False
    return True


def validate_runtime() -> None:
    if (flag("WISDOMTWIN_USE_FIXTURES") or flag("WISDOMTWIN_AUTH_DISABLED")) and not local_test_mode():
        raise RuntimeError("Fixture and auth-disabled modes require WISDOMTWIN_ENV=local/test and a loopback host/origin")
    max_source_fetches()
    openai_max_output_tokens()
    openai_reasoning_effort()
    # Lazy: auth_provider imports this module. A malformed allowlist then fails
    # deploy.sh --check and admin.py, not only the web service at startup.
    from auth_provider import metadata_document_client_ids

    metadata_document_client_ids()
    if not local_test_mode():
        from oauth_connectors import public_base_url

        if not public_base_url().startswith("https://"):
            raise RuntimeError("Production requires a configured HTTPS PUBLIC_BASE_URL")
        for name in ("DATABASE_URL", "REDIS_URL", "CONNECTOR_TOKEN_KEY", "OAUTH_CLIENT_ID", "OAUTH_REDIRECT_URIS"):
            if not os.environ.get(name, "").strip():
                raise RuntimeError(f"Production requires {name}")
