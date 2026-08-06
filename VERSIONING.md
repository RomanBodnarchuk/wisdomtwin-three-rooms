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
- [x] v2.2 (2026-08-06) — Full-film recut 7:37→4:34: rapid-fire cold open (was 1:38), safe decline
  at 0:29–0:45 (was 3:03), narrator explains after proof, Legal trimmed to gate one, honest label.
  Also fixed dialoguePlayer multi-window drift bug (analysis replayed over decline caption).
- [x] v2.3 (2026-08-06) — hero_B_2 wired as the cinematic hero image (272KB optimized JPEG);
  three unused kitchen stills removed. NOTE: scene image path is now
  images/scene/ceo-kitchen-hero.jpg.

## Backlog (in priority order — one per day)

1. [ ] ~~Full film honest recut to ~3:30~~ → DONE in v2.2 as 4:34. Optional further tightening:
   drop cmo-01 category line (−11.5s) and buzz-blockers (−7.2s) to reach ~4:10, or slice
   legal-03/cfo-03 windows to reach sub-4:00. Renumber remaining items when picking.
2. [ ] **Delete the five spoken twin introductions** ("Your CRO's twin." etc.) — roles already
   on screen. Buys back ~8s. Caption/text change only if audio lines are separate files;
   if intros are baked into the role audio files, skip audio and trim where clean.
3. [ ] **Break the 38-second Legal block** (legal-02, 1:45–2:23) — split into two beats with a
   CEO interruption ("English. What kills it?") using existing ceo audio or a text-only caption beat.
4. [ ] **Fix 19 vs 21 days.** Narrator audio says "three weeks" (=21), buzz-close audio says
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
