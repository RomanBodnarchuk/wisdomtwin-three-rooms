# Tavus company PALs

Checked again at 2:25 PM America/Toronto on Tuesday, October 6, 2026. The Tavus API key stays outside this repository, mode 600. This file does not contain the key. No conversation was started. `POST /v2/conversations` was not called. The Lindsay Meet link was not changed, and `wisdomtwin-roman@tavusinvite.com` was not removed from that event.

Lindsay's WisdomTwin PAL is on the Canva office portrait for the 3:45 PM call. The switch was already on the live PAL before 3:40 PM Toronto.

## Docs used before the N5R create

Auth for every call is header `x-api-key`. Base URL `https://tavusapi.com`.

| Doc | Method and path | Required fields |
| --- | --- | --- |
| Create Face | `POST /v2/faces` | `model_name` plus exactly one of `train_image_url` or `train_video_url`. Image training also needs `voice_name` or `default_voice_id`. `consent_video_url` is legacy and must not be sent. |
| Choose a model | Same create call | Phoenix-4.5 for a chest-up photo or video. Video is one continuous take: 30 seconds speaking, then 30 seconds listening. |
| Face overview | Rights | The account must have rights to the likeness. Stock faces are not a personal face. |
| Create PAL | `POST /v2/pals` | `default_face_id` is required. `system_prompt` is required for `pipeline_mode` `full`. |
| TTS | `layers.tts` on create or update | A private ElevenLabs voice needs `tts_engine` `elevenlabs`, `external_voice_id`, and the ElevenLabs API key. |
| Meetings | `layers.conferencing` | `username` plus `allowlist`. An empty allowlist lets any sender invite the PAL. |

Phoenix-4.5 photo rules: JPG or PNG, at least 512×512, one adult, chest-up, centered, looking straight at the camera, face unobstructed. `auto_fix_training_image` can adjust framing. It cannot fix a covered face, a minor, or a non-human subject.

## Face

| Field | Value |
| --- | --- |
| Face id | `r0a149c5fd3f` |
| Name | Roman Bodnarchuk |
| Type | `user` |
| Model | `phoenix-4.5` |
| Status | `completed` (preview is usable) |
| Finetune status | `training` |
| Training progress | `20/100` |
| Default voice id | `v1f73c4a86a76` |
| Error | none |

`GET /v2/faces/r0a149c5fd3f?verbose=true` at 2:25 PM Toronto. The thumbnail is Roman in the navy sweater, chest-up, in the beige office with floating shelves, plants, and framed photos. It matches the Canva still, not the carousel screenshot. `finetune_status` `training` means Lindsay's preview can still carry the Phoenix-4.5 watermark until tuning finishes. The face id does not change when tuning finishes.

This face was created at `2026-10-06T18:23:28Z` from a crop of the Canva still, under the temporary name "Roman Canva Portrait Crop 2026 10 06". Status reached `completed` at `2026-10-06T18:24:27Z`. This pass renamed it to Roman Bodnarchuk and set `default_voice_id` to the existing user voice `v1f73c4a86a76` (also named Roman Bodnarchuk, `voice_type` `user`, status `completed`). `original_voice_id` stayed null. `consent_video_url` was not sent.

The uncropped Canva still was already rejected and was not submitted again:

| Face id | Status | Progress | Error |
| --- | --- | --- | --- |
| `r90acf2a16df` | `error` | `0/100` | Wide Canva still rejected. Tavus required a crop at or above the navel and hands at or below chest height. |

Older ids `rabe3912f421`, `rbf68d68d1f0`, and `rc3773cf9e1c` now return 404. They were not retrained. `r03ae208f108` is a separate completed Phoenix-4.5 face of the same name, created `2026-10-06T18:03:53Z`, finetune `training` at `67/100`, with a close speaking crop and its own user voice. It is not the seated portrait, so the company PALs were not left on it.

## Canva source

Design `DAHFUgIBiUQ`, title "Roman Bodnarchuk Twin", one page, 2400×1339, no text overlay. The PNG export is the clean office portrait: one adult, navy sweater, wood desk, beige wall, floating shelves, plants, framed photos, face unobstructed. The carousel screenshot (black bars, "2 of 3") was not used. The 200×200 Calendly avatar was not used.

The same design exports as MP4. That file is 5.0 seconds, 1926×1074, 30 fps, and has no audio stream. It does not meet the one-take rule (about 30 seconds speaking, then 30 seconds listening), so the video path was not used.

## Company PALs on this face

Both company PALs use `pipeline_mode` `full` and `default_face_id` `r0a149c5fd3f`. Neither has document ids. The investor deck is not attached. Conferencing allowlists are the two exact addresses `roman@n5r.com` and `roman@wisdomtwin.ai`.

Lindsay's PAL was switched. `GET /v2/pals/p70d2aae706a` at 2:25 PM Toronto already had `default_face_id` `r0a149c5fd3f` (`updated_at` `2026-10-06T18:24:55Z`). A replace of that same value returned 304. N5R was patched on this pass at `2026-10-06T18:25:39Z`. Conferencing, prompts, and TTS were not edited.

| Company | PAL id | PAL name | Conferencing username | Address returned or derived | TTS |
| --- | --- | --- | --- | --- | --- |
| WisdomTwin | `p70d2aae706a` | WisdomTwin Roman Digital Twin | `wisdomtwin-roman` | Username is set. `GET` did not return `conferencing_email`. Docs render that username as `wisdomtwin-roman@tavusinvite.com`. | `tts_engine` `elevenlabs`, private `external_voice_id` set. The provider key field is present and is 8 characters, so it is not a usable ElevenLabs API key. |
| N5R | `pce648b51455` | N5R Roman Digital Twin | `n5r-roman` | Create returned `n5r-roman@tavusinvite.com`. | `tts_engine` `tavus-auto`. No external voice and no provider key. |

N5R was created earlier the same day, `2026-10-06T17:41:10Z`. Username `n5r-roman` was available immediately before create. The first spoken line is "I'm Roman Bodnarchuk's AI twin for N5R, not Roman himself." `disclosure_type` is `always`. The prompt is buyer training at `https://n5r.ai`, with no WisdomTwin branding, no grant guarantee, and no quoted price.

WisdomTwin was already on the earlier green-screen face before the N5R create, and is on the office portrait as of 2:25 PM Toronto. Its greeting discloses an AI twin in the first sentence. Pricing is deferred. The prompt does not quote the unapproved WisdomTwin figures or an N5R price floor. Fundraising and SAFE are refused. Talent Lab stays a client outcome, not WisdomTwin revenue. WisdomTwin's truth line stays pre-revenue.

The PAL will not sound like the private ElevenLabs voice `OtTgp0gIgmfhqSXfyakl` until a real ElevenLabs API key is stored. `ELEVENLABS_API_KEY` is not in this environment. The face was usable without that key. N5R uses Tavus default TTS on purpose. WisdomTwin names the private voice, but the stored provider key is too short to authenticate ElevenLabs.

## Left unchanged

These PALs were not edited on this pass. They are not the two company PALs.

| PAL id | Name |
| --- | --- |
| `pc304da53b20` | Roman Bodnerchuk |
| `pa5b0d4c5228` | Roman |

`p50395813bfa` ("Roman Bodnarchuk WisdomTwin ai Digital Twin Sales") still has an empty `default_face_id`. It was not edited and it is not one of the two company PALs.

## Source media that was not submitted

The Calendly avatar at the known CloudFront URL is a 200×200 JPEG. Phoenix-4.5 requires at least 512×512, so it was not uploaded. `Roman-bw.jpg` in Drive is 512×512 and looks away from the camera, off center. Drive files titled as a HeyGen look or a studio twin portrait are a different person and were not used. Podcast frames of Roman have a microphone over the mouth, which the photo rules reject.

## Still open

- Lindsay's 3:45 PM PAL face was changed to `r0a149c5fd3f` before 3:40 PM Toronto. Finetune is still `training` at `20/100`, so the call uses the watermarked preview until `finetune_status` is `completed`. No second face switch is required when tuning finishes.
- If Lindsay's Meet requires the host to admit guests, Roman still has to be in `https://meet.google.com/qwf-ojru-kwm` to let the PAL in. The invite address stays `wisdomtwin-roman@tavusinvite.com`.
- WisdomTwin TTS is still `elevenlabs` with an 8-character provider key, so that PAL will not use the private ElevenLabs voice until a real key is stored. The face default voice `v1f73c4a86a76` is what N5R's `tavus-auto` can use. Do not invent an ElevenLabs key.
- The Canva design is not a one-take training video. A later video face still needs about 30 seconds speaking, then 30 seconds listening, in one take. Do not resubmit the 5-second export or the uncropped wide still.
- Do not quote the unapproved WisdomTwin overage or the unapproved N5R floor. Roman follows up with approved terms.

Pipeline movement: none.

## One twin, and the October 6 canon pass

Darren's room had two replicas of the same WisdomTwin PAL: an API `meeting_url` join and a calendar invite. `services/salesperson-worker/src/singleJoin.ts` now blocks the second path when the PAL is already a guest or when that Meet link already has a conversation. A meeting gets one path. WisdomTwin meetings use `wisdomtwin-roman@tavusinvite.com` only. N5R meetings use `n5r-roman`. Those two addresses are not invited to the same event.

Live read after the script update on October 6, 2026:

| PAL | Face at this read | Conferencing | Prompt |
| --- | --- | --- | --- |
| `p70d2aae706a` WisdomTwin | `rfeda02190f8` | `wisdomtwin-roman`, allowlist `roman@n5r.com` and `roman@wisdomtwin.ai` | Replaced from `docs/sales-ops/prompts/live/wisdomtwin-pal-prompt.md` |
| `pce648b51455` N5R | `rfeda02190f8` | username `n5r-roman` restored, same allowlist. GET did not return `conferencing_email`. | Replaced from `docs/sales-ops/prompts/live/n5r-pal-prompt.md` |

No other PAL has a conferencing username. No conversation was started.

Sources read from Drive, modified inside the prior 90 days, and used for the spoken script:

- WisdomTwin final investor pitch, September 21, 2026, slides file `1XzoCBpwMO82likDo7c3uqqb3CfMmdzJ-Nqoy0SHdjH4`.
- `wisdomtwin-01` through `wisdomtwin-04` text files in the wisdomtwin folder.
- `n5r-01` through `n5r-03` text files in the n5r folder.

Those Drive files state the role ladder, including USD $5,000 setup and USD $500 per month beyond included roles, and state that N5R engagements start at USD $15,000. The spoken prompts quote those figures and no others. Investor CRM spreadsheets and a private agreement PDF were not uploaded.

`https://www.n5r.ai`, `https://n5r.com`, and `https://wisdomtwin.ai/demo` answered. `n5r.ca` did not complete a TLS handshake from this environment, so the twin does not describe that domain.

The sales behavior is need, impact, authority, budget, and timing, one question at a time, with urgency taken only from the guest's own delay. It is not a copied script from a named sales author. The twin books the next meeting with Roman. It does not close a contract or a SAFE. The private ElevenLabs voice is still not connected.
