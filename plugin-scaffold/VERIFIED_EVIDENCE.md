# Tested hardening checkpoint — October 1, 2026

This is a tested private candidate for PR [15](https://github.com/RomanBodnarchuk/wisdomtwin-three-rooms/pull/15), branch `cursor/wisdomtwin-mcp-plugin-8d09`. It is not a completed public deployment, provider approval, legal adoption or directory submission.

## Environment and baseline

- Saved cloud workspace: `/workspace/wisdomtwin-three-rooms`; Python 3.12.14.
- Continued the existing branch at `de212df4b15711864f7f042613cfc11641ef2692`, after fetching its current remote head. No second scaffold was generated. Repository/root instruction and skill locations were inspected before editing.
- Before changes: the original twelve fixture cases passed, and `./package.sh --check` passed. These were synthetic tests, not live source grants.
- The final exact source commit, archive hash and candidate ZIP hash are recorded in the private artifact directory's `CHECKPOINT.json`. GitHub CI results are separate evidence; local success does not establish a remote run.

## Resulting behavior

Corporate OIDC signature, issuer, subject, audience, nonce and verified email establish a stable identity. Operator-assigned domain, role and source-account membership governs access; user-supplied domain/title text confers no entitlement. Postgres stores encrypted, durable OAuth state with one-use codes/refresh rotation, resource/scope validation and grant-family revocation. Source callbacks bind Google identity or Slack workspace/user and corporate email to the provisioned member. Store operations, callbacks, jobs and retrieval enforce subject and role access.

Production rejects fixture/auth-disabled mode and requires HTTPS, durable database, queue and configured MCP client. Local synthetic mode requires explicit local/test configuration and loopback host/origin; it must never be placed behind a public tunnel.

Real ingestion retains vectors and protected provenance/keyword metadata, with raw provider excerpts transient. Retrieval re-fetches under the current user's bound source grant, validates content hash and authorship, and withholds changed, deleted, inaccessible or unsafe source material. Missing support returns exactly `I have nothing ingested on that.` Returned snippets cover the source evidence; source instructions are treated as untrusted data. Default generation is extractive for ChatGPT synthesis. Backend embeddings and optional Responses generation require explicit API spending opt-in; no paid model API calls were made for this checkpoint.

Actual chunk expansion is checked before embedding and at atomic database commit. Worker deliveries use per-job exclusion; PostgreSQL enforces one open tenure per role. Jobs report status through authenticated `GET /jobs/{job_id}`. Authenticated `DELETE /roles/{role_id}` clears the namespace, credentials, connections, jobs, pending source state and role metadata, then revokes MCP grants. A daily Celery beat task deletes inactive namespaces after the 30-day cutoff and sweeps expired security state/minimal audit events. Operator membership is removed separately with the trusted CLI.

Exactly the original four MCP tools and their input signatures remain; Query Twin and Update Twin are the only packaged skills. No source-system write tool, model training, custom UI, interview, huddle or predecessor feature was added.

## Reproduced validation

| Check | Observed result | Limit |
| --- | --- | --- |
| Fresh hash-locked Python environment | 52 pinned dependencies installed with `uv pip sync --require-hashes requirements.lock` | The lock targets Python 3.12; no floating install used for the evidence. |
| Complete offline suite | **119 passed, 3 skipped** | The three explicit PostgreSQL cases skip unless the isolated test URL is set. |
| Isolated PostgreSQL/pgvector suite | **20 passed** | Original twelve MVP cases, five worker/tenure cases and three database security/deletion cases; synthetic data only. |
| Real Celery + Redis + PostgreSQL worker smoke | Queued ingestion completed with **10 chunks**, source citations and queued retention/deletion passed | Loopback services, synthetic fixtures and ephemeral test encryption key; no source or model API calls. |
| Serialized official SDK tool scan | Four names, arguments/defaults, annotations and per-tool OAuth metadata passed | Local SDK serialization, not a public HTTPS/provider test. |
| Package suite | **16 passed** within the complete suite | Offline mutation, exclusion, ZIP integrity/determinism and release refusal tests. |
| Offline candidate validation | Complete vendored official schemas, listing fields, safe paths, square SVG, two skills and exact four signatures passed | Structural checks do not establish adoption/approval or reachable hosting. |
| Deterministic candidate ZIP | Five members; repeated bytes identical; SHA-256 below | Explicitly not for submission; placeholder MCP/legal URLs preserved. |
| Container dependency/runtime check | Offline wheelhouse build from the pinned base and identical hash-locked source passed; `pip check` passed; unconfigured production startup was rejected | Normal online Docker build could not resolve the package index in this cloud environment. Offline verification changed only the install transport to local hashed wheels. Hosting's normal online build remains unverified. |
| Syntax/patch checks | Python compile and shell syntax checks; `git diff --check` passed | Not a certification or an independent penetration test. |

PostgreSQL image: `pgvector/pgvector:pg16@sha256:ccc6e83d6e35e931dc7c5def2022729d5a6c370318d099181995567ff1fb4d6b`.
Redis image: `redis:7-alpine@sha256:858f009f9709ce576febc734aa78b8f6d624b82571f9ddb6bda4377c833b3499`.
Python base: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.

```bash
python3 -m pip install --require-hashes -r requirements.lock
python3 -m pytest -q --tb=short
WISDOMTWIN_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/wisdomtwin_test \
  python3 -m pytest -q tests/test_mvp.py tests/test_worker_concurrency.py tests/test_database.py --tb=short
WISDOMTWIN_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/wisdomtwin_test \
WISDOMTWIN_TEST_REDIS_URL=redis://127.0.0.1:56379/9 \
  python3 scripts/verify_local_worker.py
./package.sh --check
./package.sh --candidate --output-dir /workspace/wisdomtwin-plugin-artifacts
```

The database/worker commands reset the explicitly isolated test database. CI uses disposable services, pinned action/image references and the same checks. It has no deployment or submission action.

## Candidate artifact

`/workspace/wisdomtwin-plugin-artifacts/wisdomtwin-candidate-NOT-FOR-SUBMISSION.zip`

SHA-256: `ff5047ea054aa96ae357c164bd57b697c525cbcd4666a755aa8ad68d292ef1aa`.

Members: `plugin.json`, `mcp.json`, `assets/logo.svg`, `skills/query-twin/SKILL.md`, `skills/update-twin/SKILL.md`. Hash/inventory sidecars accompany the ZIP. Source code, legal drafts, fixtures, credentials and reviewer material are excluded. Production packaging refuses the placeholder host before producing a release ZIP.

## Remaining release actions

See [SUBMISSION_READINESS.md](SUBMISSION_READINESS.md) for exact dashboard/account/configuration actions. Railway currently has an empty private project, not a verified MCP service. Create and verify web/Postgres/Redis/worker/beat, real HTTPS and domain challenge; configure corporate OIDC and assigned reviewer/source identities; approve the intended Slack commercial use and any irreversible PKCE app setting; perform real auth/source/revocation/cleanup checks; verify the operator/contact and adopt only the hosted-plugin legal drafts; publish matching pages and demo/reviewer access; reconcile exact verified publisher metadata; then inspect portal scans and explicitly upload/submit.

Slack stays gated until actual provider permission and an authorized live test. Its adapter uses legacy search plus current-access reads; rate limits and one-page ingestion (up to 100 items) remain limitations. No blanket persistent-index prohibition for all `search.messages` use is asserted. Gmail and Drive remain disabled/unverified and currently retrieve snippets or names/descriptions only. Full Google content ingestion is incomplete. Existing plaintext legacy rows are withheld from production retrieval; existing data and officeholder history require operator reconciliation rather than silent reassignment. The separately supplied modular handoff remains available for selective reuse and does not replace this checkpoint.

No public deployment, merge, OAuth grant, actual app-setting change, paid API request, acceptance of legal terms, submission or publication was performed as part of these local changes.
