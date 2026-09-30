# WisdomTwin privacy policy

Effective date: September 30, 2026

## Who controls this service

WisdomTwin Inc, a Delaware corporation, incorporated August 2026, is the controller of personal data processed by WisdomTwin. Contact privacy@wisdomtwin.ai.

## What WisdomTwin is

WisdomTwin builds a private, business-only twin of one professional inside ChatGPT. The twin belongs to a role on the org chart, such as Chief Revenue Officer or VP of Sales, and to the current officeholder of that role. The product noun is twin.

Slack is the live connector. Gmail and Google Drive are built and stay off until Google verification clears. Those two connectors use read-only scopes and, until verification, run only for the test users Roman adds in the Google Cloud Console.

## Data we process

- The business domain you submit at connect time, after we reject consumer email domains.
- The role title you choose, the organization record for that domain, the current officeholder, and the open tenure.
- Business communications fetched through a connector you authorize.
- Embeddings and the short excerpts required to cite a claim.
- An audit row for each tool call: tool name, outcome, organization, and role. The audit row does not store the raw source payload.
- Connector tokens, encrypted with a key that arrives only as an environment variable.

Raw source payloads exist only during an ingestion job. After embedding, WisdomTwin stores vectors and citation metadata. It does not keep the original provider payload.

## How access works

OAuth uses authorization-code grants with PKCE. Scopes are read-only.

- Slack, production: channel and file history, search, and user email, read-only.
- Gmail, testing mode: `gmail.readonly`.
- Google Drive, testing mode: `drive.readonly`.

WisdomTwin does not request write scopes and does not send, delete, or edit mail, files, or Slack messages.

Consumer domains are rejected at connect time: gmail.com, googlemail.com, hotmail.com, outlook.com, yahoo.com, icloud.com, proton.me, protonmail.com, and aol.com. The accepted business domain is stored on the organization record.

## Why we process it

To ingest business communications into the role you named, to answer questions from that role's index, and to attach a citation to each claim. Retrieval is filtered to that role's namespace in the database.

## Model providers

When an API key is configured, WisdomTwin sends excerpts to the configured embedding model (`text-embedding-3-small`) and to the configured generation model through the Responses API, at temperature 0.3. The default generation model name is set by environment variable. WisdomTwin does not train models on user data.

## Retention

A role namespace is deleted 30 days after last activity, or when deletion is requested, whichever comes first. Deletion removes the indexed chunks for that role.

## Sharing

WisdomTwin Inc does not sell personal data. Hosting, the database, and the configured model provider process data so the service can run. Connector providers (Slack, and Google when those connectors are enabled) receive the OAuth grants you approve.

## Security

Access tokens are encrypted at rest. Secrets are environment variables and are not written into the repository, examples, or logs. SOC 2 Type II is a roadmap item. WisdomTwin Inc does not claim that certification, or any other certification, today.

## Plans

The free tier indexes 1,000 chunks per month. WisdomTwin Pro is USD 20 per month, billed by WisdomTwin Inc through WisdomTwin checkout. The plugin does not take payment inside ChatGPT.

## Your requests

Email privacy@wisdomtwin.ai to request deletion of a role namespace or to ask what this policy covers. We will delete the namespace on request.

## Changes

If this policy changes, the effective date at the top will change with it. The public copy is intended to live at https://wisdomtwin.ai/privacy.
