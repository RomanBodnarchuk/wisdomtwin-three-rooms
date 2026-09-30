"""WisdomTwin MCP server. Streamable HTTP at /mcp, health at /health."""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
import urllib.request
from typing import Literal

from pydantic import AnyHttpUrl
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse

from mcp.server import MCPServer
from mcp.server.auth.settings import AuthSettings
from mcp.types import CallToolResult, EmbeddedResource, TextContent, TextResourceContents, ToolAnnotations

import service as twin_service
from auth_provider import MCP_SCOPE, WisdomTwinAuthProvider, auth_is_required
from domain import ROLE_TITLES, connector_enabled
from oauth_connectors import public_base_url
from tokens import encrypt_token

logger = logging.getLogger("wisdomtwin")

PICKLIST = ", ".join(ROLE_TITLES)
SLACK_STATE = "live" if connector_enabled("slack") else "coming soon"
GMAIL_STATE = "live" if connector_enabled("gmail") else "coming soon"
DRIVE_STATE = "live" if connector_enabled("drive") else "coming soon"

INSTRUCTIONS = (
    "WisdomTwin keeps a private business twin for one role on the org chart. "
    f"Slack is {SLACK_STATE}. Gmail is {GMAIL_STATE}. Google Drive is {DRIVE_STATE}. "
    "Use read-only connectors. Ground every claim in retrieved excerpts and attach a citation. "
    "Refuse questions that are not about the business record."
)

_auth_provider = WisdomTwinAuthProvider()

_server_kwargs = {
    "name": "WisdomTwin",
    "instructions": INSTRUCTIONS,
}
if auth_is_required():
    base = public_base_url()
    _server_kwargs["auth"] = AuthSettings(
        issuer_url=AnyHttpUrl(base),
        resource_server_url=AnyHttpUrl(f"{base}/mcp"),
        required_scopes=[MCP_SCOPE],
        validate_token_resource=True,
    )
    _server_kwargs["auth_server_provider"] = _auth_provider

mcp = MCPServer(**_server_kwargs)


def _exchange_code(token_url: str, body: dict) -> dict:
    payload = urllib.parse.urlencode(body).encode("utf-8")
    request = urllib.request.Request(
        token_url,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "wisdomtwin"})


@mcp.custom_route("/.well-known/openai-apps-challenge", methods=["GET"])
async def openai_apps_challenge(_: Request) -> PlainTextResponse:
    token = os.environ.get("OPENAI_APPS_CHALLENGE", "").strip()
    if not token:
        return PlainTextResponse("Not configured", status_code=404)
    return PlainTextResponse(token)


@mcp.custom_route("/oauth/consent", methods=["GET"])
async def oauth_consent(request: Request) -> HTMLResponse:
    transaction = request.query_params.get("txn", "")
    safe = transaction.replace("<", "").replace(">", "").replace('"', "")
    page = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>WisdomTwin</title></head>
<body>
  <h1>Allow WisdomTwin</h1>
  <p>This grants read access to your WisdomTwin role twin.</p>
  <form method="post" action="/oauth/consent">
    <input type="hidden" name="txn" value="{safe}">
    <button type="submit">Allow</button>
  </form>
</body>
</html>"""
    return HTMLResponse(page)


@mcp.custom_route("/oauth/consent", methods=["POST"])
async def oauth_consent_approve(request: Request) -> HTMLResponse:
    form = await request.form()
    transaction = str(form.get("txn") or "")
    try:
        target = _auth_provider.approve(transaction)
    except Exception:
        logger.info("Authorization consent was rejected")
        return HTMLResponse("Authorization could not be completed.", status_code=400)
    return RedirectResponse(target, status_code=302)


@mcp.custom_route("/oauth/callback/slack", methods=["GET"])
async def slack_callback(request: Request) -> PlainTextResponse:
    from store import current_store

    state = request.query_params.get("state", "")
    code = request.query_params.get("code", "")
    pending = current_store().pop_secret(state)
    if not pending or not code:
        return PlainTextResponse("Slack authorization could not be completed.", status_code=400)
    try:
        token_body = _exchange_code(
            "https://slack.com/api/oauth.v2.access",
            {
                "client_id": os.environ.get("SLACK_CLIENT_ID", ""),
                "client_secret": os.environ.get("SLACK_CLIENT_SECRET", ""),
                "code": code,
                "redirect_uri": f"{public_base_url()}/oauth/callback/slack",
                "code_verifier": pending["verifier"],
            },
        )
    except Exception:
        logger.info("Slack token exchange failed")
        return PlainTextResponse("Slack authorization could not be completed.", status_code=400)
    authed = token_body.get("authed_user") or {}
    access_token = authed.get("access_token") or token_body.get("access_token")
    if not access_token:
        return PlainTextResponse("Slack authorization could not be completed.", status_code=400)
    current_store().save_credential(pending["role_id"], "slack", encrypt_token(access_token))
    return PlainTextResponse("Slack is connected for this role.")


@mcp.custom_route("/oauth/callback/google", methods=["GET"])
async def google_callback(request: Request) -> PlainTextResponse:
    from store import current_store

    state = request.query_params.get("state", "")
    code = request.query_params.get("code", "")
    pending = current_store().pop_secret(state)
    if not pending or not code or pending.get("service") not in {"gmail", "drive"}:
        return PlainTextResponse("Google authorization could not be completed.", status_code=400)
    try:
        token_body = _exchange_code(
            "https://oauth2.googleapis.com/token",
            {
                "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
                "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
                "code": code,
                "redirect_uri": f"{public_base_url()}/oauth/callback/google",
                "grant_type": "authorization_code",
                "code_verifier": pending["verifier"],
            },
        )
    except Exception:
        logger.info("Google token exchange failed")
        return PlainTextResponse("Google authorization could not be completed.", status_code=400)
    access_token = token_body.get("access_token")
    if not access_token:
        return PlainTextResponse("Google authorization could not be completed.", status_code=400)
    current_store().save_credential(pending["role_id"], pending["service"], encrypt_token(access_token))
    return PlainTextResponse("The business account is connected for this role.")


@mcp.tool(
    description=(
        "Connect a read-only business account for one role. "
        f"Slack is {SLACK_STATE}. Gmail is {GMAIL_STATE}. Google Drive is {DRIVE_STATE}. "
        "role_title is free text. Suggested titles: "
        f"{PICKLIST}."
    ),
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    ),
    meta={"access": "readWrite"},
)
def connect_business_account(
    service: Literal["slack", "gmail", "drive"],
    domain: str,
    role_title: str,
) -> dict:
    return twin_service.connect_business_account(service, domain, role_title)


@mcp.tool(
    description=(
        "Ingest business communications into the active role namespace. "
        "Slack is the live connector. Gmail and Google Drive return an availability message while gated. "
        "This tool reads source systems and writes the role index."
    ),
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
    meta={"access": "readWrite"},
)
def ingest_data(
    service: Literal["slack", "gmail", "drive"],
    query: str,
    max_items: int = 1000,
) -> dict:
    return twin_service.ingest_data(service, query, max_items)


@mcp.tool(
    description=(
        "Answer a business question from the active role namespace and attach a citation to every claim. "
        "Reads the index only."
    ),
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
    meta={"access": "readOnly"},
    structured_output=False,
)
def query_twin(question: str, max_results: int = 10, max_tokens: int = 512) -> CallToolResult:
    payload = twin_service.query_twin(question, max_results, max_tokens)
    content: list = [TextContent(type="text", text=payload["answer"])]
    for citation in payload["citations"]:
        content.append(
            EmbeddedResource(
                type="resource",
                resource=TextResourceContents(
                    uri=citation["uri"],
                    mime_type="application/json",
                    text=json.dumps({"uri": citation["uri"], "snippet": citation["snippet"]}),
                ),
            )
        )
    return CallToolResult(
        content=content,
        structured_content={"answer": payload["answer"], "citations": payload["citations"]},
    )


@mcp.tool(
    description="List connected role twins with ingested chunk counts, last update, and business domain.",
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
    meta={"access": "readOnly"},
)
def list_twins_status() -> list[dict]:
    return twin_service.list_twins_status()


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        json_response=True,
        stateless_http=True,
    )


if __name__ == "__main__":
    main()
