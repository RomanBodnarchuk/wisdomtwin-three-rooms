// Brand system for WisdomTwin social videos.
// Colors mirror the product site (near-black canvas, cream text, teal/gold/orange accents).

export const COLORS = {
  bg: "#0A0A0C",
  bgSoft: "#111318",
  cream: "#F7F3EA",
  creamDim: "#A8A29E",
  teal: "#4FD1C5",
  tealDeep: "#2C7A75",
  gold: "#C8A45D",
  orange: "#F37021",
  danger: "#F2544B",
  line: "rgba(255,255,255,0.10)",
  card: "rgba(255,255,255,0.04)",
} as const;

export const CALENDLY_URL = "calendly.com/romanbodnarchuk/20min";

// Vertical social canvas (9:16) used across all platforms.
export const VIDEO = {
  width: 1080,
  height: 1920,
  fps: 30,
} as const;

// Comfortable safe-area padding for text.
export const SAFE_X = 96;
