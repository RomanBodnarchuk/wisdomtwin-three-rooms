# WisdomTwin

WisdomTwin is a ChatGPT plugin that keeps a private business twin for one role on the org chart. The twin belongs to the role, and to the current officeholder. Slack is the live connector. Gmail and Google Drive are implemented and stay off until Google verification clears. Answers come from that role's index, and every claim carries a citation.

The Python MCP SDK (`mcp` 2.2.0 or newer) serves `/mcp`. This repository did not contain `plugin-scaffold/` or `_backup/`, so this tree is the MVP described in the build prompt rather than an extension of an older server.

WisdomTwin does not train on user data. The free tier is 1,000 chunks per month. WisdomTwin Pro is USD 20 per month, billed by WisdomTwin Inc through WisdomTwin checkout.

## Local setup

Install [uv](https://docs.astral.sh/uv/), then:

```bash
cd plugin-scaffold
uv venv
uv pip install -r requirements.txt
uv run pytest
```

The ten tests use Slack fixtures. With no database URL they use the in-memory store. Set `WISDOMTWIN_TEST_DATABASE_URL` to a Postgres database with pgvector to run the same ten cases against `schema.sql`:

```bash
WISDOMTWIN_TEST_DATABASE_URL=postgresql:///wisdomtwin_test uv run pytest
```

Production uses `DATABASE_URL` (Postgres with pgvector) and `REDIS_URL` (Celery). On startup the server applies `schema.sql` one statement at a time, including `CREATE EXTENSION vector` and the cosine index on chunk embeddings.

Start the server for local tool calls. `WISDOMTWIN_AUTH_DISABLED` is ignored when `PUBLIC_BASE_URL` is HTTPS, so a public deployment still requires the OAuth bearer token.

```bash
WISDOMTWIN_AUTH_DISABLED=1 \
WISDOMTWIN_USE_FIXTURES=1 \
SLACK_CLIENT_ID=local-test-client \
PORT=8000 \
uv run python server.py
```

Health check:

```bash
curl --fail --silent http://127.0.0.1:8000/health
```

In another terminal, open a tunnel when you need a public HTTPS origin for a connector callback:

```bash
ngrok http 8000
```

Set `PUBLIC_BASE_URL` to that HTTPS origin before starting the server if Slack or Google must redirect back to you.

## Curl examples

These calls match the local server above. On a public HTTPS deployment, complete the MCP authorization-code flow first and send the bearer token. The server will not list tools anonymously there.

List tools:

```bash
curl --silent --show-error \
  -X POST http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

Connect Slack for a role:

```bash
curl --silent --show-error \
  -X POST http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"connect_business_account","arguments":{"service":"slack","domain":"example-corp.com","role_title":"CRO"}}}'
```

The response includes `oauth_url`, `status`, and `role_id`. The Slack URL uses read-only user scopes and PKCE.

Ingest:

```bash
curl --silent --show-error \
  -X POST http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"ingest_data","arguments":{"service":"slack","query":"pipeline","max_items":10}}}'
```

With fixtures enabled and Redis unset, the job finishes in the request and returns a chunk count. With `REDIS_URL` set, a Celery worker runs `wisdomtwin.ingest`.

## Environment

Copy `.env.example`. Secrets stay in the environment. The sample file has empty values.

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Embeddings and generation. Absent in tests; a local grounded answer is used instead. |
| `OPENAI_GENERATION_MODEL` | Default `gpt-6.1-sol`. Any compatible model can be set here. Temperature is 0.3. |
| `OPENAI_EMBEDDING_MODEL` | Default `text-embedding-3-small`, 1536 dimensions. |
| `DATABASE_URL` | Postgres with pgvector. Unset uses memory, which is for local runs and tests. |
| `REDIS_URL` | Celery broker. Unset runs ingestion inline. |
| `SLACK_CLIENT_ID` / `SLACK_CLIENT_SECRET` | Slack app. Read-only user scopes only. |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Used only after the Gmail or Drive flag is on. |
| `SLACK_CONNECTOR_ENABLED` | Default true. |
| `GMAIL_CONNECTOR_ENABLED` | Default false. |
| `DRIVE_CONNECTOR_ENABLED` | Default false. |
| `CONNECTOR_TOKEN_KEY` | Encrypts connector tokens at rest. Required before a real grant is stored. |
| `OAUTH_CLIENT_ID` / `OAUTH_REDIRECT_URIS` | Public MCP client. Add the redirect URI shown in the OpenAI dashboard. |
| `PUBLIC_BASE_URL` | HTTPS origin of this server. |
| `OPENAI_APPS_CHALLENGE` | Exact domain-verification token from the plugin portal, served as plain text at `/.well-known/openai-apps-challenge`. |

Role titles are free text. The connect tool suggests this picklist: Chairman, Chief Executive Officer, President, Chief Operating Officer, Chief Financial Officer, Chief Strategy Officer, Chief of Staff, Corporate Secretary, Chief Technology Officer, Chief Information Officer, Chief AI Officer, Chief Information Security Officer, VP of Engineering, VP of Data and Analytics, Chief Revenue Officer, Chief Commercial Officer, Chief Marketing Officer, VP of Sales, VP of Marketing, VP of Customer Success, General Counsel, Chief Compliance Officer, Controller, Treasurer, VP of Human Resources, Head of Talent, VP of Operations, Head of Procurement, VP of Program Management, Head of Business Operations.

## Google testing mode

Gmail and Drive use restricted scopes. Until Google grants verification:

- The consent screen shows a warning that the app is not verified.
- At most 100 test users can grant access, and only if they are listed on the consent screen.
- WisdomTwin still returns an availability message for those tools because the connectors default to off.

The packet Roman needs is in `google-verification/`. Verification has not been submitted from this repository.

## Deploy

`deploy.sh` expects the Railway CLI, a logged-in session, and `RAILWAY_PUBLIC_URL`. It uploads this directory, sets variables whose names are listed in the script, and requests `/health`. It does not print variable values. Run it without shell tracing.

Set the Railway service root to `plugin-scaffold` if the service is created from the repository root. The Postgres service must provide pgvector. The server applies `schema.sql` when `DATABASE_URL` is set. Apply that file yourself as well if you want the tables in place before the first boot.

Replace `https://REPLACE_WITH_RAILWAY_PUBLIC_URL/mcp` in `mcp.json` with the real `/mcp` URL before you upload the plugin package.

## Submission checklist

Confirm each item in the dashboards. This repository cannot see them.

- Verified organization in the OpenAI dashboard. `manifest.json` and `plugin.json` use WisdomTwin Inc. Change `developer_organization` and `developerName` if the verified name differs. That confirmation is Roman's.
- Privacy policy URL https://wisdomtwin.ai/privacy is public. The page is `public/privacy/index.html`. It is live only after the site deploy that includes it.
- HTTPS MCP endpoint from Railway, then the portal's domain check. Put the portal's challenge token in `OPENAI_APPS_CHALLENGE` and redeploy. Do not commit the token.
- Five screenshots: connect with a role title, domain rejection, Slack ingest progress, a cited answer, and the status panel.
- A demo recording URL, reviewer credentials for a sample Slack workspace, and PNG icons if the uploader rejects the SVG placeholder at `assets/logo.svg`.

Package the plugin from this directory so `plugin.json` is at the archive root. Leave `.env` out.

## Limitations

Not implemented:

- The role interview
- The huddle
- Predecessor ingestion
- Microsoft 365 and Notion
- Gmail and Google Drive, pending Google verification

Also out of this build: write scopes, actions on behalf of the user, and a ChatGPT UI surface.

## Tests

```bash
uv run pytest
```

The cases cover role creation and reuse, Slack fixture ingestion with tenure metadata, a cited answer, status, namespace deletion, consumer-domain rejection, an empty index, quota, and gated Gmail.
