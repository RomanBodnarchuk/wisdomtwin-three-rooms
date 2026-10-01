# Handover: WisdomTwin MCP plugin

Paste this to Kimi and to GMN 5.3. The prototype is already real code. Do not start a second server from a prompt.

## What this is

WisdomTwin keeps a private business twin for one role on the org chart. The twin belongs to the role and to the current officeholder. Slack is the live read-only connector. Gmail and Google Drive are implemented and stay off until Google verification. Every answer carries a citation from that role's index.

Repository: https://github.com/RomanBodnarchuk/wisdomtwin-three-rooms

Branch: `cursor/wisdomtwin-mcp-plugin-8d09`

Pull request: https://github.com/RomanBodnarchuk/wisdomtwin-three-rooms/pull/15

Working tree: `plugin-scaffold/`

The official Python MCP SDK (`mcp` 2.2.0 or newer) serves streamable HTTP at `/mcp`. Python 3.12. There is also `/health` and `/terms`.

## Team split

Kimi owns the local runnable prototype: install, start the server, open a tunnel, and call the four tools with curl. Keep the tool names, arguments, and return shapes below. If a test fails, fix that behavior in this tree.

GMN 5.3 owns the package review: `plugin.json`, `mcp.json`, `package.sh --check`, the twelve pytest cases, and the limits in this file. Report mismatches. Do not invent a public host. Do not mark the package submitted or approved.

Roman still does the dashboards: Railway origin, `OPENAI_APPS_CHALLENGE`, confirming the verified organization is WisdomTwin Inc, the demo recording, the Slack reviewer account, Google verification, and the directory upload.

## The four tools

Do not add a fifth tool.

| Tool | Arguments | Returns | Access |
| --- | --- | --- | --- |
| `connect_business_account` | `service` slack \| gmail \| drive, `domain`, `role_title` | `{oauth_url, status, role_id}` | readWrite. `readOnlyHint` false |
| `ingest_data` | `service`, `query`, `max_items` default 1000 | `{job_id, progress, chunks_ingested}` | readWrite. `readOnlyHint` false |
| `query_twin` | `question`, `max_results` default 10, `max_tokens` default 512 | one text answer, then citation blocks `{uri, snippet}` | readOnly. `readOnlyHint` true |
| `list_twins_status` | none | one object per connection: `{service, role_title, ingested_chunks, last_update, domain}` | readOnly. `readOnlyHint` true |

Every tool sets `destructiveHint` false and `openWorldHint` false.

Stable errors, as the SDK tool error text: `DOMAIN_REJECTED`, `QUOTA_EXCEEDED`, `OAUTH_PENDING`, `JOB_NOT_FOUND`.

Empty index returns exactly: `I have nothing ingested on that.`

A non-business question returns exactly: `I only answer questions about this role's business record.`

Consumer domains are rejected: gmail.com, googlemail.com, hotmail.com, outlook.com, yahoo.com, icloud.com, proton.me, protonmail.com, aol.com, and their subdomains.

## Run it locally

```bash
cd plugin-scaffold
python3 -m pip install -r requirements.txt
python3 -m pytest -q
```

Twelve cases. They pass on the in-memory store. With Postgres and pgvector:

```bash
WISDOMTWIN_TEST_DATABASE_URL=postgresql:///wisdomtwin_test python3 -m pytest -q
```

Start the fixture server. This path is for curl on your machine. `WISDOMTWIN_AUTH_DISABLED` is ignored when `PUBLIC_BASE_URL` is HTTPS.

```bash
WISDOMTWIN_AUTH_DISABLED=1 \
WISDOMTWIN_USE_FIXTURES=1 \
SLACK_CLIENT_ID=local-test-client \
PORT=8000 \
python3 server.py
```

```bash
curl --fail --silent http://127.0.0.1:8000/health
```

List tools:

```bash
curl --silent --show-error \
  -X POST http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

Connect, then ingest, then ask. Use the same `CRO` title on the second connect if you want the same role id.

```bash
curl --silent --show-error \
  -X POST http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"connect_business_account","arguments":{"service":"slack","domain":"example-corp.com","role_title":"CRO"}}}'
```

```bash
curl --silent --show-error \
  -X POST http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"ingest_data","arguments":{"service":"slack","query":"pipeline","max_items":10}}}'
```

```bash
curl --silent --show-error \
  -X POST http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"query_twin","arguments":{"question":"What is the Acme pipeline stage?"}}}'
```

Expect stage 3, a citation whose uri ends in `/p1001`, and no Northwind snippet. Ten Slack fixtures live in `fixtures/slack/messages.json`.

## Tunnel

Use a tunnel when a remote client must reach the server. ngrok is the documented one. cloudflared is fine if that is what is installed. Do not commit the tunnel host.

```bash
ngrok http 8000
```

For a ChatGPT client, start the server again with auth on and the tunnel origin set before the process starts:

```bash
PUBLIC_BASE_URL=https://YOUR_TUNNEL_HOST \
OAUTH_CLIENT_ID=wisdomtwin-local \
OAUTH_REDIRECT_URIS=https://YOUR_TUNNEL_HOST/oauth/done \
WISDOMTWIN_USE_FIXTURES=1 \
SLACK_CLIENT_ID=local-test-client \
PORT=8000 \
python3 server.py
```

The MCP client is public and uses PKCE S256. Client registration is disabled. Authorize at `/authorize`, approve `POST /oauth/consent`, then exchange the code at `/token`. Send `Authorization: Bearer` on `/mcp`. The resource value is `https://YOUR_TUNNEL_HOST/mcp`.

A tunnel dies when the process dies. It is a prototype origin, not the directory host. Leave `mcp.json` on `https://REPLACE_WITH_RAILWAY_PUBLIC_URL/mcp` until Railway assigns a stable origin. Then:

```bash
./package.sh --check
MCP_SERVER_URL=https://YOUR_HOST/mcp ./package.sh
```

The ZIP is `dist/wisdomtwin-plugin.zip`. It contains `plugin.json`, `mcp.json`, and `assets/logo.svg`. Leave the server, tests, and `.env` out.

## Already decided

- Organizations, the active role, and connections are scoped to the OAuth subject. A second caller does not see the first caller's domain or chunks.
- Same stripped title on the same subject reuses the role and the open tenure. A different title is a different role.
- Citations keep excerpts that share a content term with the question. Words such as "the" do not count.
- Raw provider payloads are discarded after the job. Indexed excerpts stay for citations.
- Free tier is 1,000 chunks per month. WisdomTwin Pro is USD 20 per month, billed by WisdomTwin Inc through WisdomTwin checkout.
- Generation uses the Responses API, model from `OPENAI_GENERATION_MODEL` (default `gpt-6.1-sol`), temperature 0.3. With no API key, a local composer answers from the retrieved excerpts.
- Embeddings are 1536 dimensions. Without `OPENAI_API_KEY`, a local hashed embedding is used. Postgres stores them with pgvector.
- Chunks are about 500 tokens with 20 percent overlap.
- Role namespace is deleted 30 days after last activity, or on request.
- An audit row records tool name, outcome, organization, and role. It does not store the raw payload.
- MCP authorization codes and access tokens are in process memory. A restart asks the client to authorize again. Connector credentials are encrypted in the store.

## Do not build

Role interview, judgment seeds writer, huddle, predecessor ingestion, Microsoft 365, Notion, write scopes, actions on behalf of the user, and a ChatGPT UI surface. `judgment_seeds` exists in `schema.sql` and has no writer.

The product noun is twin. Do not print, in code, manifests, or docs: an approval probability, a review timeline, a protocol or spec version number, unverified market numbers, or a claim that this is the first plugin of its kind. Do not name the paid plan "ChatGPT Pro". Do not model an OpenAI revenue share.

Do not put secrets in files, logs, or examples. Copy `.env.example` and fill values in the shell.

## Files to read first

- `server.py` — SDK server, four tools, `/health`, `/terms`, OAuth consent, Slack and Google callbacks
- `service.py` — domain gate, quota, ingest, query, status, caller binding
- `store.py` and `schema.sql` — memory store and Postgres
- `plugin.json` and `mcp.json` — directory package
- `package.sh` — manifest check and ZIP
- `tests/test_mvp.py` — the twelve cases
- `SUBMISSION_READINESS.md` — done, blocked, and needs Roman
- `google-verification/` — packet for Roman, not a submitted request

## Known local result

On this branch, twelve pytest cases passed on memory and on local Postgres with pgvector. A two-caller HTTP review passed: health, the four tools, domain rejection, gated Gmail, quota, Slack fixture ingest of 10 chunks, the Acme citation, caller isolation, and the non-business refusal. That review used fixture mode and local OAuth. It is not a directory submission.
