import { CAMPAIGNS, type CampaignId } from "./campaigns.ts";
import type { BookingService, BookResult, Confirmation } from "./booking.ts";
import type { VerifiedContact } from "./contacts.ts";
import { CampaignIsolationError, SlotUnavailableError, WorkerError } from "./errors.ts";
import { otherCampaign } from "./campaigns.ts";
import { overlaps, utcToWall } from "./time.ts";

export interface OwnerTestReport {
  isolation: {
    wisdomtwinRejectedN5r: boolean;
    n5rRejectedWisdomtwin: boolean;
    wisdomtwinCrossCancelRejected: boolean;
    n5rCrossCancelRejected: boolean;
  };
  availabilityCounts: Record<CampaignId, number>;
  booked: Array<{
    campaign: CampaignId;
    outcome: BookResult["outcome"];
    eventUri: string;
    startTime: string;
    toronto: string;
  }>;
  duplicate: {
    outcome: BookResult["outcome"];
    eventUri: string;
    matchedFirst: boolean;
  };
  listsBeforeCancel: Record<CampaignId, string[]>;
  canceled: string[];
  listsAfterCancel: Record<CampaignId, string[]>;
}

export function selectOwnerTestSlots(
  wisdomtwin: string[],
  n5r: string[],
  now: number,
): { wisdomtwin: string; n5r: string } {
  const earliest = now + 2 * 60 * 60 * 1000;
  const first = wisdomtwin.filter((slot) => Date.parse(slot) >= earliest).sort();
  const second = n5r.filter((slot) => Date.parse(slot) >= earliest).sort();
  for (const wisdomtwinSlot of first) {
    for (const n5rSlot of second) {
      if (!overlaps(wisdomtwinSlot, n5rSlot, 15)) {
        return { wisdomtwin: wisdomtwinSlot, n5r: n5rSlot };
      }
    }
  }
  throw new SlotUnavailableError("No non-overlapping owner-test slots were open.");
}

function confirmationFor(contact: VerifiedContact, startTime: string): Confirmation {
  const wall = utcToWall(startTime, "America/Toronto");
  return {
    name: contact.name,
    email: contact.email,
    date: wall.date,
    time: wall.time,
    timezone: "America/Toronto",
    confirmed: true,
  };
}

async function rejectsOtherEventType(
  service: BookingService,
  campaign: CampaignId,
  windowStart: string,
  windowEnd: string,
): Promise<boolean> {
  try {
    await service.availability(
      campaign,
      windowStart,
      windowEnd,
      CAMPAIGNS[otherCampaign(campaign)].eventTypeUri,
    );
    return false;
  } catch (error) {
    return error instanceof CampaignIsolationError;
  }
}

export async function runOwnerTest(input: {
  service: BookingService;
  contact: VerifiedContact;
  windowStart: string;
  windowEnd: string;
  now: number;
}): Promise<OwnerTestReport> {
  const { service, contact, windowStart, windowEnd, now } = input;
  const isolation = {
    wisdomtwinRejectedN5r: await rejectsOtherEventType(service, "wisdomtwin", windowStart, windowEnd),
    n5rRejectedWisdomtwin: await rejectsOtherEventType(service, "n5r", windowStart, windowEnd),
    wisdomtwinCrossCancelRejected: false,
    n5rCrossCancelRejected: false,
  };
  if (!isolation.wisdomtwinRejectedN5r || !isolation.n5rRejectedWisdomtwin) {
    throw new CampaignIsolationError("Event type isolation did not reject the other company.");
  }

  const wisdomtwinSlots = await service.availability("wisdomtwin", windowStart, windowEnd);
  const n5rSlots = await service.availability("n5r", windowStart, windowEnd);
  const chosen = selectOwnerTestSlots(wisdomtwinSlots, n5rSlots, now);
  const created: Array<{ campaign: CampaignId; eventUri: string }> = [];
  const booked: OwnerTestReport["booked"] = [];

  const bookCampaign = async (campaign: CampaignId, startTime: string): Promise<BookResult> => {
    const result = await service.book({
      campaign,
      contact,
      confirmation: confirmationFor(contact, startTime),
    });
    if (!created.some((item) => item.eventUri === result.eventUri)) {
      created.push({ campaign, eventUri: result.eventUri });
    }
    return result;
  };

  try {
    const first = await bookCampaign("wisdomtwin", chosen.wisdomtwin);
    const duplicate = await bookCampaign("wisdomtwin", chosen.wisdomtwin);
    const second = await bookCampaign("n5r", chosen.n5r);
    for (const result of [first, second]) {
      const wall = utcToWall(result.startTime, "America/Toronto");
      booked.push({
        campaign: result.campaign,
        outcome: result.outcome,
        eventUri: result.eventUri,
        startTime: result.startTime,
        toronto: `${wall.date} ${wall.time}`,
      });
    }
    if (duplicate.eventUri !== first.eventUri) {
      throw new WorkerError("ambiguous_bookings", "A duplicate booking request created a second appointment.");
    }

    const listsBeforeCancel = {
      wisdomtwin: (await service.list("wisdomtwin", contact, windowStart, windowEnd)).map((event) => event.uri),
      n5r: (await service.list("n5r", contact, windowStart, windowEnd)).map((event) => event.uri),
    };
    if (listsBeforeCancel.wisdomtwin.includes(second.eventUri) || listsBeforeCancel.n5r.includes(first.eventUri)) {
      throw new CampaignIsolationError("A campaign list included the other company's appointment.");
    }
    if (!listsBeforeCancel.wisdomtwin.includes(first.eventUri) || !listsBeforeCancel.n5r.includes(second.eventUri)) {
      throw new WorkerError("reconciliation_required", "The booked appointment was missing from the campaign list.");
    }

    try {
      await service.cancel("wisdomtwin", contact, second.eventUri, "Owner test cleanup");
    } catch (error) {
      isolation.wisdomtwinCrossCancelRejected = error instanceof CampaignIsolationError;
    }
    if (!isolation.wisdomtwinCrossCancelRejected) {
      throw new CampaignIsolationError("WisdomTwin was able to cancel the N5R appointment.");
    }
    try {
      await service.cancel("n5r", contact, first.eventUri, "Owner test cleanup");
    } catch (error) {
      isolation.n5rCrossCancelRejected = error instanceof CampaignIsolationError;
    }
    if (!isolation.n5rCrossCancelRejected) {
      throw new CampaignIsolationError("N5R was able to cancel the WisdomTwin appointment.");
    }

    const canceled: string[] = [];
    for (const item of created) {
      await service.cancel(item.campaign, contact, item.eventUri, "Owner test cleanup");
      canceled.push(item.eventUri);
    }
    const listsAfterCancel = {
      wisdomtwin: (await service.list("wisdomtwin", contact, windowStart, windowEnd)).map((event) => event.uri),
      n5r: (await service.list("n5r", contact, windowStart, windowEnd)).map((event) => event.uri),
    };
    return {
      isolation,
      availabilityCounts: { wisdomtwin: wisdomtwinSlots.length, n5r: n5rSlots.length },
      booked,
      duplicate: {
        outcome: duplicate.outcome,
        eventUri: duplicate.eventUri,
        matchedFirst: duplicate.eventUri === first.eventUri,
      },
      listsBeforeCancel,
      canceled,
      listsAfterCancel,
    };
  } finally {
    for (const item of created) {
      try {
        const stillThere = (await service.list(item.campaign, contact, windowStart, windowEnd)).some(
          (event) => event.uri === item.eventUri,
        );
        if (stillThere) {
          await service.cancel(item.campaign, contact, item.eventUri, "Owner test cleanup");
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : "cleanup failed";
        console.error(`Owner-test cleanup failed for ${item.eventUri}: ${message}`);
      }
    }
  }
}
