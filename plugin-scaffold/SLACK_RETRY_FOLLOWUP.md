# Shared retry reservation follow-up

Independent review of `c24447903f2eeb2c9f52199075766c7af8ce4310` identified a narrow Tier 3 limiter race. With a 1.2-second reservation and `Retry-After: 2`, the reservation and provider cooldown could expire when the bounded wait ended. A retry bypassed admission while another user's request acquired the same app/workspace/method slot. Both dispatched at the same synthetic clock time.

The deterministic regression failed all four SQLite/PostgreSQL cases before the fix, covering either the retry or competing user dispatching first. The provider and clock are mocked; events coordinate the threads without real waits or provider calls.

The production change is confined to `connectors._request_json`: capture a conservative expiry before the initial database reservation, and atomically reserve again before retrying if that original reservation has expired. A competing reservation returns the existing `SourceRateLimited` guidance. Restricted 60-second pacing keeps its existing bounded short retry; no extra HTTP attempts, waits, scopes or content cache are introduced. The shared store/schema is unchanged.

Validation:

- Combined Slack recovery/retry regressions with isolated PostgreSQL: **36 passed**, zero skipped or failures.
- Full locked offline suite: **270 passed, 60 expected PostgreSQL skips**, zero failures.
- Full locked PostgreSQL suite: **330 passed**, zero skips or failures.
- Exact-commit CI results are recorded in the separate `slack-retry-followup` artifact checkpoint. The historical [four-issue checkpoint](REVIEW_ROUND2.md) and its artifacts remain unchanged. The prior offline container image is evidence for `c244479`, not a verified image of this new patch; hosting remains unverified.

Reproduce the regression on a fresh private checkout using the hash-locked Python environment:

```bash
cd plugin-scaffold
python3 -m pytest -q --tb=short tests/test_slack_retry_reservation.py
WISDOMTWIN_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/wisdomtwin_test \
  python3 -m pytest -q --tb=short tests/test_slack_retry_reservation.py tests/test_retrieval_recovery.py tests/test_slack_followup.py
```

The database must be disposable, loopback-only and named `*_test`; the full suite's existing fixture resets that explicitly selected database. SQLite-only execution passes two cases and skips two PostgreSQL variants. Existing locked setup/full-suite/worker commands and publication blockers are in [REVIEW_ROUND2.md](REVIEW_ROUND2.md) and [SUBMISSION_READINESS.md](SUBMISSION_READINESS.md).

Claude, Z.ai and Grok reviewer handoffs must use the new exact commit. Their actual external results remain unverified. Candidate packaging and production release gates are unchanged. No paid model/provider calls, real grants, deployment, merge, legal acceptance or submission occurred.
