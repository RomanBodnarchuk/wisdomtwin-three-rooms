"""PKCE MCP authorization backed by durable, revocable grants and verified login."""

from __future__ import annotations

import http.client
import ipaddress
import json
import logging
import os
import secrets
import socket
import ssl
import threading
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import anyio
import anyio.to_thread
from pydantic import AnyUrl
from mcp.server.auth.provider import (
    AccessToken, AuthorizationCode, AuthorizationParams, AuthorizeError,
    RefreshToken, RegistrationError, TokenError,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from oauth_connectors import public_base_url
from runtime import flag, local_test_mode
from security_store import GrantInvalidated, SecurityStore, security_store

logger = logging.getLogger("wisdomtwin")

MCP_SCOPE = "twin:read"
CODE_TTL_SECONDS = 300
ACCESS_TTL_SECONDS = 3600
REFRESH_TTL_SECONDS = 86400
CIMD_TIMEOUT_SECONDS = 5  # one wall-clock budget for a whole document fetch
CIMD_MAX_BYTES = 64 * 1024
CIMD_CACHE_SECONDS = 3600
CIMD_RETRY_SECONDS = 60  # no new fetch for a document URL this long after a failed one
CIMD_STALE_SECONDS = REFRESH_TTL_SECONDS  # last good client serves this long past expiry while refreshes fail
_clock = time.monotonic  # CIMD fetch budget, cache, backoff and stale expiry; tests replace it without touching the event loop


def authorization_issuer() -> str:
    """RFC 9207 iss: the issuer exactly as authorization-server metadata serves it.

    The bare public origin, with no trailing slash. RFC 8414 issuer comparison is
    exact, and package_validator.validate_release requires the issuer and the
    protected resource's authorization_servers to equal this origin. server.py
    passes it to AuthSettings as a string so the SDK preserves the empty path.
    """
    return public_base_url()


def metadata_document_client_ids() -> frozenset[str]:
    """Exact HTTPS client ID metadata document URLs an operator allows. Empty disables CIMD."""
    allowed = set()
    for item in os.environ.get("OAUTH_CIMD_CLIENT_IDS", "").split(","):
        url = item.strip()
        if not url:
            continue
        parts = urlsplit(url)
        try:
            parts.port
        except ValueError:
            raise RuntimeError("OAUTH_CIMD_CLIENT_IDS contains an invalid port") from None
        segments = parts.path.split("/")
        if (parts.scheme != "https" or not parts.hostname or "@" in parts.netloc or "#" in url
                or parts.path in {"", "/"} or "." in segments or ".." in segments):
            raise RuntimeError("OAUTH_CIMD_CLIENT_IDS must list exact HTTPS client metadata document URLs")
        allowed.add(url)
    return frozenset(allowed)


def _public_addresses(host: str, port: int) -> list[str]:
    """Every resolved address must be public; the connection is pinned to these addresses."""
    addresses = list(dict.fromkeys(info[4][0] for info in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)))
    if not addresses:
        raise ValueError("Client metadata host did not resolve")
    for address in addresses:
        ip = ipaddress.ip_address(address.split("%", 1)[0])
        if (not ip.is_global or ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_multicast or ip.is_reserved or ip.is_unspecified):
            raise ValueError("Client metadata host resolves to a non-public address")
    return addresses


def _resolve_within(host: str, port: int, budget: float) -> list[str]:
    """_public_addresses, given up on after budget seconds.

    getaddrinfo cannot be interrupted, so it runs in a daemon thread that a stalled
    resolver may keep; the fetch itself stops waiting at its deadline.
    """
    outcome: dict = {}

    def resolve() -> None:
        try:
            outcome["addresses"] = _public_addresses(host, port)
        except BaseException as exc:  # re-raised in the fetching thread
            outcome["error"] = exc

    resolver = threading.Thread(target=resolve, name="wisdomtwin-cimd-resolve", daemon=True)
    resolver.start()
    resolver.join(budget)
    if resolver.is_alive():
        raise ValueError("Client metadata document took too long")
    if "error" in outcome:
        raise outcome["error"]
    return outcome["addresses"]


def _shutdown(sock: socket.socket) -> None:
    """Wake a read blocked on sock in another thread.

    Socket-level shutdown, not SSLSocket.shutdown, which would also drop the TLS
    object from under that read.
    """
    try:
        socket.socket.shutdown(sock, socket.SHUT_RDWR)
    except OSError:
        pass


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Connects only to vetted addresses; SNI, certificate and Host checks keep the hostname.

    With a deadline (a _clock() value), connect attempts never wait past it, and the
    TLS socket exists before its handshake starts so a watchdog can shut it down.
    """

    def __init__(self, host: str, port: int, addresses: list[str], timeout: float,
                 deadline: float | None = None) -> None:
        self._tls = ssl.create_default_context()
        super().__init__(host, port, timeout=timeout, context=self._tls)
        self._addresses = addresses
        self._deadline = deadline

    def _budget(self) -> float:
        if self._deadline is None:
            return self.timeout
        remaining = self._deadline - _clock()
        if remaining <= 0:
            raise TimeoutError("Client metadata fetch deadline passed")
        return min(self.timeout, remaining)

    def connect(self) -> None:
        failure: OSError = OSError("No vetted client metadata address accepted the connection")
        for address in self._addresses:
            budget = self._budget()
            try:
                raw = socket.create_connection((address, self.port), budget)
            except OSError as exc:
                failure = exc
                continue
            try:
                self.sock = self._tls.wrap_socket(raw, server_hostname=self.host, do_handshake_on_connect=False)
            except OSError:
                raw.close()
                raise
            # Checked after self.sock is set: a watchdog that fired just before saw no socket.
            self.sock.settimeout(self._budget())
            self.sock.do_handshake()
            return
        raise failure


def fetch_metadata_document(url: str) -> dict:
    """Fetch one allowlisted client metadata document.

    Only the exact allowlisted URL is requested, so the host always equals the allowlisted
    host. HTTPS to public addresses only, no redirects and a 64 KiB cap. CIMD_TIMEOUT_SECONDS
    is one wall-clock budget for the whole fetch: resolution, connect, TLS, status, headers
    and body. Per-read socket timeouts restart on every byte, so a watchdog shuts the socket
    down at the deadline and trickled bytes cannot extend it. Blocking: event-loop callers
    use anyio.to_thread.
    """
    if url not in metadata_document_client_ids():
        raise ValueError("Client metadata URL is not allowlisted")
    parts = urlsplit(url)
    port = parts.port or 443
    deadline = _clock() + CIMD_TIMEOUT_SECONDS
    expired = threading.Event()
    connection = None

    def expire() -> None:
        expired.set()
        sock = getattr(connection, "sock", None)
        if sock is not None:
            _shutdown(sock)

    watchdog = threading.Timer(CIMD_TIMEOUT_SECONDS, expire)
    watchdog.daemon = True
    watchdog.start()
    try:
        addresses = _resolve_within(parts.hostname, port, CIMD_TIMEOUT_SECONDS)
        connection = _PinnedHTTPSConnection(parts.hostname, port, addresses, CIMD_TIMEOUT_SECONDS, deadline=deadline)
        connection.request("GET", parts.path + (f"?{parts.query}" if parts.query else ""),
                           headers={"Accept": "application/json"})
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError("Client metadata document must be served directly with HTTP 200")
        declared = response.getheader("Content-Length")
        if declared is not None and (not declared.strip().isdigit() or int(declared) > CIMD_MAX_BYTES):
            raise ValueError("Client metadata document is too large")
        body = bytearray()
        while chunk := response.read(min(16384, CIMD_MAX_BYTES + 1 - len(body))):
            body.extend(chunk)
            if len(body) > CIMD_MAX_BYTES:
                raise ValueError("Client metadata document is too large")
            if _clock() > deadline:
                raise ValueError("Client metadata document took too long")
        if expired.is_set():  # a shut-down socket can read as a short, clean end of body
            raise ValueError("Client metadata document took too long")
    except (OSError, ValueError, http.client.HTTPException) as exc:
        if expired.is_set() or isinstance(exc, TimeoutError):
            raise ValueError("Client metadata document took too long") from None
        raise
    finally:
        watchdog.cancel()
        if connection is not None:
            connection.close()
    document = json.loads(body.decode("utf-8"))
    if not isinstance(document, dict):
        raise ValueError("Client metadata document must be a JSON object")
    return document


def _https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parts = urlsplit(value)
    return parts.scheme == "https" and bool(parts.hostname) and "@" not in parts.netloc and not parts.fragment


def client_from_metadata_document(url: str, document: dict) -> OAuthClientInformationFull:
    """Register a fetched document as a public PKCE client limited to the twin scope."""
    if document.get("client_id") != url or "client_secret" in document:
        raise ValueError("Client metadata document does not describe this public client")
    redirects = document.get("redirect_uris")
    if not isinstance(redirects, list) or not redirects or not all(_https_url(item) for item in redirects):
        raise ValueError("Client metadata document needs HTTPS redirect URIs")
    return OAuthClientInformationFull(
        client_id=url, redirect_uris=[AnyUrl(item) for item in redirects],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"], token_endpoint_auth_method="none", scope=MCP_SCOPE,
    )


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
        self._document_clients = metadata_document_client_ids()
        self._document_cache: dict[str, tuple[float, OAuthClientInformationFull]] = {}
        self._document_retry_at: dict[str, float] = {}
        # Events are created by the fetching coroutine, so none is ever bound to another event loop.
        self._document_inflight: dict[str, anyio.Event] = {}

    @property
    def db(self) -> SecurityStore:
        return self.repository or security_store()

    @property
    def client_id_metadata_documents_supported(self) -> bool:
        return bool(self._document_clients)

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        """Static client, or an allowlisted metadata document client.

        Anonymous /authorize, /token and /revoke requests reach this, so document fetches are
        single-flight per URL (other callers wait for the one in progress), a failed fetch
        starts no new one for CIMD_RETRY_SECONDS, and while a refresh fails or backs off the
        last good client keeps serving for up to CIMD_STALE_SECONDS after it expired.
        """
        static = self._clients.get(client_id)
        if static is not None or client_id not in self._document_clients:
            return static
        while True:
            now = _clock()
            cached = self._document_cache.get(client_id)
            if cached and cached[0] > now:
                return cached[1]
            stale = cached[1] if cached and cached[0] + CIMD_STALE_SECONDS > now else None
            if self._document_retry_at.get(client_id, 0.0) > now:
                return stale
            inflight = self._document_inflight.get(client_id)
            if inflight is None:
                break
            await inflight.wait()
        done = self._document_inflight[client_id] = anyio.Event()
        try:
            document = await anyio.to_thread.run_sync(fetch_metadata_document, client_id)
            client = client_from_metadata_document(client_id, document)
        except (OSError, ValueError, http.client.HTTPException) as exc:
            logger.info("Client metadata document was rejected (%s)", type(exc).__name__)
            self._document_retry_at[client_id] = _clock() + CIMD_RETRY_SECONDS
            return stale
        else:
            self._document_cache[client_id] = (_clock() + CIMD_CACHE_SECONDS, client)
            self._document_retry_at.pop(client_id, None)
            return client
        finally:
            del self._document_inflight[client_id]
            done.set()

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
        query.append(("iss", authorization_issuer()))
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
