"""Stable tool error codes mapped onto the MCP SDK tool error surface."""

from mcp.server.mcpserver.exceptions import ToolError

DOMAIN_REJECTED = "DOMAIN_REJECTED"
QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
OAUTH_PENDING = "OAUTH_PENDING"
JOB_NOT_FOUND = "JOB_NOT_FOUND"

STABLE_CODES = (
    DOMAIN_REJECTED,
    QUOTA_EXCEEDED,
    OAUTH_PENDING,
    JOB_NOT_FOUND,
)


class CodedToolError(ToolError):
    """Anticipated tool failure carrying one of the four stable codes.

    The SDK turns ``ToolError`` into a tool result with ``is_error`` set and
    the message in a text block. The code is the prefix of that message.
    """

    def __init__(self, code: str, message: str) -> None:
        if code not in STABLE_CODES:
            raise ValueError(f"Unknown error code: {code}")
        self.code = code
        self.detail = message
        super().__init__(f"{code}: {message}")
