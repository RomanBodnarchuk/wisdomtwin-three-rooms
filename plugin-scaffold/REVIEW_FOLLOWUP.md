# Bounded review follow-up — October 1, 2026

This continues PR [15](https://github.com/RomanBodnarchuk/wisdomtwin-three-rooms/pull/15) from `939edde25ce9d8d83dabe60990df019c3ed982e4`. The original candidate ZIP, diff, source archive and `CHECKPOINT.json` are preserved unchanged. A separate follow-up checkpoint records the exact new source commit and artifact hashes. The original four tools and two packaged skills remain.

This is the historical `187a25f` validation record. The later four-issue follow-up and revised explicit partial-coverage behavior are described in [REVIEW_ROUND2.md](REVIEW_ROUND2.md).

## Confirmed findings and fixes

| Finding | Resulting behavior | Reproduced evidence |
| --- | --- | --- |
| A consumed initial code could mint a new family after subject revocation or reprovisioning | Consent and grants bind to a durable membership generation. Subject mutation and complete-pair issuance serialize in one database transaction; stale issuance returns `invalid_grant`. New verified sign-in works. | The original six adapter/scenario cases failed on SQLite and PostgreSQL; they now pass. |
| Used refresh replay returned `invalid_grant` while successors remained valid | Replay detection in both actual SDK loading and exchange-consume paths revokes only that family. Family relationships survive rotation until its active successor expires. | Real pinned SDK token handler; concurrent loader/issuance timings, unknown/access-token/wrong-client isolation and a synthetic clock crossing original expiry. |
| Deleted Slack `thread_not_found` aborted the query; fallback outages silently abstained | Known deletion/access loss withholds that source; other valid sources still answer. Direct/fallback provider outages remain coded failures without partial evidence. | Mixed-source, lone-deletion and direct/fallback outage regressions. |
| Slack 429 ignored `Retry-After` | At most two HTTP attempts and one wait, only for a known delay at most two seconds. Longer, unknown or repeated limits return `CONNECTOR_FAILED` and safe retry guidance without evidence. | Numeric/date delay, two/three-second boundary, repeated limit and no-partial-answer regressions; no real sleeps. |

These changes follow the replay behavior described in [RFC 9700 §4.14.2](https://www.rfc-editor.org/rfc/rfc9700.html#section-4.14.2) and the delay handling described in [Slack rate-limit guidance](https://docs.slack.dev/apis/web-api/rate-limits/). [Slack replies documentation](https://docs.slack.dev/reference/methods/conversations.replies/) describes `thread_not_found`. The tests do not establish a production security certification or the app's applicable commercial rate class.

## Locked validation

- Complete offline suite: **147 passed, 14 skipped, zero failures**. Three database cases and eleven PostgreSQL authorization variants require the isolated database URL.
- Explicit PostgreSQL/pgvector suite: **42 passed, zero skipped, zero failures**. It includes the original twenty database/MVP/worker cases and all twenty-two SQLite/PostgreSQL authorization follow-up cases.
- Independent focused suites: **22 authorization tests** and **17 Slack tests** passed. Additional seven malformed/missing rate-header probes passed without retries or waits.
- Real Celery/Redis/PostgreSQL smoke: queued ingestion completed with **10 chunks**, citations and queued retention/deletion passed; **zero model API calls**.
- Offline package checks, Python compile, shell syntax and patch whitespace checks passed. Candidate ZIP SHA-256 is unchanged: `ff5047ea054aa96ae357c164bd57b697c525cbcd4666a755aa8ad68d292ef1aa`.

The environment used the existing Python 3.12 hash-locked dependencies and pinned MCP **2.2.0**. CI's isolated database step now includes the follow-up authorization matrix. A remote result is evidence only after the exact new commit's run completes.

```bash
python3 -m pip install --require-hashes -r requirements.lock
python3 -m pytest -q --tb=short
WISDOMTWIN_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/wisdomtwin_test \
  python3 -m pytest -q tests/test_mvp.py tests/test_worker_concurrency.py tests/test_database.py tests/test_revocation_followup.py --tb=short
WISDOMTWIN_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/wisdomtwin_test \
WISDOMTWIN_TEST_REDIS_URL=redis://127.0.0.1:56379/9 \
  python3 scripts/verify_local_worker.py
./package.sh --check
./package.sh --candidate --output-dir /workspace/wisdomtwin-plugin-artifacts/review-followup
```

These commands use disposable, synthetic, loopback services. The database/worker checks reset only the explicitly isolated test database. No real grants, app settings, paid APIs, deployment, merge, legal adoption or submission occurred.

## Operational implications

Earlier grants without a membership generation fail closed and require sign-in again. A pseudonymous subject/integer generation marker remains after membership removal; deleting it casually would weaken protection against stale exchanges after reprovisioning. The hosted privacy draft now describes this minimal security state; it remains unadopted. Refresh-family relationships remain while a successor is active and are swept after expiry. Provider text handling stays transient; the existing persistent protected metadata index remains an explicit architecture boundary.

The four original files could not be saved to ChatGPT Library. The unchanged prepared-upload helper reserved their uploads, but byte transfers hit proxy 403; finalization never ran and no saved Library IDs/versions were returned. Private diagnostic state and `LIBRARY_SAVED.json` preserve the attempt. No uncertain transfer was retried or replaced by a direct-create action. This Library failure does not change their hashes or the tested source checkpoint.

Use [SUBMISSION_READINESS.md](SUBMISSION_READINESS.md) for production blockers and [PRODUCTION_LAYOUT.md](PRODUCTION_LAYOUT.md) for service/configuration names. The ZIP still contains placeholder hosting/legal URLs and is **NOT FOR SUBMISSION**.
