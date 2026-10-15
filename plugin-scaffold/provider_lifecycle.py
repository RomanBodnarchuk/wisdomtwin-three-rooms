"""Resolve existing read-only provider grants; never create a grant or enable rotation."""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from cryptography.fernet import InvalidToken
from errors import AUTHORIZATION_REQUIRED, CONNECTOR_FAILED, OAUTH_PENDING, CodedToolError
from oauth_connectors import SLACK_USER_SCOPES
from provider_binding import credential_payload, verify_slack_identity
from runtime import flag
from security_store import GrantInvalidated, require_membership, security_store
from store import current_actor, current_store
from tokens import decrypt_token, encrypt_token


def _reconnect(message: str = "Source authorization is unavailable.") -> CodedToolError:
    return CodedToolError(OAUTH_PENDING, message + " Reconnect the source using connect_business_account.")


def _bound_payload(store, role_id: str, service: str, ciphertext: str) -> tuple[dict, dict]:
    try:
        payload = json.loads(decrypt_token(ciphertext))
    except (InvalidToken, ValueError, TypeError):
        raise _reconnect("Source authorization could not be read.") from None
    if not isinstance(payload, dict) or payload.get("subject") != current_actor() or payload.get("role_id") != role_id or payload.get("service") != service:
        raise CodedToolError(AUTHORIZATION_REQUIRED, "Source authorization does not belong to this role.")
    role = store.get_role(role_id)
    org = store.get_organization(role.organization_id) if role else None
    if not role or not org:
        raise CodedToolError(AUTHORIZATION_REQUIRED, "Role access was revoked.")
    member = require_membership(current_actor(), org.domain, role.title)
    if service == "slack" and (payload.get("team_id") != member["slack_team_id"] or payload.get("user_id") != member["slack_user_id"]):
        raise CodedToolError(AUTHORIZATION_REQUIRED, "Slack identity binding does not match this member.")
    if service in {"gmail", "drive"} and payload.get("provider_subject") != member["google_subject"]:
        raise CodedToolError(AUTHORIZATION_REQUIRED, "Google identity binding does not match this member.")
    return payload, member


def resolve_connector_token(role_id: str, service: str) -> str:
    store = current_store()
    ciphertext = store.get_credential(role_id, service)
    if not ciphertext:
        raise _reconnect()
    payload, member = _bound_payload(store, role_id, service, ciphertext)
    expiry = payload.get("expires_at", 0)
    if (expiry is None and service == "slack" and payload.get("credential_version") == 2) or (isinstance(expiry, (int, float)) and expiry > time.time()):
        access = payload.get("access_token")
        if isinstance(access, str) and access:
            return access
        raise _reconnect()
    if service != "slack":
        raise _reconnect("Source authorization expired.")
    with store.credential_lock(role_id, service) as acquired:
        if not acquired:
            raise CodedToolError(CONNECTOR_FAILED, "Source refresh is in progress. Retry shortly.")
        # Another process may have refreshed/reconnected before this lock was acquired.
        ciphertext = store.get_credential(role_id, service)
        if not ciphertext:
            raise _reconnect()
        payload, member = _bound_payload(store, role_id, service, ciphertext)
        expiry = payload.get("expires_at", 0)
        if (expiry is None and payload.get("credential_version") == 2) or (isinstance(expiry, (int, float)) and expiry > time.time()):
            access = payload.get("access_token")
            if isinstance(access, str) and access:
                return access
            raise _reconnect()
        if (not flag("SLACK_TOKEN_REFRESH_ENABLED") or not os.environ.get("SLACK_CLIENT_ID") or not os.environ.get("SLACK_CLIENT_SECRET")
                or not payload.get("refresh_token") or payload.get("refresh_expires_at", 0) <= time.time()):
            raise _reconnect("Slack authorization expired; server refresh is not available.")
        if set(payload.get("scopes", [])) != set(SLACK_USER_SCOPES):
            raise _reconnect("The stored read-only Slack scope could not be verified.")
        db = security_store()
        epoch = db.subject_epoch(current_actor())
        attempt_key = hashlib.sha256(ciphertext.encode()).hexdigest()
        if db.get("provider_refresh_attempt", attempt_key):
            raise _reconnect("A previous refresh outcome is uncertain; the single-use token will not be replayed.")
        # This irreversible-use marker contains only a credential digest; subject
        # revocation must not clear it and accidentally permit a single-use replay.
        db.put("provider_refresh_attempt", attempt_key, {"attempted": True}, 30 * 86400)
        request = urllib.request.Request("https://slack.com/api/oauth.v2.access", method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
            data=urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": payload["refresh_token"],
                "client_id": os.environ["SLACK_CLIENT_ID"], "client_secret": os.environ["SLACK_CLIENT_SECRET"]}).encode())
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                body = json.loads(response.read(1024 * 1024))
            if not isinstance(body, dict):
                raise _reconnect("Slack returned an invalid refresh response.")
            if body.get("ok") is not True:
                if body.get("error") in {"invalid_refresh_token", "invalid_grant", "token_revoked", "invalid_auth", "bad_client_secret", "invalid_client_id"}:
                    raise _reconnect("Slack rejected the refresh grant.")
                raise CodedToolError(CONNECTOR_FAILED, "Slack refresh failed. Reconnect if the outcome cannot be confirmed.")
            if body.get("token_type") != "user" or set(str(body.get("scope", "")).replace(",", " ").split()) != set(SLACK_USER_SCOPES) or not body.get("refresh_token"):
                raise _reconnect("Slack did not return the expected read-only user refresh grant.")
            replacement = credential_payload(payload, body=body, token=body.get("access_token"),
                binding={"team_id": member["slack_team_id"], "user_id": member["slack_user_id"]})
            verify_slack_identity(replacement["access_token"], member)
            with db.guard_subject_epoch(current_actor(), epoch):
                _bound_payload(store, role_id, service, ciphertext)
                if not store.replace_credential(role_id, service, ciphertext, encrypt_token(json.dumps(replacement))):
                    raise CodedToolError(CONNECTOR_FAILED, "Source connection changed during refresh. Retry the current connection.")
            return replacement["access_token"]
        except CodedToolError:
            raise
        except GrantInvalidated:
            raise CodedToolError(AUTHORIZATION_REQUIRED, "Membership changed during source refresh.") from None
        except (OSError, ValueError, TypeError, KeyError):
            raise CodedToolError(CONNECTOR_FAILED, "Source refresh could not be verified. Existing credentials were preserved; reconnect if needed.") from None
