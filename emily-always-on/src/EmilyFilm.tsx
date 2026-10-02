import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadNewsreader } from "@remotion/google-fonts/Newsreader";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  OffthreadVideo,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
  Interactive,
} from "remotion";

const inter = loadInter("normal", {
  weights: ["400", "500", "600", "700"],
  subsets: ["latin"],
});
const news = loadNewsreader("normal", {
  weights: ["500", "600"],
  subsets: ["latin"],
});

const ease = Easing.bezier(0.16, 1, 0.3, 1);

const portrait = staticFile("emily.png");

export const EmilyFilm: React.FC = () => {
  let from = 0;
  return (
    <AbsoluteFill style={{ backgroundColor: "#07080c", fontFamily: inter.fontFamily }}>
      <Audio src={staticFile("narration.mp3")} />
      {scenes.map((scene) => {
        const start = from;
        from += scene.duration;
        const Comp = scene.Component;
        return (
          <Sequence key={scene.id} from={start} durationInFrames={scene.duration} name={scene.id}>
            <Scene>
              <Comp />
            </Scene>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const Scene: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        opacity: interpolate(frame, [0, 10], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: ease,
        }),
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

const Ground: React.FC<{ tint: string }> = ({ tint }) => {
  return (
    <AbsoluteFill
      style={{
        backgroundImage: `radial-gradient(900px 520px at 18% 0%, ${tint}, transparent 60%), radial-gradient(800px 500px at 100% 100%, rgba(255,255,255,0.04), transparent 55%)`,
      }}
    />
  );
};

const Avatar: React.FC<{ size: number }> = ({ size }) => {
  return (
    <Img
      src={portrait}
      style={{
        width: size,
        height: size,
        borderRadius: size,
        objectFit: "cover",
        objectPosition: "center 18%",
      }}
    />
  );
};

const Meta: React.FC<{
  kicker: string;
  time: string;
  app: string;
  accent: string;
  note: string;
}> = ({ kicker, time, app, accent, note }) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        width: 520,
        paddingLeft: 88,
        paddingTop: 118,
        display: "flex",
        flexDirection: "column",
        gap: 18,
      }}
    >
      <Interactive.Div
        name="Day"
        style={{
          color: "rgba(255,255,255,0.62)",
          fontSize: 28,
          fontWeight: 600,
          letterSpacing: 2.4,
          textTransform: "uppercase",
          opacity: interpolate(frame, [0, 12], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        {kicker}
      </Interactive.Div>
      <Interactive.Div
        name="Clock"
        style={{
          fontFamily: news.fontFamily,
          fontSize: 92,
          lineHeight: 0.92,
          color: "#f4f1ea",
          fontWeight: 500,
          translate: interpolate(frame, [0, 16], ["0px 16px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: ease,
          }),
        }}
      >
        {time}
      </Interactive.Div>
      <Interactive.Div
        name="Channel"
        style={{
          color: accent,
          fontSize: 34,
          fontWeight: 650,
          letterSpacing: -0.4,
        }}
      >
        {app}
      </Interactive.Div>
      <Interactive.Div
        name="Response note"
        style={{
          color: "rgba(244,241,234,0.78)",
          fontSize: 30,
          lineHeight: 1.35,
          maxWidth: 420,
          opacity: interpolate(frame, [28, 42], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        {note}
      </Interactive.Div>
    </div>
  );
};

const Shell: React.FC<{
  tint: string;
  kicker: string;
  time: string;
  app: string;
  accent: string;
  note: string;
  plate?: string;
  children: React.ReactNode;
}> = ({ tint, kicker, time, app, accent, note, plate, children }) => {
  return (
    <AbsoluteFill>
      {plate ? (
        <>
          <Img src={plate} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          <AbsoluteFill
            style={{
              background:
                "linear-gradient(90deg, rgba(6,8,10,0.86) 0%, rgba(6,8,10,0.62) 38%, rgba(6,8,10,0.4) 100%)",
            }}
          />
        </>
      ) : null}
      <Ground tint={tint} />
      <div style={{ display: "flex", height: "100%" }}>
        <Meta kicker={kicker} time={time} app={app} accent={accent} note={note} />
        <div
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            paddingRight: 72,
          }}
        >
          {children}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const rise = (frame: number, at: number) => ({
  opacity: interpolate(frame, [at, at + 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  }),
  translate: interpolate(frame, [at, at + 12], ["0px 22px", "0px 0px"], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: ease,
  }),
});

const Typing: React.FC<{ color: string; until: number }> = ({ color, until }) => {
  const frame = useCurrentFrame();
  if (frame >= until) return null;
  return (
    <div style={{ display: "flex", gap: 8, padding: "8px 4px", ...rise(frame, 16) }}>
      {[0, 1, 2].map((dot) => (
        <div
          key={dot}
          style={{
            width: 12,
            height: 12,
            borderRadius: 12,
            background: color,
            opacity: interpolate((frame + dot * 5) % 18, [0, 6, 12, 18], [0.25, 1, 0.25, 0.25], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        />
      ))}
    </div>
  );
};

export const Open: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <OffthreadVideo
        src={staticFile("night.mp4")}
        muted
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(90deg, rgba(5,6,10,0.88) 0%, rgba(5,6,10,0.72) 46%, rgba(5,6,10,0.28) 100%)",
        }}
      />
      <Ground tint="rgba(88, 122, 168, 0.18)" />
      <div
        style={{
          position: "absolute",
          left: 120,
          top: 180,
          display: "flex",
          flexDirection: "column",
          gap: 22,
        }}
      >
        <Interactive.Div
          name="Open day"
          style={{
            color: "rgba(255,255,255,0.6)",
            fontSize: 30,
            letterSpacing: 3,
            fontWeight: 600,
            textTransform: "uppercase",
          }}
        >
          Sunday
        </Interactive.Div>
        <Interactive.Div
          name="Open clock"
          style={{
            fontFamily: news.fontFamily,
            fontSize: 148,
            lineHeight: 0.9,
            color: "#f7f3ea",
            fontWeight: 500,
          }}
        >
          2:14 AM
        </Interactive.Div>
        <Interactive.Div
          name="Open line"
          style={{
            fontSize: 44,
            color: "#f7f3ea",
            maxWidth: 820,
            lineHeight: 1.25,
            opacity: interpolate(frame, [12, 28], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          Daniel messages Emily. She is already answering.
        </Interactive.Div>
      </div>
      <Interactive.Div
        name="Emily portrait"
        style={{
          position: "absolute",
          right: 150,
          top: 170,
          width: 520,
          height: 640,
          borderRadius: 36,
          overflow: "hidden",
          scale: interpolate(frame, [0, 24], [1.04, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: ease,
            output: "perceptual-scale",
          }),
        }}
      >
        <Img
          src={portrait}
          style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center 15%" }}
        />
        <div
          style={{
            position: "absolute",
            left: 28,
            bottom: 28,
            background: "rgba(8,10,14,0.72)",
            borderRadius: 18,
            padding: "16px 20px",
          }}
        >
          <div style={{ color: "#f7f3ea", fontSize: 32, fontWeight: 650 }}>Emily Chen</div>
          <div style={{ color: "rgba(247,243,234,0.75)", fontSize: 24, marginTop: 4 }}>
            Financial analyst · picture avatar
          </div>
        </div>
      </Interactive.Div>
    </AbsoluteFill>
  );
};

export const IMessage: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Shell
      tint="rgba(10,132,255,0.22)"
      kicker="Sunday · Daniel Mercer, CEO"
      time="2:14 AM"
      app="iMessage"
      accent="#5AC8FA"
      note="Cash, runway, and receivables. Back before he sets the phone down."
    >
      <div
        style={{
          width: 760,
          height: 860,
          borderRadius: 42,
          background: "#000",
          border: "1px solid rgba(255,255,255,0.08)",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 30px 80px rgba(0,0,0,0.45)",
        }}
      >
        <div style={{ padding: "28px 28px 18px", display: "flex", gap: 16, alignItems: "center" }}>
          <Avatar size={72} />
          <div>
            <div style={{ color: "#fff", fontSize: 32, fontWeight: 650 }}>Emily Chen</div>
            <div style={{ color: "#32D74B", fontSize: 22 }}>Active now</div>
          </div>
        </div>
        <div style={{ flex: 1, padding: "10px 26px 28px", display: "flex", flexDirection: "column", justifyContent: "flex-end", gap: 16 }}>
          <div style={{ alignSelf: "flex-end", maxWidth: 560, background: "#0A84FF", color: "#fff", fontSize: 32, lineHeight: 1.35, borderRadius: 26, padding: "18px 22px", ...rise(frame, 4) }}>
            What’s our cash position right now?
          </div>
          <Typing color="#8E8E93" until={36} />
          {frame >= 36 ? (
            <div style={{ alignSelf: "flex-start", display: "flex", gap: 12, maxWidth: 620, ...rise(frame, 36) }}>
              <Avatar size={48} />
              <div style={{ background: "#3A3A3C", color: "#fff", fontSize: 32, lineHeight: 1.35, borderRadius: 26, padding: "18px 22px" }}>
                Cash is <b>$186,400</b>. Runway is <b>7.4 months</b> at a $25,200 burn. Receivables are $64,800, and 91% is current.
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </Shell>
  );
};

export const WhatsApp: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Shell
      tint="rgba(8,16,12,0.55)"
      kicker="Monday · 6:42 AM"
      time="6:42 AM"
      app="WhatsApp"
      accent="#25D366"
      note="The invoice cleared while the office was still dark."
      plate={staticFile("morning.png")}
    >
      <div style={{ width: 760, height: 860, borderRadius: 42, background: "#0B141A", overflow: "hidden", display: "flex", flexDirection: "column", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div style={{ background: "#1F2C34", padding: "26px 24px", display: "flex", gap: 16, alignItems: "center" }}>
          <Avatar size={68} />
          <div>
            <div style={{ color: "#fff", fontSize: 32, fontWeight: 650 }}>Emily Chen</div>
            <div style={{ color: "#8FA6B2", fontSize: 22 }}>online</div>
          </div>
        </div>
        <div style={{ flex: 1, padding: 26, display: "flex", flexDirection: "column", justifyContent: "flex-end", gap: 14 }}>
          <div style={{ alignSelf: "flex-end", maxWidth: 540, background: "#005C4B", color: "#E9F7EF", fontSize: 32, lineHeight: 1.35, borderRadius: "18px 18px 6px 18px", padding: "16px 18px", ...rise(frame, 4) }}>
            Did the Meridian invoice clear?
            <div style={{ textAlign: "right", fontSize: 20, opacity: 0.7, marginTop: 6 }}>6:42 AM ✓✓</div>
          </div>
          <Typing color="#8FA6B2" until={34} />
          {frame >= 34 ? (
            <div style={{ alignSelf: "flex-start", maxWidth: 600, background: "#1F2C34", color: "#E9F7EF", fontSize: 32, lineHeight: 1.35, borderRadius: "18px 18px 18px 6px", padding: "16px 18px", ...rise(frame, 34) }}>
              Yes. <b>$18,750</b> landed at 6:11 AM. September collections are <b>$82,400</b> — 9% ahead of plan.
              <div style={{ fontSize: 20, opacity: 0.7, marginTop: 6 }}>6:42 AM</div>
            </div>
          ) : null}
        </div>
      </div>
    </Shell>
  );
};

export const Telegram: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Shell
      tint="rgba(42,171,238,0.18)"
      kicker="Thursday · 11:58 PM"
      time="11:58 PM"
      app="Telegram"
      accent="#2AABEE"
      note="Margin, by contract, while everyone else is offline."
    >
      <div style={{ width: 760, height: 860, borderRadius: 42, background: "#0E1621", overflow: "hidden", display: "flex", flexDirection: "column", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div style={{ padding: "26px 24px", display: "flex", gap: 16, alignItems: "center", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          <Avatar size={68} />
          <div>
            <div style={{ color: "#fff", fontSize: 32, fontWeight: 650 }}>Emily Chen</div>
            <div style={{ color: "#6AB3F3", fontSize: 22 }}>last seen just now</div>
          </div>
        </div>
        <div style={{ flex: 1, padding: 26, display: "flex", flexDirection: "column", justifyContent: "flex-end", gap: 14 }}>
          <div style={{ alignSelf: "flex-end", maxWidth: 540, background: "#2B5278", color: "#fff", fontSize: 32, lineHeight: 1.35, borderRadius: 16, padding: "16px 18px", ...rise(frame, 4) }}>
            Gross margin on the Q3 contracts?
          </div>
          <Typing color="#6AB3F3" until={34} />
          {frame >= 34 ? (
            <div style={{ alignSelf: "flex-start", display: "flex", gap: 12, ...rise(frame, 34) }}>
              <Avatar size={46} />
              <div style={{ maxWidth: 560, background: "#182533", color: "#fff", fontSize: 32, lineHeight: 1.35, borderRadius: 16, padding: "16px 18px" }}>
                Blended gross margin is <b>68.4%</b>. The three new retainers are at 74%. Services pulled the blend down 2.1 points.
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </Shell>
  );
};

export const Signal: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Shell
      tint="rgba(58,118,240,0.18)"
      kicker="Friday · before the board note"
      time="9:06 PM"
      app="Signal"
      accent="#3A76F0"
      note="One flag. Everything else is inside plan."
    >
      <div style={{ width: 760, height: 860, borderRadius: 42, background: "#1B1C1F", overflow: "hidden", display: "flex", flexDirection: "column", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div style={{ padding: "26px 24px", display: "flex", gap: 16, alignItems: "center" }}>
          <Avatar size={68} />
          <div>
            <div style={{ color: "#fff", fontSize: 32, fontWeight: 650 }}>Emily Chen</div>
            <div style={{ color: "#9AA0A6", fontSize: 22 }}>online</div>
          </div>
        </div>
        <div style={{ flex: 1, padding: 26, display: "flex", flexDirection: "column", justifyContent: "flex-end", gap: 14 }}>
          <div style={{ alignSelf: "flex-end", maxWidth: 560, background: "#3A76F0", color: "#fff", fontSize: 32, lineHeight: 1.35, borderRadius: 22, padding: "16px 18px", ...rise(frame, 4) }}>
            Anything I should worry about before the board note?
          </div>
          <Typing color="#9AA0A6" until={34} />
          {frame >= 34 ? (
            <div style={{ alignSelf: "flex-start", maxWidth: 600, background: "#2C2C2E", color: "#fff", fontSize: 32, lineHeight: 1.35, borderRadius: 22, padding: "16px 18px", ...rise(frame, 34) }}>
              One flag. Software is <b>$4,180</b> this month, <b>$640 over budget</b>. Everything else is inside plan. I can send the variance table.
            </div>
          ) : null}
        </div>
      </div>
    </Shell>
  );
};

export const Slack: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Shell
      tint="rgba(224,30,90,0.14)"
      kicker="Not only the CEO"
      time="3:18 PM"
      app="Slack"
      accent="#E01E5A"
      note="Priya in operations gets the same speed."
    >
      <div style={{ width: 1040, height: 760, borderRadius: 22, overflow: "hidden", display: "flex", background: "#1A1D21", border: "1px solid rgba(255,255,255,0.08)" }}>
        <div style={{ width: 250, background: "#111317", padding: "26px 18px", color: "#d8dde3" }}>
          <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 22 }}>Northline</div>
          <div style={{ fontSize: 22, color: "#fff", background: "#2B3138", borderRadius: 8, padding: "8px 10px" }}># finance</div>
          <div style={{ fontSize: 22, opacity: 0.7, padding: "10px" }}># ops</div>
          <div style={{ fontSize: 22, opacity: 0.7, padding: "10px" }}># board</div>
        </div>
        <div style={{ flex: 1, padding: "26px 28px", display: "flex", flexDirection: "column" }}>
          <div style={{ color: "#fff", fontSize: 32, fontWeight: 700, marginBottom: 22 }}># finance</div>
          <div style={{ display: "flex", gap: 14, ...rise(frame, 6) }}>
            <div style={{ width: 48, height: 48, borderRadius: 8, background: "#3F4A3C", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 20 }}>PS</div>
            <div>
              <div style={{ color: "#fff", fontSize: 26, fontWeight: 700 }}>Priya Shah <span style={{ color: "#9aa0a6", fontWeight: 500 }}>3:18 PM</span></div>
              <div style={{ color: "#e8eaed", fontSize: 30, lineHeight: 1.35, marginTop: 4 }}>Emily, can we approve the $12k contractor for Atlas?</div>
            </div>
          </div>
          <Typing color="#E01E5A" until={36} />
          {frame >= 36 ? (
            <div style={{ display: "flex", gap: 14, marginTop: 18, ...rise(frame, 36) }}>
              <Avatar size={48} />
              <div>
                <div style={{ color: "#fff", fontSize: 26, fontWeight: 700 }}>Emily Chen <span style={{ color: "#9aa0a6", fontWeight: 500 }}>Financial analyst · 3:18 PM</span></div>
                <div style={{ color: "#e8eaed", fontSize: 30, lineHeight: 1.35, marginTop: 4, maxWidth: 640 }}>
                  Yes. It sits inside the Q4 contractor envelope. Remaining after this approval: <b>$21,600</b>. I’ll log it against Atlas.
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </Shell>
  );
};

export const Mail: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Shell
      tint="rgba(90,160,255,0.14)"
      kicker="Saturday · before the 8:00 AM"
      time="7:12 AM"
      app="Email"
      accent="#8AB4F8"
      note="The close is in his inbox before the meeting starts."
    >
      <div style={{ width: 1080, height: 780, borderRadius: 18, overflow: "hidden", background: "#16181d", border: "1px solid rgba(255,255,255,0.08)", display: "flex", flexDirection: "column" }}>
        <div style={{ height: 54, display: "flex", alignItems: "center", gap: 8, padding: "0 16px", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          <div style={{ width: 12, height: 12, borderRadius: 12, background: "#FF5F57" }} />
          <div style={{ width: 12, height: 12, borderRadius: 12, background: "#FEBC2E" }} />
          <div style={{ width: 12, height: 12, borderRadius: 12, background: "#28C840" }} />
          <div style={{ color: "#c9cdd3", marginLeft: 12, fontSize: 20 }}>Inbox — Emily Chen</div>
        </div>
        <div style={{ padding: "28px 36px", display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ color: "#fff", fontSize: 40, fontWeight: 680 }}>August close</div>
          <div style={{ color: "#c9cdd3", fontSize: 24 }}>Daniel Mercer → Emily Chen · 7:11 AM</div>
          <div style={{ color: "#e8eaed", fontSize: 30, ...rise(frame, 4) }}>Need the P&amp;L before my 8am.</div>
          {frame >= 32 ? (
            <div style={{ marginTop: 8, background: "#22262e", borderRadius: 16, padding: "22px 24px", ...rise(frame, 32) }}>
              <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 12 }}>
                <Avatar size={42} />
                <div style={{ color: "#fff", fontSize: 24, fontWeight: 650 }}>Emily Chen · replied 7:12 AM</div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                {[
                  ["August revenue", "$84,200"],
                  ["Gross profit", "$57,600"],
                  ["Net income", "$11,900"],
                  ["Year to date", "$612,400"],
                ].map(([label, value]) => (
                  <div key={label} style={{ background: "#12151a", borderRadius: 12, padding: "14px 16px" }}>
                    <div style={{ color: "#9aa0a6", fontSize: 20 }}>{label}</div>
                    <div style={{ color: "#fff", fontSize: 36, fontWeight: 700 }}>{value}</div>
                  </div>
                ))}
              </div>
              <div style={{ color: "#d5d8de", fontSize: 26, marginTop: 14 }}>On pace for $1.02M this year.</div>
            </div>
          ) : null}
        </div>
      </div>
    </Shell>
  );
};

export const Zoom: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Shell
      tint="rgba(45,140,255,0.16)"
      kicker="Saturday night · the forecast"
      time="11:07 PM"
      app="Zoom"
      accent="#2D8CFF"
      note="Her picture is already in the room."
    >
      <div style={{ width: 1080, height: 760, borderRadius: 18, background: "#0b0d10", overflow: "hidden", border: "1px solid rgba(255,255,255,0.08)", display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "16px 22px", color: "#d5d8de", fontSize: 22, display: "flex", justifyContent: "space-between" }}>
          <span>Northline forecast</span>
          <span>11:07 PM</span>
        </div>
        <div style={{ flex: 1, display: "flex", gap: 16, padding: "0 18px 12px" }}>
          <div style={{ flex: 1.4, borderRadius: 16, overflow: "hidden", position: "relative", background: "#111" }}>
            <Img src={portrait} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center 18%" }} />
            <div style={{ position: "absolute", left: 16, bottom: 16, background: "rgba(0,0,0,0.55)", color: "#fff", borderRadius: 8, padding: "8px 12px", fontSize: 24 }}>
              Emily Chen
            </div>
          </div>
          <div
            style={{
              flex: 0.7,
              borderRadius: 16,
              background: "#1c2430",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 14,
            }}
          >
            <div
              style={{
                width: 132,
                height: 132,
                borderRadius: 132,
                background: "#334155",
                color: "#fff",
                fontSize: 46,
                fontWeight: 700,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              DM
            </div>
            <div style={{ color: "#fff", fontSize: 26, fontWeight: 650 }}>Daniel Mercer</div>
            <div style={{ color: "#9aa6b2", fontSize: 20 }}>Camera off</div>
          </div>
        </div>
        <div style={{ margin: "0 18px 16px", background: "rgba(255,255,255,0.06)", borderRadius: 12, padding: "14px 16px", color: "#fff", fontSize: 28, lineHeight: 1.35, ...rise(frame, 20) }}>
          Base case holds at <b>$1.02M</b>. Cash stays above $150k through January if the Meridian retainers renew.
        </div>
      </div>
    </Shell>
  );
};

export const Close: React.FC = () => {
  const frame = useCurrentFrame();
  const channels = ["iMessage", "WhatsApp", "Telegram", "Signal", "Slack", "Email", "Zoom"];
  return (
    <AbsoluteFill>
      <Ground tint="rgba(120, 150, 190, 0.2)" />
      <div style={{ position: "absolute", left: 120, top: 140, right: 120 }}>
        <div style={{ display: "flex", gap: 36, alignItems: "center" }}>
          <Avatar size={148} />
          <div>
            <div style={{ fontFamily: news.fontFamily, fontSize: 92, color: "#f7f3ea", lineHeight: 0.95 }}>She never clocks out.</div>
            <div style={{ fontSize: 36, color: "rgba(247,243,234,0.8)", marginTop: 12 }}>Emily Chen · financial analyst · about $1 million a year</div>
          </div>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 14, marginTop: 48 }}>
          {channels.map((channel, index) => (
            <Interactive.Div
              key={channel}
              name={channel}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 999,
                padding: "14px 22px",
                color: "#f7f3ea",
                fontSize: 30,
                fontWeight: 600,
                opacity: interpolate(frame, [8 + index * 4, 18 + index * 4], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
              }}
            >
              <div style={{ width: 12, height: 12, borderRadius: 12, background: "#32D74B" }} />
              {channel}
            </Interactive.Div>
          ))}
        </div>
        <Interactive.Div
          name="Always on"
          style={{
            marginTop: 56,
            fontSize: 64,
            fontWeight: 680,
            color: "#f7f3ea",
            opacity: interpolate(frame, [36, 52], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          24 hours. 7 days. Every channel.
        </Interactive.Div>
        <div style={{ marginTop: 28, color: "rgba(247,243,234,0.55)", fontSize: 22, maxWidth: 900 }}>
          Synthetic demonstration. Fictional names and figures. No customer deployment.
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const scenes = [
  { id: "open", duration: 96, Component: Open },
  { id: "imessage", duration: 150, Component: IMessage },
  { id: "whatsapp", duration: 140, Component: WhatsApp },
  { id: "telegram", duration: 140, Component: Telegram },
  { id: "signal", duration: 140, Component: Signal },
  { id: "slack", duration: 160, Component: Slack },
  { id: "email", duration: 170, Component: Mail },
  { id: "zoom", duration: 160, Component: Zoom },
  { id: "close", duration: 150, Component: Close },
];

export const FILM_DURATION = scenes.reduce((sum, scene) => sum + scene.duration, 0);
