import { readFileSync } from "node:fs";

const DEFAULT_TOKEN_FILE = "/home/ubuntu/.config/calendly.pat";

export interface TokenEnv {
  CALENDLY_API_TOKEN?: string;
  CALENDLY_TOKEN_FILE?: string;
}

/**
 * Load the Calendly personal access token from the environment or from a
 * mode-600 file outside the repository. The token is returned to the caller
 * and must be sent only as an Authorization header.
 */
export function loadCalendlyToken(
  env: TokenEnv = process.env,
  readFile: (path: string) => string = (path) => readFileSync(path, "utf8"),
): string {
  const fromEnv = env.CALENDLY_API_TOKEN?.trim();
  if (fromEnv) return fromEnv;
  const filePath = env.CALENDLY_TOKEN_FILE?.trim() || DEFAULT_TOKEN_FILE;
  let raw: string;
  try {
    raw = readFile(filePath);
  } catch {
    throw new Error("Calendly token is not configured. Set CALENDLY_API_TOKEN or CALENDLY_TOKEN_FILE.");
  }
  const token = raw.trim();
  if (!token) {
    throw new Error("Calendly token is not configured. Set CALENDLY_API_TOKEN or CALENDLY_TOKEN_FILE.");
  }
  return token;
}
