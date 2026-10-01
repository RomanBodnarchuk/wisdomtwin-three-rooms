"""Offline signed login, SDK token checks, and durable revocation regressions."""

import base64
import hashlib
import importlib
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs, urlsplit

import anyio
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm
from mcp.server.auth.provider import AuthorizationParams, TokenError
from pydantic import AnyUrl
from starlette.testclient import TestClient

from auth_provider import WisdomTwinAuthProvider
from oauth_connectors import GMAIL_SCOPE, SLACK_USER_SCOPES, new_pkce
from security_store import security_store
from store import actor_subject, current_store


BASE = "http://127.0.0.1:8000"
ISSUER = "https://identity.synthetic.test"
OIDC_CLIENT = "synthetic-corporate-client"
CALLBACK = f"{BASE}/oauth/done"


def run(fn, *args, **kwargs):
    async def call():
        return await fn(*args, **kwargs)

    return anyio.run(call)


def provision():
    return security_store().provision(
        issuer=ISSUER, provider_subject="alice", email="alice@example-corp.com",
        domain="example-corp.com", roles=["CRO"], slack_team_id="TEAM_A",
        slack_user_id="USER_A", google_subject="GOOGLE_A",
    )


class SyntheticOIDC:
    def __init__(self):
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        jwk = json.loads(RSAAlgorithm.to_jwk(self.key.public_key()))
        jwk.update(kid="synthetic-signing-key", alg="RS256", use="sig")
        self.jwks = {"keys": [jwk]}
        self.metadata = {
            "issuer": ISSUER,
            "authorization_endpoint": f"{ISSUER}/authorize",
            "token_endpoint": f"{ISSUER}/token",
            "jwks_uri": f"{ISSUER}/jwks",
        }
        self.login = {}
        self.overrides = {}
        self.token_exchanges = 0

    def request(self, url, *, body=None, token=None):
        assert token is None
        if url == f"{ISSUER}/.well-known/openid-configuration":
            return self.metadata
        if url == self.metadata["jwks_uri"]:
            return self.jwks
        assert url == self.metadata["token_endpoint"]
        assert body["grant_type"] == "authorization_code"
        assert body["client_id"] == OIDC_CLIENT
        assert body["code"] == "synthetic-provider-code"
        assert body["redirect_uri"] == f"{BASE}/oauth/callback/identity"
        challenge = base64.urlsafe_b64encode(hashlib.sha256(body["code_verifier"].encode()).digest()).decode().rstrip("=")
        assert challenge == self.login["code_challenge"][0]
        self.token_exchanges += 1
        claims = {
            "iss": ISSUER, "sub": "alice", "aud": OIDC_CLIENT,
            "iat": int(time.time()), "exp": int(time.time()) + 300,
            "nonce": self.login["nonce"][0], "email": "alice@example-corp.com",
            "email_verified": True,
        }
        claims.update(self.overrides)
        return {"id_token": jwt.encode(claims, self.key, algorithm="RS256", headers={"kid": "synthetic-signing-key"})}


@pytest.fixture
def oidc_http(monkeypatch):
    import corporate_login
    import server

    fake = SyntheticOIDC()
    with monkeypatch.context() as scoped:
        scoped.setenv("WISDOMTWIN_AUTH_DISABLED", "0")
        scoped.setenv("OIDC_ISSUER", ISSUER)
        scoped.setenv("OIDC_CLIENT_ID", OIDC_CLIENT)
        scoped.setenv("OIDC_CLIENT_SECRET", "synthetic-unused-secret")
        scoped.setattr(corporate_login, "request_json", fake.request)
        scoped.setattr("urllib.request.urlopen", lambda *a, **k: pytest.fail("Auth review must remain offline"))
        importlib.reload(server)
        with TestClient(server.mcp.streamable_http_app(json_response=True, stateless_http=True),
                        base_url=BASE, follow_redirects=False) as http:
            yield server, http, fake
    importlib.reload(server)


def begin_login(http, fake):
    verifier, challenge = new_pkce()
    response = http.get("/authorize", params={
        "response_type": "code", "client_id": "wisdomtwin-local",
        "redirect_uri": CALLBACK, "scope": "twin:read", "state": "synthetic-client-state",
        "code_challenge": challenge, "code_challenge_method": "S256", "resource": f"{BASE}/mcp",
    })
    assert response.status_code == 302
    consent_uri = response.headers["location"]
    response = http.get(consent_uri)
    assert response.status_code == 302
    fake.login = parse_qs(urlsplit(response.headers["location"]).query)
    assert fake.login["scope"] == ["openid email"]
    assert fake.login["code_challenge_method"] == ["S256"]
    return consent_uri, verifier


def complete_login(http, fake, consent_uri):
    response = http.get("/oauth/callback/identity", params={
        "state": fake.login["state"][0], "code": "synthetic-provider-code",
    })
    assert response.status_code == 302
    response = http.get(consent_uri)
    assert response.status_code == 200
    csrf = re.search(r'name="csrf" value="([^"]+)"', response.text).group(1)
    transaction = parse_qs(urlsplit(consent_uri).query)["txn"][0]
    response = http.post("/oauth/consent", headers={"Origin": BASE}, data={"txn": transaction, "csrf": csrf})
    assert response.status_code == 302
    callback = parse_qs(urlsplit(response.headers["location"]).query)
    assert callback["state"] == ["synthetic-client-state"]
    return callback["code"][0]


def exchange_body(code, verifier):
    return {
        "grant_type": "authorization_code", "client_id": "wisdomtwin-local",
        "code": code, "redirect_uri": CALLBACK, "code_verifier": verifier,
    }


def test_signed_oidc_consent_and_actual_sdk_pkce_flow(oidc_http):
    module, http, fake = oidc_http
    subject = provision()
    consent_uri, verifier = begin_login(http, fake)
    code = complete_login(http, fake, consent_uri)
    body = exchange_body(code, verifier)

    wrong_verifier = http.post("/token", data={**body, "code_verifier": "wrong-verifier"})
    assert wrong_verifier.status_code == 400
    assert wrong_verifier.json()["error"] == "invalid_grant"
    wrong_redirect = http.post("/token", data={**body, "redirect_uri": "https://substituted.synthetic.test/callback"})
    assert wrong_redirect.status_code == 400
    response = http.post("/token", data=body)
    assert response.status_code == 200
    tokens = response.json()
    assert run(module._auth_provider.load_access_token, tokens["access_token"]).subject == subject
    assert fake.token_exchanges == 1
    assert http.post("/token", data=body).status_code == 400
    replay = http.get("/oauth/callback/identity", params={
        "state": fake.login["state"][0], "code": "synthetic-provider-code",
    })
    assert replay.status_code == 400
    assert fake.token_exchanges == 1


def test_oidc_callback_requires_original_browser_cookie(oidc_http):
    _, http, fake = oidc_http
    provision()
    begin_login(http, fake)
    http.cookies.clear()
    response = http.get("/oauth/callback/identity", params={
        "state": fake.login["state"][0], "code": "synthetic-provider-code",
    })
    assert response.status_code == 400
    assert fake.token_exchanges == 0
    assert not http.cookies.get("wisdomtwin_consent")


@pytest.mark.parametrize("overrides", [
    {"nonce": "substituted-nonce"}, {"aud": "another-client"},
    {"sub": "unprovisioned-user"}, {"email": "alice@another-business.test"},
])
def test_signed_callback_substitution_cannot_create_consent(oidc_http, overrides):
    _, http, fake = oidc_http
    provision()
    begin_login(http, fake)
    fake.overrides = overrides
    response = http.get("/oauth/callback/identity", params={
        "state": fake.login["state"][0], "code": "synthetic-provider-code",
    })
    assert response.status_code == 400
    assert not http.cookies.get("wisdomtwin_consent")


@pytest.mark.parametrize("token_type", ["access_token", "refresh_token"])
def test_http_revocation_is_advertised_and_revokes_rotated_family(oidc_http, token_type):
    module, http, fake = oidc_http
    provision()
    consent_uri, verifier = begin_login(http, fake)
    code = complete_login(http, fake, consent_uri)
    initial = http.post("/token", data=exchange_body(code, verifier)).json()
    rotated_response = http.post("/token", data={
        "grant_type": "refresh_token", "client_id": "wisdomtwin-local",
        "refresh_token": initial["refresh_token"],
    })
    assert rotated_response.status_code == 200
    rotated = rotated_response.json()
    response = http.post("/revoke", data={
        "client_id": "wisdomtwin-local", "token": rotated[token_type], "token_type_hint": token_type,
    })
    assert response.status_code == 200
    metadata = http.get("/.well-known/oauth-authorization-server").json()
    assert metadata["revocation_endpoint"] == f"{BASE}/revoke"
    assert run(module._auth_provider.load_access_token, initial["access_token"]) is None
    assert run(module._auth_provider.load_access_token, rotated["access_token"]) is None
    client = run(module._auth_provider.get_client, "wisdomtwin-local")
    assert run(module._auth_provider.load_refresh_token, client, rotated["refresh_token"]) is None


def grant(provider, subject):
    client = run(provider.get_client, "wisdomtwin-local")
    _, challenge = new_pkce()
    params = AuthorizationParams(
        state="synthetic-state", scopes=["twin:read"], code_challenge=challenge,
        redirect_uri=AnyUrl(CALLBACK), redirect_uri_provided_explicitly=True, resource=f"{BASE}/mcp",
    )
    transaction = parse_qs(urlsplit(run(provider.authorize, client, params)).query)["txn"][0]
    provider.db.put("session", "synthetic-race-session", {
        "transaction": transaction, "subject": subject, "email": "alice@example-corp.com", "csrf": "synthetic-csrf",
    }, 300, subject=subject)
    callback = provider.approve(transaction, session_key="synthetic-race-session", csrf="synthetic-csrf")
    code = run(provider.load_authorization_code, client, parse_qs(urlsplit(callback).query)["code"][0])
    return client, code


@pytest.mark.parametrize("revoke_kind", ["refresh", "access"])
def test_revocation_during_refresh_cannot_leave_successors_valid(monkeypatch, revoke_kind):
    subject = provision()
    provider = WisdomTwinAuthProvider(security_store())
    client, code = grant(provider, subject)
    initial = run(provider.exchange_authorization_code, client, code)
    refresh = run(provider.load_refresh_token, client, initial.refresh_token)
    revoke_target = refresh if revoke_kind == "refresh" else run(provider.load_access_token, initial.access_token)
    issue_started, continue_issue = threading.Event(), threading.Event()
    original_issue = provider._issue

    def paused_issue(*args, **kwargs):
        issue_started.set()
        assert continue_issue.wait(5), "Synthetic revocation race was not released"
        return original_issue(*args, **kwargs)

    monkeypatch.setattr(provider, "_issue", paused_issue)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run, provider.exchange_refresh_token, client, refresh, ["twin:read"])
        try:
            assert issue_started.wait(5), "Synthetic refresh did not consume its token"
            run(provider.revoke_token, revoke_target)
        finally:
            continue_issue.set()
        rotated = future.result(timeout=5)
    assert run(provider.load_access_token, initial.access_token) is None
    assert run(provider.load_access_token, rotated.access_token) is None
    assert run(provider.load_refresh_token, client, rotated.refresh_token) is None


@pytest.mark.parametrize("grant_type", ["code", "refresh"])
def test_one_use_grants_allow_only_one_concurrent_exchange(grant_type):
    subject = provision()
    provider = WisdomTwinAuthProvider(security_store())
    client, code = grant(provider, subject)
    if grant_type == "code":
        exchange, args = provider.exchange_authorization_code, (client, code)
    else:
        initial = run(provider.exchange_authorization_code, client, code)
        refresh = run(provider.load_refresh_token, client, initial.refresh_token)
        exchange, args = provider.exchange_refresh_token, (client, refresh, ["twin:read"])
    barrier = threading.Barrier(2)

    def competing_exchange():
        barrier.wait(timeout=5)
        try:
            return run(exchange, *args)
        except TokenError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(competing_exchange) for _ in range(2)]
        results = [future.result(timeout=10) for future in futures]
    assert sum(isinstance(result, TokenError) for result in results) == 1
    assert sum(hasattr(result, "access_token") for result in results) == 1


@pytest.fixture
def connector_member(monkeypatch):
    monkeypatch.setenv("WISDOMTWIN_AUTH_DISABLED", "0")
    subject = provision()
    context = actor_subject.set(subject)
    try:
        member = security_store().membership(subject)
        org = current_store().upsert_organization(member["domain"])
        role = current_store().create_role(org.id, "CRO")
        current_store().record_connection(role.id, "slack", member["domain"], "CRO")
        pending = {"subject": subject, "role_id": role.id, "domain": member["domain"],
                   "role_title": "CRO", "service": "slack"}
        yield pending, member
    finally:
        actor_subject.reset(context)


def slack_body(scope=None):
    return {"ok": True, "team": {"id": "TEAM_A"}, "authed_user": {
        "id": "USER_A", "access_token": "synthetic-slack-token",
        "scope": ",".join(scope or SLACK_USER_SCOPES),
    }}


def fake_slack_identity(url, *, token):
    assert token == "synthetic-slack-token"
    if url == "https://slack.com/api/auth.test":
        return {"ok": True, "team_id": "TEAM_A", "user_id": "USER_A"}
    assert url.startswith("https://slack.com/api/users.info?")
    return {"ok": True, "user": {"id": "USER_A", "profile": {"email": "alice@example-corp.com"}}}


def test_slack_pkce_callback_omits_client_secret(connector_member, monkeypatch):
    import server
    import provider_binding
    from starlette.testclient import TestClient

    pending, _ = connector_member
    exchanges = []
    monkeypatch.setenv("SLACK_CLIENT_SECRET", "synthetic-secret-must-not-be-sent")
    monkeypatch.setattr(provider_binding, "request_json", fake_slack_identity)

    def exchange(url, body):
        assert url == "https://slack.com/api/oauth.v2.access"
        exchanges.append(body)
        return slack_body()

    monkeypatch.setattr(server, "_exchange_code", exchange)
    current_store().save_secret("synthetic-pkce-state", {**pending, "verifier": "synthetic-verifier"})
    with TestClient(server.mcp.streamable_http_app(json_response=True, stateless_http=True), base_url="http://127.0.0.1:8000") as client:
        callback = "/oauth/callback/slack?code=synthetic-code&state=synthetic-pkce-state"
        assert client.get(callback).status_code == 200
        assert client.get(callback).status_code == 400
    assert len(exchanges) == 1
    assert exchanges[0]["code_verifier"] == "synthetic-verifier"
    assert "client_secret" not in exchanges[0]


@pytest.mark.parametrize("substitution", ["team", "user", "token", "email"])
def test_slack_callback_identity_substitution_does_not_store_grant(connector_member, monkeypatch, substitution):
    import provider_binding

    pending, member = connector_member
    body = slack_body()
    if substitution == "team":
        body["team"]["id"] = "TEAM_B"
    elif substitution == "user":
        body["authed_user"]["id"] = "USER_B"

    def request(url, *, token):
        result = fake_slack_identity(url, token=token)
        if substitution == "token" and url.endswith("auth.test"):
            result["user_id"] = "USER_B"
        if substitution == "email" and "users.info" in url:
            result["user"]["profile"]["email"] = "bob@example-corp.com"
        return result

    monkeypatch.setattr(provider_binding, "request_json", request)
    with pytest.raises(ValueError):
        provider_binding.bind_slack(pending, member, body)
    assert current_store().get_credential(pending["role_id"], "slack") is None


def test_slack_write_scope_cannot_be_stored_as_read_only_grant(connector_member, monkeypatch):
    import provider_binding

    pending, member = connector_member
    monkeypatch.setattr(provider_binding, "request_json", fake_slack_identity)
    with pytest.raises(ValueError):
        provider_binding.bind_slack(pending, member, slack_body([*SLACK_USER_SCOPES, "chat:write"]))
    assert current_store().get_credential(pending["role_id"], "slack") is None


def test_google_write_scope_cannot_be_stored_as_read_only_grant(connector_member, monkeypatch):
    import provider_binding

    pending, member = connector_member
    pending = {**pending, "service": "gmail"}
    monkeypatch.setattr(provider_binding, "request_json", lambda *a, **k: {
        "sub": "GOOGLE_A", "email": member["email"], "email_verified": True,
    })
    with pytest.raises(ValueError):
        provider_binding.bind_google(pending, member, {
            "access_token": "synthetic-google-token",
            "scope": f"openid email {GMAIL_SCOPE} https://www.googleapis.com/auth/gmail.modify",
        })
    assert current_store().get_credential(pending["role_id"], "gmail") is None


def test_callback_keeps_original_subject_and_restores_request_actor(connector_member, monkeypatch):
    import provider_binding

    pending, member = connector_member
    current_store().save_secret("synthetic-callback-state", pending)
    monkeypatch.setattr(provider_binding, "request_json", fake_slack_identity)
    context = actor_subject.set("unrelated-caller")
    try:
        assert current_store().get_role(pending["role_id"]) is None
        with provider_binding.authorized_callback("synthetic-callback-state", "slack") as (verified_pending, verified_member):
            assert actor_subject.get() == member["subject"]
            assert verified_pending["subject"] == member["subject"]
            provider_binding.bind_slack(verified_pending, verified_member, slack_body())
        assert actor_subject.get() == "unrelated-caller"
    finally:
        actor_subject.reset(context)
    assert current_store().get_credential(pending["role_id"], "slack")
    with pytest.raises(ValueError):
        with provider_binding.authorized_callback("synthetic-callback-state", "slack"):
            pytest.fail("Callback state must be consumed only once")


def test_in_flight_callback_cannot_restore_credential_after_namespace_deletion(connector_member, monkeypatch):
    import provider_binding
    from errors import CodedToolError

    pending, _ = connector_member
    current_store().save_secret("synthetic-deleted-state", pending)
    monkeypatch.setattr(provider_binding, "request_json", fake_slack_identity)
    with provider_binding.authorized_callback("synthetic-deleted-state", "slack") as (verified_pending, verified_member):
        current_store().delete_namespace(pending["role_id"])
        with pytest.raises((ValueError, CodedToolError)):
            provider_binding.bind_slack(verified_pending, verified_member, slack_body())
    assert current_store().credentials == {}
