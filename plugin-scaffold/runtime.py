"""Explicit loopback-only fixture mode and production configuration checks."""

from __future__ import annotations

import os
from urllib.parse import urlsplit


def flag(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


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
    if not local_test_mode():
        from oauth_connectors import public_base_url

        if not public_base_url().startswith("https://"):
            raise RuntimeError("Production requires a configured HTTPS PUBLIC_BASE_URL")
        for name in ("DATABASE_URL", "REDIS_URL", "CONNECTOR_TOKEN_KEY", "OAUTH_CLIENT_ID", "OAUTH_REDIRECT_URIS"):
            if not os.environ.get(name, "").strip():
                raise RuntimeError(f"Production requires {name}")
