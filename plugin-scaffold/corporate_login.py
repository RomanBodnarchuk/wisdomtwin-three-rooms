"""Corporate OIDC login. No identity or entitlement is accepted from tool arguments."""

from __future__ import annotations

import json
import os
import secrets
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

import jwt

from oauth_connectors import new_pkce, public_base_url
from security_store import security_store, stable_subject

LOGIN_TTL = 300
SESSION_COOKIE = "wisdomtwin_consent"
LOGIN_COOKIE = "wisdomtwin_login"


def _https(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.fragment:
        raise ValueError("OIDC endpoints must be configured HTTPS URLs")
    return url


def request_json(url: str, *, body: dict | None = None, token: str | None = None) -> dict:
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = urlencode(body).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(_https(url), data=data, headers=headers), timeout=15) as response:
        return json.loads(response.read(1024 * 1024))


def configuration() -> tuple[str, str, dict]:
    issuer = os.environ.get("OIDC_ISSUER", "").strip()
    client_id = os.environ.get("OIDC_CLIENT_ID", "").strip()
    if not issuer or not client_id:
        raise RuntimeError("Corporate OIDC login has not been configured")
    metadata = request_json(_https(issuer).rstrip("/") + "/.well-known/openid-configuration")
    if metadata.get("issuer") != issuer:
        raise ValueError("OIDC issuer mismatch")
    for name in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
        _https(metadata[name])
    return issuer, client_id, metadata


def start_login(transaction: str) -> tuple[str, str]:
    db = security_store()
    if not db.get("pending", transaction):
        raise ValueError("Expired authorization request")
    issuer, client_id, metadata = configuration()
    state, nonce, browser = (secrets.token_urlsafe(32) for _ in range(3))
    verifier, challenge = new_pkce()
    db.put("login", state, {"transaction": transaction, "nonce": nonce, "browser": browser,
                           "verifier": verifier, "issuer": issuer, "client_id": client_id}, LOGIN_TTL)
    query = urlencode({"client_id": client_id, "response_type": "code", "scope": "openid email",
                       "redirect_uri": f"{public_base_url()}/oauth/callback/identity", "state": state,
                       "nonce": nonce, "code_challenge": challenge, "code_challenge_method": "S256"})
    return metadata["authorization_endpoint"] + "?" + query, browser


def verify_id_token(encoded: str, *, issuer: str, client_id: str, nonce: str, jwks: dict) -> dict:
    header = jwt.get_unverified_header(encoded)
    if header.get("alg") not in {"RS256", "ES256"}:
        raise ValueError("Unsupported identity signature")
    candidates = [key for key in jwks.get("keys", []) if key.get("kid") == header.get("kid")
                  and key.get("use", "sig") == "sig" and key.get("alg", header["alg"]) == header["alg"]]
    if len(candidates) != 1:
        raise ValueError("Unknown identity signing key")
    key = jwt.PyJWK.from_dict(candidates[0], algorithm=header["alg"]).key
    claims = jwt.decode(encoded, key, algorithms=[header["alg"]], audience=client_id, issuer=issuer,
                        options={"require": ["exp", "iat", "iss", "aud", "sub", "nonce", "email", "email_verified"]})
    if claims["email_verified"] is not True or not secrets.compare_digest(str(claims["nonce"]), nonce):
        raise ValueError("Identity email or nonce is not verified")
    if claims.get("azp", client_id) != client_id or (isinstance(claims["aud"], list) and len(claims["aud"]) > 1 and claims.get("azp") != client_id):
        raise ValueError("Identity was issued to another client")
    if not isinstance(claims["sub"], str) or not claims["sub"] or not isinstance(claims["email"], str):
        raise ValueError("Invalid corporate identity")
    return claims


def finish_login(state: str, code: str, browser: str) -> tuple[str, str]:
    db = security_store()
    pending = db.get("login", state, consume=True)
    if not code or not pending or not secrets.compare_digest(pending["browser"], browser):
        raise ValueError("Invalid corporate login state")
    issuer, client_id, metadata = configuration()
    if issuer != pending["issuer"] or client_id != pending["client_id"]:
        raise ValueError("Identity configuration changed during login")
    body = {"grant_type": "authorization_code", "client_id": client_id, "code": code,
            "code_verifier": pending["verifier"], "redirect_uri": f"{public_base_url()}/oauth/callback/identity"}
    secret = os.environ.get("OIDC_CLIENT_SECRET", "")
    if secret:
        body["client_secret"] = secret
    tokens = request_json(metadata["token_endpoint"], body=body)
    claims = verify_id_token(tokens["id_token"], issuer=issuer, client_id=client_id, nonce=pending["nonce"],
                             jwks=request_json(metadata["jwks_uri"]))
    subject = stable_subject(issuer, claims["sub"])
    member = db.membership(subject)
    email = claims["email"].strip().lower()
    if not member or member["email"] != email or email.rsplit("@", 1)[-1] != member["domain"]:
        raise ValueError("Corporate identity has no provisioned organization membership")
    if not db.get("pending", pending["transaction"]):
        raise ValueError("Expired MCP authorization request")
    session, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    db.put("session", session, {"subject": subject, "email": email, "csrf": csrf,
                               "transaction": pending["transaction"]}, LOGIN_TTL, subject=subject)
    # Provider tokens and the ID token are discarded; only the verified binding remains.
    return pending["transaction"], session
