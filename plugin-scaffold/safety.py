"""Reject obvious restricted data and instruction injection before indexing/output.

This is a conservative filter, not a DLP certification. Provider approval and
customer source selection remain prerequisites for real business data.
"""

from __future__ import annotations

import re

_PATTERNS = (
    r"ignore\s+(?:all\s+)?(?:previous|prior|system|developer)\s+(?:instructions|messages|prompts)",
    r"(?:system|developer)\s*(?:prompt|message)\s*:",
    r"(?:reveal|print|exfiltrate|send)\s+(?:all\s+)?(?:secrets|credentials|tokens|api\s*keys)",
    r"\b(?:sk-[a-zA-Z0-9_-]{16,}|gh[pousr]_[a-zA-Z0-9]{20,}|xox[baprs]-[a-zA-Z0-9-]{10,})\b",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"\b\d{3}-\d{2}-\d{4}\b",
    r"\b(?:passport|government id|social security|credit card|card number|patient|medical record|diagnosis)\b",
)


def unsafe_text(text: str) -> bool:
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in _PATTERNS):
        return True
    for candidate in re.findall(r"\b(?:\d[ -]?){13,19}\b", text):
        digits = [int(char) for char in candidate if char.isdigit()]
        if 13 <= len(digits) <= 19:
            total = sum((digit if i % 2 == 0 else (digit * 2 - 9 if digit > 4 else digit * 2))
                        for i, digit in enumerate(reversed(digits)))
            if total % 10 == 0:
                return True
    return False
