import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Audio } from "@remotion/media";
import { COLORS, SAFE_X } from "../theme";
import { body, display } from "./fonts";

// Per-scene voiceover clip, placed inside a Series.Sequence (starts near scene start).
export const Vo: React.FC<{ src: string; from?: number }> = ({ src, from = 8 }) => (
  <Audio src={staticFile(src)} from={from} volume={0.92} />
);

// Looped energetic music bed for a whole composition, with fade in/out.
export const MusicBed: React.FC<{ src: string; base?: number }> = ({ src, base = 0.16 }) => {
  const { durationInFrames } = useVideoConfig();
  return (
    <Audio
      src={staticFile(src)}
      loop
      volume={(f) =>
        interpolate(
          f,
          [0, 18, durationInFrames - 45, durationInFrames - 1],
          [0, base, base, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        )
      }
    />
  );
};

const EASE = Easing.bezier(0.16, 1, 0.3, 1);

// Wraps a scene so it fades in at the start and out at the end of its own window.
export const SceneWrap: React.FC<{
  durationInFrames: number;
  children: React.ReactNode;
  fade?: number;
}> = ({ durationInFrames, children, fade = 12 }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(
    frame,
    [0, fade, durationInFrames - fade, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE },
  );
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
};

// Animated background: deep canvas, two drifting accent glows, faint grid, vignette.
export const Backdrop: React.FC<{ tint?: "teal" | "gold" | "orange" }> = ({
  tint = "teal",
}) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();
  const t = frame / Math.max(durationInFrames, 1);

  const glowA = tint === "teal" ? COLORS.teal : tint === "gold" ? COLORS.gold : COLORS.orange;
  const glowB = tint === "orange" ? COLORS.gold : COLORS.tealDeep;

  const ax = interpolate(Math.sin(t * Math.PI * 2), [-1, 1], [0.2, 0.55]);
  const ay = interpolate(Math.cos(t * Math.PI * 2), [-1, 1], [0.15, 0.4]);
  const bx = interpolate(Math.cos(t * Math.PI * 2 + 1), [-1, 1], [0.5, 0.85]);
  const by = interpolate(Math.sin(t * Math.PI * 2 + 1), [-1, 1], [0.6, 0.9]);

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.bg, overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${ax * width}px ${ay * height}px, ${glowA}44, transparent 45%)`,
        }}
      />
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${bx * width}px ${by * height}px, ${glowB}38, transparent 48%)`,
        }}
      />
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${COLORS.line} 1px, transparent 1px), linear-gradient(90deg, ${COLORS.line} 1px, transparent 1px)`,
          backgroundSize: "120px 120px",
          opacity: 0.35,
          maskImage: "radial-gradient(circle at 50% 45%, black, transparent 80%)",
          WebkitMaskImage: "radial-gradient(circle at 50% 45%, black, transparent 80%)",
        }}
      />
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at 50% 50%, transparent 55%, rgba(0,0,0,0.65) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

// A vertically-centered content column with safe-area padding.
export const Stage: React.FC<{ children: React.ReactNode; justify?: string }> = ({
  children,
  justify = "center",
}) => (
  <AbsoluteFill
    style={{
      padding: `180px ${SAFE_X}px`,
      display: "flex",
      flexDirection: "column",
      justifyContent: justify,
      alignItems: "flex-start",
      gap: 0,
    }}
  >
    {children}
  </AbsoluteFill>
);

export const FadeUp: React.FC<{
  children: React.ReactNode;
  delay?: number;
  y?: number;
  style?: React.CSSProperties;
}> = ({ children, delay = 0, y = 60, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  return (
    <div
      style={{
        opacity: interpolate(p, [0, 1], [0, 1]),
        translate: `0px ${interpolate(p, [0, 1], [y, 0])}px`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export const Kicker: React.FC<{ children: React.ReactNode; color?: string; delay?: number }> = ({
  children,
  color = COLORS.teal,
  delay = 0,
}) => (
  <FadeUp delay={delay} y={24}>
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 18,
        fontFamily: body,
        fontWeight: 700,
        letterSpacing: 6,
        textTransform: "uppercase",
        fontSize: 30,
        color,
      }}
    >
      <span style={{ width: 54, height: 4, background: color, borderRadius: 4 }} />
      {children}
    </div>
  </FadeUp>
);

// Big headline with per-word staggered rise.
export const Headline: React.FC<{
  words: string[];
  delay?: number;
  size?: number;
  color?: string;
  accentIndices?: number[];
  accent?: string;
  lineHeight?: number;
}> = ({
  words,
  delay = 0,
  size = 108,
  color = COLORS.cream,
  accentIndices = [],
  accent = COLORS.teal,
  lineHeight = 1.02,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div
      style={{
        fontFamily: display,
        fontWeight: 900,
        fontSize: size,
        lineHeight,
        letterSpacing: -2,
        color,
        display: "flex",
        flexWrap: "wrap",
        gap: "0 22px",
      }}
    >
      {words.map((w, i) => {
        const p = spring({
          frame: frame - delay - i * 5,
          fps,
          config: { damping: 200 },
        });
        return (
          <span
            key={`${w}-${i}`}
            style={{
              display: "inline-block",
              opacity: interpolate(p, [0, 1], [0, 1]),
              translate: `0px ${interpolate(p, [0, 1], [80, 0])}px`,
              color: accentIndices.includes(i) ? accent : color,
            }}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
};

export const Body: React.FC<{
  children: React.ReactNode;
  delay?: number;
  size?: number;
  color?: string;
  style?: React.CSSProperties;
}> = ({ children, delay = 0, size = 46, color = COLORS.creamDim, style }) => (
  <FadeUp delay={delay} y={40}>
    <div
      style={{
        fontFamily: body,
        fontWeight: 500,
        fontSize: size,
        lineHeight: 1.3,
        color,
        maxWidth: 900,
        ...style,
      }}
    >
      {children}
    </div>
  </FadeUp>
);

// WisdomTwin overlapping-lens mark (gold + orange) as on the site.
export const BrandMark: React.FC<{ size?: number; delay?: number }> = ({
  size = 120,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 120 } });
  const s = interpolate(p, [0, 1], [0.6, 1]);
  const r = size * 0.32;
  return (
    <div style={{ scale: `${s}`, opacity: interpolate(p, [0, 1], [0, 1]) }}>
      <svg width={size * 1.5} height={size} viewBox="0 0 150 100">
        <circle cx={58} cy={50} r={r * 100 / size} fill="none" stroke={COLORS.gold} strokeWidth={5} />
        <circle cx={92} cy={50} r={r * 100 / size} fill="none" stroke={COLORS.orange} strokeWidth={5} />
      </svg>
    </div>
  );
};

// Part badge, e.g. PART 1 / 2.
export const PartBadge: React.FC<{ n: number; delay?: number }> = ({ n, delay = 0 }) => (
  <FadeUp delay={delay} y={16}>
    <div
      style={{
        fontFamily: body,
        fontWeight: 700,
        letterSpacing: 5,
        textTransform: "uppercase",
        fontSize: 26,
        color: COLORS.gold,
        border: `2px solid ${COLORS.gold}66`,
        borderRadius: 999,
        padding: "12px 26px",
      }}
    >
      Part {n} / 2
    </div>
  </FadeUp>
);

// Animated horizontal meter that fills to `value` (0..1).
export const Meter: React.FC<{
  label: string;
  value: number;
  color?: string;
  delay?: number;
}> = ({ label, value, color = COLORS.teal, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  const fill = interpolate(p, [0, 1], [0, value]);
  return (
    <FadeUp delay={delay} y={30} style={{ width: "100%" }}>
      <div style={{ width: "100%" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontFamily: body,
            fontWeight: 600,
            fontSize: 34,
            color: COLORS.cream,
            marginBottom: 16,
          }}
        >
          <span>{label}</span>
          <span style={{ color }}>{Math.round(fill * 100)}%</span>
        </div>
        <div
          style={{
            width: "100%",
            height: 22,
            borderRadius: 999,
            background: "rgba(255,255,255,0.08)",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${fill * 100}%`,
              height: "100%",
              borderRadius: 999,
              background: `linear-gradient(90deg, ${color}, ${COLORS.gold})`,
            }}
          />
        </div>
      </div>
    </FadeUp>
  );
};

// Playback progress bar pinned to the top — signals length on social feeds.
export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const w = interpolate(frame, [0, durationInFrames - 1], [0, 100], {
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start" }}>
      <div style={{ height: 8, width: "100%", background: "rgba(255,255,255,0.06)" }}>
        <div style={{ height: "100%", width: `${w}%`, background: COLORS.teal }} />
      </div>
    </AbsoluteFill>
  );
};

// Full-bleed call-to-action shared by both parts.
export const CTA: React.FC<{ calendly: string; sub: string; delay?: number }> = ({
  calendly,
  sub,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pulse = interpolate(
    Math.sin((frame / fps) * Math.PI * 2 * 0.8),
    [-1, 1],
    [0.9, 1],
  );
  return (
    <Stage justify="center">
      <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center" }}>
        <BrandMark size={130} delay={delay} />
        <div style={{ height: 40 }} />
        <FadeUp delay={delay + 6} y={40}>
          <div
            style={{
              fontFamily: display,
              fontWeight: 900,
              fontSize: 96,
              lineHeight: 1.0,
              letterSpacing: -2,
              color: COLORS.cream,
              textAlign: "center",
            }}
          >
            Book your
            <br />
            <span style={{ color: COLORS.teal }}>Judgment Assessment</span>
          </div>
        </FadeUp>
        <div style={{ height: 28 }} />
        <Body delay={delay + 12} size={44} color={COLORS.creamDim} style={{ textAlign: "center" }}>
          {sub}
        </Body>
        <div style={{ height: 56 }} />
        <FadeUp delay={delay + 16} y={30}>
          <div
            style={{
              scale: `${pulse}`,
              fontFamily: body,
              fontWeight: 700,
              fontSize: 46,
              color: COLORS.bg,
              background: `linear-gradient(90deg, ${COLORS.teal}, ${COLORS.gold})`,
              padding: "30px 56px",
              borderRadius: 999,
              boxShadow: `0 24px 80px ${COLORS.teal}55`,
            }}
          >
            {calendly}
          </div>
        </FadeUp>
        <div style={{ height: 34 }} />
        <FadeUp delay={delay + 20} y={20}>
          <div style={{ fontFamily: body, fontWeight: 600, fontSize: 34, color: COLORS.gold, letterSpacing: 1 }}>
            20 minutes with founder Roman Bodnarchuk
          </div>
        </FadeUp>
      </div>
    </Stage>
  );
};
