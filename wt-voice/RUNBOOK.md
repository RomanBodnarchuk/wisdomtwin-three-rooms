# WisdomTwin Buyer Twin: Outbound Voice, v2 Runbook

Version 2026-09-22 v2.1. It replaces v2 (same day), which fixed v1. v2.1 closes three release-control defects found in the independent preflight review (section 7).

**Status:** the owner-test agent and the consent gate exist. Dialing is disabled. No phone number is imported, the backend is not deployed, and the N5R.ai HubSpot portal does not yet have the `voice_*` properties, so the eligible list is empty. No phone call has been placed. The live site "WisdomTwin Launch" is untouched, and so are the other ElevenLabs agents. Sections 9 and 10 record the remote tests and the public session.

**Next milestone:** deploy the backend with dialing still disabled, attach the seven tests to the live version, and keep `WT_RELEASED_AGENT_VERSION` blocked until that proof exists. Section 4 lists the steps. Creating the HubSpot properties is properties-only and still needs the private-app token.

---

## 1. What changed from v1, mapped to the review

| Review item | v2 implementation | Where |
|---|---|---|
| A consent Boolean is not evidence | AI_CALL_ELIGIBLE defaults to false. See the full list below this table. | `_shared/eligibility.js` |
| Unrestricted test-call bypass | Removed. There is no direct outbound curl. Test mode requires a destination allowlist, an unexpired `WT_TEST_AUTHORIZED_UNTIL`, and full eligibility. `call-one.mjs` is a thin client and cannot skip any server check. | `dialModeGate`, `scripts/call-one.mjs` |
| Consent at dial vs after the call | Every dial attempt writes an immutable decision row: eligibility result, failures, policy, a snapshot of the consent evidence, and the agent version. A database trigger blocks any update except attaching the conversation_id once, and blocks all deletes. Post-call processing never re-judges the original dial. | migration `wt_voice_dial_decisions` |
| Immediate suppression | The in-call `record_opt_out` tool writes to the durable suppression table before it responds, and is fail-safe (suppress first, verify after). The post-call opt-out and the inbound opt-out line also write suppression. The pre-dial check reads that table and fails closed on a database error. | `/opt-out`, `/inbound-optout`, `wt_voice_suppression` |
| One call at a time, globally | A single-row database lock, taken atomically. It survives restarts, retries, and concurrent callers, and a stale lock clears after 10 minutes. The agent also has `agent_concurrency_limit: 1`. | `wt_voice_try_lock` |
| Recording policy | Defaults to no recording: `record_voice: false`, `delete_audio`, `delete_transcript_and_pii`, `retention_days: 1`. Twilio recording is off. The "This call is recorded" line is removed. | agent config, dial payload |
| Voicemail opt-out and voicemail policy | Voicemail is off. The agent speaks only after a human greets it, and hangs up silently on any greeting, beep, or menu. Twilio answering-machine detection (`enable`) hangs up machines through the Twilio API. An inbound opt-out webhook suppresses the caller's number automatically, with no human step. | prompt, `/elevenlabs-webhook`, `/inbound-optout` |
| Tests tied to the deployed config | `verify-release.mjs` runs all 7 registered tests through the API. It fails unless exactly 7 ran, all passed, the IDs match `tests.json`, the tests attached to the live agent match, and every run is on the live `version_id` and not a draft. It writes `release/evidence-<version>.json`. The backend refuses to dial unless the live agent's `version_id` equals `WT_RELEASED_AGENT_VERSION`, so any later change blocks dialing until tests pass again. | `scripts/verify-release.mjs`, `dial()` |
| A word scan can't police free-form output | Now three layers: the pre-push scan of every scripted line, a blocking custom guardrail at runtime (claude-haiku-4-5, rejects any canon breach before audio), and the 7 remote tests. It still does not guarantee every future response, so review transcripts after calls. | canon-lint, `platform_settings.guardrails` |
| Webhook security | ElevenLabs HMAC check, byte-for-byte equivalent to the SDK's `constructEvent` (cross-checked against the SDK). It adds a ±5-minute future bound and a 30-minute replay window, plus idempotency by event key, reversed if processing fails so a retry can land. Twilio signature check matches the official twilio library. | `_shared/security.js` |
| Long read-back; claims of sending | There is no URL read-back. `request_scheduling_link` creates a HubSpot task for Roman to send the link personally, consistent with the no-agent-email rule. The agent says "Roman will follow up with you personally" only when the tool returns `ok: true`. | prompt, `/scheduling-request` |
| Duration | The 45-second target is kept and enforced by script length: the two slogans are cut, and scripted speech on the yes path is about 69 words, roughly 26 seconds. The platform hard cap is set to 60 seconds because ElevenLabs rejects anything lower (live API, 2026-09-22: "Max duration in seconds has to be between 60 and 7200 seconds"). | agent config |

**What AI_CALL_ELIGIBLE checks.** Every check must pass, and a contact that has never been evaluated is not eligible.

- **Consent evidence:** who consented, the consented number matching the dialed number, when, the method, the accepted wording, an evidence reference, the calling entity, the purpose, and the consent's age.
- **Suppression:** no internal opt-out, not on the suppression table, and a do-not-call scrub result that is clear and less than 31 days old.
- **Jurisdiction:** on the allowlist, and consistent with the number.
- **Local time:** a valid timezone and inside the calling window.
- **Campaign and segment:** the campaign is approved, and the contact is in that campaign and an allowed segment.

**Local verification run on 2026-09-22 (evidence, not a claim of deployment)**
- `deno check` passes on the edge function. `deno test tests/` passes 9 of 9: eligibility, dial modes, HMAC, and the Twilio signature.
- The migration was applied to Postgres (PGlite). Updates and deletes on decisions are blocked, a second lock fails while one is held, a stale lock clears, duplicate webhook events are rejected, and a suppression row with no identifier is rejected.
- The function served locally. `/health` returns 200. A bad trigger secret gets 401 on `/dial`. A bad HMAC gets 401 on the webhook. A bad Twilio signature gets 403. An unknown route gets 404.
- CLI 1.3.2: `agents push --dry-run` and `tests push --dry-run` (7 tests) are clean. canon-lint passes. `--release` correctly fails on the remaining placeholders and on 0 attached tests.

## 2. Architecture (separate from the website)

```
WisdomTwin Launch (Lovable, public)        wt-voice backend (private, Supabase Edge Function + Postgres)
  consent form -> HubSpot properties  --->  /dial  (operator only, trigger secret)
                                            /opt-out /scheduling-request /outcome  (agent tools)
ElevenLabs agent (voice OtTgp0...)   <-->   /elevenlabs-webhook  (HMAC)
Twilio number(s)                     <-->   /inbound-optout      (Twilio signature)
```

The site never holds HubSpot, ElevenLabs, or Twilio server credentials.

## 3. HubSpot contact properties the gate reads

`voice_consent`, `voice_consent_phone`, `voice_consent_name`, `voice_consent_at`, `voice_consent_method` (`web_form` | `email_reply_manual`), `voice_consent_text`, `voice_consent_evidence_ref`, `voice_consent_entity`, `voice_consent_purpose`, `voice_opt_out`, `voice_dnc_listed`, `voice_dnc_checked_at`, `voice_jurisdiction` (e.g. `CA-ON`), `voice_timezone` (IANA), `voice_campaign_id`, `voice_segment`.

The server credential is a private app with `crm.objects.contacts.read`, `crm.objects.contacts.write`, and `crm.objects.notes.write`, plus task write access. I have not verified which HubSpot scope name covers tasks.

## 4. Path to the milestone (dialing stays disabled throughout)

```bash
# Prerequisites: decisions D1 and D2 approved; Supabase project created; 1Password items created.
npm install -g @elevenlabs/cli supabase          # CLI 1.3.2 / 2.117.0 validated here
elevenlabs auth login

# a. Backend
supabase link --project-ref "$REF"
supabase db push                                                     # applies the wt_voice migration
op inject -i scripts/supabase-secrets.tpl | supabase secrets set --project-ref "$REF" --env-file /dev/stdin
supabase functions deploy wt-voice --project-ref "$REF" --no-verify-jwt
curl -s "$WT_BACKEND_URL/health"                                     # expect {"ok":true}

# b. Register the post-call webhook (dashboard, HMAC) pointing to $WT_BACKEND_URL/elevenlabs-webhook.
#    Save the secret in 1Password, re-run the secrets step, and put webhook_id + backend URL into the config.

# c. Agent + proof
op run --env-file=scripts/env.op -- bash scripts/release.sh
```

**Evidence to collect before calling the milestone done:**

1. The new agent ID is in `agents.json`, and the existing site-wide Buyer Twin agent is unchanged (compare it before and after with `agents get`).
2. `release/evidence-<version>.json` shows 7/7 passed on the live `version_id`, along with the config SHA-256, the LLM, and the TTS model.
3. Signed test webhook deliveries appear once in `wt_voice_webhook_events`. A replayed delivery returns `duplicate`. An unsigned one returns 401.
4. A `/dial` against a fully evidenced test contact with `WT_DIAL_MODE=disabled` returns 409 "dialing disabled". An immutable decision row is written, and nothing is dialed.
5. Suppression works: an insert through `/opt-out` makes the next `/dial` for that contact fail on `not_suppressed`.
6. The caller ID and toll-free opt-out number are approved and the number is imported. Its voice webhook is `/inbound-optout`, and a test call to it produces a suppression row.

**Then, separately authorized:** one allowlisted call to Roman's own phone. Set `WT_DIAL_MODE=test`, `WT_TEST_ALLOWLIST=+14162205314`, and `WT_TEST_AUTHORIZED_UNTIL=<an hour from now>`. Then issue exactly one single-use grant in the Supabase SQL editor:

```sql
insert into wt_voice_test_grants (number_sha256, expires_at, authorized_by, note)
values (encode(sha256('+14162205314'::bytea), 'hex'), now() + interval '1 hour', 'Roman', 'first owner test');
```

Run `call-one.mjs <Roman's contact id>`. The grant is consumed atomically on that attempt; a second attempt is refused until a new grant is issued. Roman's contact must carry full consent evidence. Check audio, timing, interruptions, the opt-out path, and the ledger and notes. Then set the mode back to `disabled`.

## 5. Decisions for Roman

1. **D1. Policy exceptions to "credentials only in 1Password / HubSpot token only in the ElevenLabs dashboard."** The hosted backend needs a second, minimum-permission HubSpot token, plus the ElevenLabs, Twilio, and webhook secrets, in Supabase's secret store at runtime. `op inject` keeps them out of files, but they do live in Supabase after that. The alternative is a 1Password service account read at runtime, which adds a runtime dependency and needs a Deno-compatible client I have not verified. **Recommend:** approve the Supabase secret store for this service only, and rotate from 1Password.
2. **D2. Hosting.** **Recommend:** a new, dedicated Supabase project for WisdomTwin voice. It isolates WisdomTwin prospect consent data from the N5R.ai project and from the live site, and lets you set its own region (Canada Central, if the CA-first policy holds) and spend cap. It can sit in the same Supabase organization. It should not run inside the live N5R.ai project's database. Vercel is also available, but it would need a separate durable database for the lock, suppression, and decision tables.
3. **D3. Recording and transcript retention.** Your 2026-09-22 build brief said "record calls, 30-day retention." The review says the 2026-09-05 spec defaults to no recording and no raw transcript retention. These conflict. **Recommend:** keep no recording, which is the package default, until counsel defines the purpose, notice, and consent language.

**Duration (resolved by the platform):** ElevenLabs does not accept a hard cap below 60 seconds, so 45 cannot be a configured limit. v2 sets the hard cap to 60 and meets the 45-second target through the script, which runs about 26 seconds of agent speech. Measure actual call length on the first test call.

## 6. Still blocked, or not verified

- **The 2026-09-05 deployment spec.** I could not find it in Drive by title or text search. I have not checked this package against it field by field. The eligibility list above follows the review's summary of that spec. Send the file or its link to close this gap.
- **Counsel sign-off** on consent wording, jurisdictions (the allowlist is empty by default), and calling windows. The window is set conservatively at weekdays 09:00 to 21:00 and weekends 10:00 to 18:00, recipient local time.
- **A do-not-call scrub mechanism.** It needs to fill `voice_dnc_listed` and `voice_dnc_checked_at`. None exists yet, so every contact fails `dnc_clear`.
- **A toll-free number wired to `/inbound-optout`** for US opt-outs.
- **Whether live agents expose a stable `version_id` that changes on each push.** If `version_id` is null, the gate fails closed. The fallback is a config fingerprint.
- **The payload shape of the `answering_machine_detection` event.** Parsing is defensive and not validated against a real event.
- **Whether ElevenLabs accepts `eleven_flash_v2_5`** for this English agent. Falling back to `eleven_flash_v2` changes the version and requires `release.sh` to run again.
- **Whether the custom guardrail's blocking mode adds latency** acceptable within 45 seconds. Measure it on the test call.
- **Whether `supabase secrets set --env-file /dev/stdin`** works. If not, use `<(op inject ...)`.
- **Whether a system tool in a test** can be referenced as `{"id":"end_call","type":"system"}` (test WT07).

## 7. v2.1 fixes from the preflight review (2026-09-22)

| Defect found | Fix | Proof |
|---|---|---|
| `release.sh` ran `canon-lint --release` (which requires 7 attached tests) before the tests were uploaded and attached, so a fresh release always stopped. | Split the lint: `--pre-release` (content + placeholders) runs first; `--release` (adds exactly-7-attached) runs after `tests push` and `attach-tests`, before `agents push`. | `tests/release_regression.mjs`: pre-release passes with 0 tests; release fails until 7 are attached; script order asserted. |
| `verify-release.mjs` accepted runs whose `version_id` or `ran_against_draft` was missing. | Missing evidence is now a failure: every run must carry `version_id` equal to the live version, `ran_against_draft === false`, and the right `agent_id`. The invocation itself must also report the live version and non-draft. Pending runs after timeout fail. | Mock API: complete evidence passes; missing version, missing draft flag, wrong version, draft run, missing invocation version, and failed run are each rejected. |
| The test authorization was reusable: allowlist + expiry limited who and when, not how many. | New `wt_voice_test_grants` table and `wt_voice_consume_test_grant()` function. Test mode dials only after atomically consuming one unused, unexpired grant for that exact number, taken after the lock and before dialing. One grant, one attempt. | PGlite: first call consumes, second is refused, other number refused, expired grant refused. |
| Backend hardening noted in the review. | `/opt-out` no longer suppresses arbitrary contacts: it attributes the request to our own dial record, or to a live conversation on our agent, and rejects contact-ID mismatches. Post-dial bookkeeping errors are now logged instead of ignored. | `deno check` passes; 9/9 unit tests pass. |

Still true: nothing is deployed, no number is imported, and no call has been placed. The review's full report was not available to this session; if it lists other backend items, send them and they will be fixed the same way.

## 8. Recovery on 2026-09-22 (this checkout)

Drive folder `1zVFeQkt8Z-69UqGr6BUHL0yiAFCfVOLx` has the v2 zip `1xDSU0SHOcGBr6kvt_KZncbdJmzD_x0vK` (MD5 `c11a5b77e908965bdd8aba966c15b721`, the corrupted upload) and the v2.1 patch. The v2.1 zip was not in that folder. Every zip member inflated except `agent_configs/WisdomTwinBuyerTwin.json` (zlib failed at compressed byte 73). That file was rebuilt from the live owner-test agent `agent_2501m34tx48gfa9v218pndv3gfwq` (version `agtvrsn_5101m34tx5s6e76b28cxs9s08gt1`): same spoken script, voice, 60 second cap, recording off, blocking canon guardrail, and `eleven_flash_v2`. The three webhook tools and `__POST_CALL_WEBHOOK_ID__` were added from this runbook. `agents.json` is pinned to that agent id so a later `agents push` updates it. Do not push until the placeholders are real URLs and dialing is still disabled.

## 9. Remote tests on the owner-test agent (2026-09-24)

The seven tests were created in the ElevenLabs workspace and their ids are in `tests.json`. Suite `suite_3301m38jxmgtfpc80h7xz9py9xk1` passed 7/7 on agent `agent_2501m34tx48gfa9v218pndv3gfwq`, version `agtvrsn_5101m34tx5s6e76b28cxs9s08gt1`, `ran_against_draft` false. The agent config was not updated, so `attached_tests` on the live agent is still empty and `release.sh` has not run. No phone number was imported and no call was placed.

WT04's first condition treated the required product name WisdomTwin.ai as a banned web address, so the correct identity line failed. The condition now allows WisdomTwin.ai and still fails any other web address. The replaced test id is the one in `tests.json`.

`elevenlabs tests push` should update these ids. Do not push a second copy. `attach-tests.mjs` still belongs inside `release.sh`, after the backend URL and post-call webhook id are real.

## 10. Public session, no phone call (2026-09-24)

The owner-test agent can run without a phone number because auth is off. The public page is `https://elevenlabs.io/app/talk-to?agent_id=agent_2501m34tx48gfa9v218pndv3gfwq`. Speak or type first. The agent waits for a person.

A public text session, `conv_6401m38kj2cxfdk89q4fdjefcxq7`, ran on version `agtvrsn_7201m38khnysfxsv1ykb1wnbt97g` and ended because `end_call` succeeded. The spoken lines were the opener, the product description, and "Thank you. Roman will follow up. To opt out, say stop, or call one eight hundred, five five five, zero one zero zero." AI disclosure was recorded as true. No phone number was imported and no call was placed. This is not the owner PSTN test.

The first live session, `conv_7301m38k72svfq59qbc44gfng7pn`, died before any reply: the canon guardrail treated the required WisdomTwin.ai opener as a banned web address. A later session, `conv_0601m38kg7h0ev3sm1ctkgnfbezy`, got through the opener and the product line, then the guardrail stopped the approved close after the words "Thank you." The live guardrail now defaults to allow, allows WisdomTwin.ai and the scripted close, and judges only the latest reply. `evaluate_full_response_only` cannot be set on this voice agent. The same guardrail text is in `agent_configs/WisdomTwinBuyerTwin.json`. The spoken prompt on the live agent was not replaced, webhook tools were not added, and `attached_tests` is still empty.

The 7/7 suite in section 9 ran on version `agtvrsn_5101m34tx5s6e76b28cxs9s08gt1`. The live version is now `agtvrsn_7201m38khnysfxsv1ykb1wnbt97g`. The spoken script is the same. `release.sh` has not run.

A raw voice socket did not deliver audio in this environment. Use the talk-to page to hear the voice.
