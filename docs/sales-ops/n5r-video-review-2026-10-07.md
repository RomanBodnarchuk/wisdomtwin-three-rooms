# N5R video review, 2026-10-07

Recorded October 8, 2026. This note is the correction log. It does not include the review transcript.

No prospect was called, emailed, texted, or booked. No PAL was created or deleted. No second twin was invited. Firewall, DNS, release mode, and daily caps were not changed. No phone number was assigned. The WisdomTwin ElevenLabs agent was not edited.

## Required flow

HubSpot lead, then the ElevenLabs N5R call, then the N5R Calendly booking, then one Tavus PAL with prospect context. That first session is practical AI-training discovery and an honest grant-fit presentation. HubSpot is updated afterward by a real write, which this PAL does not have. A later meeting with the human Roman is separate. The first session must not say Roman is the presenter.

## ElevenLabs voice agent

Read `agent_9601m3zbep94f1rbt80q1298qed4` before any write. The live name was "Ontario Job Grant Booker (Roman's Digital Twin) · TEST ONLY, US Twilio number". The prompt was the Ontario Job Grant booking prompt. The attached custom tool was `send_n5r_booking_link_sms`. Assigned phone numbers: 1.

`agents_update` was called with that prompt and version description "Video review 2026-10-07: N5R grant fit, owner test, not dispatched." The tool rejected the prompt field: `Unexpected argument(s): prompt`. That call does not publish a prompt. No second schema was tried. The version description was not published. The live agent prompt is unchanged, including its owner-test header.

The designated prompt is saved at `docs/sales-ops/prompts/live/n5r-grant-hook-voice.md`.

A later call used `agents_update_prompt_settings`, which is the tool that accepts the prompt. It published version `agtvrsn_4201m4csse0metfv3h9jsxery7fs` on branch `agtbrch_7501m3zbep9ffbrvy1x9egrzr6e3`. The stored prompt matches that file. Existing tool id `tool_8901m4cd4x96ff5b4y25jdxpbd8j` remained attached. No call was placed. The agent still has its existing phone assignment. Outbound stays off.

## Tavus PAL

Read `pce648b51455` before the write. Name: "Roman Bodnarchuk — N5R Digital Twin". `wake_phrase` and `sleep_phrase` were already null, so they were not patched. The WisdomTwin PAL `p70d2aae706a` was not patched. Its `updated_at` stayed `2026-10-07T23:44:47.917639Z`, and its wake and sleep phrases were also null.

`PATCH /v2/pals/pce648b51455` replaced only `/system_prompt` with `docs/sales-ops/prompts/live/n5r-pal-prompt.md`. Response `200` at `2026-10-08T03:42:21.166984Z`. A second read matched that file. The meeting prompt says this session is the twin, Roman is a later meeting, one twin only, grant facts without a fixed dollar share, and no N5R service price. Tavus links in that prompt are `https://tavus.io` and `https://maker.tavus.io`.

Face `rfeda02190f8` was not changed. No face or voice asset was deleted.

Conferencing was not patched. The live username is `roman-bodnarchuk--n5r-digital-twin`, and the invite address is `roman-bodnarchuk--n5r-digital-twin@tavusinvite.com`. It is not `n5r-roman`. Allowlist remains `roman@n5r.com` and `roman@wisdomtwin.ai`.

The greeting was not changed. It still says "powered by super intelligence" and asks what work takes too long. The system prompt tells the twin not to repeat the identity line when that greeting already disclosed a Digital Twin who is not a human.

Guardrail `g112d30ef6aaa` (`n5r_no_price_discussion`) was not changed. It still mentions a $10,000 cost-share card illustration. The new system prompt forbids that card and forbids turning one-sixth or one-half into a dollar fee.

`pal_description` was not changed. It still describes qualification for a call with Roman. The system prompt is the spoken rule: this session is the twin.

## Knowledge

N5R document ids left attached:

| Id | Name |
| --- | --- |
| `d0-14a41e182672` | N5R.ai workforce training website 2026-10-06 |
| `d8-8b2114dd0e75` | N5R.com implementation website 2026-10-06 |
| `d8-9a3d7786fb06` | N5R AI live programs 2026-10-06 |
| `d3-8a6b42bee1f5` | N5R COM live implementation 2026-10-06 |

The account has an upload named "INTERNAL ONLY, never quote to guests: CRM connection setup notes 2026-10-07" (`d7-38e9fa5bbe4d`, tag `internal-only`). It is not on the N5R PAL. It is attached to WisdomTwin PAL `p70d2aae706a`. It was not detached and not deleted.

The N5R PAL has no MCP layer. A knowledge document is not HubSpot writeback. This pass did not add a connector and does not claim a CRM write exists.

## Left undone

The voice-agent prompt is not live. Booking, suppression, and Tavus attendance are still not a completed owner test. Outbound stays off.
