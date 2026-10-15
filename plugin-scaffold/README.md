# WisdomTwin plugin candidate

This is the existing private role-twin prototype in `plugin-scaffold/` on PR [15](https://github.com/RomanBodnarchuk/wisdomtwin-three-rooms/pull/15). It has four MCP tools and two packaged skills. Local synthetic checks establish prototype behavior; they do not establish a working public Slack connection or directory readiness. The Railway project has no verified public service origin, so `mcp.json` retains its placeholder.

The indexed MVP writes vectors, source URIs, chunk hashes, hashed keywords, role/tenure and source-author metadata to a protected role namespace. Real source text is transient during ingestion and querying. Before a citation is returned, the server re-fetches the source with the caller's current grant and checks its content hash and authorship. Changed or inaccessible sources are withheld. Synthetic fixture text remains local for tests. Vectors, hashes and source metadata are still protected business data.

Current-access Slack reads batch selected messages within one channel/thread and share a durable app/workspace/method cooldown. The default commercial rate class is restricted; a successful request does not establish Tier 3 eligibility. A partial answer contains only verified matching evidence, states partial coverage and provides retry/reconnect guidance. If a temporary failure leaves no verified support, the tool returns a coded failure. See [REVIEW_ROUND2.md](REVIEW_ROUND2.md) for provider lifetime, public-client discovery and optional generation checks; no real grants or paid API requests were used.

Corporate OIDC sign-in verifies signed issuer, subject and email. An operator must provision the business domain, allowed roles and exact Slack workspace/user or Google subject. Typing a domain and title does not confer access. Production OAuth state and source credentials use encrypted durable Postgres storage; SQLite and memory adapters are for explicit local tests.

Consent and grants carry a durable membership generation. Revocation, removal or reprovisioning invalidates exchanges already in progress; issuance commits the complete pair atomically with revocation. Reusing a consumed refresh token revokes its family, including successors. A new verified sign-in remains available. Earlier grants without a generation fail closed and require sign-in again. See [review follow-up evidence](REVIEW_FOLLOWUP.md).

Slack adapter code exists, but real activation requires operator setup and the necessary Slack/Salesforce authorization for the intended commercial use. Gmail and Drive remain disabled. Google code reads Gmail snippets/metadata and Drive file names/descriptions; full email bodies and document ingestion are incomplete. Verification and flags alone do not complete those adapters.

## Local verification

Install the exact hashed dependency lock, then run:

```bash
cd plugin-scaffold
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --require-hashes -r requirements.lock
python3 -m pytest -q
./package.sh --check
```

Tests configure loopback fixture mode and temporary encrypted SQLite authorization state. The original twelve MVP cases exercise four tools and ten synthetic Slack chunks. The current full suite adds security, source access, quota, deletion and worker checks; report the exact current count from its output. Historical PR comments about memory or local Postgres runs are evidence of those runs, not proof of a deployed production database. No paid model API calls were performed for this candidate.

To start the local synthetic server, use a fresh state directory and an ephemeral encryption key:

```bash
export WISDOMTWIN_ENV=local HOST=127.0.0.1 PORT=8000
export PUBLIC_BASE_URL=http://127.0.0.1:8000
export WISDOMTWIN_AUTH_DISABLED=1 WISDOMTWIN_USE_FIXTURES=1
export SLACK_CONNECTOR_ENABLED=true SLACK_CLIENT_ID=local-test-client
export GMAIL_CONNECTOR_ENABLED=false DRIVE_CONNECTOR_ENABLED=false
export WISDOMTWIN_ALLOW_PAID_MODEL_APIS=false
fixture_state_dir="$(mktemp -d)"
export WISDOMTWIN_AUTH_DB="$fixture_state_dir/auth.sqlite3"
export CONNECTOR_TOKEN_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
python3 server.py
```

Fixture and auth-disabled settings are rejected outside explicit loopback local/test mode. The local `/health` endpoint is `http://127.0.0.1:8000/health`. Use this request to list the four tools:

```bash
curl --fail --silent --show-error \
  -X POST http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

A local fixture flow calls `connect_business_account` with `service=slack`, `domain=example-corp.com`, `role_title=CRO`; `ingest_data` with `service=slack`, `query=pipeline`, `max_items=10`; then `query_twin` with `question=What is the Acme pipeline stage?`. This is synthetic behavior, not a real Slack grant.

## Runtime and operations

| Configuration | Purpose |
| --- | --- |
| `PUBLIC_BASE_URL`, `OAUTH_CLIENT_ID`, `OAUTH_REDIRECT_URIS` | Real HTTPS origin and exact registered public MCP client callbacks. |
| `OIDC_ISSUER`, `OIDC_CLIENT_ID`, optional `OIDC_CLIENT_SECRET` | Corporate identity provider, plus separately provisioned business-role entitlements. |
| `DATABASE_URL`, `CONNECTOR_TOKEN_KEY` | Durable Postgres/pgvector and encryption of authorization/source credentials. |
| `REDIS_URL` | Production ingestion queue; run a Celery worker and a beat scheduler. |
| `SLACK_CONNECTOR_ENABLED`, `SLACK_POLICY_APPROVED` | Slack remains gated until operator setup and provider authorization are established. |
| `GMAIL_CONNECTOR_ENABLED`, `DRIVE_CONNECTOR_ENABLED`, `GOOGLE_REVIEW_APPROVED` | Default off; Google scope review and unfinished connector work remain prerequisites. |
| `OPENAI_API_KEY`, `WISDOMTWIN_ALLOW_PAID_MODEL_APIS` | Actual API use needs a key and explicit spend opt-in. Fixture embeddings stay local. |
| `OPENAI_EMBEDDING_MODEL` | Intended production embedding model: `text-embedding-3-small`; indexed real ingestion requires authorized API use. |
| `WISDOMTWIN_GENERATION_MODE`, `OPENAI_GENERATION_MODEL`, `OPENAI_REASONING_EFFORT` | Default extractive evidence for ChatGPT to synthesize. Optional `responses` mode uses configured `gpt-6.1-sol` reasoning and omits temperature. |
| `OPENAI_APPS_CHALLENGE` | Exact portal challenge value, held outside Git; not a generated host or approval token. |

Run `celery -A ingest.celery_app worker --loglevel=info` for queued ingestion and `celery -A ingest.celery_app beat --loglevel=info` for the daily retention task. The 30-day inactivity cutoff makes indexes eligible for cleanup; actual execution depends on a healthy scheduler and worker. Verify deployment logs and deletion behavior before promising a deadline. User-requested deletion uses authenticated `DELETE /roles/{role_id}`; queued-job status uses authenticated `GET /jobs/{job_id}`. Neither route adds an MCP tool. Deletion clears role data and source credentials, jobs and pending connection state, and revokes MCP grants. Operator-provisioned membership is managed separately; minimal audit events have a separate 30-day retention limit. The trusted operator CLI in `admin.py` supports private membership provisioning/removal, role deletion and retention. Its verified membership input stays outside Git and the ZIP.

The current provider adapters fetch one page, up to 100 items; `max_items` is an upper bound rather than a completeness promise. Deleted Slack threads withhold that source while allowing other verified sources. Provider outages return a coded failure. HTTP 429 permits one retry only when the provider's delay is at most two seconds; longer or repeated limits return retry guidance without evidence. Slack's applicable commercial rate class still needs live validation. Slack uses a PKCE code exchange without a client secret and needs an already PKCE-enabled app. Enabling that irreversible app setting requires separate approval; no live settings were changed. Multiple open tenures in a legacy database cause the new uniqueness check to fail until an operator reconciles them; the migration does not silently change officeholder history.

The isolated database and queue checks run without source grants or model API calls:

```bash
WISDOMTWIN_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/wisdomtwin_test \
  python3 -m pytest -q tests/test_mvp.py tests/test_worker_concurrency.py tests/test_database.py tests/test_revocation_followup.py
WISDOMTWIN_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/wisdomtwin_test \
WISDOMTWIN_TEST_REDIS_URL=redis://127.0.0.1:56379/9 \
  python3 scripts/verify_local_worker.py
```

These commands reset the explicitly isolated test database. The worker smoke script also requires loopback service URLs and a database name ending in `_test`. CI uses its own disposable Postgres and Redis services. `deploy.sh --check` validates names/configuration without publishing; `--deploy` is for a separately authorized, linked Railway service.

[PRODUCTION_LAYOUT.md](PRODUCTION_LAYOUT.md) records the service layout, variable names and remaining deployment gates. It contains no credentials and does not establish a deployment.

## Build the review candidate

```bash
./package.sh --check
./package.sh --candidate
```

The deterministic artifact is `dist/wisdomtwin-candidate-NOT-FOR-SUBMISSION.zip`, with SHA-256 and member inventory sidecars. Its root contains only `plugin.json`, `mcp.json`, `assets/logo.svg`, and the two `skills/*/SKILL.md` files. ZIP entry timestamps, order and modes are fixed. Candidate mode performs no network calls and preserves placeholder URLs. It excludes server code, fixtures, legal drafts, credentials and reviewer material. `manifest.json` is an internal compatibility summary, not the portable entry point. [Schema provenance](schemas/PROVENANCE.md) records the complete official offline snapshots.

A production build (`./package.sh` or `--release`) refuses placeholders and requires real HTTPS MCP/OAuth/legal checks, an authenticated read-only tool scan, and operator records supplied through `PACKAGE_RELEASE_EVIDENCE`. `MCP_SERVER_URL` can set the staged endpoint after a real origin exists; all listing URLs and publisher fields must already be reconciled. `PACKAGE_MCP_ACCESS_TOKEN` stays in the environment. Building a ZIP never submits or publishes it. See [submission readiness](SUBMISSION_READINESS.md) for the evidence contract and dashboard actions.

## Internal product decisions

The MVP quota is 1,000 indexed chunks per organization per month. WisdomTwin Pro at USD 20/month is an internal product design decision, not a plugin offer. The package and skills contain no subscription listing, upgrade pitch, checkout, or payment tool. Access to existing entitlements may be explained without advertising new subscriptions. [OpenAI's plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines) govern the directory experience.

Role interviews, huddles, predecessor ingestion, Microsoft 365, Notion, source-write actions and a custom ChatGPT UI are outside this build. The hosted-plugin [privacy](privacy-policy.md) and [terms](terms-of-service.md) are unadopted drafts. They do not replace the existing website's policy or govern other customer engagements. Entity/contact verification, legal adoption, public hosting, provider permission, reviewer access and actual submission remain open.
