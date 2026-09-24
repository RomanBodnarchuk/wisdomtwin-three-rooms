import React from "react";
import {
  AbsoluteFill,
  interpolate,
  Series,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { COLORS, CALENDLY_URL } from "../theme";
import { VO1, MUSIC, SFX } from "../audio";
import { body, display } from "../lib/fonts";
import {
  Backdrop,
  Body,
  BrandMark,
  CTA,
  FadeUp,
  Headline,
  Kicker,
  MusicBed,
  PartBadge,
  ProgressBar,
  SceneWrap,
  Sfx,
  Stage,
  Vo,
} from "../lib/ui";

const FPS = 30;
const s = (sec: number) => Math.round(sec * FPS);

// Scene durations (seconds) — total kept well under 90s.
const D = {
  hook: 6,
  problem: 13,
  cost: 10,
  reframe: 8,
  brand: 11,
  stat: 13,
  tease: 9,
  cta: 10,
} as const;

export const PART1_DURATION = Object.values(D).reduce((a, b) => a + b, 0) * FPS; // 2400 frames = 80s

const Hook: React.FC = () => (
  <SceneWrap durationInFrames={s(D.hook)}>
    <Backdrop tint="teal" />
    <Stage>
      <PartBadge n={1} delay={2} />
      <div style={{ height: 34 }} />
      <Kicker delay={6}>For regulated enterprises</Kicker>
      <div style={{ height: 24 }} />
      <Headline words={["Your", "best", "decision", "is", "stuck."]} delay={12} size={128} accentIndices={[4]} accent={COLORS.orange} />
      <div style={{ height: 34 }} />
      <Body delay={34}>It is waiting for a room to open up.</Body>
    </Stage>
  </SceneWrap>
);

const Row: React.FC<{ tag: string; text: string; delay: number; color: string }> = ({
  tag,
  text,
  delay,
  color,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  return (
    <div
      style={{
        opacity: interpolate(p, [0, 1], [0, 1]),
        translate: `${interpolate(p, [0, 1], [-60, 0])}px 0px`,
        display: "flex",
        alignItems: "baseline",
        gap: 28,
        width: "100%",
      }}
    >
      <span style={{ fontFamily: display, fontWeight: 900, fontSize: 84, color, minWidth: 300, letterSpacing: -2 }}>
        {tag}
      </span>
      <span style={{ fontFamily: body, fontWeight: 500, fontSize: 44, color: COLORS.cream }}>{text}</span>
    </div>
  );
};

const Problem: React.FC = () => (
  <SceneWrap durationInFrames={s(D.problem)}>
    <Backdrop tint="orange" />
    <Stage justify="center">
      <Kicker delay={2} color={COLORS.orange}>The coordination tax</Kicker>
      <div style={{ height: 60 }} />
      <div style={{ display: "flex", flexDirection: "column", gap: 52, width: "100%" }}>
        <Row tag="Days" text="a CEO decision waits for one person." delay={20} color={COLORS.teal} />
        <Row tag="Weeks" text="a bank exception waits for committee." delay={44} color={COLORS.gold} />
        <Row tag="Months" text="a determination waits between reviewers." delay={68} color={COLORS.orange} />
      </div>
      <div style={{ height: 70 }} />
      <Body delay={110} size={50} color={COLORS.cream}>
        And when the expert leaves…
      </Body>
    </Stage>
  </SceneWrap>
);

const Cost: React.FC = () => (
  <SceneWrap durationInFrames={s(D.cost)}>
    <Backdrop tint="orange" />
    <Stage>
      <Kicker delay={2} color={COLORS.danger}>The hidden risk</Kicker>
      <div style={{ height: 30 }} />
      <Headline words={["their", "judgment", "walks", "out", "the", "door."]} delay={10} size={116} accentIndices={[0, 1]} accent={COLORS.danger} />
      <div style={{ height: 40 }} />
      <Body delay={44}>The way your best people decide is not written down. It leaves with them.</Body>
    </Stage>
  </SceneWrap>
);

const Reframe: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 6, fps, config: { damping: 200 } });
  return (
    <SceneWrap durationInFrames={s(D.reframe)}>
      <Backdrop tint="teal" />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 96 }}>
        <div
          style={{
            fontFamily: display,
            fontWeight: 900,
            fontSize: 132,
            lineHeight: 1.0,
            letterSpacing: -3,
            textAlign: "center",
            color: COLORS.cream,
            opacity: interpolate(p, [0, 1], [0, 1]),
            scale: `${interpolate(p, [0, 1], [0.85, 1])}`,
          }}
        >
          What if judgment
          <br />
          <span style={{ color: COLORS.teal }}>never had to wait?</span>
        </div>
      </AbsoluteFill>
    </SceneWrap>
  );
};

const Brand: React.FC = () => (
  <SceneWrap durationInFrames={s(D.brand)}>
    <Backdrop tint="gold" />
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 96, textAlign: "center" }}>
      <BrandMark size={190} delay={4} />
      <div style={{ height: 40 }} />
      <FadeUp delay={14} y={40}>
        <div style={{ fontFamily: display, fontWeight: 900, fontSize: 120, letterSpacing: -3, color: COLORS.cream }}>
          WisdomTwin
        </div>
      </FadeUp>
      <div style={{ height: 24 }} />
      <FadeUp delay={26} y={30}>
        <div style={{ fontFamily: body, fontWeight: 600, fontSize: 46, color: COLORS.creamDim, maxWidth: 820 }}>
          The Judgment Platform for regulated enterprises.
        </div>
      </FadeUp>
      <div style={{ height: 46 }} />
      <FadeUp delay={40} y={24}>
        <div
          style={{
            fontFamily: body,
            fontWeight: 700,
            fontSize: 40,
            color: COLORS.gold,
            border: `2px solid ${COLORS.gold}55`,
            borderRadius: 999,
            padding: "18px 40px",
          }}
        >
          Preserves institutional judgment
        </div>
      </FadeUp>
    </AbsoluteFill>
  </SceneWrap>
);

const BigStat: React.FC<{ value: string; label: string; color: string; delay: number; sub?: string }> = ({
  value,
  label,
  color,
  delay,
  sub,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        opacity: interpolate(p, [0, 1], [0, 1]),
        translate: `0px ${interpolate(p, [0, 1], [50, 0])}px`,
      }}
    >
      <div style={{ fontFamily: display, fontWeight: 900, fontSize: 200, lineHeight: 1, color, letterSpacing: -4 }}>
        {value}
      </div>
      <div style={{ fontFamily: body, fontWeight: 700, fontSize: 46, color: COLORS.cream, marginTop: 10 }}>{label}</div>
      {sub ? <div style={{ fontFamily: body, fontWeight: 500, fontSize: 34, color: COLORS.creamDim, marginTop: 8 }}>{sub}</div> : null}
    </div>
  );
};

const Stat: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const arrow = spring({ frame: frame - 150, fps, config: { damping: 200 } });
  return (
    <SceneWrap durationInFrames={s(D.stat)}>
      <Backdrop tint="teal" />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 96 }}>
        <Kicker delay={2}>From three weeks to minutes</Kicker>
        <div style={{ height: 70 }} />
        <BigStat value="21 days" label="of executive coordination" color={COLORS.orange} delay={16} />
        <div
          style={{
            fontFamily: display,
            fontWeight: 900,
            fontSize: 90,
            color: COLORS.gold,
            margin: "34px 0",
            opacity: interpolate(arrow, [0, 1], [0, 1]),
            translate: `0px ${interpolate(arrow, [0, 1], [-20, 0])}px`,
          }}
        >
          ↓
        </div>
        <BigStat value="8:42" label="one governed huddle" color={COLORS.teal} delay={168} sub="board-ready, with a full audit trail" />
      </AbsoluteFill>
    </SceneWrap>
  );
};

const Tease: React.FC = () => (
  <SceneWrap durationInFrames={s(D.tease)}>
    <Backdrop tint="gold" />
    <Stage>
      <PartBadge n={2} delay={2} />
      <div style={{ height: 30 }} />
      <Kicker delay={8} color={COLORS.gold}>Coming in Part 2</Kicker>
      <div style={{ height: 24 }} />
      <Headline words={["Watch", "one", "decision", "happen", "—", "live."]} delay={14} size={110} accentIndices={[3]} accent={COLORS.teal} />
      <div style={{ height: 36 }} />
      <Body delay={44} size={46} color={COLORS.cream}>
        Evidence. Dissent. A named human. A complete audit trail.
      </Body>
    </Stage>
  </SceneWrap>
);

export const Part1: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.bg }}>
      <Series>
        <Series.Sequence durationInFrames={s(D.hook)}><Hook /><Vo src={VO1.hook} /><Sfx src={SFX.whoosh} volume={0.32} /></Series.Sequence>
        <Series.Sequence durationInFrames={s(D.problem)}><Problem /><Vo src={VO1.problem} /><Sfx src={SFX.whoosh} volume={0.32} /></Series.Sequence>
        <Series.Sequence durationInFrames={s(D.cost)}><Cost /><Vo src={VO1.cost} /><Sfx src={SFX.whoosh} volume={0.32} /></Series.Sequence>
        <Series.Sequence durationInFrames={s(D.reframe)}><Reframe /><Vo src={VO1.reframe} /><Sfx src={SFX.whoosh} volume={0.32} /></Series.Sequence>
        <Series.Sequence durationInFrames={s(D.brand)}><Brand /><Vo src={VO1.brand} /><Sfx src={SFX.impact} from={2} volume={0.5} /></Series.Sequence>
        <Series.Sequence durationInFrames={s(D.stat)}><Stat /><Vo src={VO1.stat} /><Sfx src={SFX.whoosh} volume={0.32} /><Sfx src={SFX.impact} from={168} volume={0.42} /></Series.Sequence>
        <Series.Sequence durationInFrames={s(D.tease)}><Tease /><Vo src={VO1.tease} /><Sfx src={SFX.whoosh} volume={0.32} /></Series.Sequence>
        <Series.Sequence durationInFrames={s(D.cta)}>
          <SceneWrap durationInFrames={s(D.cta)}>
            <Backdrop tint="teal" />
            <CTA calendly={CALENDLY_URL} sub="Part 1 of 2 · Bring one decision that always waits." />
          </SceneWrap>
          <Vo src={VO1.cta} />
          <Sfx src={SFX.impact} from={4} volume={0.5} />
        </Series.Sequence>
      </Series>
      <MusicBed src={MUSIC} base={0.2} />
      <ProgressBar />
    </AbsoluteFill>
  );
};
