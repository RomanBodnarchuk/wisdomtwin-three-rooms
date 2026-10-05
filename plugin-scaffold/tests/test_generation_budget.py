"""Synthetic WT-ZAI-4 regressions; no model requests or API spending.

Responses ``max_output_tokens`` includes reasoning and visible output, and an
incomplete result can exhaust that budget before an answer exists. The operator
override is bounded and explicit; without one, the caller's cap is preserved.

Primary API documentation reviewed 2026-10-01:
https://developers.openai.com/api/docs/guides/reasoning
https://developers.openai.com/api/reference/python/resources/responses/methods/create
https://developers.openai.com/api/reference/typescript/resources/responses/methods/retrieve
https://developers.openai.com/api/docs/guides/text
https://developers.openai.com/api/docs/guides/structured-outputs
"""

from __future__ import annotations

from datetime import datetime, timezone
import io
import json
import socket
import urllib.error
import urllib.request

import pytest

from errors import CodedToolError
from generation import EMPTY_CONTEXT, answer_from_context
from store import ChunkRecord


QUESTION = "What are Acme's pipeline and Zenith's renewal status?"
SYNTHETIC_API_KEY = "synthetic-api-key-never-sent"


@pytest.fixture(autouse=True)
def synthetic_responses_only(monkeypatch):
    monkeypatch.setenv("WISDOMTWIN_ALLOW_PAID_MODEL_APIS", "true")
    monkeypatch.setenv("WISDOMTWIN_GENERATION_MODE", "responses")
    monkeypatch.setenv("OPENAI_API_KEY", SYNTHETIC_API_KEY)
    monkeypatch.setenv("OPENAI_GENERATION_MODEL", "gpt-6.1-sol")
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "max")
    monkeypatch.delenv("OPENAI_RESPONSES_MAX_OUTPUT_TOKENS", raising=False)

    def reject_network(*args, **kwargs):
        pytest.fail("These synthetic generation tests must not use the network")

    monkeypatch.setattr(urllib.request, "urlopen", reject_network)
    monkeypatch.setattr(socket, "create_connection", reject_network)


@pytest.fixture
def chunks():
    return [
        ChunkRecord(
            id=f"synthetic-chunk-{index}",
            role_id="synthetic-role",
            tenure_id="synthetic-tenure",
            author_person_id="synthetic-person",
            service="slack",
            uri=f"https://synthetic.example.invalid/record/{index}",
            excerpt=excerpt,
            embedding=[],
            created_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        )
        for index, excerpt in enumerate(
            ("Acme pipeline stage qualified", "Zenith renewal approved"), start=1
        )
    ]


def response_body(claims=None, *, status="completed", message_status="completed"):
    if claims is None:
        claims = [{"text": "Acme pipeline stage qualified", "source_ids": [1]}]
    return {
        "id": "resp_synthetic",
        "object": "response",
        "status": status,
        "error": None,
        "incomplete_details": None,
        "output": [
            {
                "id": "msg_synthetic",
                "type": "message",
                "role": "assistant",
                "status": message_status,
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps({"claims": claims}),
                        "annotations": [],
                    }
                ],
            }
        ],
        "usage": {
            "input_tokens": 100,
            "output_tokens": 400,
            "output_tokens_details": {"reasoning_tokens": 350},
            "total_tokens": 500,
        },
    }


@pytest.fixture
def transport(monkeypatch):
    """Install one deterministic raw HTTP result, recording all attempted calls."""
    requests = []

    def install(body=None, *, error=None, raw_body=None):
        def fake_urlopen(request, *args, **kwargs):
            assert request.full_url == "https://api.openai.com/v1/responses"
            assert request.get_method() == "POST"
            requests.append(json.loads(request.data.decode("utf-8")))
            if error is not None:
                raise error
            return io.BytesIO(raw_body if raw_body is not None else json.dumps(body).encode())

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        return requests

    return install


def assert_generation_failed(chunks, requests, *, expected_calls=1):
    with pytest.raises(CodedToolError) as caught:
        answer_from_context(QUESTION, chunks, max_tokens=512)
    assert caught.value.code == "GENERATION_FAILED"
    assert len(requests) == expected_calls, "Failure must not retry or increase the budget"
    message = str(caught.value)
    assert message.startswith("GENERATION_FAILED: ")
    assert caught.value.detail.strip(), "A generation error must carry safe, explicit diagnostics"
    assert "Retrieved role record" not in message
    assert EMPTY_CONTEXT not in message
    assert SYNTHETIC_API_KEY not in message
    assert "synthetic-private-provider-detail" not in message
    for chunk in chunks:
        assert chunk.excerpt not in message, "Errors must not substitute or expose source text"
    return caught.value


@pytest.mark.parametrize("status", ["incomplete", "failed", "in_progress", "queued", "cancelled"])
def test_noncompleted_response_cannot_publish_plausible_partial_claims(status, chunks, transport):
    body = response_body(status=status)
    if status == "incomplete":
        body["incomplete_details"] = {"reason": "max_output_tokens"}
    if status == "failed":
        body["error"] = {"code": "server_error", "message": "synthetic-private-provider-detail"}
    requests = transport(body)
    assert_generation_failed(chunks, requests)


def test_reasoning_exhaustion_without_visible_output_cannot_fall_back(chunks, transport):
    body = response_body(status="incomplete")
    body["output"] = []
    body["incomplete_details"] = {"reason": "max_output_tokens"}
    body["usage"]["output_tokens"] = 512
    body["usage"]["output_tokens_details"]["reasoning_tokens"] = 512
    requests = transport(body)
    error = assert_generation_failed(chunks, requests)
    assert "max_output_tokens" in str(error), "Report the exhausted cap safely"


@pytest.mark.parametrize("message_status", ["incomplete", "in_progress"])
def test_completed_envelope_does_not_accept_unfinished_message(message_status, chunks, transport):
    requests = transport(response_body(message_status=message_status))
    assert_generation_failed(chunks, requests)


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("{broken-json", id="invalid-json"),
        pytest.param('{}', id="missing-claims"),
        pytest.param('{"claims": null}', id="null-claims"),
        pytest.param('{"claims": false}', id="boolean-claims"),
        pytest.param('{"claims": {}}', id="object-claims"),
        pytest.param('{"claims": [{"text": "Acme pipeline stage qualified", "source_ids": [true]}]}', id="boolean-source-id"),
        pytest.param('{"claims": [{"text": "Acme pipeline stage qualified", "source_ids": [3]}]}', id="unknown-source-id"),
        pytest.param('{"claims": [{"text": "Acme invented forecast", "source_ids": [1]}]}', id="unsupported-fact"),
        pytest.param('{"claims": [{"text": "No Acme pipeline stage qualified", "source_ids": [1]}]}', id="short-negation"),
        pytest.param('{"claims": [{"text": "Acme pipeline stage qualified is 99", "source_ids": [1]}]}', id="short-number"),
        pytest.param('{"claims": [{"text": "Acme pipeline stage qualified in Q3", "source_ids": [1]}]}', id="short-quarter"),
        pytest.param('{"claims": [{"text": "Acme pipeline stage qualified by 5", "source_ids": [1]}]}', id="short-count"),
    ],
)
def test_completed_malformed_or_unsupported_claims_cannot_fall_back(text, chunks, transport):
    body = response_body()
    body["output"][0]["content"][0]["text"] = text
    requests = transport(body)
    assert_generation_failed(chunks, requests)


@pytest.mark.parametrize("failure", ["http-429", "http-503", "transport", "timeout", "invalid-response-json"])
def test_provider_failure_is_visible_and_does_not_retry(failure, chunks, transport):
    if failure.startswith("http-"):
        status = int(failure.rsplit("-", 1)[1])
        requests = transport(
            error=urllib.error.HTTPError(
                "https://api.openai.com/v1/responses",
                status,
                "synthetic-private-provider-detail",
                {},
                io.BytesIO(b"synthetic-private-provider-detail"),
            )
        )
    elif failure == "transport":
        requests = transport(error=urllib.error.URLError("synthetic-private-provider-detail"))
    elif failure == "timeout":
        requests = transport(error=TimeoutError("synthetic-private-provider-detail"))
    else:
        requests = transport(raw_body=b"synthetic-private-provider-detail")
    assert_generation_failed(chunks, requests)


@pytest.mark.parametrize("answer_target", [32, 512, 2048])
def test_unconfigured_total_budget_preserves_caller_cap(answer_target, chunks, transport):
    requests = transport(response_body())
    assert answer_from_context(QUESTION, chunks, max_tokens=answer_target) == "Acme pipeline stage qualified [1]"
    assert len(requests) == 1
    assert requests[0]["max_output_tokens"] == answer_target
    assert requests[0]["model"] == "gpt-6.1-sol"
    assert requests[0]["reasoning"]["effort"] == "max"
    assert requests[0]["store"] is False
    assert "temperature" not in requests[0]


@pytest.mark.parametrize("total_budget", [32, 8192, 32768])
def test_explicit_total_budget_is_independent_of_display_target(total_budget, chunks, transport, monkeypatch):
    monkeypatch.setenv("OPENAI_RESPONSES_MAX_OUTPUT_TOKENS", str(total_budget))
    requests = transport(response_body())
    assert answer_from_context(QUESTION, chunks, max_tokens=512) == "Acme pipeline stage qualified [1]"
    assert len(requests) == 1
    assert requests[0]["max_output_tokens"] == total_budget
    assert requests[0]["reasoning"]["effort"] == "max"


def test_visible_answer_target_is_prompted_without_changing_total_budget(chunks, transport, monkeypatch):
    monkeypatch.setenv("OPENAI_RESPONSES_MAX_OUTPUT_TOKENS", "8192")
    requests = transport(response_body())
    answer_from_context(QUESTION, chunks, max_tokens=512)
    prompt = "\n".join(item["content"] for item in requests[0]["input"])
    assert "512" in prompt, "The answer target must be communicated separately to the model"
    assert requests[0]["max_output_tokens"] == 8192


@pytest.mark.parametrize("configured", ["not-an-integer", "1.5", "31", "32769", ""])
def test_invalid_total_budget_fails_before_request(configured, chunks, transport, monkeypatch):
    monkeypatch.setenv("OPENAI_RESPONSES_MAX_OUTPUT_TOKENS", configured)
    requests = transport(response_body())
    assert_generation_failed(chunks, requests, expected_calls=0)


def test_completed_supported_claims_keep_their_source_citations(chunks, transport):
    requests = transport(
        response_body(
            [
                {"text": "Acme pipeline stage qualified", "source_ids": [1]},
                {"text": "Zenith renewal approved", "source_ids": [2]},
            ]
        )
    )
    assert answer_from_context(QUESTION, chunks, max_tokens=512) == (
        "Acme pipeline stage qualified [1]\nZenith renewal approved [2]"
    )
    assert len(requests) == 1


def test_supported_number_that_appears_in_the_excerpt_is_kept(chunks, transport):
    chunks[0].excerpt = "Acme pipeline stage 3"
    requests = transport(response_body([{"text": "Acme pipeline stage 3", "source_ids": [1]}]))
    assert answer_from_context(QUESTION, chunks, max_tokens=512) == "Acme pipeline stage 3 [1]"
    assert len(requests) == 1


def test_completed_empty_claims_are_exact_abstention(chunks, transport):
    requests = transport(response_body([]))
    assert answer_from_context(QUESTION, chunks, max_tokens=512) == "I have nothing ingested on that."
    assert len(requests) == 1


def test_empty_context_abstains_without_model_request():
    assert answer_from_context(QUESTION, [], max_tokens=512) == EMPTY_CONTEXT


def test_operator_budget_cannot_enable_spending_without_opt_in(chunks, monkeypatch):
    monkeypatch.setenv("WISDOMTWIN_ALLOW_PAID_MODEL_APIS", "false")
    monkeypatch.setenv("OPENAI_RESPONSES_MAX_OUTPUT_TOKENS", "8192")
    answer = answer_from_context(QUESTION, chunks, max_tokens=512)
    assert answer.startswith("Retrieved role record (untrusted source data):\n")
    assert "[1] Acme pipeline stage qualified" in answer


@pytest.mark.parametrize("include_claim", [False, True], ids=["refusal-only", "refusal-after-claim"])
def test_completed_refusal_is_an_explicit_failure(include_claim, chunks, transport):
    body = response_body()
    content = body["output"][0]["content"] if include_claim else []
    content.append({"type": "refusal", "refusal": "synthetic-private-provider-detail"})
    body["output"][0]["content"] = content
    requests = transport(body)
    error = assert_generation_failed(chunks, requests)
    assert "refus" in error.detail.lower()


@pytest.mark.parametrize("conflict", ["incomplete-response", "incomplete-message", "refusal-message"])
def test_raw_convenience_text_cannot_override_native_failure(conflict, chunks, transport):
    body = response_body()
    # output_text is an SDK convenience property, not our raw HTTP text source.
    body["output_text"] = body["output"][0]["content"][0]["text"]
    if conflict == "incomplete-response":
        body["status"] = "incomplete"
        body["incomplete_details"] = {"reason": "max_output_tokens"}
    elif conflict == "incomplete-message":
        body["output"][0]["status"] = "incomplete"
    else:
        body["output"][0]["content"] = [
            {"type": "refusal", "refusal": "synthetic-private-provider-detail"}
        ]
    requests = transport(body)
    assert_generation_failed(chunks, requests)


def test_raw_convenience_text_does_not_replace_missing_native_output(chunks, transport):
    body = response_body()
    body["output_text"] = body["output"][0]["content"][0]["text"]
    del body["output"]
    requests = transport(body)
    assert_generation_failed(chunks, requests)


@pytest.mark.parametrize("body", [None, [], "synthetic-private-provider-detail", 42])
def test_nonobject_response_envelope_has_safe_coded_error(body, chunks, transport):
    requests = transport(body)
    assert_generation_failed(chunks, requests)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("output", None, id="null-output"),
        pytest.param("output", {}, id="object-output"),
        pytest.param("output", "synthetic-private-provider-detail", id="string-output"),
        pytest.param("output", [None], id="null-output-item"),
        pytest.param("content", None, id="null-content"),
        pytest.param("content", {"type": "output_text", "text": "{}"}, id="object-content"),
        pytest.param("content", "synthetic-private-provider-detail", id="string-content"),
        pytest.param("content", [None], id="null-content-item"),
        pytest.param("content", [42], id="numeric-content-item"),
        pytest.param("content", ["synthetic-private-provider-detail"], id="string-content-item"),
        pytest.param("content", [[]], id="array-content-item"),
    ],
)
def test_malformed_output_or_content_envelope_is_a_coded_failure(field, value, chunks, transport):
    body = response_body()
    if field == "output":
        body["output"] = value
    else:
        body["output"][0]["content"] = value
    requests = transport(body)
    assert_generation_failed(chunks, requests)


def test_completed_response_with_error_envelope_rejects_plausible_claims(chunks, transport):
    body = response_body()
    body["error"] = {"code": "server_error", "message": "synthetic-private-provider-detail"}
    requests = transport(body)
    assert_generation_failed(chunks, requests)


def test_malformed_incomplete_details_cannot_escape_coded_error(chunks, transport):
    body = response_body(status="incomplete")
    body["incomplete_details"] = "synthetic-private-provider-detail"
    requests = transport(body)
    assert_generation_failed(chunks, requests)
