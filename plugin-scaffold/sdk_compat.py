"""Narrow adapters around the pinned SDK's streamable HTTP app.

The SDK requires a nullable client_secret field even for auth method 'none'.
Supply an empty default only on /revoke; the SDK still validates the configured
client and performs the complete RFC revocation flow. Remove after upgrading to
a version whose RevocationRequest gives that optional field a default.

Authorization-server metadata is the SDK's own build_metadata output with these
fields corrected: the public 'none' auth method the configured clients use at the
token endpoint and, when revocation is enabled, at the revocation endpoint, RFC 9207
iss support, and client ID metadata documents when an allowlist exists.
RFC 9207 iss is appended to the SDK's /authorize code and error redirects.
The root protected-resource alias serves the SDK's path-inserted document.
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from mcp.server import MCPServer
from mcp.server.auth.handlers.metadata import MetadataHandler
from mcp.server.auth.routes import build_metadata, build_resource_metadata_url, cors_middleware
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions, RevocationOptions
from mcp.server.transport_security import TransportSecurityMiddleware, TransportSecuritySettings
from mcp.shared.auth import OAuthMetadata
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

AUTHORIZATION_METADATA_PATH = "/.well-known/oauth-authorization-server"
ROOT_RESOURCE_METADATA_PATH = "/.well-known/oauth-protected-resource"


class PublicClientRevokeAdapter:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        content_type = dict(scope.get("headers", [])).get(b"content-type", b"").split(b";", 1)[0]
        if scope["type"] != "http" or scope.get("method") != "POST" or scope.get("path") != "/revoke" or content_type != b"application/x-www-form-urlencoded":
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > 65536:
                return await JSONResponse({"error": "invalid_request"}, status_code=413)(scope, receive, send)
            if not message.get("more_body"):
                break
        try:
            pairs = parse_qsl(body.decode("utf-8"), keep_blank_values=True)
        except UnicodeDecodeError:
            return await JSONResponse({"error": "invalid_request"}, status_code=400)(scope, receive, send)
        if not any(name == "client_secret" for name, _ in pairs):
            pairs.append(("client_secret", ""))
        encoded = urlencode(pairs).encode()
        scope = {**scope, "headers": [(key, value) for key, value in scope.get("headers", []) if key != b"content-length"] + [(b"content-length", str(len(encoded)).encode())]}
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": encoded, "more_body": False}
            return await receive()

        await self.app(scope, replay, send)


def with_issuer(location: str, issuer: str) -> str:
    """Append RFC 9207 iss to an authorization response redirect (code or error) that lacks it."""
    parts = urlsplit(location)
    names = {name for name, _ in parse_qsl(parts.query, keep_blank_values=True)}
    if not names & {"code", "error"} or "iss" in names:
        return location
    query = f"{parts.query}&" if parts.query else ""
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query + urlencode({"iss": issuer}), parts.fragment))


class AuthorizationResponseIssAdapter:
    """RFC 9207 for the SDK's /authorize redirects; the consent route adds iss itself."""

    def __init__(self, app, issuer: str):
        self.app = app
        self.issuer = issuer

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") != "/authorize":
            return await self.app(scope, receive, send)

        async def send_with_issuer(message):
            if message["type"] == "http.response.start":
                message = {**message, "headers": [
                    (name, with_issuer(value.decode("latin-1"), self.issuer).encode("latin-1") if name.lower() == b"location" else value)
                    for name, value in message.get("headers", [])]}
            await send(message)

        await self.app(scope, receive, send_with_issuer)


class TransportSecurityGuard:
    """Host and Origin checks on the MCP endpoint before bearer authentication.

    Uses the SDK's own validator, so an invalid present Origin gets 403 and an
    unlisted Host gets 421 even without a token. An absent Origin stays allowed.
    """

    def __init__(self, app, settings: TransportSecuritySettings, path: str = "/mcp"):
        self.app = app
        self.path = path
        self.security = TransportSecurityMiddleware(settings)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path") == self.path:
            rejected = await self.security.validate_request(Request(scope))
            if rejected is not None:
                return await rejected(scope, receive, send)
        await self.app(scope, receive, send)


def authorization_metadata(auth: AuthSettings, *, metadata_documents: bool) -> OAuthMetadata:
    revocation = auth.revocation_options or RevocationOptions()
    metadata = build_metadata(
        auth.issuer_url, auth.service_documentation_url,
        auth.client_registration_options or ClientRegistrationOptions(),
        revocation,
        supports_identity_assertion=auth.identity_assertion_enabled,
    )
    return metadata.model_copy(update={
        # Only the scopes the authorize step accepts; ChatGPT requests every
        # advertised scope, so nothing else may be listed here.
        "scopes_supported": list(auth.required_scopes or []),
        "token_endpoint_auth_methods_supported": ["none"],
        # Every client is public and secretless; PublicClientRevokeAdapter lets /revoke accept them.
        "revocation_endpoint_auth_methods_supported": ["none"] if revocation.enabled else None,
        "authorization_response_iss_parameter_supported": True,
        "client_id_metadata_document_supported": True if metadata_documents else None,
    })


class WisdomTwinMCPServer(MCPServer):
    def streamable_http_app(self, **kwargs):
        app = super().streamable_http_app(**kwargs)
        auth, provider = self.settings.auth, self._auth_server_provider
        if auth is not None and provider is not None:
            metadata = authorization_metadata(
                auth, metadata_documents=bool(getattr(provider, "client_id_metadata_documents_supported", False)))
            # Registered ahead of the SDK's route for the same path, which it shadows.
            app.router.routes.insert(0, Route(
                AUTHORIZATION_METADATA_PATH, endpoint=cors_middleware(MetadataHandler(metadata).handle, ["GET", "OPTIONS"]),
                methods=["GET", "OPTIONS"]))
            app.add_middleware(AuthorizationResponseIssAdapter, issuer=metadata.model_dump(mode="json")["issuer"])
        if auth is not None and auth.resource_server_url is not None:
            path = urlsplit(str(build_resource_metadata_url(auth.resource_server_url))).path
            sdk_route = next((route for route in app.router.routes if isinstance(route, Route) and route.path == path), None)
            if sdk_route is not None and path != ROOT_RESOURCE_METADATA_PATH:
                app.router.routes.append(Route(ROOT_RESOURCE_METADATA_PATH, endpoint=sdk_route.endpoint, methods=["GET", "OPTIONS"]))
        app.add_middleware(PublicClientRevokeAdapter)
        security = kwargs.get("transport_security")
        if security is not None and security.enable_dns_rebinding_protection:
            app.add_middleware(TransportSecurityGuard, settings=security, path=kwargs.get("streamable_http_path", "/mcp"))
        return app
