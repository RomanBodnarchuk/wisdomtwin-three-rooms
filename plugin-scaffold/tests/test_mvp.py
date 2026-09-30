"""Ten MVP cases for the role twin tools."""

import json

import anyio
import pytest
from mcp.server.mcpserver.exceptions import ToolError

import server
from store import ChunkRecord, current_store, reset_store


@pytest.fixture(autouse=True)
def _fresh_store():
    reset_store()
    yield
    reset_store()


def call(name: str, arguments: dict):
    async def _run():
        return await server.mcp.call_tool(name, arguments)

    return anyio.run(_run)


def as_json(result):
    return json.loads(result.content[0].text)


def test_connect_creates_org_role_and_tenure():
    result = as_json(
        call(
            "connect_business_account",
            {"service": "slack", "domain": "example-corp.com", "role_title": "CRO"},
        )
    )
    store = current_store()
    organization = store.get_organization_by_domain("example-corp.com")
    assert organization is not None
    assert organization.domain == "example-corp.com"
    assert store.role_count_for_domain("example-corp.com") == 1
    assert store.open_tenure_count(result["role_id"]) == 1
    tenure = store.find_open_tenure(result["role_id"])
    assert tenure is not None
    assert tenure.started_on is not None
    assert tenure.ended_on is None
    assert result["status"] == "authorization_required"
    assert "code_challenge=" in result["oauth_url"]
    assert "slack.com/oauth" in result["oauth_url"]
    assert any(row.tool_name == "connect_business_account" for row in store.audits())


def test_second_connect_reuses_the_role():
    first = as_json(
        call(
            "connect_business_account",
            {"service": "slack", "domain": "example-corp.com", "role_title": "CRO"},
        )
    )
    second = as_json(
        call(
            "connect_business_account",
            {"service": "slack", "domain": "example-corp.com", "role_title": "CRO"},
        )
    )
    store = current_store()
    assert first["role_id"] == second["role_id"]
    assert store.role_count_for_domain("example-corp.com") == 1
    assert store.open_tenure_count(first["role_id"]) == 1


def test_slack_fixtures_reach_ten_chunks_with_tenure_metadata():
    connected = as_json(
        call(
            "connect_business_account",
            {"service": "slack", "domain": "example-corp.com", "role_title": "CRO"},
        )
    )
    ingested = as_json(call("ingest_data", {"service": "slack", "query": "pipeline", "max_items": 10}))
    assert ingested["progress"] == 100
    assert ingested["chunks_ingested"] == 10
    chunks = current_store().chunks_for_role(connected["role_id"])
    assert len(chunks) == 10
    tenure = current_store().find_open_tenure(connected["role_id"])
    assert tenure is not None
    assert all(chunk.tenure_id == tenure.id for chunk in chunks)
    assert all(chunk.author_person_id == tenure.person_id for chunk in chunks)


def test_query_returns_an_answer_with_a_citation():
    connected = as_json(
        call(
            "connect_business_account",
            {"service": "slack", "domain": "example-corp.com", "role_title": "CRO"},
        )
    )
    call("ingest_data", {"service": "slack", "query": "pipeline", "max_items": 10})
    other = ChunkRecord(
        id="00000000-0000-0000-0000-000000000099",
        role_id="00000000-0000-0000-0000-000000000088",
        tenure_id="00000000-0000-0000-0000-000000000077",
        author_person_id="00000000-0000-0000-0000-000000000066",
        service="slack",
        uri="https://example-corp.example/slack/other-role",
        excerpt="A different role namespace mentions a secret project name Zephyr.",
        embedding=[0.0] * 1536,
        created_at=current_store().chunks_for_role(connected["role_id"])[0].created_at,
    )
    current_store().upsert_chunks([other])
    result = call("query_twin", {"question": "What is the Acme pipeline stage?"})
    assert result.content[0].text
    assert "nothing ingested" not in result.content[0].text.lower()
    citations = []
    for block in result.content[1:]:
        payload = json.loads(block.resource.text)
        citations.append(payload)
    assert citations
    assert all("uri" in item and "snippet" in item for item in citations)
    assert all(item["uri"] != other.uri for item in citations)


def test_status_lists_role_and_domain():
    call(
        "connect_business_account",
        {"service": "slack", "domain": "example-corp.com", "role_title": "CRO"},
    )
    result = call("list_twins_status", {})
    rows = [json.loads(block.text) for block in result.content]
    assert rows
    assert rows[0]["role_title"] == "CRO"
    assert rows[0]["domain"] == "example-corp.com"
    assert rows[0]["service"] == "slack"


def test_deletion_clears_the_namespace():
    from service import request_namespace_deletion

    connected = as_json(
        call(
            "connect_business_account",
            {"service": "slack", "domain": "example-corp.com", "role_title": "CRO"},
        )
    )
    call("ingest_data", {"service": "slack", "query": "pipeline", "max_items": 10})
    assert len(current_store().chunks_for_role(connected["role_id"])) == 10
    removed = request_namespace_deletion(connected["role_id"])
    assert removed == 10
    assert current_store().chunks_for_role(connected["role_id"]) == []
    result = call("query_twin", {"question": "What is the Acme pipeline stage?"})
    assert result.content[0].text == "I have nothing ingested on that."


def test_consumer_domain_is_rejected():
    with pytest.raises(ToolError) as caught:
        call(
            "connect_business_account",
            {"service": "slack", "domain": "gmail.com", "role_title": "CRO"},
        )
    assert "DOMAIN_REJECTED" in str(caught.value)
    assert current_store().get_organization_by_domain("gmail.com") is None


def test_query_on_empty_index_returns_no_context_message():
    result = call("query_twin", {"question": "What did the board decide about pricing?"})
    assert result.content[0].text == "I have nothing ingested on that."


def test_max_items_over_quota_returns_quota_exceeded():
    with pytest.raises(ToolError) as caught:
        call("ingest_data", {"service": "slack", "query": "pipeline", "max_items": 1001})
    assert "QUOTA_EXCEEDED" in str(caught.value)


def test_gmail_ingest_while_gated_returns_availability_message():
    with pytest.raises(ToolError) as caught:
        call("ingest_data", {"service": "gmail", "query": "budget", "max_items": 10})
    message = str(caught.value)
    assert "OAUTH_PENDING" in message
    assert "coming soon" in message
