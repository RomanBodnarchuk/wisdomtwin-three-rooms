import { loadFont as loadArchivo } from "@remotion/google-fonts/Archivo";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";

// Display face for headlines, body face for supporting copy.
export const display = loadArchivo("normal", {
  weights: ["800", "900"],
}).fontFamily;

export const body = loadInter("normal", {
  weights: ["400", "500", "600", "700"],
}).fontFamily;
