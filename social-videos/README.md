# WisdomTwin — 2-part social video

Vertical (9:16, 1080×1920, 30fps) kinetic-typography promo built with [Remotion](https://remotion.dev). Designed to post on every platform (TikTok, Reels, Shorts, LinkedIn, X) — each part is **90 seconds or less** and every part ends on the Calendly call to action `calendly.com/romanbodnarchuk/20min`.

| Composition | Story | Length |
| --- | --- | --- |
| `Part1` | The problem — regulated decisions wait weeks; judgment walks out the door. Brand reveal + "21 days → 8:42". Teases Part 2. | 80s |
| `Part2` | The solution in action — one-press huddle, evidence, governance (Linked/Checked/Named/Logged), three outcomes, named human, "3 weeks → 8 minutes". | 87s |

Both parts are muted-first: the on-screen kinetic captions carry the full message for silent autoplay feeds.

## Develop

```bash
npm install
npm run dev        # opens Remotion Studio to preview/edit Part1 and Part2
```

## Render

```bash
npx remotion render Part1 out/wisdomtwin_part1.mp4
npx remotion render Part2 out/wisdomtwin_part2.mp4
```

## Structure

- `src/theme.ts` — brand colors, canvas size, Calendly URL.
- `src/lib/fonts.ts` — Google Fonts (Archivo display + Inter body).
- `src/lib/ui.tsx` — reusable animated primitives (backdrop, headline, meters, CTA, etc.).
- `src/parts/Part1.tsx`, `src/parts/Part2.tsx` — the two compositions, one scene per section.

Edit copy or timing in the two `parts/*.tsx` files. Scene durations live in the `D` map at the top of each file; the composition length is derived from them, so keep each total ≤ 2700 frames (90s).
