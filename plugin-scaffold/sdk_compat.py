"""Narrow compatibility adapter for the pinned SDK's public-client revoke form.

The SDK requires a nullable client_secret field even for auth method 'none'.
Supply an empty default only on /revoke; the SDK still validates the configured
client and performs the complete RFC revocation flow. Remove after upgrading to
a version whose RevocationRequest gives that optional field a default.
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode

from mcp.server import MCPServer
from starlette.responses import JSONResponse


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


class WisdomTwinMCPServer(MCPServer):
    def streamable_http_app(self, **kwargs):
        app = super().streamable_http_app(**kwargs)
        app.add_middleware(PublicClientRevokeAdapter)
        return app
