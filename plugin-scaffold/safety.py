"""Reject obvious restricted data and instruction injection before indexing/output.

This is a conservative filter, not a DLP certification. Provider approval and
customer source selection remain prerequisites for real business data.

Two kinds of match are kept apart. Restricted identifiers (API keys, private
keys, SSN-shaped numbers, Luhn-valid card numbers) and instruction injection
are never indexed, answered or returned. Restricted topic words such as
"patient" or "credit card" are ordinary regulated-industry business language:
a question that only mentions them is answered, while source items containing
them are still skipped at ingestion as a conservative restricted-data posture.
"""

from __future__ import annotations

import re

_INJECTION_PATTERNS = (
    r"ignore\s+(?:all\s+)?(?:previous|prior|system|developer)\s+(?:instructions|messages|prompts)",
    r"(?:system|developer)\s*(?:prompt|message)\s*:",
    r"(?:reveal|print|exfiltrate|send)\s+(?:all\s+)?(?:secrets|credentials|tokens|api\s*keys)",
)
_IDENTIFIER_PATTERNS = (
    r"\b(?:sk-[a-zA-Z0-9_-]{16,}|gh[pousr]_[a-zA-Z0-9]{20,}|xox[baprs]-[a-zA-Z0-9-]{10,})\b",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"\b\d{3}-\d{2}-\d{4}\b",
)
_RESTRICTED_TOPIC = r"\b(?:passport|government id|social security|credit card|card number|patient|medical record|diagnosis)\b"

IDENTIFIER_OR_INJECTION = "identifier_or_injection"
RESTRICTED_TOPIC = "restricted_topic"


def _matches(patterns: tuple[str, ...], text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _luhn_number(text: str) -> bool:
    for candidate in re.findall(r"\b(?:\d[ -]?){13,19}\b", text):
        digits = [int(char) for char in candidate if char.isdigit()]
        if 13 <= len(digits) <= 19:
            total = sum((digit if i % 2 == 0 else (digit * 2 - 9 if digit > 4 else digit * 2))
                        for i, digit in enumerate(reversed(digits)))
            if total % 10 == 0:
                return True
    return False


def instruction_injection(text: str) -> bool:
    return _matches(_INJECTION_PATTERNS, text)


def restricted_identifier(text: str) -> bool:
    return _matches(_IDENTIFIER_PATTERNS, text) or _luhn_number(text)


def restricted_topic(text: str) -> bool:
    return re.search(_RESTRICTED_TOPIC, text, flags=re.IGNORECASE) is not None


def identifier_or_injection(text: str) -> bool:
    """True for text that must never be answered, indexed or returned, whatever its topic."""
    return restricted_identifier(text) or instruction_injection(text)


def skip_reason(text: str) -> str | None:
    """Why a source item is not indexed, as a fixed label; None when it may be indexed."""
    if identifier_or_injection(text):
        return IDENTIFIER_OR_INJECTION
    if restricted_topic(text):
        return RESTRICTED_TOPIC
    return None


def unsafe_text(text: str) -> bool:
    """The ingestion rule: identifiers, injection or restricted topic words."""
    return skip_reason(text) is not None
