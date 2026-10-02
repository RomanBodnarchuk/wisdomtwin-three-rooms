"""Business-domain gate, role-title picklist, and connector availability."""

from __future__ import annotations

import os
import re
import ipaddress

CONSUMER_DOMAINS = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "hotmail.com",
        "outlook.com",
        "yahoo.com",
        "icloud.com",
        "proton.me",
        "protonmail.com",
        "aol.com",
    }
)

ROLE_TITLES = (
    "Chairman",
    "Chief Executive Officer",
    "President",
    "Chief Operating Officer",
    "Chief Financial Officer",
    "Chief Strategy Officer",
    "Chief of Staff",
    "Corporate Secretary",
    "Chief Technology Officer",
    "Chief Information Officer",
    "Chief AI Officer",
    "Chief Information Security Officer",
    "VP of Engineering",
    "VP of Data and Analytics",
    "Chief Revenue Officer",
    "Chief Commercial Officer",
    "Chief Marketing Officer",
    "VP of Sales",
    "VP of Marketing",
    "VP of Customer Success",
    "General Counsel",
    "Chief Compliance Officer",
    "Controller",
    "Treasurer",
    "VP of Human Resources",
    "Head of Talent",
    "VP of Operations",
    "Head of Procurement",
    "VP of Program Management",
    "Head of Business Operations",
)

SERVICES = ("slack", "gmail", "drive")

MONTHLY_CHUNK_QUOTA = 1000
RETENTION_DAYS = 30
EMBEDDING_DIMENSIONS = 1536
CHUNK_TOKENS = 500
CHUNK_OVERLAP_RATIO = 0.20

COMING_SOON = {
    "gmail": "Gmail is coming soon. The connector stays off until Google verification clears.",
    "drive": "Google Drive is coming soon. The connector stays off until Google verification clears.",
}


def _flag(name: str, default: str) -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def connector_enabled(service: str) -> bool:
    if service == "slack":
        from runtime import local_test_mode
        fixture = local_test_mode() and _flag("WISDOMTWIN_USE_FIXTURES", "false")
        return _flag("SLACK_CONNECTOR_ENABLED", "false") and (fixture or _flag("SLACK_POLICY_APPROVED", "false"))
    if service == "gmail":
        return _flag("GMAIL_CONNECTOR_ENABLED", "false") and _flag("GOOGLE_REVIEW_APPROVED", "false")
    if service == "drive":
        return _flag("DRIVE_CONNECTOR_ENABLED", "false") and _flag("GOOGLE_REVIEW_APPROVED", "false")
    return False


def normalize_domain(raw: str) -> str:
    value = raw.strip().lower()
    if "@" in value:
        value = value.rsplit("@", 1)[-1]
    return value.rstrip(".")


def domain_rejection_reason(domain: str) -> str | None:
    if not domain or len(domain) > 253 or "." not in domain or not re.fullmatch(r"[a-z0-9.-]+", domain):
        return "Enter the managed business domain, such as example-corp.com."
    if any(not label or len(label) > 63 or label.startswith("-") or label.endswith("-") for label in domain.split(".")):
        return "Enter a valid managed business domain."
    try:
        ipaddress.ip_address(domain)
        return "A business domain cannot be an IP address."
    except ValueError:
        pass
    for blocked in CONSUMER_DOMAINS:
        if domain == blocked or domain.endswith("." + blocked):
            return f"{domain} is a consumer email domain and cannot be connected."
    return None


def normalize_title(title: str) -> str:
    return " ".join(title.strip().split())
