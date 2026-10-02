# Handover: existing WisdomTwin plugin prototype

Continue the existing `plugin-scaffold/` tree on branch `cursor/wisdomtwin-mcp-plugin-8d09`, PR [15](https://github.com/RomanBodnarchuk/wisdomtwin-three-rooms/pull/15). Do not create another scaffold or server. This packet is a private prototype handover and an offline package candidate. It is not a public deployment, legal adoption, submission or approval record.

## Contract to preserve

The indexed business twin is scoped to one authorized role and tenure. Preserve the original four tool names, arguments and output shapes. Do not add a fifth MCP tool.

| Tool | Arguments | Returned shape | Access |
| --- | --- | --- | --- |
| `connect_business_account` | `service`: slack/gmail/drive, `domain`, `role_title` | `{oauth_url, status, role_id}` | Writes internal role/connection state; source authorization is read-only. |
| `ingest_data` | `service`, `query`, `max_items=1000` | `{job_id, progress, chunks_ingested}` | Reads sources and writes the protected role index. |
| `query_twin` | `question`, `max_results=10`, `max_tokens=512` | Answer text followed by citation blocks `{uri, snippet}` | Read-only retrieval and current source revalidation. |
| `list_twins_status` | none | Objects with exactly `{service, role_title, ingested_chunks, last_update, domain}` | Read-only status. |

`readOnlyHint` is false for connection/ingestion and true for query/status. `destructiveHint` and `openWorldHint` remain false. Each tool declares its OAuth policy. Stable original errors are `DOMAIN_REJECTED`, `QUOTA_EXCEEDED`, `OAUTH_PENDING`, `JOB_NOT_FOUND`; hardened paths also report `AUTHORIZATION_REQUIRED` or `CONNECTOR_FAILED`. On the wire a failure is a tool result with `isError` true and the text `Error executing tool <name>: <CODE>: <message>`: the pinned SDK adds that prefix, so the stable code follows it rather than starting the text. A missing, expired, mismatched or unreadable source grant, or one the provider rejects (Slack `token_revoked`, `invalid_auth`, `account_inactive`, `token_expired`, `not_authed`; Google HTTP 401), is `OAUTH_PENDING` with a reconnect instruction on both query and ingestion, not an empty answer. An empty index returns exactly `I have nothing ingested on that.` An unrelated question returns `I only answer questions about this role's business record.`

Consumer domains are rejected. Domain/title inputs are not identity proof. Corporate OIDC must verify signature, issuer, subject, audience, nonce and verified email; operators provision exact domain/role entitlements and Slack workspace/user or Google subject. Source callbacks bind to those identities and granted scopes. Durable encrypted Postgres authorization state supports revocation across processes; fixture SQLite is not a production substitute. Optional client ID metadata documents (`OAUTH_CIMD_CLIENT_IDS`) are fetched only for allowlisted URLs, by one request per URL at a time, within one 5-second wall-clock budget for the whole fetch. A failed fetch starts no new one for 60 seconds, and while refreshes fail the last good client keeps serving for up to 24 hours after its one-hour cache expires.

The bounded [review follow-up](REVIEW_FOLLOWUP.md) adds atomic membership-generation checks to consent/issuance and family revocation on used-refresh replay. Pre-generation grants require a new sign-in. Durable generation markers survive membership removal so re-provisioning cannot resurrect an in-flight exchange; they contain a pseudonymous subject and integer, not source text or a credential.

The same file records the October 1 independent review hardening (findings H1 to H4, M1 to M6 and L1 to L5) and the adversarial review of that diff (SEC-1 to SEC-3, G1 to G6 and F1 to F8), with resulting behavior and test evidence. Before the adversarial-review fixes, the isolated PostgreSQL suite gave 42 passed and the real worker smoke passed against freshly created loopback services; on the final tree after those fixes, both reran with the same results and the offline suite gave 513 passed, 14 skipped. CI must also pass on the pushed commit.

## Data and model boundaries

Real indexes retain vectors, source URIs, chunk hashes, keyed keyword hashes (HMAC-SHA256 under a key derived from `CONNECTOR_TOKEN_KEY`), authorship and role/tenure metadata. Rotating that key requires re-indexing for keyword matching, and after memberships are re-provisioned each source asks for a reconnect. Real source text is transient during ingestion and queries. Ingestion skips items with restricted identifiers, instruction-like text or restricted topic words and logs only per-reason counts; questions that merely mention a topic word are answered. Querying re-fetches current source access and checks hash and authorship before returning citation text. It verifies ranked sources lazily, fetching first the candidates whose keyword hashes match the question, stops at three verified supporting chunks and re-fetches at most `WISDOMTWIN_MAX_SOURCE_FETCHES` (default 4) distinct sources. A provider failure after some evidence verified returns a partial answer citing only that evidence. If that limit is reached with nothing verified while candidates remain unchecked, the query returns `CONNECTOR_FAILED` asking for a narrower question or a retry, never the empty-context answer. Old stored excerpts must not become production citations. The ten-message synthetic fixture may retain text locally. Audit events contain minimal action/outcome identifiers, not source payloads.

Real ingestion is queued through Redis/Celery. The worker revalidates actor and role access. A daily beat task applies the 30-day inactivity eligibility cutoff; it needs a deployed scheduler/worker and operator evidence. Deletion clears chunks, source credentials, connections, jobs/pending state and role metadata, then revokes MCP grants. Empty organizational records are removed. Audit events have separate 30-day retention; operator-provisioned membership lasts until explicitly removed. Avoid claims of exact real deletion timing without logs and a deployment test.

Actual embedding API use is `text-embedding-3-small`, with explicit `WISDOMTWIN_ALLOW_PAID_MODEL_APIS` opt-in and an API key; local tests use synthetic embeddings. Default generation returns extractive evidence for ChatGPT. Optional Responses mode uses `gpt-6.1-sol` with reasoning effort `low` by default, a separate `OPENAI_MAX_OUTPUT_TOKENS` budget (default 16000, with a socket timeout of that budget divided by 50 seconds, between 60 and 600), strict JSON-schema output, a hashed `safety_identifier` and no temperature; it parses only `completed` responses and otherwise falls back to extractive evidence with a logged reason label. Embedding requests are batched. No paid model requests were performed in this work. Model-generated claims must have valid source support; inference and quoted evidence must remain distinguishable.

Slack adapter implementation and fixture success do not prove commercial provider permission or a working production connector. Obtain the separate Slack/Salesforce authorization applicable to this use before real activation. There is no established blanket ban on every use of `search.messages`; do not invent one. Gmail/Drive are off and unverified. Gmail currently retrieves snippets/metadata; Drive retrieves file names/descriptions. Full email and document ingestion is incomplete. Do not enable them or promise completeness just because flags or scopes exist.

## Package and evidence

`plugin.json` is the root portable entry point; root `mcp.json` declares one remote server and `skills/` contains exactly Query Twin and Update Twin. OpenAI extension metadata is inline. Existing compatibility overlays remain supported by OpenAI; no new overlay or scaffold is needed. `manifest.json` is an internal summary and stays outside the ZIP. The two skills require source citations, read-only query defaults, explicit user-confirmed ingestion scope and rejection of instructions embedded in sources.

```bash
python3 -m pip install --require-hashes -r requirements.lock
python3 -m pytest -q
./package.sh --check
./package.sh --candidate
```

`--check` performs full offline validation against checked-in official schemas plus listing/path/icon/skill and four-source-signature checks. `--candidate` creates `dist/wisdomtwin-candidate-NOT-FOR-SUBMISSION.zip` and deterministic hash/inventory sidecars. Use `--output-dir` for a separate artifact directory. Credentials, server code, synthetic fixture data, legal drafts and review account material never enter this ZIP. Production packaging requires the factual evidence contract in [SUBMISSION_READINESS.md](SUBMISSION_READINESS.md) and live verification; creating the production ZIP still does not submit it.

The parent integrator records exact test output, ZIP SHA-256 and the final source commit. The original twelve-case/ten-chunk/four-tool PR result is synthetic. Only fresh output establishes the current combined suite count. Earlier claims of public Slack, production Postgres or completed submission must not be inferred from a fixture run.

## Roman's remaining actions

[SUBMISSION_READINESS.md](SUBMISSION_READINESS.md) ends with the current ordered list, "Roman's next actions, in order". The summary below stays consistent with it. Agents must not upload or submit the plugin.

The observed verified publisher is **ROMAN GREGORY BODNARCHUK** under the selected individual developer identity. This does not establish a verified WisdomTwin, Inc. publisher. Reconcile author/listing/internal-manifest fields with the exact final selected identity. The proposed hosted-service operator **WisdomTwin, Inc.** and `privacy@wisdomtwin.ai` still need entity, authority and contact verification.

1. Finish Railway service, Postgres/pgvector, Redis, worker and beat setup. Record a real HTTPS origin, healthy service and durable state behavior; no origin has been invented in this package.
2. Provision corporate OIDC and role/source identity entitlements, exact client callbacks and read-only provider grants. For ChatGPT, list `https://chatgpt.com/connector_platform_oauth_redirect` in `OAUTH_REDIRECT_URIS`, or allowlist `https://chatgpt.com/oauth/client.json` in `OAUTH_CIMD_CLIENT_IDS`, then verify linking end to end. Confirm Slack/Salesforce commercial authorization, the applicable rate class and review access before enabling real Slack.
3. Review/adopt only the hosted-plugin legal drafts and publish matching privacy, terms and support pages. The existing website's on-premises policy is unsuitable for this hosted plugin and remains outside this edit's scope.
4. Complete public MCP domain verification and real auth/source/deletion/retention checks. Store evidence outside Git and supply the package validator with matching records.
5. Record a reviewer-accessible walkthrough, provide reviewer accounts securely in the portal, inspect tool and skill scans, then explicitly upload and submit the final reconciled ZIP. There is no custom UI or screenshot field in this candidate.
6. Treat Google scope review and full-content connector development as separate unfinished work. Use the revised `google-verification/` preparation packet; it has not been submitted or approved.

The internal monthly chunk quota is 1,000 indexed chunks per calendar month for each signed-in user's organization record (scoped per subject and domain), so colleagues do not share it. That quota and the WisdomTwin Pro USD 20 product concept do not authorize subscription advertising, upsells or checkout in the directory listing, tools or skills. Other unresolved architecture proposals do not silently replace this Slack-first indexed candidate. Role interviews, huddles, predecessor data, Microsoft 365, Notion, write actions and custom UI remain outside this build.
