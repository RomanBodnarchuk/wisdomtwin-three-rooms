"""WisdomTwin MCP server. Streamable HTTP at /mcp, health at /health."""

from __future__ import annotations

import json
import html
import logging
import os
import uuid
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse

from sdk_compat import WisdomTwinMCPServer
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions, RevocationOptions
from mcp.types import CallToolResult, EmbeddedResource, TextContent, TextResourceContents, ToolAnnotations

import service as twin_service
from auth_provider import MCP_SCOPE, WisdomTwinAuthProvider, auth_is_required
from domain import ROLE_TITLES, connector_enabled
from oauth_connectors import public_base_url
from runtime import validate_runtime, local_test_mode
from corporate_login import start_login, finish_login, SESSION_COOKIE, LOGIN_COOKIE
from provider_binding import authorized_callback, bind_slack, bind_google

validate_runtime()

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
        issuer_url=base,
        resource_server_url=AnyHttpUrl(f"{base}/mcp"),
        required_scopes=[MCP_SCOPE],
        validate_token_resource=True,
        client_registration_options=ClientRegistrationOptions(enabled=False, valid_scopes=[MCP_SCOPE]),
        revocation_options=RevocationOptions(enabled=True),
    )
    _server_kwargs["auth_server_provider"] = _auth_provider

mcp = WisdomTwinMCPServer(**_server_kwargs)


async def _request_actor(request: Request) -> str:
    from errors import AUTHORIZATION_REQUIRED, CodedToolError

    header = request.headers.get("authorization", "")
    token = await _auth_provider.load_access_token(header[7:]) if header.startswith("Bearer ") else None
    if token is None or token.resource != f"{public_base_url()}/mcp" or MCP_SCOPE not in token.scopes:
        raise CodedToolError(AUTHORIZATION_REQUIRED, "A valid role-scoped bearer token is required.")
    return token.subject


@mcp.custom_route("/jobs/{job_id}", methods=["GET"])
async def job_status(request: Request) -> JSONResponse:
    from store import actor_subject, current_store

    try:
        subject = await _request_actor(request)
    except Exception:
        return JSONResponse({"error": "AUTHORIZATION_REQUIRED"}, status_code=401)
    context = actor_subject.set(subject)
    try:
        try:
            identifier = str(uuid.UUID(request.path_params["job_id"]))
        except ValueError:
            return JSONResponse({"error": "JOB_NOT_FOUND"}, status_code=404)
        job = current_store().get_job(identifier)
        if job is None:
            return JSONResponse({"error": "JOB_NOT_FOUND"}, status_code=404)
        return JSONResponse({"job_id": job.id, "status": job.status, "progress": job.progress, "chunks_ingested": job.chunks_ingested})
    finally:
        actor_subject.reset(context)


@mcp.custom_route("/roles/{role_id}", methods=["DELETE"])
async def delete_role(request: Request) -> JSONResponse:
    from store import actor_subject

    try:
        subject = await _request_actor(request)
    except Exception:
        return JSONResponse({"error": "AUTHORIZATION_REQUIRED"}, status_code=401)
    context = actor_subject.set(subject)
    try:
        identifier = str(uuid.UUID(request.path_params["role_id"]))
        removed = twin_service.request_namespace_deletion(identifier)
        return JSONResponse({"status": "deleted", "chunks_deleted": removed})
    except Exception:
        return JSONResponse({"error": "AUTHORIZATION_REQUIRED"}, status_code=403)
    finally:
        actor_subject.reset(context)


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


@mcp.custom_route("/terms", methods=["GET"])
async def terms(_: Request) -> HTMLResponse:
    page = (Path(__file__).resolve().parent / "terms.html").read_text(encoding="utf-8")
    return HTMLResponse(page)


@mcp.custom_route("/.well-known/openai-apps-challenge", methods=["GET"])
async def openai_apps_challenge(_: Request) -> PlainTextResponse:
    token = os.environ.get("OPENAI_APPS_CHALLENGE", "").strip()
    if not token:
        return PlainTextResponse("Not configured", status_code=404)
    return PlainTextResponse(token)


@mcp.custom_route("/oauth/consent", methods=["GET"])
async def oauth_consent(request: Request) -> HTMLResponse:
    transaction = request.query_params.get("txn", "")
    session = _auth_provider.db.get("session", request.cookies.get(SESSION_COOKIE, ""))
    if not session or session["transaction"] != transaction:
        try:
            target, browser = start_login(transaction)
        except RuntimeError:
            return HTMLResponse("Corporate sign-in is not configured. Contact the workspace administrator.", status_code=503)
        except Exception:
            return HTMLResponse("Corporate authorization could not be started.", status_code=400)
        response = RedirectResponse(target, status_code=302)
        response.set_cookie(LOGIN_COOKIE, browser, max_age=300, httponly=True, secure=not local_test_mode(), samesite="lax", path="/oauth")
        return response
    pending = _auth_provider.db.get("pending", transaction)
    if not pending:
        return HTMLResponse("Authorization request expired.", status_code=400)
    safe_txn, safe_csrf = html.escape(transaction, quote=True), html.escape(session["csrf"], quote=True)
    client, email = html.escape(pending["client_id"]), html.escape(session["email"])
    return HTMLResponse(f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>WisdomTwin consent</title></head>
<body><h1>Allow WisdomTwin access</h1><p>Signed in as {email}.</p>
<p>Allow client {client} to read your assigned role and manage read-only source connections.</p>
<form method="post" action="/oauth/consent"><input type="hidden" name="txn" value="{safe_txn}">
<input type="hidden" name="csrf" value="{safe_csrf}"><button type="submit">Allow</button></form></body></html>""", headers={"Cache-Control": "no-store", "Content-Security-Policy": "default-src 'none'; form-action 'self'; frame-ancestors 'none'"})


@mcp.custom_route("/oauth/callback/identity", methods=["GET"])
async def identity_callback(request: Request) -> HTMLResponse:
    try:
        transaction, session = finish_login(request.query_params.get("state", ""), request.query_params.get("code", ""), request.cookies.get(LOGIN_COOKIE, ""))
    except Exception:
        return HTMLResponse("Corporate authorization could not be verified.", status_code=400)
    response = RedirectResponse(f"{public_base_url()}/oauth/consent?txn={urllib.parse.quote(transaction)}", status_code=302)
    response.set_cookie(SESSION_COOKIE, session, max_age=300, httponly=True, secure=not local_test_mode(), samesite="lax", path="/oauth")
    response.delete_cookie(LOGIN_COOKIE, path="/oauth")
    return response


@mcp.custom_route("/oauth/consent", methods=["POST"])
async def oauth_consent_approve(request: Request) -> HTMLResponse:
    form = await request.form()
    transaction = str(form.get("txn") or "")
    try:
        if request.headers.get("origin") != public_base_url():
            raise ValueError("Consent origin mismatch")
        target = _auth_provider.approve(transaction, session_key=request.cookies.get(SESSION_COOKIE, ""), csrf=str(form.get("csrf") or ""))
    except Exception:
        logger.info("Authorization consent was rejected")
        return HTMLResponse("Authorization could not be completed.", status_code=400)
    response = RedirectResponse(target, status_code=302)
    response.delete_cookie(SESSION_COOKIE, path="/oauth")
    return response


@mcp.custom_route("/oauth/callback/slack", methods=["GET"])
async def slack_callback(request: Request) -> PlainTextResponse:
    try:
        code = request.query_params.get("code", "")
        if not code:
            raise ValueError("Missing code")
        with authorized_callback(request.query_params.get("state", ""), "slack") as (pending, member):
            body = _exchange_code("https://slack.com/api/oauth.v2.access", {
                "client_id": os.environ.get("SLACK_CLIENT_ID", ""),
                "code": code, "redirect_uri": f"{public_base_url()}/oauth/callback/slack", "code_verifier": pending["verifier"],
            })
            bind_slack(pending, member, body)
    except Exception:
        logger.info("Slack identity binding was rejected")
        return PlainTextResponse("Slack authorization could not be verified.", status_code=400)
    return PlainTextResponse("Slack is connected for the verified role.")


@mcp.custom_route("/oauth/callback/google", methods=["GET"])
async def google_callback(request: Request) -> PlainTextResponse:
    try:
        code = request.query_params.get("code", "")
        if not code:
            raise ValueError("Missing code")
        with authorized_callback(request.query_params.get("state", ""), {"gmail", "drive"}) as (pending, member):
            body = _exchange_code("https://oauth2.googleapis.com/token", {
                "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""), "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
                "code": code, "redirect_uri": f"{public_base_url()}/oauth/callback/google", "grant_type": "authorization_code", "code_verifier": pending["verifier"],
            })
            bind_google(pending, member, body)
    except Exception:
        logger.info("Google identity binding was rejected")
        return PlainTextResponse("Google authorization could not be verified.", status_code=400)
    return PlainTextResponse("The verified business account is connected for this role.")


@mcp.tool(
    description=(
        "Connect a read-only business account for one role. "
        f"Slack is {SLACK_STATE}. Gmail is {GMAIL_STATE}. Google Drive is {DRIVE_STATE}. "
        "role_title is free text. Suggested titles: "
        f"{PICKLIST}."
    ),
    title="Connect a business account",
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
    meta={"access": "readWrite", "securitySchemes": [{"type": "oauth2", "scopes": [MCP_SCOPE]}]},
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
        f"Slack is {SLACK_STATE}. Gmail is {GMAIL_STATE}. Google Drive is {DRIVE_STATE}. "
        "This tool reads enabled source systems and writes vectors and metadata to the role index. "
        "Gmail currently supplies snippets; Drive supplies names and descriptions."
    ),
    title="Ingest into the role",
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=False,
    ),
    meta={"access": "readWrite", "securitySchemes": [{"type": "oauth2", "scopes": [MCP_SCOPE]}]},
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
        "Revalidates source evidence using the current user's read-only grant. "
        "Returns the exact empty-context response when no accessible supporting evidence exists."
    ),
    title="Ask the role twin",
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
    meta={"access": "readOnly", "securitySchemes": [{"type": "oauth2", "scopes": [MCP_SCOPE]}]},
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
    title="List role twin status",
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
    meta={"access": "readOnly", "securitySchemes": [{"type": "oauth2", "scopes": [MCP_SCOPE]}]},
)
def list_twins_status() -> list[dict]:
    return twin_service.list_twins_status()


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    validate_runtime()
    host = os.environ.get("HOST", "127.0.0.1" if local_test_mode() else "0.0.0.0")
    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        json_response=True,
        stateless_http=True,
    )


if __name__ == "__main__":
    main()
