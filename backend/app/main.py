"""FastAPI application exposing the WisdomTwin Copilot Plugin REST endpoints and Audio Huddle API.

Implements the exact OpenAPI 3.1 paths required for Microsoft 365 Copilot Declarative Agent certification:
- POST /twin/query        (operationId: queryTwin)
- GET  /twin/roles        (operationId: listRoles)
- GET  /twin/judgments/{judgment_id} (operationId: getJudgment)
- POST /twin/huddle       (operationId: startHuddle)
- POST /twin/huddle/turn  (operationId: runHuddleTurn)
- GET  /twin/audit        (operationId: listAuditLogs)
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .extraction.engine import DecisionExtractionEngine
from .graph.context_graph import TemporalContextGraph
from .huddle.orchestrator import AudioHuddleOrchestrator
from .ingestion.ms_graph import MicrosoftGraphConnector, WebhookChangeNotification
from .schemas.decision_episode import (
    DecisionEpisode,
    HuddleStartRequest,
    HuddleStartResponse,
    HuddleTurnRequest,
    HuddleTurnResponse,
    QueryTwinRequest,
    QueryTwinResponse,
    RoleSummary,
)
from .seed.demo_corpus import seed_canonical_demo_graph

app = FastAPI(
    title="WisdomTwin Enterprise Judgment & Copilot API",
    version="3.8.0",
    description=(
        "Ask role-specific digital twins about the judgment behind past decisions — why leaders "
        "chose what they chose, what alternatives they rejected, and where governance gates apply."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize canonical Temporal Context Graph and Huddle Orchestrator
context_graph = seed_canonical_demo_graph(TemporalContextGraph())
huddle_orchestrator = AudioHuddleOrchestrator(context_graph)
graph_connector = MicrosoftGraphConnector()
extraction_engine = DecisionExtractionEngine()


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "wisdomtwin-enterprise-api",
        "version": "3.8.0",
        "tagline": "WisdomTwin preserves institutional judgment.",
        "episodes_loaded": len(context_graph.list_episodes()),
    }


@app.post(
    "/twin/query",
    response_model=QueryTwinResponse,
    operation_id="queryTwin",
    summary="Ask a role's digital twin a question about past decisions and precedent",
    tags=["CopilotPlugin"],
)
def query_twin(request: QueryTwinRequest) -> QueryTwinResponse:
    """Queries the role-specific temporal context graph with Entra ACL and Purview label enforcement."""
    return context_graph.query_precedent(request)


@app.get(
    "/twin/roles",
    response_model=List[RoleSummary],
    operation_id="listRoles",
    summary="List all executive role twins, document counts, and historical date ranges covered",
    tags=["CopilotPlugin"],
)
def list_roles() -> List[RoleSummary]:
    """Returns every executive role that has a Wisdom Twin built with its coverage metadata."""
    return context_graph.get_role_summaries()


@app.get(
    "/twin/judgments/{judgment_id}",
    response_model=DecisionEpisode,
    operation_id="getJudgment",
    summary="Drill into a specific DecisionEpisode record, verbatim evidence, and dissent notes",
    tags=["CopilotPlugin"],
)
def get_judgment(judgment_id: str) -> DecisionEpisode:
    """Returns the full DecisionEpisode node from the temporal context graph."""
    episode = context_graph.get_episode(judgment_id)
    if episode is None:
        raise HTTPException(status_code=404, detail=f"Judgment '{judgment_id}' not found")
    return episode


@app.post(
    "/twin/huddle",
    response_model=HuddleStartResponse,
    operation_id="startHuddle",
    summary="Start a multi-role Audio Executive Huddle session",
    tags=["CopilotPlugin", "AudioHuddle"],
)
def start_huddle(request: HuddleStartRequest) -> HuddleStartResponse:
    """Initializes an Audio Executive Huddle session across selected executive role twins."""
    return huddle_orchestrator.start_huddle(request)


@app.post(
    "/twin/huddle/turn",
    response_model=HuddleTurnResponse,
    operation_id="runHuddleTurn",
    summary="Send a spoken or typed executive prompt into an active Audio Huddle session",
    tags=["AudioHuddle"],
)
def run_huddle_turn(request: HuddleTurnRequest) -> HuddleTurnResponse:
    """Routes the prompt to the relevant role twins, enforces safe decline, and returns voice + UI state."""
    return huddle_orchestrator.process_turn(request)


@app.post(
    "/webhooks/ms-graph",
    summary="Receive Microsoft Graph change notifications and trigger incremental delta sync (<3s ack)",
    tags=["Ingestion"],
)
async def ms_graph_webhook(notifications: List[WebhookChangeNotification]) -> Dict[str, Any]:
    """Acknowledges Microsoft Graph webhook notifications within 3 seconds and queues delta sync."""
    return await graph_connector.handle_webhook_notification(
        notifications=notifications,
        expected_client_state="wisdomtwin-graph-secret-state",
        trigger_delta_callback=lambda resource: {"triggered": resource},
    )


@app.get(
    "/twin/audit",
    summary="Inspect compliance audit records for Purview & Entra ID access reviews",
    tags=["Compliance"],
)
def list_audit_logs() -> List[Dict[str, Any]]:
    return [entry.model_dump() for entry in context_graph.audit_logger.list_entries()]
