# Production handoff — configuration names only

The intended target is Roman's existing private Railway project `wisdomtwin-plugin`. No services, public domain or successful deployment are established by this handoff. Do not create a duplicate project. The source remains the approved branch and PR [15](https://github.com/RomanBodnarchuk/wisdomtwin-three-rooms/pull/15).

## Exact intended layout

| Service | Source/start | Required relationship |
| --- | --- | --- |
| Web | Repository root `plugin-scaffold`; pinned Dockerfile; `python server.py` | HTTPS origin; health/MCP/OAuth/domain-challenge routes; durable authorization/index storage. |
| Worker | Same exact source/image; `celery -A ingest.celery_app worker --loglevel=info` | Same PostgreSQL, Redis and encryption key as web; executes ingestion and retention. |
| Beat | Same exact source/image; `celery -A ingest.celery_app beat --loglevel=info` | One scheduler instance; same queue/database/configuration; schedules daily cleanup. |
| PostgreSQL | PostgreSQL with pgvector | Persistent volume; protected private connection; 1536-dimension index; shared by all app processes. |
| Redis | Queue/broker service | Protected private connection; shared by worker, beat and web. |

The Python base digest and database/Redis verification image digests are in [VERIFIED_EVIDENCE.md](VERIFIED_EVIDENCE.md). The local normal online Docker build was blocked by package-index DNS. Offline hash-verified wheel builds passed for the original and current source; the current image passed dependency checks, fail-closed production startup and the offline suite with synthetic tests/fixtures mounted read-only and network disabled. The hosting platform's normal build and deployed image remain unverified. Local Python/database/worker tests passed for the follow-up.

## Variable names

| Group | Names | Purpose / gate |
| --- | --- | --- |
| App runtime | `WISDOMTWIN_ENV`, `HOST`, `PORT`, `PUBLIC_BASE_URL` | Production binding and actual verified HTTPS origin. `RAILWAY_PUBLIC_URL` is an optional origin fallback. |
| Shared durable state | `DATABASE_URL`, `REDIS_URL`, `CONNECTOR_TOKEN_KEY` | Same private services and encryption key across web, worker and beat. A real key is provisioned outside Git. |
| MCP public client | `OAUTH_CLIENT_ID`, `OAUTH_REDIRECT_URIS` | Registered client and exact permitted HTTPS callbacks. |
| Corporate identity | `OIDC_ISSUER`, `OIDC_CLIENT_ID`, optional `OIDC_CLIENT_SECRET` | Authorized corporate IdP and exact identity callback. Operator-provisioned roles/source identities remain a separate trusted input. |
| Slack activation | `SLACK_CLIENT_ID`, `SLACK_CONNECTOR_ENABLED`, `SLACK_POLICY_APPROVED` | Only after actual commercial permission, authorized PKCE app configuration and a permitted live grant/test. PKCE code exchange does not use a Slack client secret. |
| Slack method limits | `SLACK_HISTORY_RATE_CLASS` | Default `restricted`: one current-access history/replies read per app/workspace/method per minute, with pages of at most 15 messages. `tier3` is an explicit operator assertion of verified Marketplace/internal/exempt eligibility; never infer it from a successful request. Search is conservatively paced at 20 requests/minute. |
| Existing Slack grant refresh | `SLACK_TOKEN_REFRESH_ENABLED`, `SLACK_CLIENT_SECRET` | Default off. Refresh only an existing rotating read-only user grant; HTTPS server refresh requires the existing app secret. This does not enable rotation, alter app settings or create a new grant. Nonrotating Slack tokens have no invented expiry. |
| Model operation | `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, `WISDOMTWIN_ALLOW_PAID_MODEL_APIS` | Separately authorized API spending is required for real indexed ingestion. Subscription credits do not establish API access. |
| Optional backend generation | `WISDOMTWIN_GENERATION_MODE`, `OPENAI_GENERATION_MODEL`, `OPENAI_REASONING_EFFORT`, optional `OPENAI_RESPONSES_MAX_OUTPUT_TOKENS` | Default extractive evidence supports ChatGPT synthesis; backend Responses requires the same spending approval. The optional total reasoning/output budget is an explicit integer 32..32768. If absent, the caller's existing cap is preserved. An empty value is invalid. No automatic increase or paid retry occurs. |
| Hosted listing/challenge | `PRIVACY_POLICY_URL`, `TERMS_OF_SERVICE_URL`, `SUPPORT_URL`, `OPENAI_APPS_CHALLENGE` | Adopted published pages and portal's actual challenge; reconcile package metadata before release. |
| Guarded test modes | `WISDOMTWIN_USE_FIXTURES`, `WISDOMTWIN_AUTH_DISABLED`, `WISDOMTWIN_AUTH_DB` | Loopback synthetic tests only. Public deployment must keep fixture/auth-disabled modes off. |
| Gated Google scope | `GMAIL_CONNECTOR_ENABLED`, `DRIVE_CONNECTOR_ENABLED`, `GOOGLE_REVIEW_APPROVED`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Remain off; provider verification and full-content implementation are unfinished. |

No values, credentials, actual provider grants or adopted legal terms are supplied here. [.env.example](.env.example) supplies conservative defaults. Production configuration requires OIDC in addition to core runtime names; a healthy container alone does not establish a working corporate/source login.

## Safe next action

First review the exact tested follow-up commit and the [readiness checklist](SUBMISSION_READINESS.md). Then, within the separately approved hosting/configuration scope, prepare these five services in the existing private project, register the intended callbacks and assign identities. Run `./deploy.sh --check` privately with the actual required configuration; it performs no deployment. Before any public run, verify the host's hash-locked build and fail-closed auth configuration. Actual service creation/deployment, new credentials/grants, irreversible Slack PKCE changes, model spending and legal adoption remain Roman/parent-coordinated approval steps.

After hosting approval, validate real HTTPS discovery, signed login/PKCE/resource checks, current-access retrieval, revocation/replay, deletion and queued retention. Only observed evidence can replace the package's placeholder origin. Do not upload the current candidate ZIP as a completed plugin.
