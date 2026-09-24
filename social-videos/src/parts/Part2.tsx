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
import { VO2, MUSIC } from "../audio";
import { body, display } from "../lib/fonts";
import {
  Backdrop,
  Body,
  CTA,
  FadeUp,
  Headline,
  Kicker,
  Meter,
  MusicBed,
  PartBadge,
  ProgressBar,
  SceneWrap,
  Stage,
  Vo,
} from "../lib/ui";

const FPS = 30;
const s = (sec: number) => Math.round(sec * FPS);

const D = {
  recap: 6,
  press: 10,
  evidence: 11,
  limits: 10,
  gov: 12,
  outcomes: 11,
  named: 10,
  payoff: 8,
  cta: 9,
} as const;

export const PART2_DURATION = Object.values(D).reduce((a, b) => a + b, 0) * FPS; // 2610 frames = 87s

const Recap: React.FC = () => (
  <SceneWrap durationInFrames={s(D.recap)}>
    <Backdrop tint="teal" />
    <Stage>
      <PartBadge n={2} delay={2} />
      <div style={{ height: 34 }} />
      <Kicker delay={6}>You saw the problem</Kicker>
      <div style={{ height: 24 }} />
      <Headline words={["Now", "watch", "the", "fix."]} delay={12} size={140} accentIndices={[3]} accent={COLORS.teal} />
      <div style={{ height: 34 }} />
      <Body delay={34}>One press. One governed decision. Eight minutes.</Body>
    </Stage>
  </SceneWrap>
);

const Chip: React.FC<{ role: string; name: string; delay: number; color: string }> = ({
  role,
  name,
  delay,
  color,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 18,
        background: "rgba(255,255,255,0.05)",
        border: `1px solid ${COLORS.line}`,
        borderRadius: 20,
        padding: "18px 22px",
        opacity: interpolate(p, [0, 1], [0, 1]),
        translate: `0px ${interpolate(p, [0, 1], [30, 0])}px`,
      }}
    >
      <div style={{ width: 46, height: 46, borderRadius: 999, background: color, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: display, fontWeight: 900, fontSize: 24, color: COLORS.bg }}>
        {role[0]}
      </div>
      <div style={{ display: "flex", flexDirection: "column" }}>
        <span style={{ fontFamily: body, fontWeight: 700, fontSize: 30, color: COLORS.cream }}>{role}</span>
        <span style={{ fontFamily: body, fontWeight: 500, fontSize: 24, color: COLORS.creamDim }}>{name}</span>
      </div>
    </div>
  );
};

const Phone: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame, fps, config: { damping: 200 } });
  return (
    <div
      style={{
        width: 620,
        height: 1200,
        borderRadius: 72,
        background: "linear-gradient(180deg, #16181F, #0C0D11)",
        border: "10px solid #23262F",
        boxShadow: `0 40px 120px rgba(0,0,0,0.6), 0 0 0 2px ${COLORS.teal}22`,
        padding: 34,
        opacity: interpolate(p, [0, 1], [0, 1]),
        scale: `${interpolate(p, [0, 1], [0.9, 1])}`,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 26 }}>
        <span style={{ fontFamily: body, fontWeight: 700, fontSize: 26, color: COLORS.cream, letterSpacing: 1 }}>WISDOMTWIN</span>
        <span style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: body, fontWeight: 700, fontSize: 24, color: COLORS.danger }}>
          <span style={{ width: 16, height: 16, borderRadius: 999, background: COLORS.danger }} /> LIVE
        </span>
      </div>
      {children}
    </div>
  );
};

const OnePress: React.FC = () => (
  <SceneWrap durationInFrames={s(D.press)}>
    <Backdrop tint="teal" />
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 70 }}>
      <FadeUp delay={2} y={30}>
        <div style={{ fontFamily: display, fontWeight: 900, fontSize: 84, letterSpacing: -2, color: COLORS.cream, textAlign: "center", marginBottom: 40 }}>
          One press <span style={{ color: COLORS.teal }}>convenes the room.</span>
        </div>
      </FadeUp>
      <Phone>
        <div style={{ fontFamily: body, fontWeight: 600, fontSize: 26, color: COLORS.creamDim, marginBottom: 22 }}>
          Executive huddle · assembling
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <Chip role="CEO" name="Daniel Mercer" delay={16} color={COLORS.teal} />
          <Chip role="CFO" name="Priya Rao" delay={26} color={COLORS.gold} />
          <Chip role="CTO" name="Marcus Feld" delay={36} color={COLORS.orange} />
          <Chip role="Legal" name="Chief Legal Officer" delay={46} color="#8B9DF7" />
        </div>
        <div style={{ marginTop: "auto", fontFamily: body, fontWeight: 500, fontSize: 24, color: COLORS.creamDim }}>
          No new meeting. No calendar dependency.
        </div>
      </Phone>
    </AbsoluteFill>
  </SceneWrap>
);

const SourceCard: React.FC<{ label: string; meta: string; delay: number }> = ({ label, meta, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 24,
        width: "100%",
        background: COLORS.card,
        border: `1px solid ${COLORS.line}`,
        borderRadius: 24,
        padding: "28px 32px",
        opacity: interpolate(p, [0, 1], [0, 1]),
        translate: `${interpolate(p, [0, 1], [50, 0])}px 0px`,
      }}
    >
      <div style={{ width: 56, height: 56, borderRadius: 999, background: `${COLORS.teal}22`, color: COLORS.teal, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 34, fontWeight: 900 }}>
        ✓
      </div>
      <div style={{ display: "flex", flexDirection: "column" }}>
        <span style={{ fontFamily: body, fontWeight: 700, fontSize: 40, color: COLORS.cream }}>{label}</span>
        <span style={{ fontFamily: body, fontWeight: 500, fontSize: 30, color: COLORS.creamDim }}>{meta}</span>
      </div>
    </div>
  );
};

const Evidence: React.FC = () => (
  <SceneWrap durationInFrames={s(D.evidence)}>
    <Backdrop tint="teal" />
    <Stage justify="center">
      <Kicker delay={2}>Evidence, not opinions</Kicker>
      <div style={{ height: 30 }} />
      <Headline words={["Authorized", "evidence", "arrives", "with", "the", "question."]} delay={8} size={82} accentIndices={[0]} accent={COLORS.teal} lineHeight={1.05} />
      <div style={{ height: 50 }} />
      <div style={{ display: "flex", flexDirection: "column", gap: 26, width: "100%" }}>
        <SourceCard label="Board packet" meta="source-backed · permissioned" delay={40} />
        <SourceCard label="Risk policy v4" meta="linked · version-tracked" delay={58} />
        <SourceCard label="Prior precedent" meta="cited · in the customer boundary" delay={76} />
      </div>
    </Stage>
  </SceneWrap>
);

const Limits: React.FC = () => (
  <SceneWrap durationInFrames={s(D.limits)}>
    <Backdrop tint="gold" />
    <Stage justify="center">
      <Kicker delay={2} color={COLORS.gold}>Limits stated with the answer</Kicker>
      <div style={{ height: 46 }} />
      <Meter label="Decision confidence" value={0.62} color={COLORS.orange} delay={18} />
      <div style={{ height: 40 }} />
      <Meter label="Governance threshold" value={0.8} color={COLORS.teal} delay={38} />
      <div style={{ height: 60 }} />
      <Headline words={["Completeness", "is", "not", "permission."]} delay={70} size={72} accentIndices={[3]} accent={COLORS.orange} lineHeight={1.05} />
    </Stage>
  </SceneWrap>
);

const Pillar: React.FC<{ word: string; desc: string; delay: number; color: string }> = ({
  word,
  desc,
  delay,
  color,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
      <div
        style={{
          width: "100%",
          height: interpolate(p, [0, 1], [0, 260]),
          borderRadius: 22,
          background: `linear-gradient(180deg, ${color}, ${color}44)`,
          alignSelf: "flex-end",
        }}
      />
      <span style={{ fontFamily: display, fontWeight: 900, fontSize: 46, color: COLORS.cream, opacity: interpolate(p, [0, 1], [0, 1]) }}>{word}</span>
      <span style={{ fontFamily: body, fontWeight: 500, fontSize: 26, color: COLORS.creamDim, textAlign: "center", opacity: interpolate(p, [0, 1], [0, 1]) }}>{desc}</span>
    </div>
  );
};

const Governance: React.FC = () => (
  <SceneWrap durationInFrames={s(D.gov)}>
    <Backdrop tint="teal" />
    <Stage justify="center">
      <Kicker delay={2}>Governance in the path of the answer</Kicker>
      <div style={{ height: 20 }} />
      <Headline words={["Every", "answer", "is", "governed."]} delay={8} size={84} accentIndices={[3]} accent={COLORS.teal} />
      <div style={{ height: 96 }} />
      <div style={{ display: "flex", alignItems: "flex-end", gap: 30, width: "100%", height: 380 }}>
        <Pillar word="Linked" desc="to authorized sources" delay={40} color={COLORS.teal} />
        <Pillar word="Checked" desc="against policy limits" delay={58} color={COLORS.gold} />
        <Pillar word="Named" desc="a human is accountable" delay={76} color={COLORS.orange} />
        <Pillar word="Logged" desc="a complete audit trail" delay={94} color="#8B9DF7" />
      </div>
    </Stage>
  </SceneWrap>
);

const OutcomeCard: React.FC<{ title: string; desc: string; color: string; delay: number }> = ({
  title,
  desc,
  color,
  delay,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  return (
    <div
      style={{
        width: "100%",
        borderRadius: 28,
        padding: "34px 38px",
        background: COLORS.card,
        borderLeft: `10px solid ${color}`,
        border: `1px solid ${COLORS.line}`,
        borderLeftWidth: 10,
        borderLeftColor: color,
        opacity: interpolate(p, [0, 1], [0, 1]),
        translate: `0px ${interpolate(p, [0, 1], [40, 0])}px`,
      }}
    >
      <div style={{ fontFamily: display, fontWeight: 900, fontSize: 58, color, letterSpacing: -1 }}>{title}</div>
      <div style={{ fontFamily: body, fontWeight: 500, fontSize: 36, color: COLORS.cream, marginTop: 8 }}>{desc}</div>
    </div>
  );
};

const Outcomes: React.FC = () => (
  <SceneWrap durationInFrames={s(D.outcomes)}>
    <Backdrop tint="gold" />
    <Stage justify="center">
      <Kicker delay={2} color={COLORS.gold}>Three honest outcomes</Kicker>
      <div style={{ height: 50 }} />
      <div style={{ display: "flex", flexDirection: "column", gap: 30, width: "100%" }}>
        <OutcomeCard title="Recommend" desc="a bounded action the policy layer can inspect." color={COLORS.teal} delay={20} />
        <OutcomeCard title="Escalate" desc="route to the role that can actually decide." color={COLORS.gold} delay={40} />
        <OutcomeCard title="Safe decline" desc="missing permission blocks release. On purpose." color={COLORS.danger} delay={60} />
      </div>
    </Stage>
  </SceneWrap>
);

const Named: React.FC = () => (
  <SceneWrap durationInFrames={s(D.named)}>
    <Backdrop tint="teal" />
    <Stage>
      <Kicker delay={2}>A human stays accountable</Kicker>
      <div style={{ height: 30 }} />
      <Headline words={["A", "named", "human", "approves", "—", "on", "the", "record."]} delay={10} size={92} accentIndices={[1, 2]} accent={COLORS.teal} lineHeight={1.05} />
      <div style={{ height: 44 }} />
      <Body delay={48} size={46} color={COLORS.cream}>
        We model how the role decides. We never replace who is responsible.
      </Body>
    </Stage>
  </SceneWrap>
);

const Payoff: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 6, fps, config: { damping: 200 } });
  return (
    <SceneWrap durationInFrames={s(D.payoff)}>
      <Backdrop tint="gold" />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 96, textAlign: "center" }}>
        <div style={{ opacity: interpolate(p, [0, 1], [0, 1]), scale: `${interpolate(p, [0, 1], [0.86, 1])}` }}>
          <div style={{ fontFamily: display, fontWeight: 900, fontSize: 150, lineHeight: 1, letterSpacing: -3, color: COLORS.cream }}>
            3 weeks
          </div>
          <div style={{ fontFamily: display, fontWeight: 900, fontSize: 64, color: COLORS.gold, margin: "18px 0" }}>becomes</div>
          <div style={{ fontFamily: display, fontWeight: 900, fontSize: 190, lineHeight: 1, letterSpacing: -4, color: COLORS.teal }}>
            8 minutes
          </div>
          <div style={{ fontFamily: body, fontWeight: 700, fontSize: 48, color: COLORS.cream, marginTop: 26 }}>
            Fast. Governed. On the record.
          </div>
        </div>
      </AbsoluteFill>
    </SceneWrap>
  );
};

export const Part2: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.bg }}>
      <Series>
        <Series.Sequence durationInFrames={s(D.recap)}><Recap /><Vo src={VO2.recap} /></Series.Sequence>
        <Series.Sequence durationInFrames={s(D.press)}><OnePress /><Vo src={VO2.press} /></Series.Sequence>
        <Series.Sequence durationInFrames={s(D.evidence)}><Evidence /><Vo src={VO2.evidence} /></Series.Sequence>
        <Series.Sequence durationInFrames={s(D.limits)}><Limits /><Vo src={VO2.limits} /></Series.Sequence>
        <Series.Sequence durationInFrames={s(D.gov)}><Governance /><Vo src={VO2.gov} /></Series.Sequence>
        <Series.Sequence durationInFrames={s(D.outcomes)}><Outcomes /><Vo src={VO2.outcomes} /></Series.Sequence>
        <Series.Sequence durationInFrames={s(D.named)}><Named /><Vo src={VO2.named} /></Series.Sequence>
        <Series.Sequence durationInFrames={s(D.payoff)}><Payoff /><Vo src={VO2.payoff} /></Series.Sequence>
        <Series.Sequence durationInFrames={s(D.cta)}>
          <SceneWrap durationInFrames={s(D.cta)}>
            <Backdrop tint="teal" />
            <CTA calendly={CALENDLY_URL} sub="Part 2 of 2 · See it run on your workflow." />
          </SceneWrap>
          <Vo src={VO2.cta} />
        </Series.Sequence>
      </Series>
      <MusicBed src={MUSIC} />
      <ProgressBar />
    </AbsoluteFill>
  );
};
