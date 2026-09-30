# WisdomTwin terms of service

Effective date: September 30, 2026

These terms cover the WisdomTwin plugin and the MCP server that serves it. WisdomTwin Inc, a Delaware corporation, incorporated August 2026, provides the service. Contact privacy@wisdomtwin.ai.

## The service

WisdomTwin keeps a private business twin for one role on the org chart, and for the current officeholder of that role. Slack is the live connector. Gmail and Google Drive stay off until Google verification clears. Answers are drawn from that role's index, and each claim carries a citation.

## Acceptable use

Connect a managed business domain. Consumer email domains are rejected. Use the connectors with read-only scopes. Do not ask WisdomTwin to send messages, change files, or act in a connected account. The plugin has no write scopes.

## Your data

During an ingestion job, WisdomTwin reads the communications you authorize. After embedding, it keeps vectors and the short excerpts needed for citations and keyword search. Raw source payloads are not kept after the job. A role namespace is deleted 30 days after last activity, or when you ask, whichever comes first. WisdomTwin does not train models on user data.

## Accounts

Connector access uses OAuth with PKCE. You can disconnect by asking WisdomTwin Inc to delete the role namespace. Reviewer and production credentials stay outside this package.

## Fees

The free tier indexes 1,000 chunks per month. WisdomTwin Pro is USD 20 per month, billed by WisdomTwin Inc through WisdomTwin checkout. This plugin does not take payment.

## Availability

The service can be interrupted for maintenance, quota, or a connector that is still gated. Gmail and Google Drive return an availability message until those connectors are turned on.

## No certification claim

SOC 2 Type II is a roadmap item. WisdomTwin Inc does not claim that certification, or any other certification, today.
