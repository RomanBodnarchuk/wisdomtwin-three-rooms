import { CALENDLY_USER_TIMEZONE, CALENDLY_USER_URI, OWNER_EMAIL, OWNER_NAME } from "./campaigns.ts";
import { BookingService } from "./booking.ts";
import { CAMPAIGNS, CAMPAIGN_IDS } from "./campaigns.ts";
import { HttpCalendlyClient } from "./calendly.ts";
import { verifyOwnerTestContact } from "./contacts.ts";
import { OWNER_HUBSPOT_CONTACT_ID } from "./campaigns.ts";
import { redactSecrets } from "./errors.ts";
import { assertEventTypeUnchanged, type LiveEventType } from "./guard.ts";
import { runOwnerTest } from "./ownerTest.ts";
import { loadCalendlyToken } from "./token.ts";
import { utcToWall } from "./time.ts";

function iso(ms: number): string {
  return new Date(ms).toISOString().replace(/\.\d{3}Z$/, "Z");
}

function asLiveEventType(record: Record<string, unknown>): LiveEventType {
  return {
    uri: typeof record.uri === "string" ? record.uri : "",
    name: typeof record.name === "string" ? record.name : "",
    slug: typeof record.slug === "string" ? record.slug : "",
    active: record.active === true,
    duration: typeof record.duration === "number" ? record.duration : Number(record.duration),
    scheduling_url: typeof record.scheduling_url === "string" ? record.scheduling_url : "",
    locations: Array.isArray(record.locations)
      ? record.locations.map((location) => {
          const kind = location && typeof location === "object" && "kind" in location ? location.kind : undefined;
          return { kind: typeof kind === "string" ? kind : undefined };
        })
      : [],
  };
}

async function main(): Promise<void> {
  const command = process.argv[2] ?? "availability";
  const client = new HttpCalendlyClient(loadCalendlyToken());
  const user = await client.getCurrentUser();
  if (user.email.toLowerCase() !== OWNER_EMAIL || user.name !== OWNER_NAME || user.uri !== CALENDLY_USER_URI) {
    throw new Error("Calendly user does not match Roman Bodnarchuk.");
  }
  const service = new BookingService({ userUri: user.uri, client });

  if (command === "users-me") {
    console.log(JSON.stringify({
      name: user.name,
      email: user.email,
      uri: user.uri,
      timezone: user.timezone,
      slug: user.slug,
      schedulingUrl: user.schedulingUrl,
    }, null, 2));
    return;
  }

  const now = Date.now();
  const windowStart = iso(now + 2 * 60 * 60 * 1000);
  const windowEnd = iso(now + 2 * 24 * 60 * 60 * 1000);

  if (command === "availability") {
    const availability: Record<string, { count: number; firstToronto: string[] }> = {};
    for (const id of CAMPAIGN_IDS) {
      const live = asLiveEventType(await client.getEventType(CAMPAIGNS[id].eventTypeUri));
      assertEventTypeUnchanged(CAMPAIGNS[id], live);
      const slots = await service.availability(id, windowStart, windowEnd);
      availability[id] = {
        count: slots.length,
        firstToronto: slots.slice(0, 5).map((slot) => {
          const wall = utcToWall(slot, "America/Toronto");
          return `${wall.date} ${wall.time} America/Toronto`;
        }),
      };
    }
    console.log(JSON.stringify({
      user: { name: user.name, email: user.email, timezone: user.timezone, expectedTimezone: CALENDLY_USER_TIMEZONE },
      windowStart,
      windowEnd,
      availability,
    }, null, 2));
    return;
  }

  if (command === "owner-test") {
    if (!process.argv.includes("--book-owner-test")) {
      throw new Error("Refusing to book without --book-owner-test.");
    }
    for (const id of CAMPAIGN_IDS) {
      assertEventTypeUnchanged(CAMPAIGNS[id], asLiveEventType(await client.getEventType(CAMPAIGNS[id].eventTypeUri)));
    }
    const organization = user.currentOrganization
      ? await client.getOrganization(user.currentOrganization)
      : {};
    const contact = verifyOwnerTestContact({
      email: OWNER_EMAIL,
      name: OWNER_NAME,
      hubspotContactId: OWNER_HUBSPOT_CONTACT_ID,
    });
    const report = await runOwnerTest({ service, contact, windowStart, windowEnd, now });
    console.log(JSON.stringify({
      user: {
        name: user.name,
        email: user.email,
        uri: user.uri,
        timezone: user.timezone,
      },
      organization: {
        plan: organization.plan ?? null,
        stage: organization.stage ?? null,
        kind: organization.kind ?? null,
      },
      windowStart,
      windowEnd,
      report,
    }, null, 2));
    return;
  }

  throw new Error("Unknown command. Use users-me, availability, or owner-test.");
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : "Command failed.";
  console.error(redactSecrets(message));
  process.exitCode = 1;
});
