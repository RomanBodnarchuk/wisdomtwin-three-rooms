// Audio asset paths (relative to public/). Voiceover: HeyGen TTS, one clip per scene.
// Music: energetic instrumental bed, looped under the whole composition.

export const MUSIC = "music/bed.mp3";

export const SFX = {
  whoosh: "sfx/whoosh.mp3",
  impact: "sfx/impact.mp3",
} as const;

export const VO1 = {
  hook: "vo/p1/hook.mp3",
  problem: "vo/p1/problem.mp3",
  cost: "vo/p1/cost.mp3",
  reframe: "vo/p1/reframe.mp3",
  brand: "vo/p1/brand.mp3",
  stat: "vo/p1/stat.mp3",
  tease: "vo/p1/tease.mp3",
  cta: "vo/p1/cta.mp3",
} as const;

export const VO2 = {
  recap: "vo/p2/recap.mp3",
  press: "vo/p2/press.mp3",
  evidence: "vo/p2/evidence.mp3",
  limits: "vo/p2/limits.mp3",
  gov: "vo/p2/gov.mp3",
  outcomes: "vo/p2/outcomes.mp3",
  named: "vo/p2/named.mp3",
  payoff: "vo/p2/payoff.mp3",
  cta: "vo/p2/cta.mp3",
} as const;
