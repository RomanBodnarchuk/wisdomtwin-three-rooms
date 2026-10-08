import { CAMPAIGN_IDS, OWNER_TIMEZONE, type CampaignId } from "./campaigns.ts";
import type { CalendlyClient, CreateInviteeInput, ScheduledEvent } from "./calendly.ts";
import { assertVerifiedContact, type VerifiedContact } from "./contacts.ts";
import {
  AmbiguousBookingsError,
  CalendlyHttpError,
  CalendlyTimeoutError,
  CalendlyUncertainError,
  CampaignIsolationError,
  ConfirmationRequiredError,
  ReconciliationRequiredError,
  SlotUnavailableError,
  WorkerError,
} from "./errors.ts";
import { resolveEventType } from "./guard.ts";
import { sameInstant, wallTimeToUtc } from "./time.ts";

export interface Confirmation {
  name: string;
  email: string;
  date: string;
  time: string;
  timezone: string;
  confirmed: boolean;
}

export interface BookInput {
  campaign: CampaignId;
  contact: VerifiedContact;
  confirmation: Confirmation;
  requestedEventTypeUri?: string;
}

export interface BookResult {
  outcome: "booked" | "already_booked";
  eventUri: string;
  startTime: string;
  inviteeEmail: string;
  campaign: CampaignId;
}

const THIRTY_ONE_DAYS_MS = 31 * 24 * 60 * 60 * 1000;

export class BookingService {
  private readonly inflight = new Map<string, Promise<BookResult>>();
  private readonly options: {
    userUri: string;
    client: CalendlyClient;
    now?: () => number;
  };

  constructor(options: {
    userUri: string;
    client: CalendlyClient;
    now?: () => number;
  }) {
    this.options = options;
  }

  availability(
    campaignId: CampaignId,
    startTime: string,
    endTime: string,
    requestedEventTypeUri?: string,
  ): Promise<string[]> {
    const campaign = resolveEventType(campaignId, requestedEventTypeUri);
    const start = Date.parse(startTime);
    const end = Date.parse(endTime);
    if (Number.isNaN(start) || Number.isNaN(end) || end <= start || end - start > THIRTY_ONE_DAYS_MS) {
      throw new WorkerError("confirmation_required", "Availability window must be within 31 days.");
    }
    return this.options.client.listAvailableTimes(campaign.eventTypeUri, startTime, endTime);
  }

  async list(
    campaignId: CampaignId,
    contact: VerifiedContact,
    minStartTime: string,
    maxStartTime: string,
    requestedEventTypeUri?: string,
  ): Promise<ScheduledEvent[]> {
    const campaign = resolveEventType(campaignId, requestedEventTypeUri);
    const verified = assertVerifiedContact(contact);
    const events = await this.options.client.listScheduledEvents({
      user: this.options.userUri,
      inviteeEmail: verified.email,
      status: "active",
      minStartTime,
      maxStartTime,
    });
    return events.filter((event) => event.eventType === campaign.eventTypeUri && event.status === "active");
  }

  book(input: BookInput): Promise<BookResult> {
    let startTime: string;
    try {
      startTime = this.validateBooking(input);
    } catch (error) {
      return Promise.reject(error);
    }
    const verified = assertVerifiedContact(input.contact);
    const key = `${input.campaign}|${verified.email}|${startTime}`;
    const existing = this.inflight.get(key);
    if (existing) return existing;
    const promise = this.bookOnce(input, startTime).finally(() => {
      if (this.inflight.get(key) === promise) this.inflight.delete(key);
    });
    this.inflight.set(key, promise);
    return promise;
  }

  async cancel(
    campaignId: CampaignId,
    contact: VerifiedContact,
    eventUri: string,
    reason: string,
    requestedEventTypeUri?: string,
  ): Promise<void> {
    const campaign = resolveEventType(campaignId, requestedEventTypeUri);
    const verified = assertVerifiedContact(contact);
    const event = await this.options.client.getScheduledEvent(eventUri);
    if (event.eventType !== campaign.eventTypeUri) {
      throw new CampaignIsolationError(`${campaign.label} cannot cancel the other company's appointment.`);
    }
    if (event.status === "canceled") return;
    const invitees = await this.options.client.listInvitees(eventUri);
    const active = invitees.filter((invitee) => invitee.status === "active");
    if (
      active.length === 0 ||
      active.some((invitee) => invitee.email.trim().toLowerCase() !== verified.email)
    ) {
      throw new WorkerError(
        "unverified_contact",
        "This appointment is not held only by the verified contact, so it was not canceled.",
      );
    }
    await this.options.client.cancelEvent(eventUri, reason);
  }

  private validateBooking(input: BookInput): string {
    if (!CAMPAIGN_IDS.includes(input.campaign)) {
      throw new CampaignIsolationError("Unknown campaign.");
    }
    resolveEventType(input.campaign, input.requestedEventTypeUri);
    const contact = assertVerifiedContact(input.contact);
    const confirmation = input.confirmation;
    if (
      confirmation.confirmed !== true ||
      !confirmation.name ||
      !confirmation.email ||
      !confirmation.date ||
      !confirmation.time ||
      !confirmation.timezone
    ) {
      throw new ConfirmationRequiredError();
    }
    if (confirmation.email.trim().toLowerCase() !== contact.email || confirmation.name.trim() !== contact.name) {
      throw new ConfirmationRequiredError("The confirmed name and email must match the verified contact.");
    }
    if (confirmation.timezone !== OWNER_TIMEZONE) {
      throw new ConfirmationRequiredError("The owner test invitee timezone must be America/Toronto.");
    }
    return wallTimeToUtc(confirmation.date, confirmation.time, confirmation.timezone);
  }

  private async bookOnce(input: BookInput, startTime: string): Promise<BookResult> {
    const campaign = resolveEventType(input.campaign, input.requestedEventTypeUri);
    const contact = assertVerifiedContact(input.contact);
    const now = this.options.now?.() ?? Date.now();
    if (Date.parse(startTime) < now + 60_000) {
      throw new SlotUnavailableError("Choose a slot at least one minute in the future.");
    }
    const window = availabilityWindow(startTime, now);
    const open = await this.options.client.listAvailableTimes(campaign.eventTypeUri, window.start, window.end);
    if (!open.some((slot) => sameInstant(slot, startTime))) {
      const existing = await this.findExact(campaign.eventTypeUri, contact, startTime);
      if (existing.length === 1) return this.fromEvent("already_booked", input.campaign, contact.email, existing[0]);
      throw new SlotUnavailableError();
    }
    const existing = await this.findExact(campaign.eventTypeUri, contact, startTime);
    if (existing.length === 1) return this.fromEvent("already_booked", input.campaign, contact.email, existing[0]);
    if (existing.length > 1) throw new AmbiguousBookingsError();

    const payload: CreateInviteeInput = {
      eventTypeUri: campaign.eventTypeUri,
      startTime,
      name: contact.name,
      email: contact.email,
      timezone: input.confirmation.timezone,
      locationKind: campaign.locationKind,
    };
    try {
      const created = await this.options.client.createInvitee(payload);
      if (created.email.trim().toLowerCase() !== contact.email || created.status !== "active") {
        throw new CalendlyUncertainError(201, "Calendly confirmed a booking that does not match the verified contact.");
      }
      return {
        outcome: "booked",
        eventUri: created.eventUri,
        startTime,
        inviteeEmail: contact.email,
        campaign: input.campaign,
      };
    } catch (error) {
      if (
        error instanceof CalendlyTimeoutError ||
        error instanceof CalendlyUncertainError ||
        (error instanceof CalendlyHttpError && (error.status === 400 || error.status === 404 || error.status === 409))
      ) {
        const found = await this.findExact(campaign.eventTypeUri, contact, startTime);
        if (found.length === 1) return this.fromEvent("already_booked", input.campaign, contact.email, found[0]);
        if (found.length > 1) throw new AmbiguousBookingsError();
        if (error instanceof CalendlyTimeoutError || error instanceof CalendlyUncertainError) {
          throw new ReconciliationRequiredError();
        }
      }
      throw error;
    }
  }

  private async findExact(
    eventTypeUri: string,
    contact: VerifiedContact,
    startTime: string,
  ): Promise<ScheduledEvent[]> {
    const startMs = Date.parse(startTime);
    const events = await this.options.client.listScheduledEvents({
      user: this.options.userUri,
      inviteeEmail: contact.email,
      status: "active",
      minStartTime: new Date(startMs - 60_000).toISOString(),
      maxStartTime: new Date(startMs + 60_000).toISOString(),
    });
    return events.filter(
      (event) => event.eventType === eventTypeUri && event.status === "active" && sameInstant(event.startTime, startTime),
    );
  }

  private fromEvent(
    outcome: BookResult["outcome"],
    campaign: CampaignId,
    inviteeEmail: string,
    event: ScheduledEvent,
  ): BookResult {
    return {
      outcome,
      eventUri: event.uri,
      startTime: event.startTime,
      inviteeEmail,
      campaign,
    };
  }
}

function availabilityWindow(startTime: string, now: number): { start: string; end: string } {
  const slot = Date.parse(startTime);
  const start = Math.max(now + 5_000, slot - 60 * 60_000);
  if (start > slot) {
    throw new SlotUnavailableError("That time is no longer available.");
  }
  const end = slot + 60 * 60_000;
  return {
    start: new Date(start).toISOString().replace(".000Z", "Z"),
    end: new Date(end).toISOString().replace(".000Z", "Z"),
  };
}
