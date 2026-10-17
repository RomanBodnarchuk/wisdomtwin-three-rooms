# WisdomTwin and N5R Virtual Sales Agent Kit

Version 0.1.0, built 2026-10-04. Owner: Roman Bodnarchuk.

## What this is

This kit holds every file needed to run Roman's two-company video sales twin on Tavus. It also connects the twin to the booking and CRM loop around it:

1. A HubSpot lead is approved.
2. The company's ElevenLabs phone twin calls the lead.
3. The lead books a demo on that company's Calendly event.
4. One minute before the meeting starts, that company's Tavus PAL joins the existing Google Meet. The PAL has Roman's face and Roman's ElevenLabs voice.
5. The PAL runs a 12-to-15-minute qualifying session.
6. The outcome, a summary of what was captured, the transcript and the dated next step are written back to HubSpot.

Nothing here has been applied to any live account yet. Every script defaults to a dry run.

## Status

| Part | State |
|---|---|
| PAL prompts, objectives, guardrails, knowledge base (both companies) | Written, checked against canon, ready to apply |
| Tavus setup script (`tavus:plan`, `tavus:apply`) | Built. The dry run was tested without a Tavus key. **Not yet applied.** |
| Worker (Calendly booking, PAL dispatch, Tavus callbacks, HubSpot write-back) | Built. 14 automated behaviour tests pass. Not deployed. |
| HubSpot and Calendly setup scripts | Built, dry-run by default, not yet run |
| Live owner tests | Not started. Blocked on the items in `ROMAN-ACTIONS.md`. |

## Folder map

```
config/campaigns.json        trusted routing: which event type -> which company PAL, CRM targets, release mode
tavus/prompts/               system prompts (WisdomTwin, N5R)
tavus/pals/                  POST /v2/pals payload templates (placeholders resolved at apply time)
tavus/objectives/            4-step qualification objectives per company (structured outputs -> HubSpot)
tavus/guardrails/            9 guardrails, attached by tag (shared core + per company)
tavus/knowledge/             knowledge base documents (.txt, English, Tavus-supported format)
scripts/tavus-inventory.mjs  READ-ONLY: faces, training status, PALs, conferencing usernames
scripts/tavus-provision.mjs  idempotent setup: guardrails -> objectives -> documents -> PAL -> conferencing
scripts/hubspot-setup.mjs    campaign-membership and idempotency properties; prints meeting-outcome values
scripts/calendly-setup.mjs   lists event types; creates the signed webhook (Standard plan required)
worker/                      the small always-on service (Node 20+, no dependencies)
tests/worker.test.mjs        behaviour tests: routing, owner gate, kill switch, capacity, duplicates, retries
docs/                        architecture, API verification log, owner test plan, runbook, decisions
.env.example                 secret NAMES only; values live in 1Password and the host's .env
```

## Run order

```bash
npm test                          # 14 behaviour tests, no network
npm run tavus:inventory           # read-only, needs TAVUS_API_KEY
npm run tavus:plan                # dry run, prints every request with secrets redacted
npm run tavus:apply -- --campaign=wisdomtwin
npm run tavus:apply -- --campaign=n5r
npm run calendly:list             # copy the two buyer event URIs into config/campaigns.json
npm run hubspot:plan && npm run hubspot:apply
npm run worker                    # on Mac Studio HQ, exposed over HTTPS (see docs/04-runbook.md)
npm run calendly:apply            # creates the webhook once the worker URL is live
```

Then run the owner tests in `docs/03-owner-test-plan.md`. `config/campaigns.json` keeps `release.mode` set to `owner_test` until every gate passes and Roman approves a campaign batch. In that mode, the PAL joins only bookings made from Roman's own addresses.

## Design choices that matter

- **Joining the meeting by API.** The worker sends the PAL into the Meet with `meeting_url`. It does not use a calendar invite to the PAL's email. Tavus documents callbacks and a per-call duration cap only for the API path, and the API path stops a public booking page from summoning the PAL during owner tests.
- **Company routing.** The company is chosen only from `config/campaigns.json`, by Calendly event type. The investor `/20min` event is on an explicit exclude list, so a PAL can never join it.
- **Structured outcomes.** Results come from Tavus objectives, not from an extra AI summary. HubSpot gets what the twin captured, labelled as participant statements that have not been verified. Roman reviews the transcript before acting.
- **No double sessions.** A dispatch timeout is treated as "outcome unknown" and raises an alert. It is never retried blindly, because a retry could put two PALs in one meeting.
- **No guessing.** Unknown conversations and unknown contacts are quarantined, not matched to the nearest record.
- **Secrets.** Every secret is injected from environment variables at runtime. Logs, backups and dry runs redact them.
