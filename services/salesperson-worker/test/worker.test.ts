import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

import { BookingService, type BookInput } from "../src/booking.ts";
import {
  CALENDLY_USER_URI,
  CAMPAIGNS,
  OWNER_EMAIL,
  OWNER_HUBSPOT_CONTACT_ID,
  OWNER_NAME,
} from "../src/campaigns.ts";
import {
  HttpCalendlyClient,
  type CalendlyClient,
  type CreateInviteeInput,
  type CreatedInvitee,
  type InviteeRecord,
  type ListEventsQuery,
  type ScheduledEvent,
} from "../src/calendly.ts";
import { verifyOwnerTestContact } from "../src/contacts.ts";
import {
  CampaignIsolationError,
  ProspectBookingBlockedError,
  ReconciliationRequiredError,
  redactSecrets,
  CalendlyTimeoutError,
} from "../src/errors.ts";
import { resolveEventType } from "../src/guard.ts";
import { runOwnerTest } from "../src/ownerTest.ts";
import { loadCalendlyToken } from "../src/token.ts";
import { utcToWall, wallTimeToUtc } from "../src/time.ts";

const NOW = Date.parse("2026-10-06T17:00:00Z");
const WINDOW_START = "2026-10-06T19:00:00Z";
const WINDOW_END = "2026-10-08T17:00:00Z";
const WT_SLOT = "2026-10-07T17:45:00Z";
const N5R_SLOT = "2026-10-07T11:00:00Z";

function contact() {
  return verifyOwnerTestContact({
    email: OWNER_EMAIL,
    name: OWNER_NAME,
    hubspotContactId: OWNER_HUBSPOT_CONTACT_ID,
  });
}

function confirmation(startTime: string, overrides: Partial<BookInput["confirmation"]> = {}): BookInput["confirmation"] {
  const wall = utcToWall(startTime, "America/Toronto");
  return {
    name: OWNER_NAME,
    email: OWNER_EMAIL,
    date: wall.date,
    time: wall.time,
    timezone: "America/Toronto",
    confirmed: true,
    ...overrides,
  };
}

class FakeCalendly implements CalendlyClient {
  creates = 0;
  cancelCalls: string[] = [];
  events: ScheduledEvent[] = [];
  invitees = new Map<string, InviteeRecord[]>();
  available: Record<string, string[]>;
  createMode: "ok" | "timeout" | "create-then-timeout" = "ok";
  releaseCreate: (() => void) | null = null;
  private createGate: Promise<void> | null = null;

  constructor() {
    this.available = {
      [CAMPAIGNS.wisdomtwin.eventTypeUri]: [WT_SLOT],
      [CAMPAIGNS.n5r.eventTypeUri]: [N5R_SLOT],
    };
  }

  holdCreates(): void {
    this.createGate = new Promise((resolve) => {
      this.releaseCreate = resolve;
    });
  }

  async getCurrentUser() {
    throw new Error("not used");
  }

  async getOrganization() {
    throw new Error("not used");
  }

  async getEventType() {
    throw new Error("not used");
  }

  async listAvailableTimes(eventTypeUri: string, startTime: string, endTime: string): Promise<string[]> {
    const start = Date.parse(startTime);
    const end = Date.parse(endTime);
    return (this.available[eventTypeUri] ?? []).filter((slot) => {
      const time = Date.parse(slot);
      return time >= start && time < end;
    });
  }

  async listScheduledEvents(query: ListEventsQuery): Promise<ScheduledEvent[]> {
    if (query.inviteeEmail !== OWNER_EMAIL) {
      throw new Error("list was called with an unexpected email");
    }
    const min = Date.parse(query.minStartTime);
    const max = Date.parse(query.maxStartTime);
    return this.events.filter((event) => {
      const time = Date.parse(event.startTime);
      return event.status === query.status && time >= min && time <= max;
    });
  }

  async getScheduledEvent(eventUri: string): Promise<ScheduledEvent> {
    const event = this.events.find((item) => item.uri === eventUri);
    if (!event) throw new Error("missing event");
    return event;
  }

  async listInvitees(eventUri: string): Promise<InviteeRecord[]> {
    return this.invitees.get(eventUri) ?? [];
  }

  async createInvitee(input: CreateInviteeInput): Promise<CreatedInvitee> {
    this.creates += 1;
    if (this.createGate) await this.createGate;
    if (this.createMode === "timeout") throw new CalendlyTimeoutError();
    const uri = `https://api.calendly.com/scheduled_events/evt-${this.creates}`;
    this.events.push({
      uri,
      eventType: input.eventTypeUri,
      startTime: input.startTime,
      endTime: input.startTime,
      status: "active",
      name: input.name,
    });
    this.invitees.set(uri, [{
      uri: `${uri}/invitees/1`,
      email: input.email,
      name: input.name,
      status: "active",
      timezone: input.timezone,
    }]);
    this.available[input.eventTypeUri] = (this.available[input.eventTypeUri] ?? []).filter(
      (slot) => Date.parse(slot) !== Date.parse(input.startTime),
    );
    if (this.createMode === "create-then-timeout") throw new CalendlyTimeoutError();
    return {
      eventUri: uri,
      inviteeUri: `${uri}/invitees/1`,
      status: "active",
      email: input.email,
      timezone: input.timezone,
    };
  }

  async cancelEvent(eventUri: string): Promise<void> {
    this.cancelCalls.push(eventUri);
    const event = this.events.find((item) => item.uri === eventUri);
    if (event) event.status = "canceled";
  }
}

function service(fake = new FakeCalendly()): { fake: FakeCalendly; service: BookingService } {
  return {
    fake,
    service: new BookingService({ userUri: CALENDLY_USER_URI, client: fake, now: () => NOW }),
  };
}

test("converts the WisdomTwin sample slot into America/Toronto", () => {
  assert.deepEqual(utcToWall(WT_SLOT, "America/Toronto"), { date: "2026-10-07", time: "13:45" });
  assert.equal(wallTimeToUtc("2026-10-07", "13:45", "America/Toronto"), WT_SLOT);
  assert.equal(wallTimeToUtc("2026-10-07", "07:00", "America/Toronto"), N5R_SLOT);
});

test("WisdomTwin guard rejects the N5R event type and the reverse", () => {
  assert.equal(
    resolveEventType("wisdomtwin", CAMPAIGNS.wisdomtwin.eventTypeUri).eventTypeUri,
    CAMPAIGNS.wisdomtwin.eventTypeUri,
  );
  assert.throws(
    () => resolveEventType("wisdomtwin", CAMPAIGNS.n5r.eventTypeUri),
    CampaignIsolationError,
  );
  assert.throws(
    () => resolveEventType("n5r", CAMPAIGNS.wisdomtwin.eventTypeUri),
    CampaignIsolationError,
  );
});

test("a self-asserted email cannot become a verified contact", () => {
  assert.throws(
    () => verifyOwnerTestContact({
      email: "someoneelse@example.com",
      name: OWNER_NAME,
      hubspotContactId: OWNER_HUBSPOT_CONTACT_ID,
    }),
    ProspectBookingBlockedError,
  );
  assert.throws(
    () => verifyOwnerTestContact({
      email: OWNER_EMAIL,
      name: OWNER_NAME,
      hubspotContactId: "223451166888",
    }),
  );
});

test("booking rejects the other event type, an unconfirmed request, and a non-owner email", async () => {
  const { fake, service: bookings } = service();
  const owner = contact();
  await assert.rejects(
    bookings.book({
      campaign: "wisdomtwin",
      contact: owner,
      confirmation: confirmation(WT_SLOT),
      requestedEventTypeUri: CAMPAIGNS.n5r.eventTypeUri,
    }),
    CampaignIsolationError,
  );
  await assert.rejects(
    bookings.book({
      campaign: "n5r",
      contact: owner,
      confirmation: confirmation(N5R_SLOT),
      requestedEventTypeUri: CAMPAIGNS.wisdomtwin.eventTypeUri,
    }),
    CampaignIsolationError,
  );
  await assert.rejects(
    bookings.book({
      campaign: "wisdomtwin",
      contact: owner,
      confirmation: confirmation(WT_SLOT, { confirmed: false }),
    }),
  );
  await assert.rejects(
    bookings.list(
      "wisdomtwin",
      { email: "someoneelse@example.com", name: "Someone Else", hubspotContactId: "1", verification: "owner-test" },
      WINDOW_START,
      WINDOW_END,
    ),
    ProspectBookingBlockedError,
  );
  assert.equal(fake.creates, 0);
  assert.equal(fake.cancelCalls.length, 0);
});

test("duplicate and concurrent booking requests create one appointment", async () => {
  const fake = new FakeCalendly();
  fake.holdCreates();
  const bookings = new BookingService({ userUri: CALENDLY_USER_URI, client: fake, now: () => NOW });
  const input: BookInput = {
    campaign: "wisdomtwin",
    contact: contact(),
    confirmation: confirmation(WT_SLOT),
  };
  const first = bookings.book(input);
  const second = bookings.book(input);
  await new Promise((resolve) => setTimeout(resolve, 10));
  assert.equal(fake.creates, 1);
  fake.releaseCreate?.();
  const [booked, duplicate] = await Promise.all([first, second]);
  assert.equal(booked.outcome, "booked");
  assert.equal(duplicate.eventUri, booked.eventUri);
  const third = await bookings.book(input);
  assert.equal(third.outcome, "already_booked");
  assert.equal(third.eventUri, booked.eventUri);
  assert.equal(fake.creates, 1);
});

test("a timed out create is reconciled and is not posted twice", async () => {
  const created = new FakeCalendly();
  created.createMode = "create-then-timeout";
  const bookings = new BookingService({ userUri: CALENDLY_USER_URI, client: created, now: () => NOW });
  const input: BookInput = {
    campaign: "wisdomtwin",
    contact: contact(),
    confirmation: confirmation(WT_SLOT),
  };
  const result = await bookings.book(input);
  assert.equal(result.outcome, "already_booked");
  assert.equal(created.creates, 1);
  const again = await bookings.book(input);
  assert.equal(again.eventUri, result.eventUri);
  assert.equal(created.creates, 1);

  const missing = new FakeCalendly();
  missing.createMode = "timeout";
  const retry = new BookingService({ userUri: CALENDLY_USER_URI, client: missing, now: () => NOW });
  await assert.rejects(retry.book(input), ReconciliationRequiredError);
  assert.equal(missing.creates, 1);
});

test("campaign lists and cancels stay inside the permitted event type", async () => {
  const { fake, service: bookings } = service();
  const owner = contact();
  const wisdomtwin = await bookings.book({
    campaign: "wisdomtwin",
    contact: owner,
    confirmation: confirmation(WT_SLOT),
  });
  const n5r = await bookings.book({
    campaign: "n5r",
    contact: owner,
    confirmation: confirmation(N5R_SLOT),
  });
  const wisdomtwinList = await bookings.list("wisdomtwin", owner, WINDOW_START, WINDOW_END);
  const n5rList = await bookings.list("n5r", owner, WINDOW_START, WINDOW_END);
  assert.deepEqual(wisdomtwinList.map((event) => event.uri), [wisdomtwin.eventUri]);
  assert.deepEqual(n5rList.map((event) => event.uri), [n5r.eventUri]);
  await assert.rejects(
    bookings.cancel("wisdomtwin", owner, n5r.eventUri, "Owner test cleanup"),
    CampaignIsolationError,
  );
  await assert.rejects(
    bookings.cancel("n5r", owner, wisdomtwin.eventUri, "Owner test cleanup"),
    CampaignIsolationError,
  );
  assert.equal(fake.cancelCalls.length, 0);
  await bookings.cancel("wisdomtwin", owner, wisdomtwin.eventUri, "Owner test cleanup");
  assert.deepEqual(fake.cancelCalls, [wisdomtwin.eventUri]);
});

test("owner test books one slot per company, rejects the cross cancel, and cleans up", async () => {
  const { fake, service: bookings } = service();
  const report = await runOwnerTest({
    service: bookings,
    contact: contact(),
    windowStart: WINDOW_START,
    windowEnd: WINDOW_END,
    now: NOW,
  });
  assert.equal(report.isolation.wisdomtwinRejectedN5r, true);
  assert.equal(report.isolation.n5rRejectedWisdomtwin, true);
  assert.equal(report.isolation.wisdomtwinCrossCancelRejected, true);
  assert.equal(report.isolation.n5rCrossCancelRejected, true);
  assert.equal(report.duplicate.matchedFirst, true);
  assert.equal(report.duplicate.outcome, "already_booked");
  assert.equal(fake.creates, 2);
  assert.equal(report.listsAfterCancel.wisdomtwin.length, 0);
  assert.equal(report.listsAfterCancel.n5r.length, 0);
  assert.equal(report.booked[0]?.toronto, "2026-10-07 13:45");
  assert.equal(report.booked[1]?.toronto, "2026-10-07 07:00");
});

test("token loader reads only the supplied env or file and redacts credential shapes", () => {
  assert.equal(loadCalendlyToken({ CALENDLY_API_TOKEN: "local-test-value" }), "local-test-value");
  assert.equal(
    loadCalendlyToken({ CALENDLY_TOKEN_FILE: "/tmp/does-not-matter" }, () => "  file-token \n"),
    "file-token",
  );
  assert.throws(() => loadCalendlyToken({}, () => {
    throw new Error("missing");
  }));
  const redacted = redactSecrets("Bearer local-test-value eyJhbGciOiJub25lIn0.eyJ0ZXN0IjoxfQ.sig");
  assert.equal(redacted.includes("local-test-value"), false);
  assert.equal(redacted.includes("eyJhbGci"), false);
});

test("http client sends the token as a bearer header and does not log it", async () => {
  const seen: string[] = [];
  const fetchImpl: typeof fetch = async (_input, init) => {
    seen.push(new Headers(init?.headers).get("authorization") ?? "");
    return new Response(JSON.stringify({
      resource: {
        uri: CALENDLY_USER_URI,
        name: OWNER_NAME,
        email: OWNER_EMAIL,
        timezone: "America/New_York",
        scheduling_url: "https://calendly.com/romanbodnarchuk",
        slug: "romanbodnarchuk",
        current_organization: "https://api.calendly.com/organizations/example",
      },
    }), { status: 200 });
  };
  const client = new HttpCalendlyClient("local-test-value", fetchImpl);
  const user = await client.getCurrentUser();
  assert.equal(user.email, OWNER_EMAIL);
  assert.deepEqual(seen, ["Bearer local-test-value"]);
});

test("worker source does not contain a personal access token", () => {
  const root = join(import.meta.dirname, "..");
  const jwt = /eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}/;
  const files: string[] = [];
  const walk = (dir: string) => {
    for (const name of readdirSync(dir)) {
      if (name === "node_modules") continue;
      const path = join(dir, name);
      if (statSync(path).isDirectory()) walk(path);
      else files.push(path);
    }
  };
  walk(root);
  for (const path of files) {
    const text = readFileSync(path, "utf8");
    assert.equal(jwt.test(text), false, path);
  }
});
