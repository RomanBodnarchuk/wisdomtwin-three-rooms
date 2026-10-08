# Salesperson worker

Small Calendly booking worker for two companies on one account: WisdomTwin and N5R. The Vite demo in this repository does not import it.

Isolation is enforced here before any Calendly write. WisdomTwin can use only `https://calendly.com/romanbodnarchuk/20min` (15 minutes, Google Meet). N5R can use only the existing 15-minute business-call event. The worker does not rename events, change their duration, or change their location.

The only invitee this worker will book, list, or cancel is the owner-test contact `roman@n5r.com` (HubSpot contact `143893597452`). A caller-supplied email is not treated as verification. A booking that would email anyone else is refused.

Confirm name, email, date, time, and timezone before a booking is sent. The owner-test timezone is `America/Toronto`. Success is reported only after Calendly returns an active invitee, or after a follow-up read finds the same appointment. A timed-out create is reconciled before another create is attempted.

## Configuration

Copy `.env.example`. Set `CALENDLY_API_TOKEN` in the environment, or set `CALENDLY_TOKEN_FILE` to a mode-600 file outside this repository. Do not commit a token value.

```bash
node --experimental-strip-types --test test/**/*.test.ts
node --experimental-strip-types src/cli.ts users-me
node --experimental-strip-types src/cli.ts availability
node --experimental-strip-types src/cli.ts owner-test --book-owner-test
```

`owner-test` books one non-overlapping slot for each company for `roman@n5r.com`, checks that a duplicate request does not create a second appointment, checks the campaign guard, then cancels those owner-test appointments. Calendly sends the normal owner notification for that booking and cancellation.

This worker is not attached to the live ElevenLabs branches.
