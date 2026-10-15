# Reported issues WT-ZAI-1–4 — tested follow-up

This continues the existing branch and draft PR [15](https://github.com/RomanBodnarchuk/wisdomtwin-three-rooms/pull/15) from `187a25f1eb4bb9f9ff8f344d18839709ab2ab2b2`. The baseline reproduced **147 passed, 14 skipped** before these changes. Earlier checkpoint artifacts remain immutable. The new exact commit, test outputs, source archive, diff and CI evidence belong in the separate `review-round2` artifact directory. Exactly four MCP tools and two packaged skills remain.

This records the historical `c244479` checkpoint. The subsequent narrow Tier 3 retry-admission fix is documented separately in [SLACK_RETRY_FOLLOWUP.md](SLACK_RETRY_FOLLOWUP.md).

The supplied report was independently checked against code, synthetic regressions and primary documentation. Claimed Claude corroboration has no verified review artifact. No callable authenticated Claude, Z.ai or Grok reviewer has been established in this cloud session; the parent coordinates those reviews. Local test results must not be described as results from those services.

## Confirmed fixes and report corrections

| Report | Verified behavior and resulting change | Evidence / limits |
| --- | --- | --- |
| WT-ZAI-1: invented expiry and dropped refresh | Store the provider's positive integer `expires_in` without a 24-hour cap. Nonrotating Slack grants explicitly have no invented expiry. Encrypted rotating grants keep refresh credentials and read-only scopes. Expiry returns a reconnect error; optional existing-grant server refresh verifies workspace/user/email and uses compare-and-replace under the subject epoch guard. Deletion, reauthorization or membership mutation cannot restore a stale credential. An uncertain single-use refresh is marked durably and is never automatically replayed. | 74 lifetime cases across memory/Postgres credential stores; six additional real-Postgres authority cases. Refresh stays off unless explicitly configured with an existing app secret. No actual grant, app rotation setting or provider request was created. |
| WT-ZAI-2: source reads fail all evidence and exceed sustainable method rates | Batch selected messages by channel/thread with one bounded current-access read and a maximum page of 15. Share a durable app/workspace/method cooldown across processes and user tokens; default history/replies pacing is one request/minute, search 20/minute. `Retry-After` extends the cooldown; a successful short retry preserves the full subsequent method interval. Return matching verified evidence with an explicit partial-coverage/retry notice when another source is unavailable; return a coded failure if no matching verified support remains. A missing page is uncertain coverage, not a deletion claim. | 15 retrieval-recovery cases and the updated 17 Slack follow-up cases. Hash, authorship, current grant and injection checks remain; no raw-text cache or stale-search substitution. `tier3` is only an operator assertion of verified eligible rate class. Real commercial permission, rate class and live behavior remain unverified. |
| WT-ZAI-3: public-client OAuth interoperability | Fix the genuine SDK discovery mismatch: token and revocation metadata advertise `none`, matching the predefined public client. Preserve the exact issuer string and advertise `twin:read`. Existing SDK client validation, PKCE, resource checks and revocation remain. | Ten actual SDK/HTTP discovery, authorization and token/revocation cases. Predefined client registration is officially supported; absent dynamic registration is not a defect. Callback-specific legacy issuer handling is supported when issuer identification is not advertised. No unsupported blanket requirement to add DCR or `iss` was adopted. Real ChatGPT HTTPS sign-in remains untested. |
| WT-ZAI-4: reasoning/output budget and concealed failures | Keep `gpt-6.1-sol` with `reasoning.effort=max`. Separate the visible-answer target from an optional explicit total Responses reasoning/output budget. With no override, preserve the caller's existing budget. Require native response/message completion, reject refusal/malformed output and unsupported provenance, and return `GENERATION_FAILED` without content/provider-detail logging or an opaque extractive fallback. | 60 offline generation cases. Default extractive operation is unchanged. No automatic budget increase, paid retry, API credit consumption or claim of live model access. `max` is valid for the requested model. |

The original provider-lifetime matrix failed all 27 applicable baseline cases; the original OAuth matrix failed four of ten; seven of the original nine recovery cases failed. The first 37 generation cases failed 30 before the fix; later refusal/envelope variants added coverage. These were local synthetic reproductions, not external-model judgments.

## Current validation

- Full hash-locked offline suite: **268 passed, 58 skipped**, zero failures. Skips require the explicitly isolated PostgreSQL URL.
- Full hash-locked PostgreSQL/pgvector suite: **326 passed, zero skipped**, zero failures. Real PG authority, credential CAS and atomic cross-process rate reservations are included.
- Real Redis/Celery/Postgres smoke: queued ingestion completed with **10 chunks**, citations and queued retention/deletion passed; **zero model API calls**.
- Offline complete package checks, Python compile, shell syntax and patch whitespace checks passed. CI now runs the full suite both without and with the isolated database, followed by the worker/package checks. CI success is established only by the exact committed SHA's completed run.
- The pinned-base offline hashed-wheel container passed `pip check`, rejected unconfigured production before serving, and passed **268 tests with 58 skips** using read-only mounted synthetic tests/fixtures and `--network=none`. The production image excludes tests/fixtures. Only installation transport changed for local verification; the hosting platform's normal online build remains unverified.
- Deterministic five-member candidate ZIP remains unchanged: SHA-256 `ff5047ea054aa96ae357c164bd57b697c525cbcd4666a755aa8ad68d292ef1aa`.

The full PG run initially found five existing memory-specific test assumptions. Four tests now inspect the appropriate backend's persisted records; the historical quota fixture explicitly backdates only its synthetic database row because production correctly stamps actual insertion time. No quota behavior was relaxed.

## Safe commands for Claude, Z.ai and Grok reviewers

Use a fresh private checkout of the exact commit in `ROUND2_CHECKPOINT.json`; do not review a floating branch or replace the existing working checkout. Read `HANDOVER.md`, this document and `SUBMISSION_READINESS.md`. The same commands apply to each reviewer with an authorized local runtime; they do not establish access to any review service.

```bash
cd plugin-scaffold
python3 -m venv /tmp/wisdomtwin-review-venv
/tmp/wisdomtwin-review-venv/bin/python -m pip install --require-hashes -r requirements.lock
/tmp/wisdomtwin-review-venv/bin/python -m pytest -q --tb=short
PATH=/tmp/wisdomtwin-review-venv/bin:$PATH ./package.sh --check
```

With disposable loopback Postgres/pgvector and Redis only:

```bash
WISDOMTWIN_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/wisdomtwin_test \
  /tmp/wisdomtwin-review-venv/bin/python -m pytest -q --tb=short
WISDOMTWIN_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/wisdomtwin_test \
WISDOMTWIN_TEST_REDIS_URL=redis://127.0.0.1:56379/9 \
  /tmp/wisdomtwin-review-venv/bin/python scripts/verify_local_worker.py
PATH=/tmp/wisdomtwin-review-venv/bin:$PATH ./package.sh --candidate --output-dir /tmp/wisdomtwin-review-candidate
```

The full database/worker checks reset the explicitly isolated `*_test` database; use no shared or production database. All providers/models are synthetic mocks, public auth-disabled tunnels are prohibited, and the candidate ZIP is not submitted by these commands. Review source current-access isolation, substitution/revocation races, shared method limits, public-client metadata and incomplete/refused generation. Report the exact reviewed SHA, actual executed checks, findings with file/line references and untested areas. Do not deploy, submit, grant OAuth scopes, enable irreversible app settings, spend API credits or accept terms.

## Primary sources checked October 1, 2026

[Slack token rotation](https://docs.slack.dev/authentication/using-token-rotation/) distinguishes nonrotating long-lived grants from rotating grants. [Slack PKCE](https://docs.slack.dev/authentication/using-pkce/) specifies the code/refresh exchanges and 30-day PKCE refresh lifetime; the desktop exception is not assumed for an HTTPS server. [OAuth v2 access](https://docs.slack.dev/reference/methods/oauth.v2.access/) documents rotating user-grant responses.

[Slack history](https://docs.slack.dev/reference/methods/conversations.history/), [replies](https://docs.slack.dev/reference/methods/conversations.replies/), [search](https://docs.slack.dev/reference/methods/search.messages/) and [rate limits](https://docs.slack.dev/apis/web-api/rate-limits/) distinguish qualifying commercial non-Marketplace limits from Marketplace/internal/exempt installations. No blanket assertion about every existing installation or prohibition on all `search.messages` use is made.

[OpenAI plugin authentication](https://developers.openai.com/plugins/build/auth) supports predefined clients and describes callback-specific issuer handling; the [plugin changelog](https://developers.openai.com/plugins/changelog) preserves legacy callback flow. The [MCP authorization specification](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) conditions issuer-response validation on advertised support. The pinned MCP 2.2.0 SDK metadata implementation hardcodes secret-based methods; the adapter corrects only this server's configured public-client discovery.

[GPT-6.1 Sol model documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol) supports the requested effort. [Reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning) explains that `max_output_tokens` covers reasoning and visible output and can end incomplete. Native Responses envelopes/refusals are checked rather than accepting an SDK convenience `output_text` field as a raw HTTP contract.

## Release blockers and retained-data boundary

The candidate retains placeholder MCP/legal URLs. [SUBMISSION_READINESS.md](SUBMISSION_READINESS.md) names the required accounts, settings and evidence: verified hosting/HTTPS and corporate/provider authorization, commercial Slack permission/rate class, real sign-in/source/revocation/cleanup checks, verified operator/contact and adopted hosted legal pages, demo/reviewer access and explicit dashboard submission. Google integrations remain disabled and incomplete.

Provider text stays transient. The existing persistent protected vector/provenance index is not session-only storage and must be disclosed and approved as such. Minimal opaque refresh-attempt markers last 30 days; rate markers last until their cooldown and are swept by maintenance. Neither includes source plaintext or raw credentials. Fixture-only success does not establish production cleanup timing or processor retention.

No public deployment, merge, new grant/credential, app-setting change, paid model call, legal acceptance, directory submission or publication occurred. The ZIP is **NOT FOR SUBMISSION**. External Claude, Z.ai and Grok results are pending actual authorized review access and artifacts.
