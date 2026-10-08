# Tavus calendar joins for 2026-10-06

Roman asked, about 1:56 PM America/Toronto, to have the company PAL join the 2:00 PM call with Darren and take the 3:45 PM call with Lindsay. Both existing Google Calendar events were updated. No second event and no second Meet room were created. Times, titles, and descriptions were left as they were. Roman stayed on both guest lists. HubSpot was not written.

Both Calendly events use event type `https://api.calendly.com/event_types/DGDHPUSUU24UVHEM` (WisdomTwin, 15-Min Intro). The N5R event type was not on either booking, so the N5R PAL was not invited.

Organizer on both events is `roman@n5r.com`, which is on the PAL allowlist. Notifications were sent at `ALL` so the PAL receives the calendar invite. Acceptance below is the guest response at re-read. It is not proof the PAL entered the room.

## Darren Pereira — 2:00 PM EDT

| Field | Value |
| --- | --- |
| Title | Darren Pereira and Roman Bodnarchuk |
| Local start | 2:00 PM EDT, Tuesday October 6, 2026 |
| Local end | 2:15 PM EDT |
| Company | WisdomTwin |
| PAL | `p70d2aae706a` |
| PAL email added | `wisdomtwin-roman@tavusinvite.com` |
| Google event id | `328siu438jum53qas3kq4m9ha4` |
| Meet | `meet.google.com/fsy-jtsy-zqh` (unchanged) |
| Invite sent | 1:58:50 PM EDT (`2026-10-06T17:58:50Z`) |
| PAL response at re-read | `needsAction` |
| Guest list | Grew by that one address. Prior guests remain `roman@n5r.com` (accepted, organizer), `1culturebit@gmail.com` (Darren Pereira), and `boardy@boardy.ai`. |

Admission: Roman is the organizer and is attending. If Meet requires the host to admit guests, Roman can admit the PAL. The invite went out about one minute before the start, so this meeting may already be in progress when the PAL accepts. An in-progress invite is expected to join shortly after acceptance. Whether the PAL entered is in the review section below. The RSVP in this table is not that proof.

## Lindsay Smith — 3:45 PM EDT

| Field | Value |
| --- | --- |
| Title | Lindsay Smith and Roman Bodnarchuk |
| Local start | 3:45 PM EDT, Tuesday October 6, 2026 |
| Local end | 4:00 PM EDT |
| Company | WisdomTwin |
| PAL | `p70d2aae706a` |
| PAL email added | `wisdomtwin-roman@tavusinvite.com` |
| Google event id | `e5h3895iaa62plvahgt9rgu7ps` |
| Meet | `meet.google.com/qwf-ojru-kwm` (unchanged) |
| Invite sent | 1:58:51 PM EDT (`2026-10-06T17:58:51Z`) |
| PAL response at re-read | `needsAction` |
| Guest list | Grew by that one address. Prior guests remain `roman@n5r.com` (accepted, organizer) and `lindsay.anne.smith@gmail.com`. Roman was not removed. |

Admission: this meeting is still in the future, so a future invite is expected to join about one minute before 3:45 PM EDT after the PAL accepts. Roman remains on the event. If he does not enter the room and Meet requires the host to admit guests, nobody is in the room to admit the PAL. This note does not promise entry into a locked room.

## Review at 2:16 PM EDT

Re-read both events on `roman@n5r.com` after the Darren slot. `wisdomtwin-roman@tavusinvite.com` is still `needsAction` on both. Google `updated` is unchanged: Darren `2026-10-06T17:59:09Z`, Lindsay `2026-10-06T17:59:11Z`. A second read a few minutes later was the same. `needsAction` is the guest RSVP. It is not, by itself, proof the PAL stayed out.

`GET /v2/conversations?limit=50` returned `total_count` 6 and no further page. Two conversations used `https://meet.google.com/fsy-jtsy-zqh`. None used Lindsay's Meet link. No recording was downloaded.

### Observed on Darren's Meet

The PAL entered the room. Two replicas joined the same Meet.

| Conversation | Created (UTC) | Replica joined | Shutdown | Reason |
| --- | --- | --- | --- | --- |
| `cf7a97033db94477`, name "Darren Pereira intro 2026 10 06", `pal_id` `p70d2aae706a`, `face_id` `rabe3912f421` | 17:55:59 | 17:56:03 | 18:11:03 | `max_call_duration` |
| `c9e4841f96c7148f`, name "New Conversation …", verbose `persona_id` `p70d2aae706a`, `replica_id` `rabe3912f421` | 17:59:17 | 17:59:20 | 18:00:16 | `attendee_meeting_ended` |

The first conversation was created before the calendar invite at 17:58:50Z, under a human-written name. That is an API `meeting_url` join. It stayed about fifteen minutes and then hit the duration cap, at 2:11 PM EDT, while the scheduled slot ran to 2:15 PM.

The second conversation's context is the Darren calendar event: organizer `roman@n5r.com`, the Calendly description, and the Google invite footer that contains `https://meet.google.com/fsy-jtsy-zqh`. The participant line names `boardy@boardy.ai`, `1culturebit@gmail.com`, and `bot23@tavusinvite.com`. `botN` is a reserved Tavus-internal name, not this PAL's username. This is the calendar path. It joined even though the organizer's guest row still says `needsAction`. It left about one minute later, while the first replica was still in the room.

Verbose transcripts, assistant and user turns only:

- Both replicas' first spoken assistant line disclosed that the speaker is Roman Bodnarchuk's digital twin from WisdomTwin.ai and is not a human, then asked what prompted the booking.
- The longer transcript has 9 assistant turns and 33 user turns. After the disclosure, assistant turns are short fragments. The user turns are the people in the room. One user turn says the digital twin is on the call and listening. Another says they could not hear "Roman" and thought he was muted, then that audio returned. Those lines do not identify a TTS failure.
- No assistant turn states a SAFE amount, a valuation, a commitment, or a signed deal. No assistant turn claims the speaker is the human Roman. The assistant's company line is WisdomTwin.

Inference, separate from those facts: the calendar replica's `attendee_meeting_ended` shutdown is consistent with a second replica being dropped while the earlier API replica kept the room. The duration cap on the early API join is why that replica left before 2:15 PM. The muted-audio remark is not enough to prove the ElevenLabs stub produced silence.

`GET /v2/faces/rabe3912f421` returned 404 "Replica not found" on this pass. The same id still joined as `replica_id`, so face lookup was not what blocked entry.

### Config checked and left in place

`GET /v2/pals/p70d2aae706a` at this review:

| Field | Value |
| --- | --- |
| Conferencing username | `wisdomtwin-roman` |
| Conferencing email | `wisdomtwin-roman@tavusinvite.com` |
| Allowlist | `roman@n5r.com`, `roman@wisdomtwin.ai` only |
| Organizer match | `roman@n5r.com` is on the allowlist |
| `disclosure_type` | `always` |
| TTS | `tts_engine` `elevenlabs`, private external voice id set, provider key length 8 |

The allowlist was not widened. The username was not renamed. The Darren event was not edited. The PAL was not removed from Lindsay. The N5R PAL was not added.

The provider key is the known 8-character stub. No real ElevenLabs key was invented or copied onto the PAL. The engine was left on `elevenlabs`. Switching it to `tavus-auto` immediately before 3:45 PM could change a voice that already produced a spoken disclosure. The limitation stands: this PAL will not use the private ElevenLabs voice until a real provider key is stored.

The installed prompt still refuses service prices, investor terms, and financing. The Darren transcript does not show a missed disclosure, a refusal to attend, an invented SAFE, a claim that Roman the human was the speaker, or the wrong company in the assistant's own lines. The prompt was not patched. No SAFE terms, valuation, commitment, or price ladder were added.

### What changed for Lindsay's 3:45 PM call

No Tavus write and no calendar write on this pass.

The calendar path is not dead. The same PAL, the same organizer, and the same invite shape produced a join on Darren's Meet about 27 seconds after that invite, without the Google RSVP leaving `needsAction`. Lindsay's invite is already on the event. No conversation for `meet.google.com/qwf-ojru-kwm` exists yet, which is what a future start looks like. Docs say a scheduled meeting is joined about one minute before the start.

`POST /v2/conversations` was not called for Lindsay, and a 3:43 PM America/Toronto join was not scheduled. Darren shows why: an early `meeting_url` join starts immediately, can burn the duration cap before the slot ends, and a second replica in the same room can be ended within about a minute.

Admission risk: both Darren replicas joined while people were already speaking, so that room either admitted them or did not require a host click. This calendar payload does not show whether Lindsay's Meet requires the host to admit guests. If it does, and Roman is not in `https://meet.google.com/qwf-ojru-kwm`, the PAL can sit in the lobby with nobody to admit it. Roman is needed for that click. He is not required to accept the calendar invite again.

HubSpot was not written. Pipeline movement: none.

## Portrait face after this review

At 2:25 PM America/Toronto the WisdomTwin PAL `p70d2aae706a` and the N5R PAL `pce648b51455` both had `default_face_id` `r0a149c5fd3f` (Roman Bodnarchuk, Phoenix-4.5, status `completed`, finetune `training`). That is the Canva office portrait. `rabe3912f421` still 404s and is no longer the live face. Conferencing, the Meet link, and `wisdomtwin-roman@tavusinvite.com` were not changed. Detail is in `docs/sales-ops/tavus-pals.md`.
