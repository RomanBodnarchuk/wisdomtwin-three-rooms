"""Bind every connector grant to the verified subject, role and provider identity."""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from urllib.parse import urlencode

from corporate_login import request_json
from domain import connector_enabled
from oauth_connectors import SLACK_USER_SCOPES, GMAIL_SCOPE, DRIVE_SCOPE
from security_store import require_membership
from store import actor_subject, current_store
from tokens import encrypt_token


@contextmanager
def authorized_callback(state: str, service: str | set[str]):
    pending = current_store().pop_secret(state)
    allowed = {service} if isinstance(service, str) else service
    if not pending or pending.get("service") not in allowed or not connector_enabled(pending["service"]):
        raise ValueError("Expired, wrong-provider, or disabled authorization state")
    service = pending["service"]
    member = require_membership(pending["subject"], pending["domain"], pending["role_title"])
    context = actor_subject.set(pending["subject"])
    try:
        role = current_store().get_role(pending["role_id"])
        if not role or role.title != pending["role_title"]:
            raise ValueError("Role access has been revoked")
        org = current_store().get_organization(role.organization_id)
        if not org or org.domain != pending["domain"] or not any(
            row.role_id == role.id and row.service == service for row in current_store().connections()
        ):
            raise ValueError("Connection was deleted or substituted")
        yield pending, member
    finally:
        actor_subject.reset(context)


def bind_slack(pending: dict, member: dict, body: dict) -> None:
    user = body.get("authed_user") or {}
    token = user.get("access_token")
    team_id = (body.get("team") or {}).get("id")
    user_id = user.get("id")
    scopes = set(str(user.get("scope", "")).replace(",", " ").split())
    if body.get("ok") is not True or not token or scopes != set(SLACK_USER_SCOPES):
        raise ValueError("A read-only Slack user grant is required")
    if not member["slack_team_id"] or not member["slack_user_id"] or team_id != member["slack_team_id"] or user_id != member["slack_user_id"]:
        raise ValueError("Slack team or user does not match the provisioned member")
    identity = request_json("https://slack.com/api/auth.test", token=token)
    if identity.get("ok") is not True or identity.get("team_id") != team_id or identity.get("user_id") != user_id:
        raise ValueError("Slack token identity does not match the callback")
    profile = request_json("https://slack.com/api/users.info?" + urlencode({"user": user_id}), token=token)
    verified_user = profile.get("user") or {}
    email = (verified_user.get("profile") or {}).get("email", "").strip().lower()
    if profile.get("ok") is not True or verified_user.get("deleted") or verified_user.get("is_bot") or verified_user.get("id") != user_id or email != member["email"]:
        raise ValueError("Slack corporate email does not match the login")
    _save(pending, body=user, token=token, binding={"team_id": team_id, "user_id": user_id})


def bind_google(pending: dict, member: dict, body: dict) -> None:
    token = body.get("access_token")
    required = GMAIL_SCOPE if pending["service"] == "gmail" else DRIVE_SCOPE
    scopes = set(str(body.get("scope", "")).split())
    allowed = {required, "openid", "email", "https://www.googleapis.com/auth/userinfo.email"}
    if not token or required not in scopes or not scopes <= allowed:
        raise ValueError("The expected Google scope was not granted")
    identity = request_json("https://openidconnect.googleapis.com/v1/userinfo", token=token)
    if identity.get("email_verified") is not True or not member["google_subject"] or identity.get("sub") != member["google_subject"] or identity.get("email", "").strip().lower() != member["email"]:
        raise ValueError("Google identity does not match the provisioned corporate member")
    _save(pending, body=body, token=token, binding={"provider_subject": identity["sub"]})


def _save(pending: dict, *, body: dict, token: str, binding: dict) -> None:
    expires = max(1, min(int(body.get("expires_in", 86400)), 86400))
    payload = {"access_token": token, "subject": pending["subject"], "role_id": pending["role_id"],
               "service": pending["service"], "expires_at": time.time() + expires, **binding}
    current_store().save_credential(pending["role_id"], pending["service"], encrypt_token(json.dumps(payload)))
