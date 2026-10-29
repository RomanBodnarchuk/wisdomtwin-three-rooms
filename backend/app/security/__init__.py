"""Microsoft Entra ID ACL & Purview sensitivity enforcement and immutable compliance audit logger."""

from .permissions import AuditLogEntry, ComplianceAuditLogger, PermissionEnforcer

__all__ = [
    "AuditLogEntry",
    "ComplianceAuditLogger",
    "PermissionEnforcer",
]
