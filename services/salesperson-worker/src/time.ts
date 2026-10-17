import { ConfirmationRequiredError } from "./errors.ts";

const DATE_RE = /^(\d{4})-(\d{2})-(\d{2})$/;
const TIME_RE = /^([01]\d|2[0-3]):([0-5]\d)$/;

export function assertIanaTimeZone(timeZone: string): void {
  try {
    new Intl.DateTimeFormat("en-US", { timeZone }).format(0);
  } catch {
    throw new ConfirmationRequiredError("Timezone must be an IANA name such as America/Toronto.");
  }
}

interface WallParts {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
}

function wallParts(instant: Date, timeZone: string): WallParts {
  const fmt = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hourCycle: "h23",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const bag: Record<string, string> = {};
  for (const part of fmt.formatToParts(instant)) {
    if (part.type !== "literal") bag[part.type] = part.value;
  }
  let hour = Number(bag.hour);
  if (hour === 24) hour = 0;
  return {
    year: Number(bag.year),
    month: Number(bag.month),
    day: Number(bag.day),
    hour,
    minute: Number(bag.minute),
  };
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

export function utcToWall(isoUtc: string, timeZone: string): { date: string; time: string } {
  assertIanaTimeZone(timeZone);
  const instant = new Date(isoUtc);
  if (Number.isNaN(instant.getTime())) {
    throw new ConfirmationRequiredError("Start time is not a valid UTC timestamp.");
  }
  const parts = wallParts(instant, timeZone);
  return {
    date: `${parts.year}-${pad(parts.month)}-${pad(parts.day)}`,
    time: `${pad(parts.hour)}:${pad(parts.minute)}`,
  };
}

export function wallTimeToUtc(date: string, time: string, timeZone: string): string {
  assertIanaTimeZone(timeZone);
  const dateMatch = DATE_RE.exec(date);
  const timeMatch = TIME_RE.exec(time);
  if (!dateMatch || !timeMatch) {
    throw new ConfirmationRequiredError("Date must be YYYY-MM-DD and time must be HH:mm.");
  }
  const year = Number(dateMatch[1]);
  const month = Number(dateMatch[2]);
  const day = Number(dateMatch[3]);
  const hour = Number(timeMatch[1]);
  const minute = Number(timeMatch[2]);
  const desired = Date.UTC(year, month - 1, day, hour, minute, 0);
  let utc = desired;
  for (let attempt = 0; attempt < 4; attempt += 1) {
    const parts = wallParts(new Date(utc), timeZone);
    const asUtc = Date.UTC(parts.year, parts.month - 1, parts.day, parts.hour, parts.minute, 0);
    const diff = asUtc - desired;
    if (diff === 0) break;
    utc -= diff;
  }
  const check = wallParts(new Date(utc), timeZone);
  if (
    check.year !== year ||
    check.month !== month ||
    check.day !== day ||
    check.hour !== hour ||
    check.minute !== minute
  ) {
    throw new ConfirmationRequiredError("That date and time do not exist in the given timezone.");
  }
  return new Date(utc).toISOString().replace(".000Z", "Z");
}

export function sameInstant(left: string, right: string): boolean {
  const a = Date.parse(left);
  const b = Date.parse(right);
  return !Number.isNaN(a) && a === b;
}

export function overlaps(startA: string, startB: string, durationMinutes: number): boolean {
  const a = Date.parse(startA);
  const b = Date.parse(startB);
  const duration = durationMinutes * 60_000;
  return a < b + duration && b < a + duration;
}
