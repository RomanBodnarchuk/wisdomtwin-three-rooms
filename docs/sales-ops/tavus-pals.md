# Tavus company PALs

Checked Tuesday, October 6, 2026. The Tavus API key stays outside this repository, mode 600. This file does not contain the key. No conversation was started.

A user face named Roman Bodnarchuk already existed when this pass created the N5R PAL. It was reused. A second face was not trained.

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
| Face id | `rabe3912f421` |
| Name | Roman Bodnarchuk |
| Type | `user` |
| Model | `phoenix-4.5` |
| Status | `completed` (preview is usable) |
| Finetune status | `training` |
| Training progress | `20/100` |
| Default voice id | none |
| Error | none |

`GET /v2/faces/rabe3912f421?verbose=true` at this check. The thumbnail is a chest-up frame of Roman on a green background. Two other user faces with the same name failed and were not reused:

| Face id | Status | Progress | Error |
| --- | --- | --- | --- |
| `rbf68d68d1f0` | `error` | `0/100` | Training photo rejected because the face was largely covered. |
| `rc3773cf9e1c` | `error` | `8/100` | Training video rejected because the required 30-second listening segment was not detected. |

## Company PALs on this face

Both company PALs use `pipeline_mode` `full` and `default_face_id` `rabe3912f421`. Neither has document ids. The investor deck is not attached. Conferencing allowlists are the two exact addresses `roman@n5r.com` and `roman@wisdomtwin.ai`.

| Company | PAL id | PAL name | Conferencing username | Address returned or derived | TTS |
| --- | --- | --- | --- | --- | --- |
| WisdomTwin | `p70d2aae706a` | WisdomTwin Roman Digital Twin | `wisdomtwin-roman` | Username is set. `GET` did not return `conferencing_email`. Docs render that username as `wisdomtwin-roman@tavusinvite.com`. | `tts_engine` `elevenlabs`, private `external_voice_id` set. The provider key field is present and is 8 characters, so it is not a usable ElevenLabs API key. |
| N5R | `pce648b51455` | N5R Roman Digital Twin | `n5r-roman` | Create returned `n5r-roman@tavusinvite.com`. | `tts_engine` `tavus-auto`. No external voice and no provider key. |

N5R was created on this pass, `2026-10-06T17:41:10Z`. Username `n5r-roman` was available immediately before create. The first spoken line is "I'm Roman Bodnarchuk's AI twin for N5R, not Roman himself." `disclosure_type` is `always`. The prompt is buyer training at `https://n5r.ai`, with no WisdomTwin branding, no grant guarantee, and no quoted price.

WisdomTwin was already on this face before the N5R create. Its greeting discloses an AI twin in the first sentence. Pricing is deferred. The prompt does not quote the unapproved WisdomTwin figures or an N5R price floor. Fundraising and SAFE are refused. Talent Lab stays a client outcome, not WisdomTwin revenue. WisdomTwin's truth line stays pre-revenue.

The PAL will not sound like the private ElevenLabs voice `OtTgp0gIgmfhqSXfyakl` until a real ElevenLabs API key is stored. `ELEVENLABS_API_KEY` is not in this environment. The face was usable without that key. N5R uses Tavus default TTS on purpose. WisdomTwin names the private voice, but the stored provider key is too short to authenticate ElevenLabs.

## Left unchanged

These PALs were not edited on this pass. At the last read, both pointed at `rabe3912f421` rather than the earlier stock faces Lee and Mateo.

| PAL id | Name |
| --- | --- |
| `pc304da53b20` | Roman Bodnerchuk |
| `pa5b0d4c5228` | Roman |

`p50395813bfa` ("Roman Bodnarchuk WisdomTwin ai Digital Twin Sales") still has an empty `default_face_id`. It was not edited and it is not one of the two company PALs.

## Source media that was not submitted

The Calendly avatar at the known CloudFront URL is a 200×200 JPEG. Phoenix-4.5 requires at least 512×512, so it was not uploaded. `Roman-bw.jpg` in Drive is 512×512 and looks away from the camera, off center. Drive files titled as a HeyGen look or a studio twin portrait are a different person and were not used. Podcast frames of Roman have a microphone over the mouth, which the photo rules reject.

## Still open

- Finetune is still `training` at `20/100`. The preview can be used. The unwatermarked tuned face replaces it when `finetune_status` is `completed`.
- Store a real ElevenLabs API key, then set `tts_engine` `elevenlabs` and `external_voice_id` `OtTgp0gIgmfhqSXfyakl` on N5R as well. Until then, neither PAL sounds like that clone.
- Do not quote the unapproved WisdomTwin overage or the unapproved N5R floor. Roman follows up with approved terms.
