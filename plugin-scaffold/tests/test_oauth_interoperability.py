"""Current public-client discovery and conditional RFC 9207 response contract.

OpenAI supports predefined clients; neither DCR nor issuer-identification support
is unconditionally required. Advertising a capability must match actual behavior.
All authentication and HTTP requests below use synthetic local state only.
"""

import importlib
import secrets
import uuid
from urllib.parse import parse_qs, urlsplit

import anyio
import pytest
from starlette.testclient import TestClient

from oauth_connectors import new_pkce, public_base_url


BASE = "http://127.0.0.1:8000"
CLIENT_ID = "synthetic-predefined-plugin-client"
CALLBACK = f"{BASE}/oauth/done"
STATE = "synthetic client + unicode δ"


def run(fn, *args):
    async def call():
        return await fn(*args)

    return anyio.run(call)


@pytest.fixture
def authenticated_http(monkeypatch):
    import server

    with monkeypatch.context() as scoped:
        scoped.setenv("WISDOMTWIN_AUTH_DISABLED", "0")
        scoped.setenv("PUBLIC_BASE_URL", BASE)
        scoped.setenv("OAUTH_CLIENT_ID", CLIENT_ID)
        scoped.setenv("OAUTH_REDIRECT_URIS", CALLBACK)
        scoped.setattr("urllib.request.urlopen", lambda *a, **k: pytest.fail("OAuth interoperability tests must remain offline"))
        importlib.reload(server)
        with TestClient(server.mcp.streamable_http_app(json_response=True, stateless_http=True),
                        base_url=BASE, follow_redirects=False) as http:
            yield server, http
    importlib.reload(server)


def metadata(http):
    response = http.get("/.well-known/oauth-authorization-server")
    assert response.status_code == 200
    return response.json()


def authorization_params():
    verifier, challenge = new_pkce()
    return verifier, {
        "client_id": CLIENT_ID, "response_type": "code", "redirect_uri": CALLBACK,
        "state": STATE, "scope": "twin:read", "resource": f"{BASE}/mcp",
        "code_challenge": challenge, "code_challenge_method": "S256",
    }


def approved_callback(module, http, params):
    response = http.get("/authorize", params=params)
    assert response.status_code == 302
    transaction = parse_qs(urlsplit(response.headers["location"]).query)["txn"][0]
    repository = module._auth_provider.db
    subject = repository.provision(
        issuer="https://synthetic-interoperability-idp.test", provider_subject=uuid.uuid4().hex,
        email="reviewer@example-corp.com", domain="example-corp.com", roles=["CRO"],
    )
    session, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    epoch = repository.subject_epoch(subject)
    repository.put_subject_entry("session", session, {
        "subject": subject, "email": "reviewer@example-corp.com", "transaction": transaction,
        "csrf": csrf, "subject_epoch": epoch,
    }, 300, subject=subject, expected_epoch=epoch)
    http.cookies.set(module.SESSION_COOKIE, session, domain="127.0.0.1", path="/oauth")
    response = http.post("/oauth/consent", data={"txn": transaction, "csrf": csrf}, headers={"Origin": BASE})
    assert response.status_code == 302
    callback = urlsplit(response.headers["location"])
    assert f"{callback.scheme}://{callback.netloc}{callback.path}" == CALLBACK
    return parse_qs(callback.query)


@pytest.mark.parametrize("field", ["token_endpoint_auth_methods_supported", "revocation_endpoint_auth_methods_supported"])
def test_discovery_advertises_the_configured_public_client_method(authenticated_http, field):
    module, http = authenticated_http
    client = run(module._auth_provider.get_client, CLIENT_ID)
    assert client.token_endpoint_auth_method == "none"
    assert client.client_secret is None
    advertised = metadata(http)
    # Only predefined public clients are configured; secret methods are neither
    # needed nor useful to advertise for this server's current registration policy.
    assert advertised[field] == ["none"]


def test_discovery_keeps_the_configured_canonical_issuer_for_release(authenticated_http):
    _, http = authenticated_http
    advertised = metadata(http)
    protected = http.get("/.well-known/oauth-protected-resource/mcp").json()
    # package_validator's real release gate compares the exact configured origin.
    # Root-slash issuers are otherwise legal; this assertion is our app contract.
    assert advertised["issuer"] == public_base_url()
    assert protected["authorization_servers"] == [advertised["issuer"]]
    assert protected["resource"] == f"{BASE}/mcp"
    assert "S256" in advertised["code_challenge_methods_supported"]


def test_discovery_advertises_the_scope_required_by_the_existing_release_gate(authenticated_http):
    _, http = authenticated_http
    advertised = metadata(http)
    # AS scopes_supported is optional in RFC 8414, but the existing app release
    # gate explicitly requires this supported scope and production must satisfy it.
    assert advertised.get("scopes_supported") == ["twin:read"]


def test_predefined_client_completes_pkce_without_dynamic_registration(authenticated_http):
    module, http = authenticated_http
    advertised = metadata(http)
    assert not advertised.get("registration_endpoint")
    assert not advertised.get("client_id_metadata_document_supported")
    assert http.post("/register", json={"redirect_uris": [CALLBACK]}).status_code == 404
    verifier, params = authorization_params()
    callback = approved_callback(module, http, params)
    assert callback["state"] == [STATE]
    response = http.post("/token", data={
        "grant_type": "authorization_code", "client_id": CLIENT_ID,
        "redirect_uri": CALLBACK, "code": callback["code"][0],
        "code_verifier": verifier, "resource": f"{BASE}/mcp",
    })
    assert response.status_code == 200, response.text
    assert run(module._auth_provider.load_access_token, response.json()["access_token"]) is not None


def assert_issuer_contract(advertised, response_params):
    support = advertised.get("authorization_response_iss_parameter_supported") is True
    if support:
        assert response_params.get("iss") == [advertised["issuer"]]
    elif "iss" in response_params:
        # Present issuer identifiers always require exact matching. A server that
        # implements RFC 9207 must also advertise the capability truthfully.
        assert response_params["iss"] == [advertised["issuer"]]
        assert support
    # Missing support and missing iss is a supported callback-ID-specific mode;
    # it is not an unconditional failure under current OpenAI/MCP requirements.


def test_authorization_success_matches_advertised_issuer_support(authenticated_http):
    module, http = authenticated_http
    _, params = authorization_params()
    callback = approved_callback(module, http, params)
    assert callback["state"] == [STATE]
    assert callback.get("code")
    assert_issuer_contract(metadata(http), callback)


@pytest.mark.parametrize("invalid", ["scope", "resource", "response_type"])
def test_sdk_authorization_error_matches_advertised_issuer_support(authenticated_http, invalid):
    _, http = authenticated_http
    _, params = authorization_params()
    params[invalid] = {"scope": "unsupported:scope", "resource": "https://another-synthetic-resource.test/mcp",
                       "response_type": "token"}[invalid]
    response = http.get("/authorize", params=params)
    assert response.status_code == 302
    callback = urlsplit(response.headers["location"])
    assert f"{callback.scheme}://{callback.netloc}{callback.path}" == CALLBACK
    response_params = parse_qs(callback.query)
    assert response_params.get("error")
    assert response_params["state"] == [STATE]
    assert "code" not in response_params
    assert_issuer_contract(metadata(http), response_params)


def test_unknown_client_error_never_redirects_to_an_unregistered_callback(authenticated_http):
    _, http = authenticated_http
    _, params = authorization_params()
    params.update(client_id="unknown-synthetic-client", redirect_uri="https://unregistered-synthetic-client.test/callback")
    response = http.get("/authorize", params=params)
    assert response.status_code == 400
    assert "location" not in response.headers
    body = response.json()
    assert body.get("error")
    assert body["state"] == STATE
    assert_issuer_contract(metadata(http), {key: [value] for key, value in body.items()})
