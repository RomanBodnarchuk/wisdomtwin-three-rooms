"""Read-only fetchers. Slack is the production path. Gmail and Drive run only when enabled."""

from __future__ import annotations

import json
import math
import os
import re
import time
import contextvars
from contextlib import contextmanager
import urllib.error
import urllib.parse
import urllib.request
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "slack" / "messages.json"
MAX_RATE_LIMIT_WAIT_SECONDS = 2
SLACK_UNAVAILABLE_ERRORS = frozenset({"message_not_found", "thread_not_found", "channel_not_found",
    "not_in_channel", "token_revoked", "account_inactive", "invalid_auth", "missing_scope", "access_denied"})
_slack_rate_scope = contextvars.ContextVar("wisdomtwin_slack_rate_scope", default=None)


class SourceUnavailable(RuntimeError):
    """Source was deleted or the current user no longer has access."""


class SourceRateLimited(RuntimeError):
    """A bounded request could not complete within the provider's retry window."""

    def __init__(self, retry_after_seconds: float | None) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__("Source provider is rate limited")


class SourceRevalidationIncomplete(RuntimeError):
    """A bounded page did not establish whether a selected source still exists."""


@contextmanager
def slack_rate_context(*, team_id: str, app_id: str):
    """Use the verified workspace and configured app, never a user's access token."""
    if not all(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", value)
               for value in (team_id, app_id)):
        raise ValueError("Verified Slack workspace and app identifiers are required")
    marker = _slack_rate_scope.set((team_id, app_id))
    try:
        yield
    finally:
        _slack_rate_scope.reset(marker)


def _slack_rate_key(url: str) -> tuple[str, float] | None:
    scope = _slack_rate_scope.get()
    parsed = urllib.parse.urlsplit(url)
    if not scope or parsed.scheme != "https" or parsed.netloc != "slack.com":
        return None
    method = parsed.path.removeprefix("/api/")
    if method == "search.messages":
        interval = 3.0  # Tier 2: conservative 20 requests/minute.
    elif method in {"conversations.history", "conversations.replies"}:
        rate_class = os.environ.get("SLACK_HISTORY_RATE_CLASS", "restricted").strip().lower()
        if rate_class not in {"restricted", "tier3"}:
            raise ValueError("Slack history rate class must be explicitly configured")
        # Tier 3 is an operator assertion of Marketplace/internal/exempt eligibility.
        # Qualifying commercial non-Marketplace apps default to one request/minute.
        interval = 60.0 if rate_class == "restricted" else 1.2
    else:
        return None
    return json.dumps([scope[1], scope[0], method]), interval


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
    rate = _slack_rate_key(url)
    if rate:
        from security_store import security_store

        delay = security_store().reserve_provider_request(*rate)
        if delay:
            raise SourceRateLimited(delay)
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
            if rate:
                security_store().extend_provider_cooldown(rate[0], rate[1])
            return body
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                delay = _retry_after_seconds(exc.headers.get("Retry-After") if exc.headers else None)
                exc.close()
                if rate and delay is not None:
                    security_store().extend_provider_cooldown(rate[0], delay)
                if attempt == 0 and delay is not None and delay <= MAX_RATE_LIMIT_WAIT_SECONDS:
                    time.sleep(delay)
                    continue
                if rate:
                    remaining = security_store().reserve_provider_request(*rate)
                    delay = max(delay or 0, remaining)
                raise SourceRateLimited(delay) from None
            if exc.code in {401, 403, 404}:
                raise SourceUnavailable("Source access is unavailable") from None
            raise RuntimeError(f"Connector request failed with status {exc.code}") from None


def fetch_slack(token: str, query: str, max_items: int) -> list[dict[str, str]]:
    if use_fixtures() or not token:
        if use_fixtures():
            return load_slack_fixtures(max_items)
        raise RuntimeError("Slack is not connected for this role")
    params = urllib.parse.urlencode({"query": query or "in:#general", "count": min(max_items, 100)})
    body = _request_json(f"https://slack.com/api/search.messages?{params}", token)
    if body.get("ok") is not True:
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


def _slack_reference(uri: str) -> tuple[str, str, str]:
    parsed = urllib.parse.urlsplit(uri)
    if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(".slack.com") or parsed.username:
        raise ValueError("Invalid Slack reference")
    match = re.fullmatch(r"/archives/([A-Z0-9]+)/p([0-9]{7,})", parsed.path)
    if not match:
        raise ValueError("Invalid Slack message reference")
    channel, compact_ts = match.groups()
    ts = compact_ts[:-6] + "." + compact_ts[-6:]
    thread_ts = urllib.parse.parse_qs(parsed.query).get("thread_ts", [""])[0]
    if thread_ts and not re.fullmatch(r"[0-9]+\.[0-9]{6}", thread_ts):
        raise ValueError("Invalid Slack thread reference")
    return channel, ts, thread_ts


def refetch_slack(token: str, uri: str) -> dict[str, str] | None:
    """Revalidate message access with this user's grant; never fetch arbitrary URLs."""
    channel, ts, thread_ts = _slack_reference(uri)
    params = urllib.parse.urlencode({"channel": channel, "oldest": ts, "latest": ts, "inclusive": "true", "limit": 1})
    if thread_ts:
        params = urllib.parse.urlencode({"channel": channel, "ts": thread_ts, "oldest": ts, "latest": ts, "inclusive": "true", "limit": 1})
    body = _request_json("https://slack.com/api/" + ("conversations.replies?" if thread_ts else "conversations.history?") + params, token)
    if body.get("ok") is not True:
        if body.get("error") in SLACK_UNAVAILABLE_ERRORS:
            return None
        raise RuntimeError("Source access was rejected")
    for message in body.get("messages", []):
        if message.get("ts") == ts and message.get("text") and message.get("user"):
            return {"uri": uri, "text": message["text"], "author_provider_id": message["user"]}
    if body.get("has_more") or (body.get("response_metadata") or {}).get("next_cursor"):
        raise SourceRevalidationIncomplete("Current source page is incomplete")
    if not thread_ts:
        params = urllib.parse.urlencode({"channel": channel, "ts": ts, "oldest": ts, "latest": ts, "inclusive": "true", "limit": 1})
        body = _request_json("https://slack.com/api/conversations.replies?" + params, token)
        if body.get("ok") is not True:
            if body.get("error") in SLACK_UNAVAILABLE_ERRORS:
                return None
            raise RuntimeError("Source access was rejected")
        for message in body.get("messages", []):
            if message.get("ts") == ts and message.get("text") and message.get("user"):
                return {"uri": uri, "text": message["text"], "author_provider_id": message["user"]}
        if body.get("has_more") or (body.get("response_metadata") or {}).get("next_cursor"):
            raise SourceRevalidationIncomplete("Current source page is incomplete")
    return None


def refetch_slack_batch(token: str, uris: list[str]) -> dict[str, dict | None | Exception]:
    """One bounded current-access read per channel/thread; retain no provider text."""
    results: dict[str, dict | None | Exception] = {}
    groups: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for uri in dict.fromkeys(uris):
        try:
            channel, ts, thread_ts = _slack_reference(uri)
            groups.setdefault((channel, thread_ts), []).append((uri, ts))
        except ValueError as exc:
            results[uri] = exc
    for (channel, thread_ts), targets in groups.items():
        try:
            if len(targets) == 1:
                results[targets[0][0]] = refetch_slack(token, targets[0][0])
                continue
            timestamps = [ts for _, ts in targets]
            params = {"channel": channel, "oldest": min(timestamps), "latest": max(timestamps),
                      "inclusive": "true", "limit": 15}
            if thread_ts:
                params["ts"] = thread_ts
            method = "conversations.replies" if thread_ts else "conversations.history"
            body = _request_json(f"https://slack.com/api/{method}?" + urllib.parse.urlencode(params), token)
            if body.get("ok") is not True:
                if body.get("error") in SLACK_UNAVAILABLE_ERRORS:
                    for uri, _ in targets:
                        results[uri] = None
                    continue
                raise RuntimeError("Source access was rejected")
            messages = {row.get("ts"): row for row in body.get("messages", [])
                        if isinstance(row, dict) and row.get("text") and row.get("user")}
            incomplete = body.get("has_more") or (body.get("response_metadata") or {}).get("next_cursor")
            for uri, ts in targets:
                row = messages.get(ts)
                if row:
                    results[uri] = {"uri": uri, "text": row["text"], "author_provider_id": row["user"]}
                elif incomplete:
                    results[uri] = SourceRevalidationIncomplete("Current source page is incomplete")
                elif not thread_ts:
                    # A permalink may omit thread_ts; only a replies check can
                    # distinguish a missing thread message from deletion.
                    query = urllib.parse.urlencode({"channel": channel, "ts": ts, "oldest": ts,
                                                   "latest": ts, "inclusive": "true", "limit": 1})
                    try:
                        reply = _request_json("https://slack.com/api/conversations.replies?" + query, token)
                        if reply.get("ok") is not True:
                            if reply.get("error") in SLACK_UNAVAILABLE_ERRORS:
                                results[uri] = None
                                continue
                            raise RuntimeError("Source access was rejected")
                        found = next((row for row in reply.get("messages", []) if row.get("ts") == ts
                                      and row.get("text") and row.get("user")), None)
                        results[uri] = ({"uri": uri, "text": found["text"], "author_provider_id": found["user"]}
                                        if found else (SourceRevalidationIncomplete("Current source page is incomplete")
                                        if reply.get("has_more") or (reply.get("response_metadata") or {}).get("next_cursor") else None))
                    except Exception as exc:
                        results[uri] = exc
                else:
                    results[uri] = None
        except Exception as exc:
            for uri, _ in targets:
                results[uri] = exc
    return results


def fetch_gmail(token: str, query: str, max_items: int) -> list[dict[str, str]]:
    listed = _request_json(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages?"
        + urllib.parse.urlencode({"q": query, "maxResults": min(max_items, 100)}),
        token,
    )
    items: list[dict[str, str]] = []
    for message in listed.get("messages", [])[:max_items]:
        detail = _request_json(
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
                "uri": f"https://mail.google.com/mail/u/0/#inbox/{message['id']}",
                "text": snippet,
                "author_provider_id": _gmail_author(detail),
            }
        )
    return items


def fetch_drive(token: str, query: str, max_items: int) -> list[dict[str, str]]:
    safe_query = query.replace("\\", "\\\\").replace("'", "\\'")
    drive_query = f"trashed = false and fullText contains '{safe_query}'" if query else "trashed = false"
    listed = _request_json(
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
        match = re.fullmatch(r"https://mail\.google\.com/mail/u/0/#inbox/([a-zA-Z0-9_-]+)", uri)
        if not match:
            raise ValueError("Invalid Gmail reference")
        detail = _request_json(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{match[1]}?format=metadata", token)
        if "TRASH" in detail.get("labelIds", []):
            return None
        return {"uri": uri, "text": detail.get("snippet", ""), "author_provider_id": _gmail_author(detail)}
    if service == "drive":
        match = re.fullmatch(r"https://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)/view", uri)
        if not match:
            raise ValueError("Invalid Drive reference")
        detail = _request_json(f"https://www.googleapis.com/drive/v3/files/{match[1]}?fields=id,name,description,trashed,lastModifyingUser(permissionId)", token)
        if detail.get("trashed") is True:
            return None
        text = " ".join(part for part in (detail.get("name"), detail.get("description")) if part)
        return {"uri": uri, "text": text, "author_provider_id": (detail.get("lastModifyingUser") or {}).get("permissionId", "")}
    raise ValueError("Unsupported source provider")
