"""Read-only OAuth authorize URLs for Slack, Gmail, and Drive. PKCE via the MCP SDK."""

from __future__ import annotations

import os
from urllib.parse import urlencode

from mcp.client.auth.oauth2 import PKCEParameters

SLACK_USER_SCOPES = (
    "channels:history",
    "channels:read",
    "groups:history",
    "groups:read",
    "search:read",
    "users:read",
    "users:read.email",
    "files:read",
)

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly"


def public_base_url() -> str:
    for name in ("PUBLIC_BASE_URL", "RAILWAY_PUBLIC_URL"):
        raw = os.environ.get(name, "").strip().rstrip("/")
        if raw.startswith("https://") or raw.startswith("http://127.0.0.1") or raw.startswith("http://localhost"):
            return raw
    port = os.environ.get("PORT", "8000")
    return f"http://127.0.0.1:{port}"


def new_pkce() -> tuple[str, str]:
    params = PKCEParameters.generate()
    return params.code_verifier, params.code_challenge


def slack_authorize_url(*, state: str, code_challenge: str) -> str:
    query = urlencode(
        {
            "client_id": os.environ.get("SLACK_CLIENT_ID", ""),
            "user_scope": " ".join(SLACK_USER_SCOPES),
            "redirect_uri": f"{public_base_url()}/oauth/callback/slack",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"https://slack.com/oauth/v2/authorize?{query}"


def google_authorize_url(*, service: str, state: str, code_challenge: str) -> str:
    scope = GMAIL_SCOPE if service == "gmail" else DRIVE_SCOPE
    query = urlencode(
        {
            "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
            "redirect_uri": f"{public_base_url()}/oauth/callback/google",
            "response_type": "code",
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "online",
            "include_granted_scopes": "false",
        }
    )
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
