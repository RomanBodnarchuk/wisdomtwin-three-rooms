# Two-company virtual salesperson: Step 3 Calendly booking

Checked Tuesday, October 6, 2026. The Calendly personal access token is stored only in a mode-600 file outside this repository. It is not committed, and it is not printed here. The env template names `CALENDLY_API_TOKEN` and contains no value.

Rollback for this step is complete. The two owner-test appointments created here were canceled. Event types were not edited. No HubSpot record was written. No ElevenLabs branch was edited.

## Verdict

Direct booking works for both companies from `services/salesperson-worker`. One personal access token can call both event types because they are on one account. Isolation is a server-side guard in that worker. A WisdomTwin caller cannot book, list, or cancel the N5R event type, and the reverse is also refused.

One owner-test slot was booked for each company, for `roman@n5r.com` only. A duplicate WisdomTwin request returned the same appointment. Each campaign list showed only its own appointment. Each campaign was refused when it tried to cancel the other company's appointment. Both appointments were then canceled, and a follow-up read showed no active owner appointment in the test window.

Prospect booking stays blocked. A self-asserted email is not verification. The worker will not email anyone other than the owner-test contact.

## Account

`GET https://api.calendly.com/users/me` returned 200 when the request carried `Authorization: Bearer` and a User-Agent. The same call without a User-Agent returned 403. The worker sends `wisdomtwin-salesperson-worker/0.1`. The token is read from the environment variable `CALENDLY_API_TOKEN` or from `CALENDLY_TOKEN_FILE`. This run used the outside file.

| Field | Value |
| --- | --- |
| Name | Roman Bodnarchuk |
| Email | `roman@n5r.com` |
| User URI | `https://api.calendly.com/users/DBHDBPAOK4RMWSRQ` |
| Slug | `romanbodnarchuk` |
| Scheduling page | `https://calendly.com/romanbodnarchuk` |
| User time zone | `America/New_York` |
| Organization | `https://api.calendly.com/organizations/BDBDAJGOIYV5UVPH`, plan `standard`, stage `paid`, kind `single` |

The JWT payload `user_uuid` is `DBHDBPAOK4RMWSRQ`, which matches the user URI. Granted scope names from that payload, and only the names:

`availability:read`, `availability:write`, `event_types:read`, `event_types:write`, `locations:read`, `routing_forms:read`, `shares:write`, `scheduled_events:read`, `scheduled_events:write`, `scheduling_links:write`, `meeting_recaps:read`, `meeting_recaps:write`, `contacts:read`, `contacts:write`, `groups:read`, `organizations:read`, `organizations:write`, `users:read`, `activity_log:read`, `data_compliance:write`, `outgoing_communications:read`, `webhooks:read`, `webhooks:write`.

This step used reads of the user, organization, event types, available times, and scheduled events, plus `scheduled_events:write` for the owner-test create and cancel. The available-times path names `availability:read` in the OpenAPI description, and the scope catalog also lists that path under `event_types:read`. The token has both, and the call returned 200. This step did not create or edit an event type, a webhook, a contact, or a compliance deletion.

Invitee time zone for the owner test was `America/Toronto`. Google Calendar for `roman@n5r.com` remains `America/Toronto`. The Calendly user time zone remains `America/New_York`. The worker does not rewrite one into the other.

## Event types

Read again on October 6, 2026. Neither record was patched. The WisdomTwin slug `20min` was not shortened or renamed. No second N5R event was created.

| Event | URI | Booking URL | Duration | Location | Slug |
| --- | --- | --- | --- | --- | --- |
| 15-Min Intro: WisdomTwin.ai | `https://api.calendly.com/event_types/DGDHPUSUU24UVHEM` | `https://calendly.com/romanbodnarchuk/20min` | 15 minutes | `google_conference` | `20min` |
| Roman Bodnarchuk, N5R.ai, 15-Minute Business Call | `https://api.calendly.com/event_types/803240ac-719e-4b20-a346-e8bc5b167262` | `https://calendly.com/romanbodnarchuk/roman-bodnarchuk-n5r-ai-15-minute-business-call` | 15 minutes | `google_conference` | `roman-bodnarchuk-n5r-ai-15-minute-business-call` |

The live N5R name uses vertical bars. It was not renamed. WisdomTwin has no custom questions. N5R has one optional preparation question. The booking request omitted it. Both types are active and `solo`.

## Availability before booking

Read through the worker, before the owner-test create. Window `2026-10-06T19:21:02Z` through `2026-10-08T17:21:02Z`. Times below are `America/Toronto`.

| Campaign | Open slots | First slots |
| --- | --- | --- |
| WisdomTwin | 10 | 2026-10-07 13:45, 14:00, 14:15, 14:30, 14:45 |
| N5R | 16 | 2026-10-06 18:00, 18:30, 2026-10-07 07:00, 07:30, 08:00 |

The worker then chose the earliest pair that does not overlap: WisdomTwin at 13:45 on October 7, and N5R at 18:00 on October 6.

## Owner test

The verified contact is HubSpot `143893597452`, email `roman@n5r.com`, name Roman Bodnarchuk. This step did not write HubSpot. Confirmation required the name, email, date, time, and time zone before create. Success was printed only after Calendly returned an active invitee.

| Campaign | Toronto start | UTC start | Scheduled event | Create result |
| --- | --- | --- | --- | --- |
| WisdomTwin | 2026-10-07 13:45 | `2026-10-07T17:45:00Z` | `https://api.calendly.com/scheduled_events/09ddeeb9-4e49-49d0-8a32-5b9214e9938f` | `booked` |
| WisdomTwin duplicate | same slot | same instant | same URI | `already_booked` |
| N5R | 2026-10-06 18:00 | `2026-10-06T22:00:00Z` | `https://api.calendly.com/scheduled_events/c844910d-db68-4697-a108-c19b735356c9` | `booked` |

Before cancel, the WisdomTwin list contained only the WisdomTwin URI, and the N5R list contained only the N5R URI. WisdomTwin cancel of the N5R URI was rejected. N5R cancel of the WisdomTwin URI was rejected. The matching cancels then succeeded with reason `Owner test cleanup`.

Follow-up reads after cancel:

| Event | Status | Event type | Invitee | Invitee time zone |
| --- | --- | --- | --- | --- |
| `09ddeeb9-4e49-49d0-8a32-5b9214e9938f` | `canceled` | WisdomTwin URI above | `roman@n5r.com`, status `canceled` | `America/Toronto` |
| `c844910d-db68-4697-a108-c19b735356c9` | `canceled` | N5R URI above | `roman@n5r.com`, status `canceled` | `America/Toronto` |

Active scheduled events for `roman@n5r.com` inside the test window: 0.

Calendly generated the normal booking and cancellation notices to `roman@n5r.com`. No other address was invited. No guest was added. No SMS reminder number was sent.

## Tests

`node --experimental-strip-types --test test/**/*.test.ts` in `services/salesperson-worker`: 11 passed, 0 failed.

Covered without the live token: Toronto conversion of both sample slots, both directions of the event-type guard, rejection of a self-asserted email and of the send-domain HubSpot id `223451166888`, refusal to book without confirmation, one create for concurrent duplicate requests, reconcile-after-timeout without a second create in the same call, campaign list and cancel isolation, and the full owner-test procedure against a fake Calendly client. The HTTP client test uses the literal `local-test-value`, not the personal access token. A scan of the worker tree rejects a long JWT-shaped string.

## ElevenLabs

The native Calendly integration expects the personal access token in the ElevenLabs UI. Checked October 6, 2026: [Calendly integration](https://elevenlabs.io/docs/eleven-agents/customization/integrations/calendly). A workspace secret can be created with `POST https://api.elevenlabs.io/v1/convai/secrets` ([Create secret](https://elevenlabs.io/docs/eleven-agents/api-reference/workspace/secrets/create)). The 200 response returns `secret_id` and `name`, not the value.

That create was not called. `ELEVENLABS_API_KEY` is unset. The connected agent tools can list secret names and do not expose a create-secret tool. `agents_list_secrets` with search `CALENDLY` returned no secrets. Passing the token through a tool argument would put it in the tool log, so that path was not used.

No tool was attached to a branch. Live mains were not edited: WisdomTwin `agtbrch_7001m34tx5mzfb39nqav060x19sj` and N5R `agtbrch_0601m3zh2q66fhparbx5vjdtsnep`. The 0 percent branches were also left unchanged: WisdomTwin `agtbrch_4801m41hzcaqfymrmhq7cbs3yvsh` and N5R `agtbrch_3201m41hzgc8e2frd6jdmv14xd0b`.

## Still blocked

- Prospect booking. The worker has no verified contact other than the owner test. HubSpot verification of a buyer is a later step, and this run did not start outreach.
- ElevenLabs. The worker is not hosted and is not attached to an agent.
- Step 2 already proved `dataHostingLocation` `na1` and then deleted its owner-test CRM records. The ElevenLabs HubSpot paste is still not done. The Step 2 note says to narrow the private app before that paste.
- Tavus still has no trained Roman face. No PAL was created. The unapproved drafts in `docs/sales-ops/prompts/` were not installed.
- The US Twilio number `+16282015824` was not assigned.

## Documentation log

Checked October 6, 2026, before the owner-test writes.

| Topic | URL | What was confirmed |
| --- | --- | --- |
| ElevenLabs Calendly | `https://elevenlabs.io/docs/eleven-agents/customization/integrations/calendly` | Personal access token in the integration UI. Availability, booking, list, and cancel. Zero retention is not supported. |
| Schedule with AI agents | `https://developer.calendly.com/docs/api-guides/schedule-events-with-ai-agents` | `GET /event_type_available_times`, then `POST /invitees` with UTC `start_time`, invitee name, email, and IANA time zone. Location kind is required when the event type has a location. Paid plan required. Availability window max 31 days. |
| Scopes | `https://developer.calendly.com/docs/authentication/scopes` | Scope catalog. `scheduled_events:write` covers create invitee and cancel. `event_types:read` covers available times. |
| OpenAPI | `https://developer.calendly.com/openapi/calendly-api.yaml` | Create body, Google conference location, list events by user and `invitee_email`, cancel `POST /scheduled_events/{uuid}/cancellation`. List events has no event-type query, so the worker filters `event_type` after the read. |
| ElevenLabs secret create | `https://elevenlabs.io/docs/eleven-agents/api-reference/workspace/secrets/create` | `POST /v1/convai/secrets`. Not called. |

## Single next action

Make this worker reachable from the 0 percent salesperson branches only. That requires the Calendly token inside ElevenLabs, either pasted into the Calendly integration by Roman or stored with `POST /v1/convai/secrets` once `ELEVENLABS_API_KEY` is available without logging the value. Do not attach the tool to either live main branch. Do not book a prospect until a server-side contact check exists for that person.
