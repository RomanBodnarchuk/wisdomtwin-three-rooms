"""End-to-end verification tests for the WisdomTwin backend, Graph ingestion,
Decision-Episode extraction, Purview/Entra permission layer, and Audio Huddle orchestrator.
"""

from __future__ import annotations

import asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.ingestion.ms_graph import MicrosoftGraphConnector
from app.schemas.decision_episode import (
    PurviewRight,
    QueryTwinRequest,
    RoleTag,
    SourceSystem,
)

client = TestClient(app)


def test_health_endpoint() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["tagline"] == "WisdomTwin preserves institutional judgment."
    assert body["episodes_loaded"] >= 8


def test_list_roles_endpoint() -> None:
    res = client.get("/twin/roles")
    assert res.status_code == 200
    roles = res.json()
    role_ids = {r["role"] for r in roles}
    assert {"CFO", "CTO", "CRO", "CMO", "LEGAL", "CEO"}.issubset(role_ids)


def test_query_cfo_twin_preserves_non_negotiable_numbers_and_drift() -> None:
    res = client.post(
        "/twin/query",
        json={
            "question": "What is the board spending cap and can Phase one fit beneath it?",
            "role": "CFO",
            "time_range": "all_time",
            "top_k": 5,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["safe_decline_active"] is False
    assert "$11M" in data["answer"] or "eleven million" in data["answer"].lower()
    assert "$7.4M" in data["answer"] or "seven point four" in data["answer"].lower()
    # Includes both 2026 cap and superseded 2019 precedent via SUPERSEDES graph edge
    judgment_ids = [j["judgment_id"] for j in data["judgments"]]
    assert "ep_cfo_cap_2026" in judgment_ids
    assert "ep_cfo_cap_2019" in judgment_ids


def test_query_cto_safe_decline_triggers_named_human_escalation() -> None:
    res = client.post(
        "/twin/query",
        json={
            "question": "Can we handle peak-load throughput at the proposed volume on day one?",
            "role": "CTO",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["safe_decline_active"] is True
    assert data["governance_action"] == "safe_decline"
    assert data["escalation_reviewer"] == "Vice President of Clinical Operations"
    assert data["estimated_review_minutes"] == 38


def test_get_judgment_by_id() -> None:
    res = client.get("/twin/judgments/ep_legal_gates_2026")
    assert res.status_code == 200
    ep = res.json()
    assert ep["role"] == "LEGAL"
    assert any(c["is_counterfactual_boundary"] for c in ep["constraints_and_thresholds"])


def test_start_huddle_and_run_turn() -> None:
    start_res = client.post(
        "/twin/huddle",
        json={
            "roles": ["CFO", "CTO", "CRO", "CMO", "LEGAL"],
            "topic": "Thursday Board Packet — Prior-Authorization AI",
            "voice_provider": "grok_voice_3",
        },
    )
    assert start_res.status_code == 200
    session = start_res.json()
    assert session["session_id"].startswith("hud_")
    assert session["voice_provider"] == "grok_voice_3"

    turn_res = client.post(
        "/twin/huddle/turn",
        json={
            "session_id": session["session_id"],
            "prompt": "What are the budget cap and public cloud PHI constraints?",
        },
    )
    assert turn_res.status_code == 200
    turn_data = turn_res.json()
    assert len(turn_data["turns"]) >= 2
    assert len(turn_data["blockers"]) == 5
    assert len(turn_data["board_artifacts"]) == 7


def test_delta_query_persists_token_only_after_downstream_commit() -> None:
    connector = MicrosoftGraphConnector()
    committed_docs = []

    def fake_graph_page(_prior_token: str | None) -> dict:
        return {
            "value": [
                {
                    "id": "msg-cfo-001",
                    "subject": "March Board Cap $11M Vote 7-2",
                    "bodyPreview": "The board capped new-program spending at $11M. Vote 7-2.",
                    "createdDateTime": "2026-03-18T16:00:00",
                    "entraGroupIds": ["grp-cfo-office"],
                    "sensitivityLabel": {"id": "lbl-conf", "name": "Confidential"},
                    "author": {
                        "id": "entra-cfo-2026",
                        "displayName": "Elena Vance",
                        "emailAddress": "elena.vance@enterprise.local",
                        "jobTitle": "Chief Financial Officer",
                    },
                }
            ],
            "@odata.deltaLink": "https://graph.microsoft.com/v1.0/users/cfo/messages/delta?$deltatoken=tok_abc123",
        }

    result = asyncio.run(
        connector.sync_delta_resource(
            resource_key="users/cfo/messages",
            source_system=SourceSystem.MS_GRAPH_MAIL,
            fetch_page_fn=fake_graph_page,
            downstream_sink=lambda docs: committed_docs.extend(docs),
        )
    )
    assert len(committed_docs) == 1
    assert result["delta_link"].endswith("tok_abc123")
    assert connector.token_store.get_delta_link("users/cfo/messages") == result["delta_link"]


def test_purview_and_entra_acl_enforcement_excludes_unauthorized_requester() -> None:
    from app.main import context_graph

    # Unauthorized user not in allowed_user_ids or allowed_group_ids receives 0 judgments
    res = context_graph.query_precedent(
        QueryTwinRequest(
            question="What is the $11M board spending cap?",
            role=RoleTag.CFO,
            requester_upn="external.contractor@vendor.example",
            requester_groups=["grp-external-guests"],
        )
    )
    assert res.safe_decline_active is True
    # Audit log records ACL exclusions
    latest_audit = context_graph.audit_logger.list_entries(limit=1)[0]
    assert latest_audit.excluded_by_acl_count >= 1

    # User with VIEW only (missing EXTRACT right) is blocked by Purview enforcement
    context_graph.permission_enforcer.grant_user_rights(
        "elena.vance@enterprise.local", [PurviewRight.VIEW]
    )
    res_no_extract = context_graph.query_precedent(
        QueryTwinRequest(
            question="What is the $11M board spending cap?",
            role=RoleTag.CFO,
            requester_upn="elena.vance@enterprise.local",
            requester_groups=["grp-exec-officers"],
        )
    )
    latest_audit_purview = context_graph.audit_logger.list_entries(limit=1)[0]
    assert latest_audit_purview.excluded_by_purview_count >= 1
    assert len(res_no_extract.citations) == 0
    # Restore default rights
    context_graph.permission_enforcer.grant_user_rights(
        "elena.vance@enterprise.local", [PurviewRight.VIEW, PurviewRight.EXTRACT]
    )
