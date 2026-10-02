# WisdomTwin plugin candidate

This is the existing private role-twin prototype in `plugin-scaffold/` on PR [15](https://github.com/RomanBodnarchuk/wisdomtwin-three-rooms/pull/15). It has four MCP tools and two packaged skills. Local synthetic checks establish prototype behavior; they do not establish a working public Slack connection or directory readiness. The Railway project has no verified public service origin, so `mcp.json` retains its placeholder.

The indexed MVP writes vectors, source URIs, chunk hashes, keyed keyword hashes, role/tenure and source-author metadata to a protected role namespace. Keyword hashes are HMAC-SHA256 values under a server-held key derived from `CONNECTOR_TOKEN_KEY`, so a database reader without that key cannot recover a chunk's vocabulary with a dictionary pass. Real source text is transient during ingestion and querying. Before a citation is returned, the server re-fetches the source with the caller's current grant and checks its content hash and authorship. Changed or inaccessible sources are withheld. Synthetic fixture text remains local for tests. Vectors, hashes and source metadata are still protected business data.

Ingestion skips source items that contain restricted identifiers (API keys, private keys, SSN-shaped numbers, Luhn-valid card numbers), instruction-like text, or restricted topic words such as "patient" or "credit card". Skipped text is never stored; each job logs only a count per reason at INFO level. The `ingest_data` search query itself still rejects topic words, with its own message: "This search query names a restricted topic (for example patient or credit card); items on these topics are not indexed." Search queries carrying identifiers or injection keep the restricted-identifiers message. A question that merely mentions a topic word, such as one about a credit card processing vendor, is answered from the index; questions carrying identifiers or injection get the business-record refusal.

Corporate OIDC sign-in verifies signed issuer, subject and email. An operator must provision the business domain, allowed roles and exact Slack workspace/user or Google subject. Typing a domain and title does not confer access. Production OAuth state and source credentials use encrypted durable Postgres storage; SQLite and memory adapters are for explicit local tests.

Consent and grants carry a durable membership generation. Revocation, removal or reprovisioning invalidates exchanges already in progress; issuance commits the complete pair atomically with revocation. Reusing a consumed refresh token revokes its family, including successors. A new verified sign-in remains available. Earlier grants without a generation fail closed and require sign-in again. See [review follow-up evidence](REVIEW_FOLLOWUP.md).

The authorization-server metadata advertises the public-client method `none` for the token and revocation endpoints and RFC 9207 `iss` support, and every authorization redirect to the client, code or error, carries `iss` equal to the served issuer. With `iss` support, ChatGPT uses its stable callback `https://chatgpt.com/connector_platform_oauth_redirect`; a static client must list that exact URI in `OAUTH_REDIRECT_URIS`. The issuer and the protected resource's `authorization_servers` are the bare origin with no trailing slash, and `scopes_supported` is `twin:read`, matching the release validator. Client ID metadata documents are off unless `OAUTH_CIMD_CLIENT_IDS` lists exact URLs. `/.well-known/oauth-protected-resource` serves the same document as the path-inserted `/mcp` form. Account linking in ChatGPT itself has not been demonstrated against a real deployment.

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

Tests configure loopback fixture mode and temporary encrypted SQLite authorization state. The original twelve MVP cases exercise four tools and ten synthetic Slack chunks. The current full suite adds security, source access, quota, deletion, worker and review-hardening checks; report the exact current count from its output. Historical PR comments about memory or local Postgres runs are evidence of those runs, not proof of a deployed production database. No paid model API calls were performed for this candidate.

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

Tool failures return a tool result with `isError` set to true and one text block in the form `Error executing tool <name>: <CODE>: <message>`. The SDK adds the `Error executing tool <name>: ` prefix, so the stable code (`DOMAIN_REJECTED`, `QUOTA_EXCEEDED`, `OAUTH_PENDING`, `JOB_NOT_FOUND`, `AUTHORIZATION_REQUIRED` or `CONNECTOR_FAILED`) follows that prefix rather than starting the text. Uncoded failures carry the prefix and a message without a code, and an unexpected crash returns only `Error executing tool <name>`, keeping its details on the server.

## Runtime and operations

| Configuration | Purpose |
| --- | --- |
| `PUBLIC_BASE_URL`, `OAUTH_CLIENT_ID`, `OAUTH_REDIRECT_URIS` | Real HTTPS origin and the static public MCP client; production startup requires all three. For ChatGPT, `OAUTH_REDIRECT_URIS` must contain `https://chatgpt.com/connector_platform_oauth_redirect` exactly. Outside local mode, `PUBLIC_BASE_URL` also sets the only Host and Origin that `/mcp` accepts (see below). |
| `OAUTH_CIMD_CLIENT_IDS` | Optional client ID metadata documents; empty by default, which keeps them off. A comma-separated list of exact HTTPS document URLs; the recommended value is `https://chatgpt.com/oauth/client.json`. Listing a URL trusts whoever controls it to define that client's redirect URIs, so list only ChatGPT's own document. Unlisted URLs are never fetched. The fetch reaches public addresses only, follows no redirect, and is limited to 64 KiB within one 5-second wall-clock budget that covers name resolution, connection, headers and body; the document must name itself as `client_id`, carry no secret and list HTTPS redirect URIs. An accepted document becomes a public PKCE client limited to `twin:read`, cached for one hour. Each URL is fetched by one request at a time while others wait for it. After a failed fetch no new fetch starts for 60 seconds, and while refreshes fail the last good client keeps serving for up to 24 hours after its cache expires; a client never fetched successfully stays unknown. A malformed entry fails `./deploy.sh --check`, `admin.py` and server startup. |
| `OIDC_ISSUER`, `OIDC_CLIENT_ID`, optional `OIDC_CLIENT_SECRET` | Corporate identity provider, plus separately provisioned business-role entitlements. |
| `DATABASE_URL`, `CONNECTOR_TOKEN_KEY` | Durable Postgres/pgvector. `CONNECTOR_TOKEN_KEY` encrypts authorization and source credentials and, through HKDF, keys the stored keyword hashes. Rotating it makes everything already encrypted under it unreadable (source credentials and authorization records, including memberships) and stops keyword matching on existing rows until they are re-indexed; vector search keeps working. After the operator re-provisions memberships, each source asks for a reconnect, which stores its grant under the new key. |
| `REDIS_URL` | Production ingestion queue; run a Celery worker and a beat scheduler. |
| `SLACK_CONNECTOR_ENABLED`, `SLACK_POLICY_APPROVED` | Slack remains gated until operator setup and provider authorization are established. |
| `GMAIL_CONNECTOR_ENABLED`, `DRIVE_CONNECTOR_ENABLED`, `GOOGLE_REVIEW_APPROVED` | Default off; Google scope review and unfinished connector work remain prerequisites. |
| `WISDOMTWIN_MAX_SOURCE_FETCHES` | Distinct sources one `query_twin` call may re-fetch from Slack or Google; default `4`. Chunks of an already-fetched source do not count. Zero, negative or non-integer values stop startup. |
| `OPENAI_API_KEY`, `WISDOMTWIN_ALLOW_PAID_MODEL_APIS` | Actual API use needs a key and explicit spend opt-in. Fixture embeddings stay local. |
| `OPENAI_EMBEDDING_MODEL` | Intended production embedding model: `text-embedding-3-small`; indexed real ingestion requires authorized API use. Requests are split in order into batches of at most 256 inputs and 250,000 estimated tokens. |
| `WISDOMTWIN_GENERATION_MODE`, `OPENAI_GENERATION_MODEL` | Default extractive evidence for ChatGPT to synthesize. Optional `responses` mode uses `gpt-6.1-sol` with strict JSON-schema output, a hashed `safety_identifier` and no temperature. A failed request, or a response that is not `completed` with supported citations, falls back to extractive evidence and logs one fixed reason label. |
| `OPENAI_MAX_OUTPUT_TOKENS` | Responses `max_output_tokens` budget, covering reasoning and visible output; default `16000`. It is separate from `query_twin`'s `max_tokens`, which caps visible answer words. Must be a positive integer. The request's socket timeout is this budget divided by 50, in seconds, kept between 60 and 600 (320 at the default). |
| `OPENAI_REASONING_EFFORT` | Responses reasoning effort; default `low`. Allowed values: `low`, `medium`, `high`, `xhigh`, `max`. Any other value stops startup. |
| `OPENAI_APPS_CHALLENGE` | Exact portal challenge value, held outside Git; not a generated host or approval token. |

Outside local mode, `/mcp` accepts a request only when its Host is the `PUBLIC_BASE_URL` host (any port) and any Origin it carries is that origin, `https://chatgpt.com` or `https://chat.openai.com`. Requests without an Origin are allowed. These checks run before bearer authentication: a foreign Origin gets 403 and a wrong Host gets 421, even without a token. The proxy must preserve the Host header, and a second public hostname (for example a custom domain next to the Railway domain) is rejected on `/mcp`. Local mode keeps the SDK's loopback protection. `python3 server.py` serves exactly this guarded app through uvicorn.

Run `celery -A ingest.celery_app worker --loglevel=info` for queued ingestion and `celery -A ingest.celery_app beat --loglevel=info` for the daily retention task. The 30-day inactivity cutoff makes indexes eligible for cleanup; actual execution depends on a healthy scheduler and worker. Verify deployment logs and deletion behavior before promising a deadline. User-requested deletion uses authenticated `DELETE /roles/{role_id}`; queued-job status uses authenticated `GET /jobs/{job_id}`. Neither route adds an MCP tool. Deletion clears role data and source credentials, jobs and pending connection state, and revokes MCP grants. Operator-provisioned membership is managed separately; minimal audit events have a separate 30-day retention limit. The trusted operator CLI in `admin.py` supports private membership provisioning/removal, role deletion and retention. Its verified membership input stays outside Git and the ZIP.

Source grants keep only the lifetime the provider returns. A Slack user token without token rotation carries none and stays usable until revoked. When a grant is missing, expired, bound to another identity or unreadable (for example stored under a rotated key), or the provider rejects the grant itself (Slack `token_revoked`, `invalid_auth`, `account_inactive`, `token_expired` or `not_authed`; Google HTTP 401), `query_twin` and `ingest_data` return `OAUTH_PENDING` with a reconnect instruction (for example "Reconnect Slack with connect_business_account to restore cited answers.") instead of an empty answer, and a queued job with a lapsed or rejected grant fails without a Celery retry. A query still cites evidence another service verified. Per-source denials, such as a deleted message or a channel the user left, withhold only that source. Slack grants stored before this change carry an artificial 24-hour expiry and need one reconnect after it passes. No refresh tokens are stored, so keep Slack token rotation off. Google requests online access only, so a Google grant needs reconnecting after the lifetime Google returns.

The current provider adapters fetch one page, up to 100 items; `max_items` is an upper bound rather than a completeness promise. `query_twin` verifies ranked sources lazily: it stops once three verified supporting chunks exist and re-fetches at most `WISDOMTWIN_MAX_SOURCE_FETCHES` distinct sources per call. Candidates whose stored keyword hashes match a question term (keyed, or legacy bare SHA-256) are fetched first, in rank order; the rest are moved back, not dropped. If the limit is reached with nothing verified while candidates remain unchecked, the call returns `CONNECTOR_FAILED` "No supporting source verified within this query's source-check limit. Ask a narrower question or retry." rather than the empty-context answer. Deleted Slack threads withhold that source while allowing other verified sources. HTTP 429 permits one retry only when the provider's delay is at most two seconds. A rate limit or outage after some evidence verified ends fetching and returns a partial answer that cites only the verified evidence; the output shape has no marker for this. With nothing verified, the call returns `CONNECTOR_FAILED` with retry guidance and no evidence. Slack's applicable commercial rate class still needs live validation; until the app has Marketplace or internal-app status, most real queries can be expected to return partial or rate-limited answers. Gmail citations use `https://mail.google.com/mail/#all/<id>` without an account index; legacy `u/0/#inbox/<id>` rows still re-fetch. Slack uses a PKCE code exchange without a client secret and needs an already PKCE-enabled app. Enabling that irreversible app setting requires separate approval; no live settings were changed. Multiple open tenures in a legacy database cause the new uniqueness check to fail until an operator reconciles them; the migration does not silently change officeholder history.

The isolated database and queue checks run without source grants or model API calls:

```bash
WISDOMTWIN_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/wisdomtwin_test \
  python3 -m pytest -q tests/test_mvp.py tests/test_worker_concurrency.py tests/test_database.py tests/test_revocation_followup.py
WISDOMTWIN_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/wisdomtwin_test \
WISDOMTWIN_TEST_REDIS_URL=redis://127.0.0.1:56379/9 \
  python3 scripts/verify_local_worker.py
```

These commands reset the explicitly isolated test database. The worker smoke script also requires loopback service URLs and a database name ending in `_test`. CI uses its own disposable Postgres and Redis services. On October 1, 2026, before the adversarial-review fixes, both commands ran against freshly created, verified-empty loopback services: the PostgreSQL suite gave 42 passed and the worker smoke passed with zero model API calls. On the final tree, after those fixes, both reran against the same services with the same results, and the offline suite gave 513 passed, 14 skipped; see [review follow-up](REVIEW_FOLLOWUP.md). `deploy.sh --check` validates names/configuration without publishing; `--deploy` is for a separately authorized, linked Railway service.

[PRODUCTION_LAYOUT.md](PRODUCTION_LAYOUT.md) records the service layout, variable names and remaining deployment gates. It contains no credentials and does not establish a deployment.

## Build the review candidate

```bash
./package.sh --check
./package.sh --candidate
```

The deterministic artifact is `dist/wisdomtwin-candidate-NOT-FOR-SUBMISSION.zip`, with SHA-256 and member inventory sidecars. Its root contains only `plugin.json`, `mcp.json`, `assets/logo.svg`, and the two `skills/*/SKILL.md` files. ZIP entry timestamps, order and modes are fixed. Candidate mode performs no network calls and preserves placeholder URLs. It excludes server code, fixtures, legal drafts, credentials and reviewer material. `manifest.json` is an internal compatibility summary, not the portable entry point. [Schema provenance](schemas/PROVENANCE.md) records the complete official offline snapshots.

A production build (`./package.sh` or `--release`) refuses placeholders and requires real HTTPS MCP/OAuth/legal checks, an authenticated read-only tool scan, and operator records supplied through `PACKAGE_RELEASE_EVIDENCE`. `MCP_SERVER_URL` can set the staged endpoint after a real origin exists; all listing URLs and publisher fields must already be reconciled. `PACKAGE_MCP_ACCESS_TOKEN` stays in the environment. Building a ZIP never submits or publishes it. Its discovery expectations (bare-origin issuer and `authorization_servers`, `none` and `twin:read`) match what the server serves in code, as `test_discovery_matches_the_release_validator_contract` checks offline, and are checked live only during `--release`; see [submission readiness](SUBMISSION_READINESS.md) for the evidence contract and dashboard actions.

## Internal product decisions

The MVP quota is 1,000 indexed chunks per calendar month (UTC) for each signed-in user's organization record. Organization records are scoped per signed-in subject and business domain, so colleagues at the same domain each have their own record and their own 1,000-chunk budget: the quota is not shared across colleagues and is not a company-wide cap. One user's roles under the same domain share that user's budget. `max_items` above 1,000 is rejected with `QUOTA_EXCEEDED`. Pricing assumptions should treat the quota as per signed-in user. WisdomTwin Pro at USD 20/month is an internal product design decision, not a plugin offer. The package and skills contain no subscription listing, upgrade pitch, checkout, or payment tool. Access to existing entitlements may be explained without advertising new subscriptions. [OpenAI's plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines) govern the directory experience.

Role interviews, huddles, predecessor ingestion, Microsoft 365, Notion, source-write actions and a custom ChatGPT UI are outside this build. The hosted-plugin [privacy](privacy-policy.md) and [terms](terms-of-service.md) are unadopted drafts. They do not replace the existing website's policy or govern other customer engagements. Entity/contact verification, legal adoption, public hosting, provider permission, reviewer access and actual submission remain open.
