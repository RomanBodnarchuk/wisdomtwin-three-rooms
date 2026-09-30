"""OAuth authorization server for the MCP endpoint, built on the SDK provider protocol.

Client registration stays disabled. A single public client is configured from
the environment and proves possession with PKCE, which the SDK token handler
checks before this provider exchanges the code.
"""

from __future__ import annotations

import os
import secrets
import time
from urllib.parse import urlencode

from pydantic import AnyUrl

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    AuthorizeError,
    RefreshToken,
    RegistrationError,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from oauth_connectors import public_base_url

MCP_SCOPE = "twin:read"
CODE_TTL_SECONDS = 300
ACCESS_TTL_SECONDS = 3600


class WisdomTwinAuthProvider:
    def __init__(self) -> None:
        self._clients: dict[str, OAuthClientInformationFull] = {}
        self._codes: dict[str, AuthorizationCode] = {}
        self._refresh: dict[str, RefreshToken] = {}
        self._access: dict[str, AccessToken] = {}
        self._pending: dict[str, dict] = {}
        self._install_default_client()

    def _install_default_client(self) -> None:
        client_id = os.environ.get("OAUTH_CLIENT_ID", "wisdomtwin-local").strip() or "wisdomtwin-local"
        redirects = [
            item.strip()
            for item in os.environ.get("OAUTH_REDIRECT_URIS", "http://127.0.0.1:8000/oauth/done").split(",")
            if item.strip()
        ]
        self._clients[client_id] = OAuthClientInformationFull(
            client_id=client_id,
            redirect_uris=[AnyUrl(item) for item in redirects],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            token_endpoint_auth_method="none",
            scope=MCP_SCOPE,
        )

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        return self._clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        raise RegistrationError(error="invalid_client_metadata", error_description="Client registration is not enabled")

    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        transaction = secrets.token_urlsafe(24)
        self._pending[transaction] = {
            "client_id": client.client_id,
            "redirect_uri": str(params.redirect_uri),
            "redirect_uri_provided_explicitly": params.redirect_uri_provided_explicitly,
            "code_challenge": params.code_challenge,
            "scopes": params.scopes or [MCP_SCOPE],
            "state": params.state,
            "resource": params.resource,
        }
        return f"{public_base_url()}/oauth/consent?txn={transaction}"

    def approve(self, transaction: str) -> str:
        pending = self._pending.pop(transaction, None)
        if pending is None:
            raise AuthorizeError(error="invalid_request", error_description="Authorization request expired")
        code = secrets.token_urlsafe(32)
        self._codes[code] = AuthorizationCode(
            code=code,
            scopes=list(pending["scopes"]),
            expires_at=time.time() + CODE_TTL_SECONDS,
            client_id=pending["client_id"],
            code_challenge=pending["code_challenge"],
            redirect_uri=AnyUrl(pending["redirect_uri"]),
            redirect_uri_provided_explicitly=pending["redirect_uri_provided_explicitly"],
            resource=pending["resource"],
            subject="wisdomtwin-user",
        )
        query = {"code": code}
        if pending["state"]:
            query["state"] = pending["state"]
        return f"{pending['redirect_uri']}?{urlencode(query)}"

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        return self._codes.get(authorization_code)

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        self._codes.pop(authorization_code.code, None)
        access = secrets.token_urlsafe(32)
        refresh = secrets.token_urlsafe(32)
        scopes = list(authorization_code.scopes)
        self._access[access] = AccessToken(
            token=access,
            client_id=client.client_id,
            scopes=scopes,
            expires_at=int(time.time()) + ACCESS_TTL_SECONDS,
            resource=authorization_code.resource or f"{public_base_url()}/mcp",
            subject=authorization_code.subject,
        )
        self._refresh[refresh] = RefreshToken(
            token=refresh,
            client_id=client.client_id,
            scopes=scopes,
            resource=authorization_code.resource,
            subject=authorization_code.subject,
        )
        return OAuthToken(
            access_token=access,
            token_type="Bearer",
            expires_in=ACCESS_TTL_SECONDS,
            scope=" ".join(scopes),
            refresh_token=refresh,
        )

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        token = self._refresh.get(refresh_token)
        if token and token.client_id == client.client_id:
            return token
        return None

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        self._refresh.pop(refresh_token.token, None)
        granted = scopes or list(refresh_token.scopes)
        access = secrets.token_urlsafe(32)
        rotated = secrets.token_urlsafe(32)
        self._access[access] = AccessToken(
            token=access,
            client_id=client.client_id,
            scopes=granted,
            expires_at=int(time.time()) + ACCESS_TTL_SECONDS,
            resource=refresh_token.resource or f"{public_base_url()}/mcp",
            subject=refresh_token.subject,
        )
        self._refresh[rotated] = RefreshToken(
            token=rotated,
            client_id=client.client_id,
            scopes=granted,
            resource=refresh_token.resource,
            subject=refresh_token.subject,
        )
        return OAuthToken(
            access_token=access,
            token_type="Bearer",
            expires_in=ACCESS_TTL_SECONDS,
            scope=" ".join(granted),
            refresh_token=rotated,
        )

    async def load_access_token(self, token: str) -> AccessToken | None:
        loaded = self._access.get(token)
        if loaded is None:
            return None
        if loaded.expires_at is not None and loaded.expires_at < int(time.time()):
            self._access.pop(token, None)
            return None
        return loaded

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        if isinstance(token, AccessToken):
            self._access.pop(token.token, None)
        else:
            self._refresh.pop(token.token, None)


def auth_is_required() -> bool:
    flag = os.environ.get("WISDOMTWIN_AUTH_DISABLED", "").strip().lower()
    if flag not in {"1", "true", "yes", "on"}:
        return True
    base = os.environ.get("PUBLIC_BASE_URL", "")
    if base.startswith("https://"):
        return True
    return False
