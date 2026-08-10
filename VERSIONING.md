# WisdomTwin Executive Huddle — Daily Versioning Playbook

One new version ships every day. Each daily run: pick the TOP unchecked item below,
implement it in `src/`, verify (`npx tsc --noEmit && npm run build`), bump the version in
`package.json`, commit as `vX.Y: <what shipped>`, push to `main`, then deploy with
`gh workflow run pages.yml --repo RomanBodnarchuk/wisdomtwin-three-rooms --ref main`
(push does NOT auto-trigger the Pages workflow — always dispatch manually and confirm
the run succeeds with `gh run list --repo RomanBodnarchuk/wisdomtwin-three-rooms --limit 1`).
Finally, check the item off here with the date and version.

Live site: https://romanbodnarchuk.github.io/wisdomtwin-three-rooms/

## Non-negotiables (from brand vault + teardowns)

- Brand: WisdomTwin only. No "WisdomClone", no clone language. Huddle is a feature, not a brand.
- Colors: #F37021 (orange), #0B1F3A (navy), #C8A45D (gold); dark cinematic theme vars already exist.
- One tagline: "WisdomTwin preserves institutional judgment." Open and close.
- NEVER soften the numbers: $11M cap, 7–2 vote, dissent preserved, 12,400 decisions, 91/9 split,
  $7.4M phase one, 38 minutes human review, 62→91% confidence.
- NEVER cut the safe-decline beat. Move it earlier, never remove it.
- Keep the synthetic-data disclosure small in the footer. Do not enlarge it.
- One CTA only: https://calendly.com/romanbodnarchuk/20min (+ text 416 220 5314).
- Do not regress: 45s cut stays default; investor mode stays behind ?investor; single start button.

## Shipped

- [x] v2.0 (2026-08-06) — Hormozi #1–#5: 45s default cut, one brand + outcome title,
  CTA endcard + persistent pill, outcome-first start screen, disclosure demoted to footer.
  Source rebuilt from sourcemaps (Vite + React + TS + Tailwind v4); workflow builds dist on push.
- [x] v2.1 (2026-08-06) — Calendly CTA + phone line, Her/She→His/He fix, outcome cut labels,
  "iPhone 19 Max"→"iPhone", investor mode behind ?investor, tab-switch pause/resume.
- [x] v2.2 (2026-08-06) — Full-film recut 7:37→4:34: rapid-fire cold open, safe decline at 0:45.
  Also fixed dialoguePlayer multi-window drift bug (analysis replayed over decline caption).
- [x] v2.3 (2026-08-06) — hero_B_2 wired as the cinematic hero image (272KB optimized JPEG).
  NOTE: scene image path is images/scene/ceo-kitchen-hero.jpg.
- [x] v2.4 (2026-08-06) — Restored the original full film (superseded same-day, see v2.6).
- [x] v2.5 (2026-08-06, parallel session) — Removed 45s cut from selector, defaulted to full film.
- [x] v2.6 (2026-08-06) — **FINAL DECISION, locked by Roman: "I like the long 4 minute version
  best."** The 4:34 recut (rapid-fire cold open, safe decline at 0:45, narrator after proof,
  Legal trimmed to gate one) IS the demo. Single-film experience: no cut selector, one button,
  useDemoPlayback('full'). DO NOT resurrect the 8:07 cut as the default, do not re-add cut
  toggles, do not recut the story. Improve THIS film in place: pacing polish, visuals, captions,
  audio quality, CTA, analytics. The 8:07 original remains in git history (tag commits v2.4) if
  ever needed; investor60/outreach45 configs stay in code but are not shown in UI.

- [x] v2.7 (2026-08-06) — **Longest cut only = original 8:07 boardroom film.** Restored fullTimeline
  from v2.4 (487000ms). No cut selector. 4:34 recut remains in git history (v2.2/v2.6) if needed.
- [x] v2.8 (2026-08-10, parallel session) — 19 vs 21 days: matched narrator "three weeks" across
  start screen, close caption, data model. NOTE: buzz-close AUDIO still says "nineteen days"
  (baked mp3) — caption reverted to match audio in v2.9 until the line is re-recorded.
- [x] v2.9 (2026-08-10) — **Investor cut (4:00) is the default film** (V6 source-of-truth alignment:
  decks promise "1-4 min audio huddles"). Based on the v2.6 4:34 film Roman locked, trimmed:
  CMO category line, CEO sleep beat, end cards 34s→16s. End card stage 5 = V6 closer
  ("Every employee, backed by a Wisdom Twin." / "We sell speed. One press moves the decision forward.").
  Start screen + chrome updated. Removed dead WalkingAtmosphere ("The Walk") component.
  Re-applied the 8:07 timeline audio resync (evidence/blockers/scene events anchored to dialogue;
  legal-build window 348528→230854) — it had been wiped uncommitted. QA: 400/400 data checks pass
  (wisdomtwin-three-rooms-qa/validate.js).
- [x] v2.8 (2026-08-10) — **Fix 19 vs 21 days.** Start screen, buzz-close caption, and blockers data
  model all now read "three weeks" / "twenty-one days" to match narrator audio. Items #2–#3 blocked
  (intros baked into per-role MP3s; no ElevenLabs API key to re-render or trim).

## Backlog (in priority order — one per day)

1. [ ] ~~Full film honest recut~~ → SUPERSEDED by Roman's v2.4 decision: the original full
   film is canonical. Improve it in place instead. The remaining items below all apply to the
   ORIGINAL film (same event ids in fullTimeline.ts).
2. [ ] ~~Delete the five spoken twin introductions~~ → BLOCKED: intros baked into single
   per-role MP3 files. No ELEVENLABS_API_KEY to re-render. Cannot trim without audio tooling.
   Defer until voice re-render pass (backlog #10) or audio editing tools available.
3. [ ] **Break the 38-second Legal block** (legal-02, 1:45–2:23) — split into two beats with a
   CEO interruption ("English. What kills it?") using existing ceo audio or a text-only caption beat.
4. [x] **Fix 19 vs 21 days.** (v2.8, 2026-08-10) Narrator audio says "three weeks" (=21), buzz-close audio says
   "nineteen days". Re-record ONE line with ElevenLabs (buzz voice id SAz9YHcvj6GT2YYXdXww) if
   ELEVENLABS_API_KEY is available; otherwise change the on-screen completion card to match the
   narrator ("21 days") and queue the audio fix. Never ship captions that contradict the audio.
5. [ ] **Decline-moment full stop.** At the safe-decline beat: drop music bed to silence 1.5s
   BEFORE the line, hold the blocker register visual, no other motion. Silence sells it.
6. [ ] **Money-math card after huddle end.** "21 days of a CEO + five senior officers waiting
   on a decision ≈ $400K in delayed execution. One huddle: 8 minutes." One card, endcard stage 4.
7. [ ] **Tagline consistency.** "WisdomTwin preserves institutional judgment" — once at open
   (start screen subhead), once at close. Remove competing closers except in investor contrast box.
8. [ ] **Captions: bigger, kinetic, money phrases highlighted** in warm gold (#C8A45D):
   "declining to answer", "seven to two", "twenty-one days", "ninety-one percent".
9. [ ] **"Three rooms. One night. One decision."** title card during first room transition so the
   structure name pays off (internal mechanic may stay in code, not in copy).
10. [ ] **Buzz voice authority pass.** Re-render the 6 buzz lines with a lower, slower, chief-of-staff
    voice (ElevenLabs). Deterministic playback beats browser TTS fallback.
11. [ ] **Mobile simplification.** Phones: hide side panels/evidence chrome; keep headline, captions,
    play control, CTA. Verify at 390px width.
12. [ ] **Thursday boardroom closing image or VO line** — the buyer buys the Monday morning after.
13. [ ] **Analytics instrumentation.** Track start rate, 25/50/75/100% completion, CTA clicks
    (privacy-friendly, e.g. Plausible or simple endpoint). Without these four numbers every future
    change is guesswork.
14. [ ] **Buzz dependency line.** One line establishing twins join any huddle surface
    (Teams, Zoom, Slack), so the demo doesn't read as a feature of someone else's product.

## Repo facts

- Entry: `src/features/demo/DemoShell.tsx`; start screen: `src/components/StartExperience.tsx`;
  endcard: `src/components/EndCard.tsx`; timelines: `src/data/*Timeline.ts`;
  audio map: `src/lib/dialoguePlayer.ts` (DIALOGUE_AUDIO_MAP).
- Audio assets: `public/audio/dialogue/*.mp3` (ElevenLabs, manifest at
  `public/audio/dialogue/manifest.json`).
- Cuts: `outreach45` (default, 45s), `investor60` (60s), `full` (7:37 — mislabeled, see backlog #1).
- Build: `npm ci && npm run build` → `dist/` (workflow deploys `dist/`).
- gh CLI is authenticated as RomanBodnarchuk; commit with
  user.email RomanBodnarchuk@users.noreply.github.com (email privacy blocks other addresses).
