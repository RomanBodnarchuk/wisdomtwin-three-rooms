"""Stable tool error codes mapped onto the MCP SDK tool error surface."""

from mcp.server.mcpserver.exceptions import ToolError

AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
CONNECTOR_FAILED = "CONNECTOR_FAILED"

DOMAIN_REJECTED = "DOMAIN_REJECTED"
QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
OAUTH_PENDING = "OAUTH_PENDING"
JOB_NOT_FOUND = "JOB_NOT_FOUND"

STABLE_CODES = (
    AUTHORIZATION_REQUIRED,
    CONNECTOR_FAILED,
    DOMAIN_REJECTED,
    QUOTA_EXCEEDED,
    OAUTH_PENDING,
    JOB_NOT_FOUND,
)


class CodedToolError(ToolError):
    """Anticipated tool failure carrying a stable application error code.

    The exception text is "<CODE>: <message>". The pinned SDK re-raises every
    ``ToolError`` with its own prefix and returns a tool result with
    ``is_error`` set, so the client reads one text block:
    "Error executing tool <name>: <CODE>: <message>". The stable code follows
    that SDK prefix; it does not start the text.
    """

    def __init__(self, code: str, message: str) -> None:
        if code not in STABLE_CODES:
            raise ValueError(f"Unknown error code: {code}")
        self.code = code
        self.detail = message
        super().__init__(f"{code}: {message}")
