# Submission readiness

OpenAI reviews the package. Google reviews the restricted scopes. This file records what is in the repository and which steps still happen in a dashboard.

`RAILWAY_PUBLIC_URL` was not supplied, so `mcp.json` still contains a placeholder. `DEVELOPER_DASHBOARD_ORG` was not supplied. The manifests use WisdomTwin Inc, which is the controller named in the privacy policy, and Roman must confirm that string matches the verified organization. The privacy policy URL used here is https://wisdomtwin.ai/privacy.

| Requirement | Status | Next action |
| --- | --- | --- |
| MCP server on the official Python SDK, streamable HTTP at `/mcp` | done | Keep `mcp` at 2.2.0 or newer. |
| `/health` | done | `deploy.sh` calls it after Railway is up. |
| Four tools, role title, tenure metadata, citations, audit row | done | Covered by `tests/test_mvp.py`. |
| Stable errors DOMAIN_REJECTED, QUOTA_EXCEEDED, OAUTH_PENDING, JOB_NOT_FOUND on the SDK tool error | done | Raised as `ToolError`. JOB_NOT_FOUND is used when an ingestion job id is missing. |
| Domain gate and read-only scopes | done | Slack scopes are read-only. Gmail and Drive scopes are the two readonly scopes. |
| Slack connector | done in code | Create the Slack app, set `SLACK_CLIENT_ID` and `SLACK_CLIENT_SECRET`, and use the redirect `{PUBLIC_BASE_URL}/oauth/callback/slack`. |
| Gmail and Drive connectors, testing mode, off by default | done in code | Follow `google-verification/submission-steps.md`. Do not flip the flags until Google grants the scopes. |
| Postgres role schema and pgvector index | done locally | The ten cases pass on memory and on local Postgres when `WISDOMTWIN_TEST_DATABASE_URL` is set. On Railway, use a Postgres service with pgvector. The server applies `schema.sql` at startup. |
| Celery ingestion | done in code | Set `REDIS_URL` and run the Procfile worker. |
| Privacy policy, controller WisdomTwin Inc, no certification claim, no training | done in repo | Deploy the site so https://wisdomtwin.ai/privacy serves `public/privacy/index.html`. Open the URL and confirm the page before submission. |
| `manifest.json` and directory `plugin.json` / `mcp.json` | done, URL blocked | Replace the MCP URL after Railway assigns the origin. Confirm developer name WisdomTwin Inc against the verified organization. |
| No secrets in the tree | done | Keep keys in the shell. `deploy.sh` does not echo them. |
| Pytest, ten cases | done | `cd plugin-scaffold && uv run pytest` uses memory. The same file passes with `WISDOMTWIN_TEST_DATABASE_URL` pointed at Postgres with pgvector. |
| Verified developer organization | needs Roman | OpenAI dashboard: organization settings, complete verification, then Plugins, and choose that identity when uploading. If the displayed name is not WisdomTwin Inc, edit the manifests before the ZIP. |
| Public HTTPS MCP endpoint | needs Roman | Create the Railway service with root `plugin-scaffold`, set the variables named in `deploy.sh`, run `./deploy.sh`, and confirm `{RAILWAY_PUBLIC_URL}/health`. |
| Domain verification for the MCP host | needs Roman | In the plugin portal, open MCPs, Connect, and copy the challenge token. Set `OPENAI_APPS_CHALLENGE` to that exact value and redeploy. Fetch `https://<host>/.well-known/openai-apps-challenge` and confirm the body is only the token. |
| Plugin ZIP upload | needs Roman | From `plugin-scaffold/`, zip the package so `plugin.json` is at the root. Open the OpenAI dashboard, Plugins, Upload plugin, and select the ZIP. Fix whatever the portal reports. Do not upload `.env`. |
| Screenshots (connect with role title, domain rejection, Slack ingest progress, cited answer, status panel) | needs Roman | Capture these five from a real session and add them under `assets/` if the portal requires files in the package. |
| Demo recording and reviewer credentials | needs Roman | Record the five positive cases. In the plugin's review details, enter a sample Slack workspace and test account. Keep that account out of the ZIP. |
| Google restricted-scope verification | needs Roman | Use `google-verification/`. Submit the consent screen yourself. This repository does not claim the request was sent or accepted. |
| Directory submission and publication | needs Roman | After the portal checks are clear, submit the draft for review from the Plugins page. Publishing, if review accepts the package, is a separate click. This build stops before both. |
