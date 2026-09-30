"""Read-only fetchers. Slack is the production path. Gmail and Drive run only when enabled."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "slack" / "messages.json"


def use_fixtures() -> bool:
    return os.environ.get("WISDOMTWIN_USE_FIXTURES", "").strip().lower() in {"1", "true", "yes", "on"}


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
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Connector request failed with status {exc.code}") from None


def fetch_slack(token: str, query: str, max_items: int) -> list[dict[str, str]]:
    if use_fixtures() or not token:
        if use_fixtures():
            return load_slack_fixtures(max_items)
        raise RuntimeError("Slack is not connected for this role")
    params = urllib.parse.urlencode({"query": query or "in:#general", "count": min(max_items, 100)})
    body = _request_json(f"https://slack.com/api/search.messages?{params}", token)
    if not body.get("ok", True) and body.get("error"):
        raise RuntimeError("Slack search was rejected")
    matches = body.get("messages", {}).get("matches", [])
    items: list[dict[str, str]] = []
    for match in matches[:max_items]:
        channel = (match.get("channel") or {}).get("id", "channel")
        timestamp = str(match.get("ts", "")).replace(".", "")
        text = match.get("text") or ""
        if not text:
            continue
        items.append(
            {
                "uri": f"https://slack.com/archives/{channel}/p{timestamp}",
                "text": text,
            }
        )
    return items


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
        snippet = detail.get("snippet") or ""
        if not snippet:
            continue
        items.append(
            {
                "uri": f"https://mail.google.com/mail/u/0/#inbox/{message['id']}",
                "text": snippet,
            }
        )
    return items


def fetch_drive(token: str, query: str, max_items: int) -> list[dict[str, str]]:
    safe_query = query.replace("\\", "\\\\").replace("'", "\\'")
    drive_query = f"fullText contains '{safe_query}'" if query else "trashed = false"
    listed = _request_json(
        "https://www.googleapis.com/drive/v3/files?"
        + urllib.parse.urlencode(
            {
                "q": drive_query,
                "pageSize": min(max_items, 100),
                "fields": "files(id,name,description)",
            }
        ),
        token,
    )
    items: list[dict[str, str]] = []
    for file_row in listed.get("files", [])[:max_items]:
        text = " ".join(part for part in (file_row.get("name"), file_row.get("description")) if part)
        if not text:
            continue
        items.append(
            {
                "uri": f"https://drive.google.com/file/d/{file_row['id']}/view",
                "text": text,
            }
        )
    return items
