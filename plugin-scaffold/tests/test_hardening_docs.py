"""Documented behavior and documentation consistency (review findings L1 and L2, and
follow-up findings F2 to F6 and F8).

L1: on the wire, the stable error code follows the SDK's "Error executing tool <name>: "
prefix. L2: the monthly chunk quota belongs to the signed-in user's organization record,
which is scoped to subject and domain, so colleagues never share it. F2 to F6 and F8: the
records match the measured database results, .env.example, deploy.sh, the startup
requirements, the release validator, the collected test cases and the callback threading.
Fixture Slack and auth-disabled loopback mode only; real sockets fail the test. One test
collects the suite in a subprocess, which opens no connection.
"""

import inspect
import re
import socket
import subprocess
import sys
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

import pytest
from starlette.testclient import TestClient

import domain
import errors
import provider_binding
import runtime
import server
import service
from domain import COMING_SOON, domain_rejection_reason
from errors import CodedToolError
from store import actor_subject, current_store


ROOT = Path(__file__).resolve().parent.parent
BASE = "http://127.0.0.1:8000"
MCP_HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
WIRE_ERROR = re.compile(r"Error executing tool (?P<tool>[a-z_]+): (?P<code>[A-Z_]+): (?P<message>.+)", re.DOTALL)
HARDENED_DOCS = ("README.md", "HANDOVER.md", "REVIEW_FOLLOWUP.md", "SUBMISSION_READINESS.md",
                 "PRODUCTION_LAYOUT.md", "privacy-policy.md")
FINDINGS = ("H1", "H2", "H3", "H4", "M1", "M2", "M3", "M4", "M5", "M6", "L1", "L2", "L3", "L4", "L5")
ADVERSARIAL_FINDINGS = ("SEC-1", "SEC-2", "SEC-3", "G1", "G2", "G3", "G4", "G5", "G6",
                        "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8")
HARDENING_SECTION = "## Independent Claude review and hardening, October 1, 2026"
# Measured on October 1 against fresh loopback services, before the adversarial-review fixes.
POSTGRES_RESULT = "42 passed"
FINAL_OFFLINE_RESULT = "513 passed, 14 skipped"
WORKER_SMOKE = ('{"queued_ingestion": "passed", "chunks_ingested": 10, "source_citations": "passed", '
                '"queued_retention": "passed", "model_api_calls": 0}')
STALE_POSTGRES_CLAIMS = re.compile(r"not run|Neither command was run|Docker VM|disk I/O|Troubleshoot", re.IGNORECASE)
CHATGPT_REDIRECT = "https://chatgpt.com/connector_platform_oauth_redirect"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        pytest.fail("Hardening tests must not open network connections")

    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr("urllib.request.urlopen", refuse)


def tools_call(http: TestClient, name: str, arguments: dict) -> dict:
    response = http.post("/mcp", headers=MCP_HEADERS, json={
        "jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": name, "arguments": arguments}})
    assert response.status_code == 200
    return response.json()["result"]


# L1: the wire format of a coded tool error


@pytest.mark.parametrize(("tool", "arguments", "code", "message"), [
    ("connect_business_account", {"service": "slack", "domain": "gmail.com", "role_title": "CRO"},
     errors.DOMAIN_REJECTED, domain_rejection_reason("gmail.com")),
    ("connect_business_account", {"service": "gmail", "domain": "example-corp.com", "role_title": "CRO"},
     errors.OAUTH_PENDING, COMING_SOON["gmail"]),
    ("ingest_data", {"service": "slack", "query": "pipeline", "max_items": 1001},
     errors.QUOTA_EXCEEDED, "max_items is outside the free-tier monthly quota of 1000 chunks."),
])
def test_stable_code_follows_the_sdk_prefix_on_the_wire(tool, arguments, code, message):
    with TestClient(server.http_app(), base_url=BASE) as http:
        result = tools_call(http, tool, arguments)
    assert result["isError"] is True
    assert result["content"] == [{"type": "text", "text": f"Error executing tool {tool}: {code}: {message}"}]
    text = result["content"][0]["text"]
    assert not text.startswith(code)
    parsed = WIRE_ERROR.fullmatch(text)
    assert parsed is not None
    assert (parsed["tool"], parsed["code"], parsed["message"]) == (tool, code, message)
    assert parsed["code"] in errors.STABLE_CODES


def test_uncoded_tool_errors_carry_only_the_sdk_prefix():
    with TestClient(server.http_app(), base_url=BASE) as http:
        result = tools_call(http, "connect_business_account",
                            {"service": "slack", "domain": "example-corp.com", "role_title": "   "})
    assert result["isError"] is True
    assert result["content"][0]["text"] == "Error executing tool connect_business_account: A role title is required."
    assert WIRE_ERROR.fullmatch(result["content"][0]["text"]) is None


def test_coded_error_text_before_the_sdk_prefix_is_code_then_message():
    error = CodedToolError(errors.JOB_NOT_FOUND, "Ingestion job was not found.")
    assert str(error) == "JOB_NOT_FOUND: Ingestion job was not found."
    assert (error.code, error.detail) == (errors.JOB_NOT_FOUND, "Ingestion job was not found.")
    assert "Error executing tool <name>: <CODE>: <message>" in CodedToolError.__doc__


# L2: the quota belongs to each signed-in user's organization record


@contextmanager
def signed_in(subject: str):
    context = actor_subject.set(subject)
    try:
        yield
    finally:
        actor_subject.reset(context)


def connect(role_title: str = "CRO") -> dict:
    return service.connect_business_account("slack", "example-corp.com", role_title)


def ingest(max_items: int) -> dict:
    return service.ingest_data("slack", "pipeline", max_items)


@pytest.fixture
def ten_chunk_quota(monkeypatch):
    # service imports the constant by name; ingest and store read it from domain at call time.
    monkeypatch.setattr(domain, "MONTHLY_CHUNK_QUOTA", 10)
    monkeypatch.setattr(service, "MONTHLY_CHUNK_QUOTA", 10)


def test_colleagues_at_one_domain_each_have_their_own_quota(ten_chunk_quota):
    store = current_store()
    with signed_in("synthetic-subject-alice"):
        connect()
        assert ingest(10)["chunks_ingested"] == 10
        with pytest.raises(CodedToolError, match="QUOTA_EXCEEDED"):
            ingest(1)
        alice = store.get_organization_by_domain("example-corp.com")
        assert store.monthly_chunk_count(alice.id) == 10
    with signed_in("synthetic-subject-bob"):
        assert store.get_organization_by_domain("example-corp.com") is None
        connect()
        assert ingest(10)["chunks_ingested"] == 10
        bob = store.get_organization_by_domain("example-corp.com")
        assert store.monthly_chunk_count(bob.id) == 10
        # Each record is private to its subject, so one colleague cannot even read the other's count.
        with pytest.raises(CodedToolError, match="AUTHORIZATION_REQUIRED"):
            store.monthly_chunk_count(alice.id)
    assert alice.id != bob.id
    assert alice.domain == bob.domain == "example-corp.com"
    assert (alice.subject, bob.subject) == ("synthetic-subject-alice", "synthetic-subject-bob")


def test_one_users_roles_at_one_domain_share_that_users_quota(ten_chunk_quota):
    store = current_store()
    with signed_in("synthetic-subject-alice"):
        first = connect("CRO")
        assert ingest(10)["chunks_ingested"] == 10
        second = connect("CFO")
        assert first["role_id"] != second["role_id"]
        with pytest.raises(CodedToolError, match="QUOTA_EXCEEDED"):
            ingest(1)
        organization = store.get_organization_by_domain("example-corp.com")
        assert {store.get_role(first["role_id"]).organization_id,
                store.get_role(second["role_id"]).organization_id} == {organization.id}
        assert store.monthly_chunk_count(organization.id) == 10


# Documentation consistency for the hardened behavior


def doc(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def prose(text: str) -> str:
    """Markdown without fenced code blocks or link targets, where style rules apply."""
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"\]\([^)]*\)", "]", text)


@pytest.mark.parametrize("name", HARDENED_DOCS)
def test_hardened_docs_follow_the_house_style(name):
    text = prose(doc(name))
    assert "\u2014" not in text  # the em dash character
    assert "!" not in text
    banned = r"\b(?:delve|landscape|tapestry|game-changer|revolutioni[sz]e|unlock|seamless|robust|leverag\w*|judgment layer|clone)\b"
    assert re.search(banned, text, flags=re.IGNORECASE) is None


@pytest.mark.parametrize("name", ["README.md", "PRODUCTION_LAYOUT.md"])
def test_documented_runtime_defaults_match_the_code(name):
    text = doc(name)
    for variable, default in (("WISDOMTWIN_MAX_SOURCE_FETCHES", runtime.DEFAULT_MAX_SOURCE_FETCHES),
                              ("OPENAI_MAX_OUTPUT_TOKENS", runtime.DEFAULT_OPENAI_MAX_OUTPUT_TOKENS),
                              ("OPENAI_REASONING_EFFORT", runtime.DEFAULT_OPENAI_REASONING_EFFORT)):
        assert re.search(rf"`{variable}`[^\n]*default `{default}`", text), variable
    assert "`OAUTH_CIMD_CLIENT_IDS`" in text
    assert "https://chatgpt.com/oauth/client.json" in text
    assert "https://chatgpt.com/connector_platform_oauth_redirect" in text


def test_quota_wording_matches_the_organization_scope():
    assert domain.MONTHLY_CHUNK_QUOTA == 1000
    readme = doc("README.md")
    assert "1,000 indexed chunks per calendar month" in readme
    assert "organization record" in readme and "not shared across colleagues" in readme
    for name in HARDENED_DOCS:
        assert "per organization per month" not in doc(name)


def test_review_record_lists_every_finding_and_the_postgres_results():
    text = doc("REVIEW_FOLLOWUP.md")
    section = text.split(HARDENING_SECTION, 1)[1]
    for finding in FINDINGS:
        assert re.search(rf"\|\s*{finding}\b", section), finding
    assert "WisdomTwin-PR15-Claude-Review-2026-10-01.md" in section
    adversarial = section.split("### Adversarial review of the hardening diff", 1)[1]
    for finding in ADVERSARIAL_FINDINGS:
        assert re.search(rf"^\|\s*{re.escape(finding)}\.", adversarial, flags=re.MULTILINE), finding
    # F2: both database commands have run, before and after the adversarial-review fixes.
    assert f"**{POSTGRES_RESULT}**" in section
    assert WORKER_SMOKE in section
    assert f"**{FINAL_OFFLINE_RESULT}**" in section and "commit message" not in section
    assert "NOT run" not in section


def readiness_steps() -> list[str]:
    final = doc("SUBMISSION_READINESS.md").rsplit("\n## ", 1)[1]
    return re.split(r"^\d+\. ", final, flags=re.MULTILINE)


def test_readiness_ends_with_ordered_actions_and_no_agent_submission():
    text = doc("SUBMISSION_READINESS.md")
    final = text.rsplit("\n## ", 1)[1]
    assert final.startswith("Roman's next actions, in order")
    assert [int(number) for number in re.findall(r"^(\d+)\. ", final, flags=re.MULTILINE)] == list(range(1, 8))
    assert "Agents must not submit" in final
    # F2: the checks already ran, so the first step is CI on the pushed commit, not a Docker repair.
    assert readiness_steps()[1].startswith("Confirm CI on the pushed commit")
    assert "Docker Desktop" not in final


# F2: the PostgreSQL suite and the worker smoke are recorded as run


@pytest.mark.parametrize("name", HARDENED_DOCS)
def test_no_record_says_the_postgres_checks_were_not_run(name):
    text = doc(name)
    assert STALE_POSTGRES_CLAIMS.search(text) is None
    if name != "privacy-policy.md":
        assert POSTGRES_RESULT in text and FINAL_OFFLINE_RESULT in text and "commit message" not in text


# F3: .env.example and deploy.sh forwarding


def env_example() -> dict[str, str]:
    values = {}
    for line in doc(".env.example").splitlines():
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            values[name] = value
    return values


def deploy_list(name: str) -> list[str]:
    match = re.search(rf"^{name}=\(\n(.*?)^\)", doc("deploy.sh"), flags=re.MULTILINE | re.DOTALL)
    assert match is not None, name
    return match[1].split()


def test_layout_matches_env_example_and_deploy_forwarding():
    example = env_example()
    assert example["OAUTH_CIMD_CLIENT_IDS"] == ""
    assert example["OPENAI_REASONING_EFFORT"] == runtime.DEFAULT_OPENAI_REASONING_EFFORT
    assert example["OPENAI_MAX_OUTPUT_TOKENS"] == str(runtime.DEFAULT_OPENAI_MAX_OUTPUT_TOKENS)
    assert example["WISDOMTWIN_MAX_SOURCE_FETCHES"] == str(runtime.DEFAULT_MAX_SOURCE_FETCHES)
    newer = ("OAUTH_CIMD_CLIENT_IDS", "WISDOMTWIN_MAX_SOURCE_FETCHES", "OPENAI_MAX_OUTPUT_TOKENS")
    assert set(newer) <= set(deploy_list("optional"))

    layout = doc("PRODUCTION_LAYOUT.md")
    assert "`OAUTH_CIMD_CLIENT_IDS` (empty)" in layout
    for name in ("OPENAI_REASONING_EFFORT", "OPENAI_MAX_OUTPUT_TOKENS", "WISDOMTWIN_MAX_SOURCE_FETCHES"):
        assert f"`{name}={example[name]}`" in layout, name
    forwarding = next(part for part in layout.split("\n\n") if part.startswith("`./deploy.sh --deploy`"))
    for name in newer:
        assert f"`{name}`" in forwarding, name
    assert "turns client metadata documents on" in forwarding
    for name in ("PRODUCTION_LAYOUT.md", "REVIEW_FOLLOWUP.md"):
        for stale in ("does not forward", "did not edit", "was not edited", "may be missing from it"):
            assert stale not in doc(name), (name, stale)


# F4: the runbook sets what startup needs before anything depends on it


def production_runtime(patch) -> None:
    for name, value in {
        "WISDOMTWIN_ENV": "production", "PUBLIC_BASE_URL": "https://twin.example.test",
        "WISDOMTWIN_USE_FIXTURES": "0", "WISDOMTWIN_AUTH_DISABLED": "0",
        "DATABASE_URL": "postgresql://synthetic@192.0.2.10/wisdomtwin", "REDIS_URL": "redis://192.0.2.10:6379/0",
        "OAUTH_CLIENT_ID": "synthetic-chatgpt-client", "OAUTH_REDIRECT_URIS": CHATGPT_REDIRECT,
    }.items():
        patch.setenv(name, value)
    for name in ("HOST", "OIDC_ISSUER", "OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET", "OAUTH_CIMD_CLIENT_IDS"):
        patch.delenv(name, raising=False)


def test_runbook_sets_the_startup_oauth_values_before_provisioning(monkeypatch):
    steps = readiness_steps()
    deploy, sign_in = steps[2], steps[3]
    assert deploy.startswith("Build the Railway service")
    assert "`OAUTH_CLIENT_ID`" in deploy and f"`OAUTH_REDIRECT_URIS={CHATGPT_REDIRECT}`" in deploy
    assert "before the first deploy" in deploy
    assert "OIDC is needed for corporate sign-in" in deploy and "not for startup" in deploy
    assert deploy.index("OAUTH_REDIRECT_URIS=") < deploy.index("/health")
    assert "admin.py provision" in sign_in and "railway ssh" in sign_in
    assert "OAuth and OIDC values" not in doc("SUBMISSION_READINESS.md")
    # The code agrees: startup, deploy.sh --check and admin.py need the OAuth client values, not OIDC.
    production_runtime(monkeypatch)
    runtime.validate_runtime()
    for name in ("OAUTH_CLIENT_ID", "OAUTH_REDIRECT_URIS"):
        with monkeypatch.context() as patch:
            patch.delenv(name)
            with pytest.raises(RuntimeError, match=f"Production requires {name}"):
                runtime.validate_runtime()


# F5: the release discovery expectations match the served metadata in code


def test_release_discovery_is_documented_as_aligned():
    readme = doc("README.md")
    assert "do not yet match" not in readme
    assert "`test_discovery_matches_the_release_validator_contract`" in readme
    assert "checked live only during `--release`" in readme
    assert "discovery mismatch" not in doc("SUBMISSION_READINESS.md")
    assert "`test_discovery_matches_the_release_validator_contract`" in readiness_steps()[7]
    auth_tests = (ROOT / "tests" / "test_hardening_auth.py").read_text(encoding="utf-8")
    assert "def test_discovery_matches_the_release_validator_contract(" in auth_tests


# F6: recorded case counts come from the collected suite


def collected_cases(home: Path) -> Counter:
    """Collect the whole suite in a subprocess. Collection imports modules and runs no test."""
    env = {"PATH": f"{Path(sys.executable).parent}:/usr/bin:/bin", "HOME": str(home), "TMPDIR": str(home)}
    result = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "tests"],
                            cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    cases = Counter()
    for line in result.stdout.splitlines():
        if "::" in line:
            path, name = line.split("::", 1)
            cases[(Path(path).name, name.split("[", 1)[0])] += 1
    return cases


def test_recorded_case_counts_match_the_collected_tests(tmp_path):
    cases = collected_cases(tmp_path)
    per_test = {name: count for (_, name), count in cases.items()}
    assert len(per_test) == len(cases)  # test names are unique across files
    per_file = Counter()
    for (path, _), count in cases.items():
        per_file[path] += count
    section = doc("REVIEW_FOLLOWUP.md").split(HARDENING_SECTION, 1)[1]
    validation = section.split("### Validation for this pass", 1)[1]
    for name in ("test_hardening_auth.py", "test_hardening_grants.py", "test_hardening_model.py", "test_hardening_docs.py"):
        recorded = re.search(rf"(\d+)(?: cases)? \(`{re.escape(name)}`\)", validation)
        assert recorded is not None and int(recorded[1]) == per_file[name], name
    # Every test the record names exists, and every case count it states is current. In the
    # evidence tables a name without a count is a single case.
    for line in section.splitlines():
        for match in re.finditer(r"`(?:tests/[\w.]+::)?(test_\w+)`(?: \((\d+)\b)?", line):
            name, recorded = match[1], match[2]
            assert name in per_test, name
            if recorded is not None or line.startswith("|"):
                assert int(recorded or 1) == per_test[name], name
    h3 = next(line for line in section.splitlines() if line.startswith("| H3."))
    assert "`test_metadata_document_fetch_is_pinned_bounded_and_registers_a_public_client`" in h3


# F8: the source callbacks' authorization checks run on the event loop


def test_callback_threading_is_described_accurately():
    text = doc("REVIEW_FOLLOWUP.md")
    assert "source callbacks now run their `SecurityStore`" not in text
    assert "`provider_binding.authorized_callback` still run on the event loop" in text
    for callback in (server.slack_callback, server.google_callback):
        source = inspect.getsource(callback)
        assert source.index("with authorized_callback(") < source.index("anyio.to_thread.run_sync"), callback.__name__
    checks = inspect.getsource(provider_binding.authorized_callback)
    assert "to_thread" not in checks
    assert all(call in checks for call in ("pop_secret", "require_membership", "get_role", "get_organization", "connections()"))
