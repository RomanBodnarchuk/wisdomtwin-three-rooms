"""ChatGPT linking, transport checks and event-loop hardening (review findings H3, M1, M2, L5,
and follow-up findings SEC-1, SEC-2, SEC-3 and F7).

Synthetic identities and documents only. Every identity, provider and client metadata
call is patched, and apps are built in-process without binding. Real sockets fail the test,
except the loopback TLS server the metadata document trickle tests start for themselves.
"""

import datetime
import importlib
import io
import json
import socket
import ssl
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import anyio
import jwt
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import NameOID
from jwt.algorithms import RSAAlgorithm
from mcp.server.auth.provider import AuthorizationParams
from mcp.server.auth.routes import build_metadata
from mcp.server.auth.settings import ClientRegistrationOptions
from starlette.testclient import TestClient

import auth_provider
import runtime
from auth_provider import WisdomTwinAuthProvider
from oauth_connectors import GMAIL_SCOPE, SLACK_USER_SCOPES, new_pkce
from sdk_compat import with_issuer
from security_store import security_store
from store import actor_subject, current_store


BASE = "http://127.0.0.1:8000"
CALLBACK = f"{BASE}/oauth/done"
PUBLIC = "https://twin.example.test"
ISSUER = "https://identity.synthetic.test"
OIDC_CLIENT = "synthetic-corporate-client"
CHATGPT_CLIENT = "https://chatgpt.com/oauth/client.json"
CHATGPT_REDIRECT = "https://chatgpt.com/connector_platform_oauth_redirect"
METADATA = "/.well-known/oauth-authorization-server"
TOOLS_LIST = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
MCP_HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
PUBLIC_V4, PUBLIC_V6 = "104.18.32.47", "2606:4700::6812:202f"
# Captured before the offline fixture replaces them; only the loopback trickle tests restore them.
REAL_CREATE_CONNECTION, REAL_GETADDRINFO = socket.create_connection, socket.getaddrinfo
MALFORMED_ALLOWLISTS = [
    "http://chatgpt.com/oauth/client.json", "https://chatgpt.com", "https://chatgpt.com/",
    "https://user@chatgpt.com/oauth/client.json", "https://chatgpt.com/oauth/../client.json",
    "https://chatgpt.com/oauth/client.json#fragment", "https://chatgpt.com:99999/oauth/client.json",
]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        pytest.fail("Hardening tests must not open network connections")

    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr("urllib.request.urlopen", refuse)


@contextmanager
def reloaded_server(monkeypatch, *, auth: bool, **env):
    import server

    try:
        with monkeypatch.context() as scoped:
            scoped.setenv("WISDOMTWIN_AUTH_DISABLED", "0" if auth else "1")
            for name, value in env.items():
                scoped.setenv(name, value)
            yield importlib.reload(server), scoped
    finally:
        importlib.reload(server)


@pytest.fixture
def auth_server(monkeypatch):
    with reloaded_server(monkeypatch, auth=True) as loaded:
        yield loaded


@pytest.fixture
def cimd_server(monkeypatch):
    with reloaded_server(monkeypatch, auth=True, OAUTH_CIMD_CLIENT_IDS=CHATGPT_CLIENT) as loaded:
        yield loaded


@pytest.fixture
def fixture_server(monkeypatch):
    with reloaded_server(monkeypatch, auth=False) as loaded:
        yield loaded


@pytest.fixture
def cimd_env(monkeypatch):
    monkeypatch.setenv("OAUTH_CIMD_CLIENT_IDS", CHATGPT_CLIENT)


def production_like(patch):
    patch.setenv("PUBLIC_BASE_URL", PUBLIC)
    patch.setenv("WISDOMTWIN_ENV", "production")
    patch.delenv("HOST", raising=False)


class LoopThreads:
    """Records which threads run the event loop that serves requests."""

    def __init__(self, app):
        self.app = app
        self.idents = set()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            self.idents.add(threading.get_ident())
        await self.app(scope, receive, send)


def provision():
    return security_store().provision(
        issuer=ISSUER, provider_subject="alice", email="alice@example-corp.com",
        domain="example-corp.com", roles=["CRO"], slack_team_id="TEAM_A",
        slack_user_id="USER_A", google_subject="GOOGLE_A",
    )


def authorize_params(client_id, redirect_uri, challenge):
    return {
        "response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri,
        "scope": "twin:read", "state": "synthetic-client-state", "code_challenge": challenge,
        "code_challenge_method": "S256", "resource": f"{BASE}/mcp",
    }


def consent(http, provider, subject, consent_uri):
    """Stand in for the verified corporate sign-in, then approve through the real consent route."""
    transaction = parse_qs(urlsplit(consent_uri).query)["txn"][0]
    provider.db.put("session", "synthetic-session", {
        "transaction": transaction, "subject": subject, "email": "alice@example-corp.com",
        "csrf": "synthetic-csrf", "subject_epoch": provider.db.subject_epoch(subject),
    }, 300, subject=subject)
    response = http.post("/oauth/consent", data={"txn": transaction, "csrf": "synthetic-csrf"},
                         headers={"Origin": BASE, "Cookie": "wisdomtwin_consent=synthetic-session"})
    assert response.status_code == 302
    return response.headers["location"]


def mint_access_token(provider, subject):
    client = anyio.run(provider.get_client, "wisdomtwin-local")
    _, challenge = new_pkce()
    params = AuthorizationParams(state="s", scopes=["twin:read"], code_challenge=challenge,
                                 redirect_uri=client.redirect_uris[0], redirect_uri_provided_explicitly=True,
                                 resource=f"{BASE}/mcp")
    transaction = parse_qs(urlsplit(anyio.run(provider.authorize, client, params)).query)["txn"][0]
    provider.db.put("session", "synthetic-mint", {
        "transaction": transaction, "subject": subject, "email": "alice@example-corp.com",
        "csrf": "synthetic-csrf", "subject_epoch": provider.db.subject_epoch(subject),
    }, 300, subject=subject)
    redirect = provider.approve(transaction, session_key="synthetic-mint", csrf="synthetic-csrf")
    code = anyio.run(provider.load_authorization_code, client, parse_qs(urlsplit(redirect).query)["code"][0])
    return anyio.run(provider.exchange_authorization_code, client, code).access_token


# H3: authorization-server metadata


def test_metadata_advertises_the_public_client_method_and_rfc9207(auth_server):
    server, _ = auth_server
    with TestClient(server.http_app(), base_url=BASE) as http:
        response = http.get(METADATA)
    assert response.status_code == 200
    metadata = response.json()
    assert metadata["token_endpoint_auth_methods_supported"] == ["none"]
    assert metadata["revocation_endpoint_auth_methods_supported"] == ["none"]
    assert metadata["authorization_response_iss_parameter_supported"] is True
    assert "client_id_metadata_document_supported" not in metadata
    assert "registration_endpoint" not in metadata
    assert metadata["issuer"] == auth_provider.authorization_issuer()
    assert metadata["scopes_supported"] == ["twin:read"]
    auth = server.mcp.settings.auth
    sdk = build_metadata(auth.issuer_url, auth.service_documentation_url, ClientRegistrationOptions(),
                         auth.revocation_options).model_dump(mode="json", exclude_none=True)
    corrected = {"token_endpoint_auth_methods_supported", "revocation_endpoint_auth_methods_supported",
                 "authorization_response_iss_parameter_supported", "scopes_supported"}
    assert {key: value for key, value in metadata.items() if key not in corrected} == {
        key: value for key, value in sdk.items() if key not in corrected}


def test_discovery_matches_the_release_validator_contract(auth_server):
    # Mirrors package_validator.validate_release: issuer and authorization_servers
    # are the bare origin, and discovery declares PKCE, code flow, none and twin:read.
    server, _ = auth_server
    origin = auth_provider.authorization_issuer()
    assert not origin.endswith("/")
    with TestClient(server.http_app(), base_url=BASE) as http:
        challenge = http.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                              headers={"Accept": "application/json, text/event-stream"})
        assert challenge.status_code == 401
        resource_url = challenge.headers["www-authenticate"].split('resource_metadata="', 1)[1].split('"', 1)[0]
        protected = http.get(urlsplit(resource_url).path).json()
        oauth = http.get(METADATA).json()
    assert protected["resource"] == f"{origin}/mcp" and protected["authorization_servers"] == [origin]
    assert oauth["issuer"] == origin
    assert "S256" in oauth["code_challenge_methods_supported"]
    assert "authorization_code" in oauth["grant_types_supported"] and "code" in oauth["response_types_supported"]
    assert "none" in oauth["token_endpoint_auth_methods_supported"] and "twin:read" in oauth["scopes_supported"]
    for key in ("authorization_endpoint", "token_endpoint"):
        assert urlsplit(oauth[key]).netloc == urlsplit(origin).netloc


def test_metadata_advertises_client_metadata_documents_only_with_an_allowlist(cimd_server):
    server, _ = cimd_server
    with TestClient(server.http_app(), base_url=BASE) as http:
        metadata = http.get(METADATA).json()
    assert metadata["client_id_metadata_document_supported"] is True
    assert metadata["token_endpoint_auth_methods_supported"] == ["none"]


# L5: root protected-resource alias


def test_root_protected_resource_alias_serves_the_same_document(auth_server):
    server, _ = auth_server
    with TestClient(server.http_app(), base_url=BASE) as http:
        root = http.get("/.well-known/oauth-protected-resource")
        inserted = http.get("/.well-known/oauth-protected-resource/mcp")
        issuer = http.get(METADATA).json()["issuer"]
    assert root.status_code == inserted.status_code == 200
    assert root.json() == inserted.json()
    assert root.json()["resource"] == f"{BASE}/mcp"
    assert root.json()["authorization_servers"] == [issuer]


# H3: RFC 9207 iss on every authorization response


def test_consent_success_redirect_carries_the_served_issuer(auth_server):
    server, _ = auth_server
    subject = provision()
    verifier, challenge = new_pkce()
    with TestClient(server.http_app(), base_url=BASE, follow_redirects=False) as http:
        issuer = http.get(METADATA).json()["issuer"]
        response = http.get("/authorize", params=authorize_params("wisdomtwin-local", CALLBACK, challenge))
        assert response.status_code == 302
        consent_uri = response.headers["location"]
        assert "iss" not in parse_qs(urlsplit(consent_uri).query)
        callback = parse_qs(urlsplit(consent(http, server._auth_provider, subject, consent_uri)).query)
        assert set(callback) == {"code", "state", "iss"}
        assert callback["iss"] == [issuer]
        assert callback["state"] == ["synthetic-client-state"]
        token = http.post("/token", data={"grant_type": "authorization_code", "client_id": "wisdomtwin-local",
                                          "code": callback["code"][0], "redirect_uri": CALLBACK, "code_verifier": verifier})
    assert token.status_code == 200


@pytest.mark.parametrize("override,error", [
    ({"scope": "admin:write"}, "invalid_scope"),
    ({"resource": "https://attacker.test/mcp"}, "invalid_request"),
])
def test_sdk_authorize_error_redirect_carries_the_served_issuer(auth_server, override, error):
    server, _ = auth_server
    _, challenge = new_pkce()
    with TestClient(server.http_app(), base_url=BASE, follow_redirects=False) as http:
        issuer = http.get(METADATA).json()["issuer"]
        response = http.get("/authorize", params={**authorize_params("wisdomtwin-local", CALLBACK, challenge), **override})
    assert response.status_code == 302
    location = urlsplit(response.headers["location"])
    query = parse_qs(location.query)
    assert f"{location.scheme}://{location.netloc}{location.path}" == CALLBACK
    assert query["error"] == [error]
    assert query["state"] == ["synthetic-client-state"]
    assert query["iss"] == [issuer]


def test_issuer_is_added_once_and_only_to_authorization_responses():
    issuer = "https://twin.example.test/"
    consent_hop = "https://twin.example.test/oauth/consent?txn=abc"
    assert with_issuer(consent_hop, issuer) == consent_hop
    once = with_issuer("https://chatgpt.com/cb?code=c&state=s", issuer)
    assert parse_qs(urlsplit(once).query) == {"code": ["c"], "state": ["s"], "iss": [issuer]}
    assert with_issuer(once, issuer) == once
    assert parse_qs(urlsplit(with_issuer("https://chatgpt.com/cb?error=access_denied", issuer)).query)["iss"] == [issuer]


# H3: allowlisted client ID metadata documents


def test_allowlisted_metadata_document_client_links_off_the_event_loop(cimd_server, monkeypatch):
    server, _ = cimd_server
    subject = provision()
    fetches = []

    def fetch(url):
        fetches.append((url, threading.get_ident()))
        return {"client_id": CHATGPT_CLIENT, "client_name": "ChatGPT", "redirect_uris": [CHATGPT_REDIRECT],
                "token_endpoint_auth_method": "none"}

    monkeypatch.setattr(auth_provider, "fetch_metadata_document", fetch)
    app = LoopThreads(server.http_app())
    verifier, challenge = new_pkce()
    with TestClient(app, base_url=BASE, follow_redirects=False) as http:
        issuer = http.get(METADATA).json()["issuer"]
        response = http.get("/authorize", params=authorize_params(CHATGPT_CLIENT, CHATGPT_REDIRECT, challenge))
        assert response.status_code == 302
        callback = urlsplit(consent(http, server._auth_provider, subject, response.headers["location"]))
        query = parse_qs(callback.query)
        assert f"{callback.scheme}://{callback.netloc}{callback.path}" == CHATGPT_REDIRECT
        assert query["iss"] == [issuer]
        token = http.post("/token", data={"grant_type": "authorization_code", "client_id": CHATGPT_CLIENT,
                                          "code": query["code"][0], "redirect_uri": CHATGPT_REDIRECT, "code_verifier": verifier})
    assert token.status_code == 200
    assert "access_token" in token.json()
    assert [url for url, _ in fetches] == [CHATGPT_CLIENT], "The document is fetched once, then cached"
    assert app.idents and fetches[0][1] not in app.idents


def test_unlisted_metadata_document_url_is_never_fetched(cimd_server, monkeypatch):
    server, _ = cimd_server
    original = auth_provider.fetch_metadata_document
    monkeypatch.setattr(auth_provider, "fetch_metadata_document", lambda url: pytest.fail("Unlisted client IDs must not be fetched"))
    unlisted = "https://attacker.test/oauth/client.json"
    assert anyio.run(server._auth_provider.get_client, unlisted) is None
    assert anyio.run(server._auth_provider.get_client, "wisdomtwin-local").client_id == "wisdomtwin-local"
    _, challenge = new_pkce()
    with TestClient(server.http_app(), base_url=BASE, follow_redirects=False) as http:
        response = http.get("/authorize", params=authorize_params(unlisted, "https://attacker.test/cb", challenge))
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"
    with pytest.raises(ValueError):
        original(unlisted)


def test_metadata_documents_are_disabled_without_an_allowlist(auth_server, monkeypatch):
    server, _ = auth_server
    monkeypatch.setattr(auth_provider, "fetch_metadata_document", lambda url: pytest.fail("CIMD is disabled by default"))
    assert anyio.run(server._auth_provider.get_client, CHATGPT_CLIENT) is None


@pytest.mark.parametrize("value", MALFORMED_ALLOWLISTS)
def test_metadata_document_allowlist_requires_exact_https_urls(monkeypatch, value):
    monkeypatch.setenv("OAUTH_CIMD_CLIENT_IDS", value)
    with pytest.raises(RuntimeError):
        WisdomTwinAuthProvider()


def resolve_to(monkeypatch, *addresses):
    def getaddrinfo(host, port, *args, **kwargs):
        assert host == "chatgpt.com"
        return [(socket.AF_INET6 if ":" in address else socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port))
                for address in addresses]

    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)


class FakeResponse:
    def __init__(self, status, body, headers):
        self.status = status
        self._body = io.BytesIO(body)
        self._headers = headers

    def getheader(self, name, default=None):
        return self._headers.get(name, default)

    def read(self, amount=-1):
        return self._body.read(amount)


def serve_document(monkeypatch, *, status=200, body=b"", headers=None):
    """Replace the pinned HTTPS connection with an offline fake and record what it was asked."""
    calls = []

    class Connection:
        def __init__(self, host, port, addresses, timeout, deadline=None):
            calls.append({"host": host, "port": port, "addresses": addresses, "timeout": timeout})

        def request(self, method, target, headers=None):
            calls[-1].update(method=method, target=target)

        def getresponse(self):
            return FakeResponse(status, body, headers or {})

        def close(self):
            calls[-1]["closed"] = True

    monkeypatch.setattr(auth_provider, "_PinnedHTTPSConnection", Connection)
    return calls


def document(**overrides):
    return json.dumps({"client_id": CHATGPT_CLIENT, "redirect_uris": [CHATGPT_REDIRECT], **overrides}).encode()


def test_metadata_document_fetch_is_pinned_bounded_and_registers_a_public_client(cimd_env, monkeypatch):
    resolve_to(monkeypatch, PUBLIC_V4, PUBLIC_V6)
    calls = serve_document(monkeypatch, body=document(token_endpoint_auth_method="private_key_jwt"))
    client = anyio.run(WisdomTwinAuthProvider().get_client, CHATGPT_CLIENT)
    assert calls == [{"host": "chatgpt.com", "port": 443, "addresses": [PUBLIC_V4, PUBLIC_V6],
                      "timeout": auth_provider.CIMD_TIMEOUT_SECONDS, "method": "GET",
                      "target": "/oauth/client.json", "closed": True}]
    assert client.client_id == CHATGPT_CLIENT
    assert [str(uri) for uri in client.redirect_uris] == [CHATGPT_REDIRECT]
    assert client.token_endpoint_auth_method == "none"
    assert client.grant_types == ["authorization_code", "refresh_token"]
    assert client.scope == "twin:read"
    assert client.client_secret is None


@pytest.mark.parametrize("address", [
    "10.0.0.7", "127.0.0.1", "169.254.169.254", "100.64.0.1", "224.0.0.1", "0.0.0.0",
    "::1", "fd00::1", "fe80::1%en0", "::ffff:10.0.0.7",
])
def test_metadata_document_host_with_any_private_address_is_rejected(cimd_env, monkeypatch, address):
    resolve_to(monkeypatch, PUBLIC_V4, address)
    calls = serve_document(monkeypatch, body=document())
    with pytest.raises(ValueError, match="non-public"):
        auth_provider.fetch_metadata_document(CHATGPT_CLIENT)
    assert anyio.run(WisdomTwinAuthProvider().get_client, CHATGPT_CLIENT) is None
    assert calls == []


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_metadata_document_redirect_is_not_followed(cimd_env, monkeypatch, status):
    resolve_to(monkeypatch, PUBLIC_V4)
    calls = serve_document(monkeypatch, status=status, headers={"Location": "http://169.254.169.254/latest/meta-data"})
    with pytest.raises(ValueError, match="HTTP 200"):
        auth_provider.fetch_metadata_document(CHATGPT_CLIENT)
    assert anyio.run(WisdomTwinAuthProvider().get_client, CHATGPT_CLIENT) is None
    assert [call["target"] for call in calls] == ["/oauth/client.json", "/oauth/client.json"]


@pytest.mark.parametrize("declare_length", [True, False])
def test_oversize_metadata_document_is_rejected(cimd_env, monkeypatch, declare_length):
    resolve_to(monkeypatch, PUBLIC_V4)
    body = document(client_name="x" * auth_provider.CIMD_MAX_BYTES)
    serve_document(monkeypatch, body=body, headers={"Content-Length": str(len(body))} if declare_length else {})
    with pytest.raises(ValueError, match="too large"):
        auth_provider.fetch_metadata_document(CHATGPT_CLIENT)
    assert anyio.run(WisdomTwinAuthProvider().get_client, CHATGPT_CLIENT) is None


def test_metadata_document_must_arrive_within_the_time_budget(cimd_env, monkeypatch):
    resolve_to(monkeypatch, PUBLIC_V4)
    serve_document(monkeypatch, body=document())
    clock = iter([0.0, auth_provider.CIMD_TIMEOUT_SECONDS + 1])
    monkeypatch.setattr(auth_provider, "_clock", lambda: next(clock))
    with pytest.raises(ValueError, match="too long"):
        auth_provider.fetch_metadata_document(CHATGPT_CLIENT)


@pytest.mark.parametrize("body", [
    document(client_id="https://chatgpt.com/oauth/another-client.json"),
    document(client_id=CHATGPT_CLIENT + "?"),
    document(redirect_uris=[]),
    document(redirect_uris="https://chatgpt.com/connector_platform_oauth_redirect"),
    document(redirect_uris=["http://chatgpt.com/connector_platform_oauth_redirect"]),
    document(client_secret="synthetic-secret-must-not-appear"),
    b"[]",
    b"not json",
], ids=["other-client-id", "near-miss-client-id", "no-redirects", "redirects-not-a-list",
        "http-redirect", "client-secret", "json-array", "not-json"])
def test_metadata_document_must_identify_this_public_https_client(cimd_env, monkeypatch, body):
    resolve_to(monkeypatch, PUBLIC_V4)
    serve_document(monkeypatch, body=body)
    assert anyio.run(WisdomTwinAuthProvider().get_client, CHATGPT_CLIENT) is None


def test_metadata_document_cache_expires_after_an_hour(cimd_env, monkeypatch):
    fetches = []
    monkeypatch.setattr(auth_provider, "fetch_metadata_document",
                        lambda url: fetches.append(url) or json.loads(document()))
    provider = WisdomTwinAuthProvider()
    clock = [1000.0]
    monkeypatch.setattr(auth_provider, "_clock", lambda: clock[0])
    anyio.run(provider.get_client, CHATGPT_CLIENT)
    clock[0] += auth_provider.CIMD_CACHE_SECONDS - 1
    anyio.run(provider.get_client, CHATGPT_CLIENT)
    assert len(fetches) == 1
    clock[0] += 2
    anyio.run(provider.get_client, CHATGPT_CLIENT)
    assert len(fetches) == 2


# SEC-1: single-flight document fetches, failure backoff and a bounded stale fallback


def failing_upstream(monkeypatch, *, delay=0.0):
    """Replace the fetch with a synthetic upstream that fails until switched up."""
    upstream = {"up": False, "fetches": []}

    def fetch(url):
        upstream["fetches"].append(url)
        time.sleep(delay)
        if not upstream["up"]:
            raise OSError("synthetic upstream outage")
        return json.loads(document())

    monkeypatch.setattr(auth_provider, "fetch_metadata_document", fetch)
    return upstream


@pytest.mark.parametrize("up", [False, True], ids=["failing", "succeeding"])
def test_concurrent_metadata_document_lookups_share_one_slow_fetch(cimd_env, monkeypatch, up):
    upstream = failing_upstream(monkeypatch, delay=0.2)
    upstream["up"] = up
    provider = WisdomTwinAuthProvider()
    results = []

    async def lookups():
        async def lookup():
            results.append(await provider.get_client(CHATGPT_CLIENT))

        async with anyio.create_task_group() as group:
            for _ in range(60):
                group.start_soon(lookup)

    anyio.run(lookups)
    assert upstream["fetches"] == [CHATGPT_CLIENT], "Every concurrent caller waits for the one fetch in flight"
    assert len(results) == 60
    if up:
        assert all(client is results[0] for client in results) and results[0].client_id == CHATGPT_CLIENT
    else:
        assert results == [None] * 60


def test_failed_metadata_document_fetch_backs_off_and_a_never_fetched_client_stays_unknown(cimd_env, monkeypatch):
    assert auth_provider.CIMD_RETRY_SECONDS == 60
    clock = [1000.0]
    monkeypatch.setattr(auth_provider, "_clock", lambda: clock[0])
    upstream = failing_upstream(monkeypatch)
    provider = WisdomTwinAuthProvider()
    assert anyio.run(provider.get_client, CHATGPT_CLIENT) is None
    upstream["up"] = True
    clock[0] += auth_provider.CIMD_RETRY_SECONDS - 1
    assert anyio.run(provider.get_client, CHATGPT_CLIENT) is None, "No stale client exists, and the backoff starts no fetch"
    assert len(upstream["fetches"]) == 1
    clock[0] += 2
    assert anyio.run(provider.get_client, CHATGPT_CLIENT).client_id == CHATGPT_CLIENT
    assert len(upstream["fetches"]) == 2


def test_expired_metadata_document_client_keeps_refresh_and_revoke_working_through_an_outage(cimd_server, monkeypatch):
    assert auth_provider.CIMD_STALE_SECONDS == auth_provider.REFRESH_TTL_SECONDS
    server, _ = cimd_server
    provider = server._auth_provider
    subject = provision()
    clock = [1000.0]
    monkeypatch.setattr(auth_provider, "_clock", lambda: clock[0])
    upstream = failing_upstream(monkeypatch)
    upstream["up"] = True
    verifier, challenge = new_pkce()
    with TestClient(server.http_app(), base_url=BASE, follow_redirects=False) as http:
        response = http.get("/authorize", params=authorize_params(CHATGPT_CLIENT, CHATGPT_REDIRECT, challenge))
        assert response.status_code == 302
        query = parse_qs(urlsplit(consent(http, provider, subject, response.headers["location"])).query)
        initial = http.post("/token", data={"grant_type": "authorization_code", "client_id": CHATGPT_CLIENT,
                                            "code": query["code"][0], "redirect_uri": CHATGPT_REDIRECT,
                                            "code_verifier": verifier})
        assert initial.status_code == 200
        clock[0] += auth_provider.CIMD_CACHE_SECONDS + 1
        upstream["up"] = False
        rotated = http.post("/token", data={"grant_type": "refresh_token", "client_id": CHATGPT_CLIENT,
                                            "refresh_token": initial.json()["refresh_token"]})
        assert rotated.status_code == 200
        revoked = http.post("/revoke", data={"client_id": CHATGPT_CLIENT, "token": rotated.json()["refresh_token"],
                                             "token_type_hint": "refresh_token"})
        assert revoked.status_code == 200
    assert upstream["fetches"] == [CHATGPT_CLIENT] * 2, "One failed refresh; the backoff then serves /revoke"
    assert anyio.run(provider.load_access_token, rotated.json()["access_token"]) is None
    clock[0] += auth_provider.CIMD_STALE_SECONDS
    assert anyio.run(provider.get_client, CHATGPT_CLIENT) is None, "The stale fallback ends a refresh lifetime after expiry"
    assert len(upstream["fetches"]) == 3


# SEC-2: one wall-clock budget for the whole document fetch


TRICKLE_BUDGET, TRICKLE_MARGIN, TRICKLE_INTERVAL = 1.0, 0.5, 0.05
SYNTHETIC_METADATA_HOST = "cimd.synthetic.test"


class TricklingMetadataServer:
    """Loopback TLS server for a synthetic metadata host with a self-signed certificate.

    It answers one request and can send the headers or the body one byte per interval,
    each byte arriving well inside the per-read socket timeout.
    """

    def __init__(self, directory, mode):
        key = ec.generate_private_key(ec.SECP256R1())
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, SYNTHETIC_METADATA_HOST)])
        now = datetime.datetime.now(datetime.timezone.utc)
        certificate = (
            x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(minutes=5)).not_valid_after(now + datetime.timedelta(hours=1))
            .add_extension(x509.SubjectAlternativeName([x509.DNSName(SYNTHETIC_METADATA_HOST)]), critical=False)
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(key, hashes.SHA256()))
        pem = certificate.public_bytes(serialization.Encoding.PEM)
        certfile, keyfile = directory / "synthetic-cert.pem", directory / "synthetic-key.pem"
        certfile.write_bytes(pem)
        keyfile.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                              serialization.NoEncryption()))
        self.server_tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.server_tls.load_cert_chain(certfile, keyfile)
        self.client_tls = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.client_tls.load_verify_locations(cadata=pem.decode())
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(1)
        self.listener.settimeout(10)
        self.url = f"https://{SYNTHETIC_METADATA_HOST}:{self.listener.getsockname()[1]}/oauth/client.json"
        body = json.dumps({"client_id": self.url, "client_name": "Synthetic " + "x" * 200,
                           "redirect_uris": [CHATGPT_REDIRECT]}).encode()
        head = (b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                b"X-Synthetic-Padding: " + b"p" * 160 + b"\r\n"
                b"Content-Length: %d\r\n\r\n" % len(body))
        self.prompt, self.trickled = {"prompt": (head + body, b""), "headers": (b"", head + body),
                                      "body": (head, body)}[mode]
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.serve, daemon=True)
        self.thread.start()

    def serve(self):
        try:
            raw, _ = self.listener.accept()
        except OSError:
            return
        with raw:
            raw.settimeout(10)
            try:
                with self.server_tls.wrap_socket(raw, server_side=True) as conn:
                    request = b""
                    while b"\r\n\r\n" not in request:
                        data = conn.recv(4096)
                        if not data:
                            return
                        request += data
                    conn.sendall(self.prompt)
                    for byte in self.trickled:
                        if self.stop.wait(TRICKLE_INTERVAL):
                            return
                        conn.sendall(bytes([byte]))
            except OSError:
                return

    def close(self):
        self.stop.set()
        self.listener.close()
        self.thread.join(5)


@pytest.fixture
def trickling_server(monkeypatch, tmp_path, request):
    server = TricklingMetadataServer(tmp_path, request.param)

    def vetted(host, port):
        assert host == SYNTHETIC_METADATA_HOST
        return ["127.0.0.1"]

    def loopback_only(host, port, *args, **kwargs):
        assert host == "127.0.0.1", "Only the in-process loopback server may be reached"
        return REAL_GETADDRINFO(host, port, *args, **kwargs)

    monkeypatch.setenv("OAUTH_CIMD_CLIENT_IDS", server.url)
    monkeypatch.setattr(auth_provider, "CIMD_TIMEOUT_SECONDS", TRICKLE_BUDGET)
    monkeypatch.setattr(auth_provider, "_public_addresses", vetted)
    monkeypatch.setattr(socket, "create_connection", REAL_CREATE_CONNECTION)
    monkeypatch.setattr(socket, "getaddrinfo", loopback_only)
    monkeypatch.setattr(ssl, "create_default_context", lambda: server.client_tls)
    try:
        yield server
    finally:
        server.close()


@pytest.mark.parametrize("trickling_server", ["prompt"], indirect=True)
def test_loopback_metadata_document_server_is_fetched_when_prompt(trickling_server):
    fetched = auth_provider.fetch_metadata_document(trickling_server.url)
    assert fetched["client_id"] == trickling_server.url


@pytest.mark.parametrize("trickling_server", ["headers", "body"], indirect=True)
def test_trickled_metadata_document_cannot_extend_the_time_budget(trickling_server):
    trickled_seconds = len(trickling_server.trickled) * TRICKLE_INTERVAL
    assert trickled_seconds > 4 * (TRICKLE_BUDGET + TRICKLE_MARGIN)
    started = time.monotonic()
    with pytest.raises(ValueError, match="took too long"):
        auth_provider.fetch_metadata_document(trickling_server.url)
    assert time.monotonic() - started < TRICKLE_BUDGET + TRICKLE_MARGIN


def test_metadata_document_resolution_counts_toward_the_time_budget(cimd_env, monkeypatch):
    released = threading.Event()
    monkeypatch.setattr(auth_provider, "CIMD_TIMEOUT_SECONDS", TRICKLE_BUDGET)
    monkeypatch.setattr(auth_provider, "_public_addresses", lambda host, port: released.wait(30) and [PUBLIC_V4])
    calls = serve_document(monkeypatch, body=document())
    started = time.monotonic()
    try:
        with pytest.raises(ValueError, match="took too long"):
            auth_provider.fetch_metadata_document(CHATGPT_CLIENT)
        elapsed = time.monotonic() - started
    finally:
        released.set()
    assert elapsed < TRICKLE_BUDGET + TRICKLE_MARGIN
    assert calls == [], "No connection is attempted after the budget is spent resolving"


# F7: the allowlist is part of runtime validation


def production_runtime(patch, allowlist):
    production_like(patch)
    for name, value in {
        "WISDOMTWIN_USE_FIXTURES": "0", "WISDOMTWIN_AUTH_DISABLED": "0",
        "DATABASE_URL": "postgresql://synthetic@192.0.2.10/wisdomtwin", "REDIS_URL": "redis://192.0.2.10:6379/0",
        "OAUTH_CLIENT_ID": "synthetic-predefined-client", "OAUTH_REDIRECT_URIS": CHATGPT_REDIRECT,
        "OAUTH_CIMD_CLIENT_IDS": allowlist,
    }.items():
        patch.setenv(name, value)


@pytest.mark.parametrize("value", MALFORMED_ALLOWLISTS)
def test_runtime_validation_rejects_a_malformed_metadata_document_allowlist(monkeypatch, value):
    production_runtime(monkeypatch, CHATGPT_CLIENT)
    runtime.validate_runtime()
    monkeypatch.setenv("OAUTH_CIMD_CLIENT_IDS", value)
    with pytest.raises(RuntimeError, match="OAUTH_CIMD_CLIENT_IDS"):
        runtime.validate_runtime()


@pytest.mark.parametrize("allowlist,accepted", [(CHATGPT_CLIENT, True), ("", True),
                                                ("http://chatgpt.com/oauth/client.json", False)])
def test_deploy_check_validates_the_metadata_document_allowlist(tmp_path, allowlist, accepted):
    # --check exits before any Railway command; synthetic values only, nothing is contacted.
    env = {"PATH": f"{Path(sys.executable).parent}:/usr/bin:/bin", "HOME": str(tmp_path), "TMPDIR": str(tmp_path),
           "PUBLIC_BASE_URL": PUBLIC, "DATABASE_URL": "postgresql://synthetic@192.0.2.10/wisdomtwin",
           "REDIS_URL": "redis://192.0.2.10:6379/0", "CONNECTOR_TOKEN_KEY": "synthetic-connector-token-key",
           "OAUTH_CLIENT_ID": "synthetic-predefined-client", "OAUTH_REDIRECT_URIS": CHATGPT_REDIRECT,
           "OIDC_ISSUER": ISSUER, "OIDC_CLIENT_ID": OIDC_CLIENT, "OAUTH_CIMD_CLIENT_IDS": allowlist}
    result = subprocess.run(["/bin/bash", "deploy.sh", "--check"], cwd=Path(auth_provider.__file__).parent,
                            env=env, capture_output=True, text=True, timeout=120)
    if accepted:
        assert result.returncode == 0, result.stderr
        assert "No deployment performed" in result.stdout
    else:
        assert result.returncode != 0
        assert "OAUTH_CIMD_CLIENT_IDS must list exact HTTPS client metadata document URLs" in result.stderr


# M1: production Host and Origin validation


def test_production_transport_settings_follow_the_public_origin(monkeypatch):
    import server

    production_like(monkeypatch)
    settings = server.transport_security()
    assert settings.enable_dns_rebinding_protection is True
    assert settings.allowed_hosts == ["twin.example.test", "twin.example.test:*"]
    assert settings.allowed_origins == [PUBLIC, "https://chatgpt.com", "https://chat.openai.com"]
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://twin.example.test:8443")
    assert server.transport_security().allowed_origins[0] == "https://twin.example.test:8443"
    monkeypatch.setenv("WISDOMTWIN_ENV", "test")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.delenv("PUBLIC_BASE_URL")
    assert server.transport_security() is None


@pytest.mark.parametrize("headers,status", [
    ({}, 200),
    ({"Origin": "https://chatgpt.com"}, 200),
    ({"Origin": "https://chat.openai.com"}, 200),
    ({"Origin": PUBLIC}, 200),
    ({"Host": "twin.example.test:443"}, 200),
    ({"Origin": "https://attacker.test"}, 403),
    ({"Origin": "https://chatgpt.com.attacker.test"}, 403),
    ({"Origin": "http://chatgpt.com"}, 403),
    ({"Origin": "null"}, 403),
    ({"Host": "attacker.test"}, 421),
    ({"Host": "twin.example.test.attacker.test"}, 421),
])
def test_production_mcp_endpoint_validates_host_and_origin(fixture_server, headers, status):
    server, scoped = fixture_server
    production_like(scoped)
    with TestClient(server.http_app(), base_url=PUBLIC) as http:
        response = http.post("/mcp", json=TOOLS_LIST, headers={**MCP_HEADERS, **headers})
    assert response.status_code == status
    if status == 200:
        assert len(response.json()["result"]["tools"]) == 4


def test_production_origin_and_host_are_checked_before_bearer_authentication(auth_server):
    server, scoped = auth_server
    provider = server._auth_provider
    # The SQLite test store exists only in loopback test mode, so pin it before leaving that mode.
    scoped.setattr(provider, "repository", security_store())
    token = mint_access_token(provider, provision())
    production_like(scoped)
    bearer = {**MCP_HEADERS, "Authorization": f"Bearer {token}"}
    with TestClient(server.http_app(), base_url=PUBLIC) as http:
        anonymous = http.post("/mcp", json=TOOLS_LIST, headers=MCP_HEADERS)
        anonymous_foreign = http.post("/mcp", json=TOOLS_LIST, headers={**MCP_HEADERS, "Origin": "https://attacker.test"})
        anonymous_wrong_host = http.post("/mcp", json=TOOLS_LIST, headers={**MCP_HEADERS, "Host": "attacker.test"})
        chatgpt = http.post("/mcp", json=TOOLS_LIST, headers={**bearer, "Origin": "https://chatgpt.com"})
        server_to_server = http.post("/mcp", json=TOOLS_LIST, headers=bearer)
        foreign = http.post("/mcp", json=TOOLS_LIST, headers={**bearer, "Origin": "https://attacker.test"})
    assert anonymous.status_code == 401
    assert "resource_metadata" in anonymous.headers["www-authenticate"]
    assert anonymous_foreign.status_code == 403
    assert anonymous_wrong_host.status_code == 421
    assert chatgpt.status_code == server_to_server.status_code == 200
    assert foreign.status_code == 403


def test_local_mode_keeps_the_sdk_loopback_protection(fixture_server):
    server, _ = fixture_server
    assert server.transport_security() is None
    with TestClient(server.http_app(), base_url=BASE) as http:
        assert http.post("/mcp", json=TOOLS_LIST, headers=MCP_HEADERS).status_code == 200
        assert http.post("/mcp", json=TOOLS_LIST, headers={**MCP_HEADERS, "Origin": "https://attacker.test"}).status_code == 403


def test_main_serves_the_guarded_app(fixture_server):
    import uvicorn

    server, scoped = fixture_server
    served = {}
    scoped.setattr(uvicorn, "run", lambda app, **options: served.update(app=app, **options))
    scoped.setattr(server, "validate_runtime", lambda: None)
    production_like(scoped)
    scoped.setenv("PORT", "8123")
    server.main()
    assert served["host"] == "0.0.0.0"
    assert served["port"] == 8123
    with TestClient(served["app"], base_url=PUBLIC) as http:
        assert http.post("/mcp", json=TOOLS_LIST, headers={**MCP_HEADERS, "Origin": "https://attacker.test"}).status_code == 403
        assert http.post("/mcp", json=TOOLS_LIST, headers={**MCP_HEADERS, "Host": "attacker.test"}).status_code == 421
        assert http.post("/mcp", json=TOOLS_LIST, headers=MCP_HEADERS).status_code == 200


# M2: blocking provider calls run in worker threads


class SyntheticIdentityProvider:
    def __init__(self):
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        jwk = json.loads(RSAAlgorithm.to_jwk(self.key.public_key()))
        jwk.update(kid="synthetic-signing-key", alg="RS256", use="sig")
        self.jwks = {"keys": [jwk]}
        self.metadata = {"issuer": ISSUER, "authorization_endpoint": f"{ISSUER}/authorize",
                         "token_endpoint": f"{ISSUER}/token", "jwks_uri": f"{ISSUER}/jwks"}
        self.nonce = ""
        self.callers = []

    def request(self, url, *, body=None, token=None):
        self.callers.append(threading.get_ident())
        if url == f"{ISSUER}/.well-known/openid-configuration":
            return self.metadata
        if url == self.metadata["jwks_uri"]:
            return self.jwks
        assert url == self.metadata["token_endpoint"] and body["code"] == "synthetic-provider-code"
        claims = {"iss": ISSUER, "sub": "alice", "aud": OIDC_CLIENT, "iat": int(time.time()),
                  "exp": int(time.time()) + 300, "nonce": self.nonce,
                  "email": "alice@example-corp.com", "email_verified": True}
        return {"id_token": jwt.encode(claims, self.key, algorithm="RS256", headers={"kid": "synthetic-signing-key"})}


def test_corporate_login_network_calls_run_off_the_event_loop(auth_server, monkeypatch):
    import corporate_login

    server, scoped = auth_server
    scoped.setenv("OIDC_ISSUER", ISSUER)
    scoped.setenv("OIDC_CLIENT_ID", OIDC_CLIENT)
    identity = SyntheticIdentityProvider()
    monkeypatch.setattr(corporate_login, "request_json", identity.request)
    provision()
    app = LoopThreads(server.http_app())
    _, challenge = new_pkce()
    with TestClient(app, base_url=BASE, follow_redirects=False) as http:
        consent_uri = http.get("/authorize", params=authorize_params("wisdomtwin-local", CALLBACK, challenge)).headers["location"]
        login = http.get(consent_uri)
        assert login.status_code == 302
        sign_in = parse_qs(urlsplit(login.headers["location"]).query)
        identity.nonce = sign_in["nonce"][0]
        callback = http.get("/oauth/callback/identity", params={"state": sign_in["state"][0], "code": "synthetic-provider-code"})
        assert callback.status_code == 302
        assert http.get(consent_uri).status_code == 200
    assert len(identity.callers) == 4
    assert app.idents and not app.idents & set(identity.callers)


@pytest.fixture
def connected_role():
    def connect(service):
        subject = provision()
        context = actor_subject.set(subject)
        try:
            member = security_store().membership(subject)
            org = current_store().upsert_organization(member["domain"])
            role = current_store().create_role(org.id, "CRO")
            current_store().record_connection(role.id, service, member["domain"], "CRO")
        finally:
            actor_subject.reset(context)
        pending = {"subject": subject, "role_id": role.id, "domain": member["domain"], "role_title": "CRO",
                   "service": service, "verifier": "synthetic-verifier"}
        current_store().save_secret(f"synthetic-{service}-state", pending)
        return pending

    return connect


def test_slack_callback_network_calls_run_off_the_event_loop(fixture_server, connected_role, monkeypatch):
    import provider_binding

    server, _ = fixture_server
    pending = connected_role("slack")
    seen = []

    def exchange(url, body):
        seen.append(("exchange", threading.get_ident(), actor_subject.get()))
        return {"ok": True, "team": {"id": "TEAM_A"}, "authed_user": {
            "id": "USER_A", "access_token": "synthetic-slack-token", "scope": ",".join(SLACK_USER_SCOPES)}}

    def identity(url, *, token):
        seen.append(("identity", threading.get_ident(), actor_subject.get()))
        if url == "https://slack.com/api/auth.test":
            return {"ok": True, "team_id": "TEAM_A", "user_id": "USER_A"}
        return {"ok": True, "user": {"id": "USER_A", "profile": {"email": "alice@example-corp.com"}}}

    monkeypatch.setattr(server, "_exchange_code", exchange)
    monkeypatch.setattr(provider_binding, "request_json", identity)
    app = LoopThreads(server.http_app())
    with TestClient(app, base_url=BASE) as http:
        response = http.get("/oauth/callback/slack", params={"code": "synthetic-code", "state": "synthetic-slack-state"})
    assert response.status_code == 200
    assert [step for step, _, _ in seen] == ["exchange", "identity", "identity"]
    assert app.idents and not app.idents & {ident for _, ident, _ in seen}
    assert {actor for _, _, actor in seen} == {pending["subject"]}
    context = actor_subject.set(pending["subject"])
    try:
        assert current_store().get_credential(pending["role_id"], "slack")
    finally:
        actor_subject.reset(context)


def test_google_callback_network_calls_run_off_the_event_loop(fixture_server, connected_role, monkeypatch):
    import provider_binding

    server, scoped = fixture_server
    # Mocked callback only: no Google request leaves the process.
    scoped.setenv("GMAIL_CONNECTOR_ENABLED", "true")
    scoped.setenv("GOOGLE_REVIEW_APPROVED", "true")
    pending = connected_role("gmail")
    seen = []

    def exchange(url, body):
        seen.append(("exchange", threading.get_ident(), actor_subject.get()))
        return {"access_token": "synthetic-google-token", "scope": f"openid email {GMAIL_SCOPE}"}

    def identity(url, *, token):
        seen.append(("identity", threading.get_ident(), actor_subject.get()))
        return {"sub": "GOOGLE_A", "email": "alice@example-corp.com", "email_verified": True}

    monkeypatch.setattr(server, "_exchange_code", exchange)
    monkeypatch.setattr(provider_binding, "request_json", identity)
    app = LoopThreads(server.http_app())
    with TestClient(app, base_url=BASE) as http:
        response = http.get("/oauth/callback/google", params={"code": "synthetic-code", "state": "synthetic-gmail-state"})
    assert response.status_code == 200
    assert [step for step, _, _ in seen] == ["exchange", "identity"]
    assert app.idents and not app.idents & {ident for _, ident, _ in seen}
    assert {actor for _, _, actor in seen} == {pending["subject"]}
