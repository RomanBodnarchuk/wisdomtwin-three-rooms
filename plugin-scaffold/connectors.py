"""Read-only fetchers. Slack is the production path. Gmail and Drive run only when enabled."""

from __future__ import annotations

import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "slack" / "messages.json"
MAX_RATE_LIMIT_WAIT_SECONDS = 2
# Errors about one source: it was deleted or this user cannot read it.
SLACK_UNAVAILABLE_ERRORS = frozenset({"message_not_found", "thread_not_found", "channel_not_found",
    "not_in_channel", "missing_scope", "access_denied"})
# Errors about the grant itself: every source is unreadable until the user reconnects.
SLACK_GRANT_ERRORS = frozenset({"token_revoked", "invalid_auth", "account_inactive", "token_expired", "not_authed"})


class SourceUnavailable(RuntimeError):
    """Source was deleted or the current user no longer has access."""


class GrantRevoked(RuntimeError):
    """The provider rejected the user's grant itself (revoked, expired or deactivated); the user must reconnect."""

    def __init__(self, service: str) -> None:
        self.service = service
        super().__init__(f"The provider rejected the {service} grant")


class _GrantRejected(SourceUnavailable):
    """HTTP 401. Google callers turn it into GrantRevoked for their service."""


class SourceRateLimited(RuntimeError):
    """A bounded request could not complete within the provider's retry window."""

    def __init__(self, retry_after_seconds: float | None) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__("Source provider is rate limited")


def _retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None
    try:
        delay = float(value)
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
            if retry_at.tzinfo is None:
                return None
            delay = retry_at.timestamp() - time.time()
        except (TypeError, ValueError, OverflowError):
            return None
    return max(0.0, delay) if math.isfinite(delay) and delay >= 0 else None


def use_fixtures() -> bool:
    from runtime import flag, local_test_mode

    if flag("WISDOMTWIN_USE_FIXTURES") and not local_test_mode():
        raise RuntimeError("Fixtures are restricted to explicit loopback tests")
    return flag("WISDOMTWIN_USE_FIXTURES") and local_test_mode()


def load_slack_fixtures(max_items: int) -> list[dict[str, str]]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    items = []
    for row in payload[:max_items]:
        items.append({"uri": row["uri"], "text": row["text"]})
    return items


def _request_json(url: str, token: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                delay = _retry_after_seconds(exc.headers.get("Retry-After") if exc.headers else None)
                exc.close()
                if attempt == 0 and delay is not None and delay <= MAX_RATE_LIMIT_WAIT_SECONDS:
                    time.sleep(delay)
                    continue
                raise SourceRateLimited(delay) from None
            if exc.code == 401:
                raise _GrantRejected("Source access is unavailable") from None
            if exc.code in {403, 404}:
                raise SourceUnavailable("Source access is unavailable") from None
            raise RuntimeError(f"Connector request failed with status {exc.code}") from None


def _google_json(service: str, url: str, token: str) -> dict:
    """A Google API request where HTTP 401 means the grant was revoked or expired, not one missing source."""
    try:
        return _request_json(url, token)
    except _GrantRejected:
        raise GrantRevoked(service) from None


def _check_slack_grant(body: dict) -> None:
    if body.get("error") in SLACK_GRANT_ERRORS:
        raise GrantRevoked("slack")


def fetch_slack(token: str, query: str, max_items: int) -> list[dict[str, str]]:
    if use_fixtures() or not token:
        if use_fixtures():
            return load_slack_fixtures(max_items)
        raise RuntimeError("Slack is not connected for this role")
    params = urllib.parse.urlencode({"query": query or "in:#general", "count": min(max_items, 100)})
    body = _request_json(f"https://slack.com/api/search.messages?{params}", token)
    if body.get("ok") is not True:
        _check_slack_grant(body)
        raise RuntimeError("Slack search was rejected")
    matches = body.get("messages", {}).get("matches", [])
    items: list[dict[str, str]] = []
    for match in matches[:max_items]:
        # Use Slack's actual workspace permalink; do not fabricate a source URL.
        permalink = match.get("permalink", "")
        parsed = urllib.parse.urlsplit(permalink)
        if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(".slack.com") or parsed.username:
            continue
        text = match.get("text") or ""
        if not text:
            continue
        items.append(
            {
                "uri": permalink,
                "text": text,
                "author_provider_id": str(match.get("user") or ""),
            }
        )
    return items


def refetch_slack(token: str, uri: str) -> dict[str, str] | None:
    """Revalidate message access with this user's grant; never fetch arbitrary URLs."""
    import re

    parsed = urllib.parse.urlsplit(uri)
    if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(".slack.com") or parsed.username:
        raise ValueError("Invalid Slack reference")
    match = re.fullmatch(r"/archives/([A-Z0-9]+)/p([0-9]{7,})", parsed.path)
    if not match:
        raise ValueError("Invalid Slack message reference")
    channel, compact_ts = match.groups()
    ts = compact_ts[:-6] + "." + compact_ts[-6:]
    params = urllib.parse.urlencode({"channel": channel, "oldest": ts, "latest": ts, "inclusive": "true", "limit": 1})
    thread_ts = urllib.parse.parse_qs(parsed.query).get("thread_ts", [""])[0]
    if thread_ts and not re.fullmatch(r"[0-9]+\.[0-9]{6}", thread_ts):
        raise ValueError("Invalid Slack thread reference")
    if thread_ts:
        params = urllib.parse.urlencode({"channel": channel, "ts": thread_ts, "oldest": ts, "latest": ts, "inclusive": "true", "limit": 1})
    body = _request_json("https://slack.com/api/" + ("conversations.replies?" if thread_ts else "conversations.history?") + params, token)
    if body.get("ok") is not True:
        _check_slack_grant(body)
        if body.get("error") in SLACK_UNAVAILABLE_ERRORS:
            return None
        raise RuntimeError("Source access was rejected")
    for message in body.get("messages", []):
        if message.get("ts") == ts and message.get("text") and message.get("user"):
            return {"uri": uri, "text": message["text"], "author_provider_id": message["user"]}
    if not thread_ts:
        params = urllib.parse.urlencode({"channel": channel, "ts": ts, "oldest": ts, "latest": ts, "inclusive": "true", "limit": 1})
        body = _request_json("https://slack.com/api/conversations.replies?" + params, token)
        if body.get("ok") is not True:
            _check_slack_grant(body)
            if body.get("error") in SLACK_UNAVAILABLE_ERRORS:
                return None
            raise RuntimeError("Source access was rejected")
        for message in body.get("messages", []):
            if message.get("ts") == ts and message.get("text") and message.get("user"):
                return {"uri": uri, "text": message["text"], "author_provider_id": message["user"]}
    return None


def fetch_gmail(token: str, query: str, max_items: int) -> list[dict[str, str]]:
    listed = _google_json(
        "gmail",
        "https://gmail.googleapis.com/gmail/v1/users/me/messages?"
        + urllib.parse.urlencode({"q": query, "maxResults": min(max_items, 100)}),
        token,
    )
    items: list[dict[str, str]] = []
    for message in listed.get("messages", [])[:max_items]:
        detail = _google_json(
            "gmail",
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message['id']}?format=metadata",
            token,
        )
        if "TRASH" in detail.get("labelIds", []):
            continue
        snippet = detail.get("snippet") or ""
        if not snippet:
            continue
        items.append(
            {
                # Omit the /u/0/ account index, which always meant the first signed-in mailbox.
                "uri": f"https://mail.google.com/mail/#all/{message['id']}",
                "text": snippet,
                "author_provider_id": _gmail_author(detail),
            }
        )
    return items


def fetch_drive(token: str, query: str, max_items: int) -> list[dict[str, str]]:
    safe_query = query.replace("\\", "\\\\").replace("'", "\\'")
    drive_query = f"trashed = false and fullText contains '{safe_query}'" if query else "trashed = false"
    listed = _google_json(
        "drive",
        "https://www.googleapis.com/drive/v3/files?"
        + urllib.parse.urlencode(
            {
                "q": drive_query,
                "pageSize": min(max_items, 100),
                "fields": "files(id,name,description,trashed,lastModifyingUser(permissionId))",
            }
        ),
        token,
    )
    items: list[dict[str, str]] = []
    for file_row in listed.get("files", [])[:max_items]:
        if file_row.get("trashed") is True:
            continue
        text = " ".join(part for part in (file_row.get("name"), file_row.get("description")) if part)
        if not text:
            continue
        items.append(
            {
                "uri": f"https://drive.google.com/file/d/{file_row['id']}/view",
                "text": text,
                "author_provider_id": (file_row.get("lastModifyingUser") or {}).get("permissionId", ""),
            }
        )
    return items


def _gmail_author(detail: dict) -> str:
    headers = (detail.get("payload") or {}).get("headers", [])
    return parseaddr(next((header.get("value", "") for header in headers if header.get("name", "").lower() == "from"), ""))[1].lower()


def refetch_google(token: str, service: str, uri: str) -> dict[str, str] | None:
    import re

    if service == "gmail":
        # Current rows use #all/<id>; legacy rows used u/0/#inbox/<id>.
        match = re.fullmatch(r"https://mail\.google\.com/mail/(?:#all|u/0/#inbox)/([a-zA-Z0-9_-]+)", uri)
        if not match:
            raise ValueError("Invalid Gmail reference")
        detail = _google_json("gmail", f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{match[1]}?format=metadata", token)
        if "TRASH" in detail.get("labelIds", []):
            return None
        return {"uri": uri, "text": detail.get("snippet", ""), "author_provider_id": _gmail_author(detail)}
    if service == "drive":
        match = re.fullmatch(r"https://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)/view", uri)
        if not match:
            raise ValueError("Invalid Drive reference")
        detail = _google_json("drive", f"https://www.googleapis.com/drive/v3/files/{match[1]}?fields=id,name,description,trashed,lastModifyingUser(permissionId)", token)
        if detail.get("trashed") is True:
            return None
        text = " ".join(part for part in (detail.get("name"), detail.get("description")) if part)
        return {"uri": uri, "text": text, "author_provider_id": (detail.get("lastModifyingUser") or {}).get("permissionId", "")}
    raise ValueError("Unsupported source provider")
