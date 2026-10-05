"""Trusted operator commands; not exposed through MCP or a public admin API."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from runtime import validate_runtime
from security_store import security_store


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    provision = commands.add_parser("provision", help="Assign a verified officeholder using a private JSON file")
    provision.add_argument("--file", required=True, type=Path)
    remove = commands.add_parser("remove-member", help="Remove membership and immediately revoke all MCP grants")
    remove.add_argument("--subject", required=True)
    purge = commands.add_parser("delete-role", help="Delete one owned namespace and revoke the subject's MCP grants")
    purge.add_argument("--subject", required=True)
    purge.add_argument("--role-id", required=True)
    commands.add_parser("retention", help="Run the same sweep scheduled by Celery beat")
    args = parser.parse_args(argv)
    validate_runtime()
    if args.command == "provision":
        payload = json.loads(args.file.read_text(encoding="utf-8"))
        if payload.get("issuer", "").rstrip("/") != os.environ.get("OIDC_ISSUER", "").rstrip("/"):
            parser.error("Membership issuer must equal the configured corporate OIDC_ISSUER")
        subject = security_store().provision(**payload)
        print(json.dumps({"status": "provisioned", "subject": subject}))
    elif args.command == "remove-member":
        security_store().remove_member(args.subject)
        print(json.dumps({"status": "revoked"}))
    elif args.command == "delete-role":
        import uuid
        from service import request_namespace_deletion
        from store import actor_subject, _maintenance
        actor = actor_subject.set(args.subject)
        maintenance = _maintenance.set(True)
        try:
            removed = request_namespace_deletion(str(uuid.UUID(args.role_id)))
            print(json.dumps({"status": "deleted", "chunks_deleted": removed}))
        finally:
            _maintenance.reset(maintenance)
            actor_subject.reset(actor)
    else:
        from service import sweep_expired
        print(json.dumps({"chunks_deleted": sweep_expired()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
