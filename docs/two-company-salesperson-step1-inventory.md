# Two-company virtual salesperson: Step 1 inventory

Checked Monday, October 5, 2026. Read-only. No HubSpot records, ElevenLabs agents, Calendly events, Slack messages, or credentials were changed. Recent call counts below are owner tests. They are not sales traction.

Rollback for this step: none. No external mutation was made.

## Verdict

Step 1 is complete as an inventory. Later configuration is blocked.

The first missing secret is `HUBSPOT_PRIVATE_APP_TOKEN`. It is required before Step 2. The connected HubSpot tool is OAuth. It is not a private app, and ElevenLabs documents a private app token (`pat-`) for its HubSpot integration. The same token is the documented way to read `dataHostingLocation`. Hosting region stays unknown until that read succeeds. Do not paste the token into chat.

`TAVUS_API_KEY` is also absent. Tavus account entitlements stay unknown. That secret is not the next action.

## Authenticated accounts

| System | Status | Evidence |
| --- | --- | --- |
| ElevenLabs | Verified | Creator and admin `roman@n5r.com`. Agents listed earlier in this run; `has_more` was false. |
| HubSpot | Verified identity, hosting unknown | Portal `66868`, user `106421`, owner `20`, `roman@n5r.com`, Roman Bodnarchuk, Founder and CEO. Account type `STANDARD`. Portal name `N5R.ai`. UI domain `app.hubspot.com`. Time zone `America/New_York`. Currency USD plus CAD. Created `1278669541000`. Onboarding not completed. |
| Calendly | Verified | User slug `romanbodnarchuk`. Scheduling page `https://calendly.com/romanbodnarchuk`. Organization kind `single`, plan `standard`, stage `paid`. |
| Google Calendar | Verified | Primary calendar `roman@n5r.com`, time zone `America/Toronto`. A WellnessLiving calendar is also present and is unrelated. |
| Tavus | Blocked | No Tavus MCP namespace. Composio search did not return a Tavus toolkit. Connected Composio apps do not include Tavus. Zapier catalog search for Tavus returned no apps. `TAVUS_API_KEY` is unset on this machine. |
| Slack | Read verified, no alert channel | Member channels: `#general`, `#random`, `#condooutlet`, `#los_suenos`, `#park_central`. A search for an alert channel returned nothing. No message was sent. |
| This repository | Verified gap | WisdomTwin Vite demo. No worker, no host, and no env file with the target secrets. `op` is not installed. The 1Password connector is in an error state and only exposes authentication. |

## Feasibility conflicts

1. The required WisdomTwin booking URL exists, and its duration is 15 minutes, not 20. Slug `20min` does not prove duration. Name: `15-Min Intro: WisdomTwin.ai`. Booking URL: `https://calendly.com/romanbodnarchuk/20min`. Location kind: `google_conference`. Active, unpaid, instant booking. Updated `2026-10-05T00:49:16Z`.
2. Live buyer-agent copy and the non-live salesperson branch still say a twenty-minute demo. The public demo site in this repository also describes a 20-minute booking. That is a copy mismatch with the live 15-minute event. Do not shorten the event and do not buy a Tavus upgrade from this finding.
3. A Tavus 15-minute conversation cap is not established for this account. Public pricing checked today is not this account's plan. See the Tavus section.
4. Calendly user time zone and the default Working hours schedule are `America/New_York` (Monday through Friday, 07:00 to 19:00, weekends closed). Google Calendar for `roman@n5r.com` is `America/Toronto`. The requested scheduling context is `America/Toronto`. The N5R agent prompt time zone field is `America/Toronto`. The event-type payload does not name the connected Google calendar. `google_conference` shows the location kind only.
5. HubSpot data hosting location is unknown. `app.hubspot.com` and portal `66868` are not proof of `na1`. ElevenLabs still documents US-hosted HubSpot only and excludes tokens that start with `pat-eu1`.
6. There is no WisdomTwin value on the deal property `brand_pipeline` or the contact property `lead_owned_by_company`.
7. Neither salesperson branch has a phone number, a Calendly tool, or a HubSpot tool. The only workspace phone number is assigned to a different test agent.

## Calendly event types

Both active event types for the connected user. Inactive types were not requested. Organization plan `standard` / `paid` meets the documented paid-plan requirement for the Scheduling API. The connector did not return granted OAuth scopes. Successful reads show `users:read`, `organizations:read`, `event_types:read`, and `availability:read` are usable. Write scopes were not tested and are not assumed.

| Event | Booking URL | Duration | Location | Notes |
| --- | --- | --- | --- | --- |
| 15-Min Intro: WisdomTwin.ai | `https://calendly.com/romanbodnarchuk/20min` | 15 minutes | Google conference | Slug `20min`. Description says a 15-minute conversation. No custom questions. |
| Roman Bodnarchuk \| N5R.ai \| 15-Minute Business Call | `https://calendly.com/romanbodnarchuk/roman-bodnarchuk-n5r-ai-15-minute-business-call` | 15 minutes | Google conference | Created `2026-10-05T00:49:16Z`. Optional preparation question. This is the N5R event. It is not missing. |

ElevenLabs Calendly integration, rechecked today, uses a Calendly personal access token, not this OAuth connector. No `CALENDLY_*` variable is set. Native Calendly tools are not attached to any inspected agent. Do not request that token until the HubSpot step is unblocked.

## ElevenLabs workspace

Phone numbers: one.

- `phnum_9801m3aewp7zfa2vsjwtg3jemg5h`, Twilio, inbound and outbound, label describes a temporary US number for the Ontario Job Grant booker.
- Assigned only to `agent_9601m3zbep94f1rbt80q1298qed4`.

Secrets, names only. Values were not returned.

- `twilio_basic_auth_628`, used by tool `send_booking_link_sms`.
- A second stored secret whose name is a Twilio account token. It is used by the phone number above.
- No HubSpot, Calendly, or Tavus secret.

Tools: one webhook, `tool_2701m3vwgah8fddrnb5h2xz4b9sp`, `send_booking_link_sms`. It posts a fixed WisdomTwin booking text to Twilio. No HubSpot tool. No Calendly tool. MCP server list is empty.

Knowledge base, neither document has dependent agents:

- `ZhZEUkzUgjJR6DuIiyv4`, WisdomTwin Objection Handling v1.0 (2026-08-11), text.
- `jtlLh3W51KIQUoqVW6ZT`, WisdomTwin E4 Investor Deck 2026-08-10, file.

Subscription tier: unknown. Documented read is `GET https://api.elevenlabs.io/v1/user/subscription` with header `xi-api-key`. No MCP tool exposes it. `ELEVENLABS_API_KEY` is unset. The OAuth connector is authenticated, so this is not an account-access failure. It is a missing plan read.

Voice `OtTgp0gIgmfhqSXfyakl`:

- Name `Roman Bodnarchuk`.
- Category `professional`.
- `is_library_voice` false. Preview source is a custom workspace voice.
- A second workspace voice, `ZIecdNSyNnsShLMj9VBW`, is named `Roman Bodnarchuk - AI Digital Twin`, category `cloned`, and is not the voice on the inspected agents.
- Stock voices in use elsewhere: `21m00Tcm4TlvDq8ikWAM` (Rachel) and `EXAVITQu4vr4xnSDxMaL` (Bella).

### Build targets already present

Do not create new agents. Do not overwrite unrelated agents. Do not merge these branches. Both salesperson branches have 0 percent live traffic and 0 calls in seven days.

| Agent | Branch | Live share | What it is |
| --- | --- | --- | --- |
| `agent_2501m34tx48gfa9v218pndv3gfwq` WisdomTwin Buyer Twin (Outbound Voice), owner test | Main `agtbrch_7001m34tx5mzfb39nqav060x19sj` | 100 percent, 8 calls in 7 days | Owner-test SMS booker. Tool `send_booking_link_sms`. No phone on the agent. Max duration 600 seconds. Knowledge empty. Prompt tells a live person it will text the `20min` link and says twenty minutes. |
| Same agent | `agtbrch_4801m41hzcaqfymrmhq7cbs3yvsh` `vs-build-2026-10-03` | 0 percent | Virtual salesperson qualification prompt. Version `agtvrsn_3501m41j9vt9evb8znv13z0dr291`. No webhook tools. System tools only: end call, skip turn, voicemail. Still offers a twenty-minute demo. Guardrail blocks prices, fundraising, and unconfirmed bookings. |
| `agent_8401m3zh2kqret69d7f1s4w6b882` N5R Ontario, Roman's AI Assistant | Main `agtbrch_0601m3zh2q66fhparbx5vjdtsnep` | 100 percent, 1 call in 7 days | Practical AI training. No tools except end call and voicemail. No phone. Max duration 180 seconds. Prompt time zone `America/Toronto`. Says the Roman call is free and 15 minutes. Does not book. |
| Same agent | `agtbrch_3201m41hzgc8e2frd6jdmv14xd0b` `vs-build-2026-10-03` | 0 percent | Virtual salesperson qualification prompt. Version `agtvrsn_2301m41ja2fhev29qd8v5efphfd1`. No calendar or HubSpot tools. Fifteen-minute N5R call. No phone. |

Other inspected agents, not build targets:

- `agent_9601m3zbep94f1rbt80q1298qed4` Ontario Job Grant Booker, test only. Holds the only phone number. Prompt expects `check_availability` and `book_meeting`, and those tools are not attached. Do not reassign this number in this pass.
- `agent_2401kmr16z5cf92vs712rxf2rb20` N5R.ai HubSpot AI Agency Agent. Rachel stock voice. No tools, no knowledge, no phone. Prompt contains unsupported commercial claims. Do not use.
- `agent_1601kmr16vrtf8dbq6fa8b26fz59` WisdomClone.ai Sales Agent. Rachel stock voice. No tools. Prompt contains unsupported commercial claims. Do not use.
- `agent_4401kztk4nhve6n9r5f6tat2bs3p` WisdomTwin Buyer Twin site-wide, draft. Bella stock voice. No tools. Max duration 240 seconds. Draft prompt contains a pricing ladder. This inventory does not adopt that ladder as an authorized offer.
- `agent_9301kztht2pgebs8dv369ztv1qqp` WisdomTwin Investor Twin. Do not use for buyer outreach. Full prompt was not re-read in this pass.
- Not re-read in this pass, so they stay untouched: `agent_6701m3zgwer2e9q88czjrjamssre`, `agent_2201m3zwpq8be8xbv599kmacvdmh`, `agent_3001m3wekqsmfpv8vvtmd43ygszt`, `agent_2901k8na8dyvfvx9zrb048zp1et1`.

## HubSpot CRM shape

Read and write are available for contact, company, deal, call, note, meeting, and task. Lead and campaign require account modification. The native connector is OAuth. No private app token is on this machine.

`get_organization_details` account information omitted `dataHostingLocation` and hublet. Official account-details responses include `dataHostingLocation`. Until `GET /account-info/v3/details` or `GET /account-info/2026-03/details` is called with an authenticated token, hosting stays unknown.

Deal pipelines read from the portal:

- `898025253` Microdosing AI Operator Pipeline
- `default` Sales Pipeline, with many legacy stage labels
- `t_c07697877e2fef80914339a523482969` Tenant Deal Pipeline
- `8086a228-382f-4cca-aa15-be5b90fce4e2` Developer Kit
- `874015340` Wisdom Clone - Lead Generation
- `897725027` Microdosing AI Revenue Pipeline
- `900486230` Microdosing AI Launch Pipeline
- `855656586` Executive AI Implementation 2026
- `890773509` RFP AI Opportunities
- `81ee3345-1b0f-42aa-9e78-580614546602` HubSpot Shared Selling Pipeline

No pipeline is named WisdomTwin.

`brand_pipeline` options, stored labels only, not validated as current offers: `n5r_agency`, `wisdomclone`, `10x_mastermind`, `ai_training`. WisdomTwin is absent.

`lead_owned_by_company` options: `N5R`, `Sociable Living`. WisdomTwin is absent.

`lead_source_campaign` is a free-text contact property. `n5r_lifecycle_stage` is a separate contact enumeration. The campaign object itself is not available to this connector.

Association label definitions are not exposed by the tools used. Contact, company, and deal records can be read. Custom association labels were not inventoried.

Teams returned: N5R (owner 20 only), Trevor David, Casaco, Sociable Living. Seat name returned: `core`.

## Tavus

Account status: unknown. No replicas, PALs, faces, conferencing usernames, or webhook subscriptions were read, because there is no credential.

Public pricing page `https://www.tavus.io/pricing`, fetched October 5, 2026, is not this account. The page shows more than one plan table. In the developer cards visible on that fetch, Google Meet and Zoom configuration counts are separate from concurrent sessions. Examples on that page: Starter lists 1 configuration and 1 concurrent session; Builder lists 3 and 3; Growth lists 7 configurations and up to 10 concurrent sessions, plus the line "No conversation duration limit." A 15-minute per-conversation cap for this account was not verified. The WisdomTwin event is 15 minutes, so the specific conflict "20-minute event versus a 15-minute Tavus cap" is not established.

Docs rechecked the same day:

- PAL meetings: conferencing is a layer with `username`, allowlist, and an address at `tavusinvite.com`. Create conversation can also join with `meeting_url`. Auth header `x-api-key`. A PAL needs `default_face_id` when conferencing is set.
- PAL TTS: `voice_id` or `external_voice_id`. ElevenLabs private voices need the provider API key. Public ElevenLabs voices do not. `voice_id` and `external_voice_id` are mutually exclusive.
- Webhooks: `callback_url` on create conversation. Events include `system.pal_joined`, `system.shutdown` (including `max_call_duration reached`), `application.transcription_ready`, and `application.recording_ready`.

This repository has no worker to receive those callbacks. No host is invented.

## Documentation log

Method for each row: public page fetch on October 5, 2026. No authenticated call was made to these vendor APIs from this machine.

| Topic | URL | What was confirmed |
| --- | --- | --- |
| ElevenLabs HubSpot | `https://elevenlabs.io/docs/eleven-agents/customization/integrations/hubspot` | Private app token. US hosting via `api.hubapi.com`. `pat-eu1-` not supported. Zero retention not supported. |
| ElevenLabs Calendly | `https://elevenlabs.io/docs/eleven-agents/customization/integrations/calendly` | Personal access token. Availability, booking, list, and cancel are described. Zero retention not supported. |
| ElevenLabs list agents | `https://elevenlabs.io/docs/api-reference/agents/list` | `GET /v1/convai/agents`. Page size max 100. Auth is the API key header on the raw API. |
| ElevenLabs subscription | `https://elevenlabs.io/docs/api-reference/user/subscription/get` | `GET /v1/user/subscription` returns `tier`. Not called. Key absent. |
| Calendly AI scheduling | `https://developer.calendly.com/docs/api-guides/schedule-events-with-ai-agents` | Map event type, `GET /event_type_available_times`, `POST /invitees`. Paid plan required. Availability window max 31 days. |
| Calendly scopes | `https://developer.calendly.com/docs/authentication/scopes` | Scope catalog. Connector did not echo the granted set. |
| HubSpot account details | `https://developers.hubspot.com/docs/api-reference/legacy/account/account-information/guide` | `GET /account-info/v3/details` returns `dataHostingLocation`. Current guide also documents `GET /account-info/2026-03/details`. |
| Tavus meetings | `https://docs.tavus.io/sections/conversational-video-interface/pal/meetings` | Conferencing identity versus ad hoc `meeting_url`. |
| Tavus TTS | `https://docs.tavus.io/sections/conversational-video-interface/pal/tts` | Tavus voice or external ElevenLabs voice. |
| Tavus webhooks | `https://docs.tavus.io/sections/webhooks-and-callbacks` | Conversation, guardrail, objective, face, and video callbacks. |
| Tavus pricing | `https://www.tavus.io/pricing` | Public cards only. Configuration count is not concurrency. Not this account. |

## Single next action

Store `HUBSPOT_PRIVATE_APP_TOKEN` in 1Password or the Cursor secret store. Do not paste it into chat.

Create it in HubSpot under Development, Legacy apps, Private. Grant only the CRM read scopes needed for the first proof read. After the secret is available to this environment, call account details and record `dataHostingLocation`. If it is not a US location, stop before connecting ElevenLabs. ElevenLabs rejects EU private-app tokens.

1Password is not usable from this run until its connector is authenticated. The `op` CLI is not installed. Env vars `HUBSPOT_PRIVATE_APP_TOKEN`, `ELEVENLABS_API_KEY`, `TAVUS_API_KEY`, and `CALENDLY_*` are unset.

Do not start prospect outreach. Do not buy a Tavus plan. Do not merge `vs-build-2026-10-03`.
