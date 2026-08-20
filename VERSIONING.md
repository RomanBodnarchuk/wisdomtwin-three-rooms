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
- [x] v3.0 (2026-08-10) — **Complete investor-grade visual edit.** Preserved the locked 4:00
  voice performance and added a six-chapter investor proof rail (governance moat → coordination
  tax → enterprise constraints → decision engine → board-ready outputs → economics), a stronger
  outcome-first start gate, kinetic number/decision captions, a full-stop safe-decline moment,
  mobile-visible three-room structure cards, a nineteen-day/≈$400K decision-economics disclosure,
  the Thursday-morning board-package payoff, compounding judgment-asset framing, one investor-meeting
  CTA, and vendor-neutral start/25/50/75/100/CTA analytics events. End-card dwell runs through 237.4s.
  The start screen also establishes Teams/Zoom/Slack/WisdomTwin-app surfaces. Brand UI now reads
  WisdomTwin; Buzz remains only an internal code/audio id.

- [x] v3.1 (2026-08-10) — **Start the investor film at 1:05.** Initial play and replay now enter
  at 65.8 seconds, immediately after the obsolete Dana Calloway narrator clip and directly into
  Daniel Mercer's male CEO sequence. Completion analytics measure the viewed 2:54 segment.

- [x] v3.2 (2026-08-10) — **Normalize the new cut's timestamps.** The player and transcript now
  display 0:00 at Daniel's entry and 2:54 at the close, while seeking remains synchronized to the
  underlying source timeline. All visible runtime labels now identify the film as 2:54.

- [x] v3.2.2 (2026-08-14) — **Public harden.** Sticky Watch CTA in short/mobile iframes so
  /demo embeds cannot hide the start button. 404.html recovers any missing path to the huddle
  (PDF paths recover to the canon E4 PDF). Static `start.html` landing that cannot 404.
  Public folder now serves the Aug 11 E4 deck (MD5 b981589af995f146462dc733fc683317) at
  WisdomTwin-Investor-Deck.pdf plus filename aliases (E4-08-10, E4-08-11, deck.pdf,
  wisdomtwin-deck.pdf). Replaced the older 35eb1234 PDF that had been in repo root / downloads.

- [x] v3.2.1 (2026-08-10) — **Clean Daniel's opening handoff.** Suppressed the residual narrator
  caption during the sub-second transition into Daniel Mercer's opening line. The investor cut now
  opens on Daniel as CEO with no narrator voice or narrator caption.

- [x] v3.3 (2026-08-18) — **Delete the five spoken twin introductions.** Trimmed
  "Your X's twin" from cro-01, cmo-01, legal-02, cfo-02, and cto-02 at the first
  post-intro silence. Captions now match the remaining audio. Safe-decline beat preserved.

- [x] v3.4 (2026-08-20) — **Buzz voice authority pass.** Re-rendered the six Buzz
  lines on ElevenLabs Adam (chief-of-staff), slower source then fitted to the
  locked windows. Captions unchanged, including the baked "nineteen days" close.

- [x] v3.5 (2026-08-20) — **Analytics provider hookup.** Plausible loads on the
  GitHub Pages host. Start, 25/50/75/100, and CTA events leave the browser.
  dataLayer is initialized. No identity or transcript data.

- [x] v3.6 (2026-08-20) — **Re-recorded Buzz close as twenty-one days.** Captions
  and money-math card now match narrator "three weeks". Close audio on Adam.

## Backlog (in priority order — one per day)

1. [ ] ~~Full film honest recut~~ → SUPERSEDED by Roman's v2.4 decision: the original full
   film is canonical. Improve it in place instead. The remaining items below all apply to the
   ORIGINAL film (same event ids in fullTimeline.ts).
2. [x] **Delete the five spoken twin introductions.** (v3.3, 2026-08-18) Trimmed the baked
   intro phrases from the five role MP3s and matched captions. Safe-decline timing shifted
   with the CTO file so captions never contradict audio.
3. [x] **Break the 38-second Legal block.** The investor cut now uses the CEO's "Legal first"
  interruption and a 12-second gate-one window; the long audio remains available to the archival cut.
4. [x] **Fix 19 vs 21 days.** Caption/data aligned in v2.8. Audio completed in v3.6
   (2026-08-20): Buzz close re-recorded as twenty-one days on Adam. Captions and
   money-math card match narrator "three weeks". Never ship captions that contradict audio.
5. [x] **Decline-moment full stop.** At the safe-decline beat: drop music bed to silence 1.5s
   BEFORE the line, hold the blocker register visual, no other motion. Silence sells it.
6. [x] **Money-math card after huddle end.** Uses the canonical twenty-one-day completion audio,
   8:42 huddle duration, and an explicitly illustrative ≈$400K delayed-execution estimate.
7. [x] **Tagline consistency.** "WisdomTwin preserves institutional judgment" appears at open and close.
8. [x] **Captions: bigger, kinetic, money phrases highlighted** in warm gold (#C8A45D).
9. [x] **"Three rooms. One night. One decision."** title card appears on the first room transition.
10. [x] **Buzz voice authority pass.** (v3.4, 2026-08-20) Re-rendered the 6 buzz
    lines with ElevenLabs Adam, lower and slower, fitted to existing windows so
    captions still match. Deterministic MP3 playback, no browser TTS.
11. [x] **Mobile simplification.** Phones hide side panels/evidence chrome and retain headline,
    captions, play control, CTA, and the room structure card.
12. [x] **Thursday boardroom closing.** Stage-four economics card now lands the board-package outcome;
    a future re-render may promote it into VO.
13. [x] **Analytics provider hookup.** (v3.5, 2026-08-20) Plausible script + queue
    stub on romanbodnarchuk.github.io. Funnel events leave the browser. dataLayer
    initialized for a later tag manager. No identity or transcript data.
14. [x] **WisdomTwin dependency line.** One line establishes that twins join any huddle surface
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
