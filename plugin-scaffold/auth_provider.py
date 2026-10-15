"""PKCE MCP authorization backed by durable, revocable grants and verified login."""

from __future__ import annotations

import os
import secrets
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import AnyUrl
from mcp.server.auth.provider import (
    AccessToken, AuthorizationCode, AuthorizationParams, AuthorizeError,
    RefreshToken, RegistrationError, TokenError,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from oauth_connectors import public_base_url
from runtime import flag, local_test_mode
from security_store import GrantInvalidated, SecurityStore, security_store

MCP_SCOPE = "twin:read"
CODE_TTL_SECONDS = 300
ACCESS_TTL_SECONDS = 3600
REFRESH_TTL_SECONDS = 86400


class WisdomTwinAuthProvider:
    def __init__(self, repository: SecurityStore | None = None) -> None:
        self.repository = repository
        client_id = os.environ.get("OAUTH_CLIENT_ID", "").strip()
        redirects = os.environ.get("OAUTH_REDIRECT_URIS", "").strip()
        if local_test_mode():
            client_id = client_id or "wisdomtwin-local"
            redirects = redirects or "http://127.0.0.1:8000/oauth/done"
        self._clients: dict[str, OAuthClientInformationFull] = {}
        if client_id and redirects:
            urls = [AnyUrl(item.strip()) for item in redirects.split(",") if item.strip()]
            if not local_test_mode() and any(url.scheme != "https" for url in urls):
                raise RuntimeError("Production MCP callback URIs must be HTTPS")
            self._clients[client_id] = OAuthClientInformationFull(
                client_id=client_id, redirect_uris=urls,
                grant_types=["authorization_code", "refresh_token"],
                response_types=["code"], token_endpoint_auth_method="none", scope=MCP_SCOPE,
            )

    @property
    def db(self) -> SecurityStore:
        return self.repository or security_store()

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        return self._clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        raise RegistrationError(error="invalid_client_metadata", error_description="Client registration is not enabled")

    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        resource = f"{public_base_url()}/mcp"
        if params.resource != resource or set(params.scopes or [MCP_SCOPE]) != {MCP_SCOPE}:
            raise AuthorizeError(error="invalid_request", error_description="Invalid resource or scopes")
        if str(params.redirect_uri) not in {str(uri) for uri in client.redirect_uris}:
            raise AuthorizeError(error="invalid_request", error_description="Invalid callback")
        transaction = secrets.token_urlsafe(32)
        self.db.put("pending", transaction, {
            "client_id": client.client_id, "redirect_uri": str(params.redirect_uri),
            "redirect_uri_provided_explicitly": params.redirect_uri_provided_explicitly,
            "code_challenge": params.code_challenge, "scopes": params.scopes or [MCP_SCOPE],
            "state": params.state, "resource": resource,
        }, CODE_TTL_SECONDS)
        return f"{public_base_url()}/oauth/consent?txn={transaction}"

    def approve(self, transaction: str, *, session_key: str, csrf: str) -> str:
        session = self.db.get("session", session_key, consume=True)
        if not session or session["transaction"] != transaction or not secrets.compare_digest(session["csrf"], csrf):
            raise AuthorizeError(error="access_denied", error_description="Verified login and consent are required")
        member = self.db.membership(session["subject"])
        epoch = session.get("subject_epoch")
        if not member or member["email"] != session["email"] or type(epoch) is not int or epoch != self.db.subject_epoch(session["subject"]):
            raise AuthorizeError(error="access_denied", error_description="Corporate membership was revoked")
        pending = self.db.get("pending", transaction, consume=True)
        if not pending:
            raise AuthorizeError(error="invalid_request", error_description="Authorization request expired")
        code = secrets.token_urlsafe(32)
        authorization = AuthorizationCode(
            code=code, scopes=pending["scopes"], expires_at=time.time() + CODE_TTL_SECONDS,
            client_id=pending["client_id"], code_challenge=pending["code_challenge"],
            redirect_uri=AnyUrl(pending["redirect_uri"]),
            redirect_uri_provided_explicitly=pending["redirect_uri_provided_explicitly"],
            resource=pending["resource"], subject=session["subject"],
        )
        payload = {**authorization.model_dump(mode="json"), "subject_epoch": epoch}
        try:
            self.db.put_subject_entry("code", code, payload, CODE_TTL_SECONDS,
                                      subject=session["subject"], expected_epoch=epoch)
        except GrantInvalidated:
            raise AuthorizeError(error="access_denied", error_description="Corporate membership was revoked") from None
        url = urlsplit(pending["redirect_uri"])
        query = list(parse_qsl(url.query)) + [("code", code)]
        if pending["state"]:
            query.append(("state", pending["state"]))
        return urlunsplit((url.scheme, url.netloc, url.path, urlencode(query), ""))

    async def load_authorization_code(self, client: OAuthClientInformationFull, authorization_code: str) -> AuthorizationCode | None:
        payload = self.db.get("code", authorization_code)
        if not payload or payload["client_id"] != client.client_id or not self._current_subject(payload["subject"], payload.get("subject_epoch")):
            return None
        return AuthorizationCode.model_validate(payload)

    async def exchange_authorization_code(self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode) -> OAuthToken:
        if authorization_code.client_id != client.client_id:
            raise TokenError(error="invalid_grant", error_description="Invalid authorization code")
        payload = self.db.get("code", authorization_code.code, consume=True)
        if not payload or {key: value for key, value in payload.items() if key != "subject_epoch"} != authorization_code.model_dump(mode="json") or not self._current_subject(payload["subject"], payload.get("subject_epoch")):
            raise TokenError(error="invalid_grant", error_description="Authorization code expired or used")
        return self._issue(client.client_id, payload["subject"], payload["scopes"], payload["resource"],
                           secrets.token_urlsafe(32), payload["subject_epoch"])

    def _current_subject(self, subject: str, epoch: int | None) -> bool:
        return type(epoch) is int and epoch == self.db.subject_epoch(subject) and self.db.membership(subject) is not None

    def _issue(self, client_id: str, subject: str, scopes: list[str], resource: str, family: str, subject_epoch: int) -> OAuthToken:
        access, refresh = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        now = int(time.time())
        at = AccessToken(token=access, client_id=client_id, scopes=scopes,
                         expires_at=now + ACCESS_TTL_SECONDS, resource=resource, subject=subject)
        rt = RefreshToken(token=refresh, client_id=client_id, scopes=scopes,
                          expires_at=now + REFRESH_TTL_SECONDS, resource=resource, subject=subject)
        entries = []
        for kind, key, token, ttl in (("access", access, at, ACCESS_TTL_SECONDS), ("refresh", refresh, rt, REFRESH_TTL_SECONDS)):
            entries.append((kind, key, {"token": token.model_dump(mode="json"), "family": family,
                                       "subject_epoch": subject_epoch}, ttl))
            entries.append(("family", key, {"family": family, "kind": kind, "client_id": client_id}, REFRESH_TTL_SECONDS))
        try:
            self.db.issue_grants(subject, subject_epoch, family, entries)
        except GrantInvalidated:
            raise TokenError(error="invalid_grant", error_description="Corporate consent or token family was revoked") from None
        return OAuthToken(access_token=access, token_type="Bearer", expires_in=ACCESS_TTL_SECONDS,
                          scope=" ".join(scopes), refresh_token=refresh)

    async def load_refresh_token(self, client: OAuthClientInformationFull, refresh_token: str) -> RefreshToken | None:
        payload = self.db.get("refresh", refresh_token)
        if not payload:
            self._revoke_replayed_refresh(client.client_id, refresh_token)
            return None
        if payload["token"]["client_id"] != client.client_id or not self._current_subject(payload["token"]["subject"], payload.get("subject_epoch")):
            return None
        return RefreshToken.model_validate(payload["token"])

    def _revoke_replayed_refresh(self, client_id: str, token: str) -> None:
        # Unknown strings, access tokens and another client's tokens cannot revoke a family.
        relationship = self.db.get("family", token)
        if relationship and relationship.get("kind") == "refresh" and relationship.get("client_id") == client_id:
            self.db.revoke_family(relationship["family"])

    async def exchange_refresh_token(self, client: OAuthClientInformationFull, refresh_token: RefreshToken, scopes: list[str]) -> OAuthToken:
        if refresh_token.client_id != client.client_id or not set(scopes or refresh_token.scopes) <= set(refresh_token.scopes):
            raise TokenError(error="invalid_grant", error_description="Invalid client or scope")
        payload = self.db.get("refresh", refresh_token.token, consume=True)
        if not payload:
            self._revoke_replayed_refresh(client.client_id, refresh_token.token)
            raise TokenError(error="invalid_grant", error_description="Refresh token expired or used")
        if payload["token"] != refresh_token.model_dump(mode="json") or not self._current_subject(refresh_token.subject, payload.get("subject_epoch")):
            raise TokenError(error="invalid_grant", error_description="Refresh token expired or used")
        return self._issue(client.client_id, refresh_token.subject, scopes or refresh_token.scopes,
                           refresh_token.resource, payload["family"], payload["subject_epoch"])

    async def load_access_token(self, token: str) -> AccessToken | None:
        payload = self.db.get("access", token)
        if not payload or not self._current_subject(payload["token"]["subject"], payload.get("subject_epoch")):
            return None
        return AccessToken.model_validate(payload["token"])

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        payload = self.db.get("family", token.token)
        if payload:
            self.db.revoke_family(payload["family"])


def auth_is_required() -> bool:
    return not (flag("WISDOMTWIN_AUTH_DISABLED") and flag("WISDOMTWIN_USE_FIXTURES") and local_test_mode())
