# Phase 2 — Tool verification (2026-09-24)

This run executed inside Cursor, not the Grok Build CLI. `grok` is not installed here, so `grok mcp add`, `grok mcp login`, `grok mcp list --json`, and `grok mcp doctor --json` were not run. HubSpot and X were already connected as Cursor MCP servers and were called read-only.

## Servers

| Server | Expected | Result |
| --- | --- | --- |
| HubSpot | `https://mcp.hubspot.com/anthropic` | Connected. Portal account `66868`. Contacts, companies, and deals are readable. Write tools exist on the connector and were not called. |
| X | Remote or stdio X MCP | Connected as the native X server. Account `@romanbodnarchuk`. Search, user lookup, and user-post tools work. |
| FirstTouch | `https://mcp.firsttouch.ai` | Missing. No FirstTouch namespace is installed. `find_leads`, `score_lead`, and enrichment tools were not discoverable. |

## HubSpot tools used

Available and used read-only: `get_user_details`, `tool_guidance`, `get_properties`, `search_properties`, `search_crm_objects`, `query_crm_data`.

Confirmed readable object types include CONTACT, COMPANY, DEAL, TICKET, NOTE, EMAIL, MEETING_EVENT, and CALL. This session did not enumerate every engagement thread.

Not used, by policy: `manage_crm_objects` and every other write, update, or delete tool.

## X tools used

Available and used: `get_users_me`, `get_users_by_username`, `get_users_by_usernames`, `search_users`, `search_posts_all`, `get_users_posts`.

Not used: `send_chat_message` and every other write tool.

## Gaps that block a full three-source scan

- FirstTouch enrichment and LinkedIn approval-queue tools are absent. No LinkedIn action was proposed to a sender.
- `@operatorcollective` was not resolved. A batched username lookup rejected it because the handle is longer than 15 characters, and no separate search was completed.
- `@FPVventures` resolves and has no posts.
- No follower-graph or home-timeline tool was called. Investor monitoring used account timelines and public search.

## Governance

HubSpot stayed read-only. No message, connection request, or CRM write was sent. Raw emails and phone numbers are omitted from filed notes because this Git repository is public.
