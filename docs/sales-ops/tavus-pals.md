# Tavus company PALs

Checked Tuesday, October 6, 2026. A new Tavus API key was stored outside this repository with mode 600. This file does not contain the key. Official docs were rechecked the same day, before any create or update.

No personal face exists on this key. No WisdomTwin PAL and no N5R PAL were created. Stock faces were not used as a stand-in for Roman.

## Identity check

Authenticated GET requests used header `x-api-key`. Base URL `https://tavusapi.com`.

| Check | Result |
| --- | --- |
| User faces | `GET /v2/faces?verbose=true&face_type=user&limit=50` returned `total_count` 0. |
| Personal face id | None. |
| All faces | 145 faces. Every one is `face_type` `system`. No face name contains Roman or Bodnarchuk. |
| PAL ids created today | None. |
| Conferencing emails | None. |
| Existing Roman-named PALs | Still present. Not deleted, not overwritten, and not reused. |

`GET /v2/pals?limit=100` returned `total_count` 38. The two PALs below are the only ones whose names suggest Roman. The same ids were on the October 5 inventory, so this key reaches that account. Their faces are stock system faces, Lee and Mateo.

| PAL id | PAL name | Face id | Face name | Face type | Training status | Finetune | Model |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pc304da53b20` | Roman Bodnerchuk | `r8495a788aa1` | Lee | system | completed | completed | phoenix-4.5 |
| `pa5b0d4c5228` | Roman | `rbb3d627a705` | Mateo | system | completed | completed | phoenix-4.5 |

Both use `pipeline_mode` `full` and `tts_engine` `tavus-auto`. Neither has an external voice, document ids, document tags, or a conferencing layer. Created October 3, 2026.

## Blocker

Roman must finish Tavus face training with a consent video. A completed personal face (`face_type` `user`, `status` `completed`) is required before either company PAL can be created. A stock face such as Lee or Mateo must not be presented as Roman.

## Voice

`ELEVENLABS_API_KEY` is not available in this environment. Official TTS docs say a private ElevenLabs voice needs all three of `tts_engine` `elevenlabs`, `external_voice_id`, and the ElevenLabs API key. The intended voice id is `OtTgp0gIgmfhqSXfyakl`. It was not placed on a PAL by itself. Until that key exists, leave Tavus default TTS. Any PAL created later will not yet sound like the ElevenLabs clone.

## Conferencing

Not configured. Official meetings docs allow `layers.conferencing.allowlist` with exact emails, which can limit invites to `roman@n5r.com` and `roman@wisdomtwin.ai`. An empty allowlist would let any sender invite the PAL, including a public Calendly guest list. Public auto-join was not turned on.

Username check was read only. Nothing was reserved.

| Username | Available | Note |
| --- | --- | --- |
| `wisdomtwin-roman` | false | Username is already taken. No email was returned, because no PAL was created. |
| `n5r-roman` | true | Free at this check. Not assigned. |

## Still missing

- A completed personal face id for Roman, after consent-video training.
- `ELEVENLABS_API_KEY`, then `tts_engine` `elevenlabs` plus `external_voice_id` `OtTgp0gIgmfhqSXfyakl`. Sound is not his clone until then.
- Approved price language. Do not state the unapproved WisdomTwin overage (USD $5,000 setup and USD $500 per month) or the unapproved N5R floor (USD $15,000). If price comes up, Roman follows up with the approved terms.
- Conferencing only after the face exists, and only with an allowlist limited to `roman@n5r.com` and `roman@wisdomtwin.ai`. `wisdomtwin-roman` is taken, so the WisdomTwin username has to be a different distinctive name. If the API cannot restrict senders to those two addresses, omit conferencing.
- Do not attach the investor deck or grant-titled knowledge documents.

## What the two PALs will be, once a personal face exists

Both use `pipeline_mode` `full`, `default_face_id` set to his trained face, and an introduction as Roman's AI twin for that company, not as Roman the human. Tavus default TTS until the ElevenLabs key exists.

WisdomTwin: Judgment Platform for regulated enterprises. Buyer outreach only. No fundraising, SAFE, valuation, or investor ask. Demo `https://www.wisdomtwin.ai/demo`. Truth baseline: pre-revenue, zero production users, zero paying customers, USD $0 product revenue, five synthetic demonstrations. Talent Lab only as a client outcome on the record (USD $5.5 million attributed to Talent Lab's CEO, not WisdomTwin revenue). Do not invent certifications.

N5R: practical AI training at `https://n5r.ai`. Ontario businesses are the campaign. Do not reject a suitable business only because it is outside a regulated industry. No WisdomTwin branding and no fundraising. Never guarantee grants or funding. Defer pricing to Roman.

## Docs rechecked

October 6, 2026:

- `https://docs.tavus.io/api-reference/authentication`
- `https://docs.tavus.io/api-reference/faces/list-faces`
- `https://docs.tavus.io/api-reference/pals/create-pal`
- `https://docs.tavus.io/api-reference/pals/list-pals`
- `https://docs.tavus.io/sections/conversational-video-interface/pal/tts`
- `https://docs.tavus.io/sections/conversational-video-interface/pal/meetings`

No conversation was started. No video minutes were spent.
