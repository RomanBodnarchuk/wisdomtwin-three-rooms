"""Offline epoch and refresh-replay regressions against real SDK token handling.

SQLite always runs. Postgres variants require an explicitly configured synthetic
WISDOMTWIN_TEST_DATABASE_URL and use independent durable repository instances.
"""

import os
import secrets
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import anyio
import pytest
from mcp.server.auth.handlers.token import TokenHandler
from mcp.server.auth.middleware.client_auth import ClientAuthenticator
from mcp.server.auth.provider import AuthorizationParams
from pydantic import AnyUrl
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.testclient import TestClient

from auth_provider import REFRESH_TTL_SECONDS, WisdomTwinAuthProvider
from oauth_connectors import new_pkce
from security_store import SecurityStore


BASE = "http://127.0.0.1:8000"
CLIENT_ID = "synthetic-revocation-client"
CALLBACK = f"{BASE}/oauth/done"


def run(fn, *args, **kwargs):
    async def call():
        return await fn(*args, **kwargs)

    return anyio.run(call)


@pytest.fixture(params=["sqlite", "postgres"])
def auth_harness(request, tmp_path, monkeypatch):
    if request.param == "postgres":
        database_url = os.environ.get("WISDOMTWIN_TEST_DATABASE_URL", "").strip()
        if not database_url:
            pytest.skip("Requires an explicitly configured synthetic Postgres test database")
        repository_kwargs = {"database_url": database_url}
    else:
        repository_kwargs = {"sqlite_path": str(tmp_path / "revocation-followup.sqlite3")}
    monkeypatch.setenv("OAUTH_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("OAUTH_REDIRECT_URIS", CALLBACK)
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: pytest.fail("Provider/API calls are forbidden in this offline regression"))
    repository = SecurityStore(**repository_kwargs)
    membership = {
        "issuer": "https://synthetic-revocation-idp.test",
        "provider_subject": uuid.uuid4().hex,
        "email": "reviewer@example-corp.com", "domain": "example-corp.com",
        "roles": ["CRO"], "slack_team_id": "SYNTHETIC_TEAM",
        "slack_user_id": "SYNTHETIC_USER", "google_subject": "SYNTHETIC_GOOGLE",
    }
    subject = repository.provision(**membership)
    provider = WisdomTwinAuthProvider(repository)
    handler = TokenHandler(provider, ClientAuthenticator(provider))
    app = Starlette(routes=[Route("/token", handler.handle, methods=["POST"])])

    def post(body):
        # Each request gets a separate event loop, as concurrent server workers do.
        with TestClient(app, base_url=BASE) as http:
            return http.post("/token", data=body)

    harness = SimpleNamespace(
        repository=repository, repository_kwargs=repository_kwargs,
        provider=provider, subject=subject, membership=membership, post=post,
        observer=lambda: WisdomTwinAuthProvider(SecurityStore(**repository_kwargs)),
    )
    try:
        yield harness
    finally:
        # Never truncate shared integration tables or touch another subject.
        repository.remove_member(subject)


def authorization_body(harness):
    provider = harness.provider
    client = run(provider.get_client, CLIENT_ID)
    verifier, challenge = new_pkce()
    params = AuthorizationParams(
        state="synthetic-client-state", scopes=["twin:read"], code_challenge=challenge,
        redirect_uri=AnyUrl(CALLBACK), redirect_uri_provided_explicitly=True,
        resource=f"{BASE}/mcp",
    )
    consent_uri = run(provider.authorize, client, params)
    transaction = parse_qs(urlsplit(consent_uri).query)["txn"][0]
    session, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    # The original implementation has no epoch; retain this fallback for its red
    # reproduction. Once provided, use the exact epoch of this explicit repo.
    epoch_reader = getattr(harness.repository, "subject_epoch", lambda subject: 0)
    harness.repository.put("session", session, {
        "subject": harness.subject, "email": harness.membership["email"],
        "transaction": transaction, "csrf": csrf,
        "subject_epoch": epoch_reader(harness.subject),
    }, 300, subject=harness.subject)
    redirect = provider.approve(transaction, session_key=session, csrf=csrf)
    code = parse_qs(urlsplit(redirect).query)["code"][0]
    return {
        "grant_type": "authorization_code", "client_id": CLIENT_ID,
        "redirect_uri": CALLBACK, "code": code, "code_verifier": verifier,
    }


def fresh_tokens(harness):
    response = harness.post(authorization_body(harness))
    assert response.status_code == 200, response.text
    tokens = response.json()
    provider = harness.observer()
    client = run(provider.get_client, CLIENT_ID)
    assert run(provider.load_access_token, tokens["access_token"]).subject == harness.subject
    assert run(provider.load_refresh_token, client, tokens["refresh_token"]).subject == harness.subject
    return tokens


def refresh_body(token):
    return {"grant_type": "refresh_token", "client_id": CLIENT_ID, "refresh_token": token}


def assert_unloadable(harness, tokens):
    # Recreate the adapter/provider so checks must observe durable invalidation.
    provider = harness.observer()
    client = run(provider.get_client, CLIENT_ID)
    assert run(provider.load_access_token, tokens["access_token"]) is None
    assert run(provider.load_refresh_token, client, tokens["refresh_token"]) is None


def assert_rejected_or_unloadable(harness, response):
    if response.status_code == 400:
        assert response.json()["error"] == "invalid_grant"
    else:
        assert response.status_code == 200, response.text
        assert_unloadable(harness, response.json())


@pytest.mark.parametrize("invalidation", ["revoke_subject", "reprovision", "remove_and_reprovision"])
def test_initial_code_exchange_cannot_survive_subject_invalidation(auth_harness, monkeypatch, invalidation):
    harness = auth_harness
    body = authorization_body(harness)
    issue_started, continue_issue = threading.Event(), threading.Event()
    original_issue = harness.provider._issue

    def paused_issue(*args, **kwargs):
        issue_started.set()
        assert continue_issue.wait(10), "Synthetic exchange was not released"
        return original_issue(*args, **kwargs)

    with monkeypatch.context() as scoped:
        scoped.setattr(harness.provider, "_issue", paused_issue)
        with ThreadPoolExecutor(max_workers=1) as executor:
            exchange = executor.submit(harness.post, body)
            try:
                assert issue_started.wait(10), "Authorization code did not reach issuance"
                other_repository = SecurityStore(**harness.repository_kwargs)
                assert other_repository.get("code", body["code"]) is None
                if invalidation == "revoke_subject":
                    other_repository.revoke_subject(harness.subject)
                else:
                    if invalidation == "remove_and_reprovision":
                        other_repository.remove_member(harness.subject)
                    assert other_repository.provision(**harness.membership) == harness.subject
            finally:
                continue_issue.set()
            response = exchange.result(timeout=10)
    assert_rejected_or_unloadable(harness, response)
    # Revocation is an epoch change, not a permanent ban on this membership.
    fresh_tokens(harness)


def test_used_refresh_replay_through_sdk_revokes_only_its_family(auth_harness):
    harness = auth_harness
    initial = fresh_tokens(harness)
    unrelated = fresh_tokens(harness)
    rotated_response = harness.post(refresh_body(initial["refresh_token"]))
    assert rotated_response.status_code == 200, rotated_response.text
    rotated = rotated_response.json()
    # Exercise SDK load_refresh_token before exchange, as the real endpoint does.
    replay = harness.post(refresh_body(initial["refresh_token"]))
    assert replay.status_code == 400
    assert replay.json()["error"] == "invalid_grant"
    assert_unloadable(harness, initial)
    assert_unloadable(harness, rotated)
    observer = harness.observer()
    client = run(observer.get_client, CLIENT_ID)
    assert run(observer.load_access_token, unrelated["access_token"]) is not None
    assert run(observer.load_refresh_token, client, unrelated["refresh_token"]) is not None
    fresh_tokens(harness)


def test_sdk_refresh_replay_during_issuance_blocks_successors(auth_harness, monkeypatch):
    harness = auth_harness
    initial = fresh_tokens(harness)
    issue_started, continue_issue = threading.Event(), threading.Event()
    original_issue = harness.provider._issue

    def paused_issue(*args, **kwargs):
        issue_started.set()
        assert continue_issue.wait(10), "Synthetic rotation was not released"
        return original_issue(*args, **kwargs)

    with monkeypatch.context() as scoped:
        scoped.setattr(harness.provider, "_issue", paused_issue)
        with ThreadPoolExecutor(max_workers=1) as executor:
            first = executor.submit(harness.post, refresh_body(initial["refresh_token"]))
            try:
                assert issue_started.wait(10), "Refresh did not reach issuance"
                # A separate HTTP event loop encounters the already consumed key.
                replay = harness.post(refresh_body(initial["refresh_token"]))
                assert replay.status_code == 400
                assert replay.json()["error"] == "invalid_grant"
            finally:
                continue_issue.set()
            first_response = first.result(timeout=10)
    assert_unloadable(harness, initial)
    assert_rejected_or_unloadable(harness, first_response)
    fresh_tokens(harness)


def test_concurrent_sdk_refreshes_loaded_before_consume_revoke_the_family(auth_harness, monkeypatch):
    harness = auth_harness
    initial = fresh_tokens(harness)
    both_loaded = threading.Barrier(2)
    original_load = harness.provider.load_refresh_token

    async def synchronized_load(client, token):
        loaded = await original_load(client, token)
        if token == initial["refresh_token"] and loaded is not None:
            both_loaded.wait(timeout=10)
        return loaded

    with monkeypatch.context() as scoped:
        scoped.setattr(harness.provider, "load_refresh_token", synchronized_load)
        with ThreadPoolExecutor(max_workers=2) as executor:
            exchanges = [executor.submit(harness.post, refresh_body(initial["refresh_token"])) for _ in range(2)]
            responses = [exchange.result(timeout=15) for exchange in exchanges]
    assert any(response.status_code == 400 and response.json()["error"] == "invalid_grant" for response in responses)
    assert_unloadable(harness, initial)
    for response in responses:
        assert_rejected_or_unloadable(harness, response)
    fresh_tokens(harness)


@pytest.mark.parametrize("invalid_kind", ["unknown", "access_as_refresh", "wrong_client_active", "wrong_client_used"])
def test_invalid_refresh_request_cannot_revoke_an_authorized_family(auth_harness, invalid_kind):
    harness = auth_harness
    initial = fresh_tokens(harness)
    live = initial
    client_id = CLIENT_ID
    if invalid_kind.startswith("wrong_client"):
        # A second synthetic registered public client exercises SDK loader client
        # checks, rather than stopping at unknown-client authentication.
        original_client = run(harness.provider.get_client, CLIENT_ID)
        client_id = "another-synthetic-revocation-client"
        harness.provider._clients[client_id] = original_client.model_copy(update={"client_id": client_id})
        if invalid_kind == "wrong_client_used":
            rotated = harness.post(refresh_body(initial["refresh_token"]))
            assert rotated.status_code == 200, rotated.text
            live = rotated.json()
        token = initial["refresh_token"]
    elif invalid_kind == "access_as_refresh":
        token = initial["access_token"]
    else:
        token = secrets.token_urlsafe(32)
    response = harness.post({**refresh_body(token), "client_id": client_id})
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_grant"
    observer = harness.observer()
    client = run(observer.get_client, CLIENT_ID)
    assert run(observer.load_access_token, initial["access_token"]) is not None
    assert run(observer.load_access_token, live["access_token"]) is not None
    assert run(observer.load_refresh_token, client, live["refresh_token"]) is not None


def test_old_refresh_lineage_survives_until_its_active_successor_expires(auth_harness, monkeypatch):
    import security_store

    harness = auth_harness
    clock = [time.time()]
    monkeypatch.setattr(security_store.time, "time", lambda: clock[0])
    initial = fresh_tokens(harness)
    # Rotate shortly before the original refresh's deadline, extending the
    # family's useful life well beyond that first token's expiration.
    clock[0] += REFRESH_TTL_SECONDS - 120
    rotated_response = harness.post(refresh_body(initial["refresh_token"]))
    assert rotated_response.status_code == 200, rotated_response.text
    rotated = rotated_response.json()
    clock[0] += 240
    harness.repository.sweep()
    observer = harness.observer()
    client = run(observer.get_client, CLIENT_ID)
    assert run(observer.load_access_token, rotated["access_token"]) is not None
    assert run(observer.load_refresh_token, client, rotated["refresh_token"]) is not None
    replay = harness.post(refresh_body(initial["refresh_token"]))
    assert replay.status_code == 400
    assert replay.json()["error"] == "invalid_grant"
    assert_unloadable(harness, rotated)
    fresh_tokens(harness)
