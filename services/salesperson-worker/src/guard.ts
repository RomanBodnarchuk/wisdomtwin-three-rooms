import { CAMPAIGNS, type Campaign, type CampaignId } from "./campaigns.ts";
import { CampaignIsolationError, EventTypeDriftError } from "./errors.ts";

export interface LiveEventType {
  uri?: string;
  name?: string;
  slug?: string;
  active?: boolean;
  duration?: number;
  scheduling_url?: string;
  locations?: Array<{ kind?: string }>;
}

export function getCampaign(id: string): Campaign {
  if (id !== "wisdomtwin" && id !== "n5r") {
    throw new CampaignIsolationError("Unknown campaign.");
  }
  return CAMPAIGNS[id];
}

/**
 * Server-side event-type isolation. A campaign may use only its own event type.
 * Prompt text is not consulted.
 */
export function resolveEventType(campaignId: CampaignId, requestedEventTypeUri?: string): Campaign {
  const campaign = getCampaign(campaignId);
  if (requestedEventTypeUri !== undefined && requestedEventTypeUri !== campaign.eventTypeUri) {
    throw new CampaignIsolationError(
      `${campaign.label} cannot book or read the other company's event type.`,
    );
  }
  return campaign;
}

export function assertEventTypeUnchanged(campaign: Campaign, live: LiveEventType): void {
  const kinds = (live.locations ?? []).map((location) => location.kind);
  const problems: string[] = [];
  if (live.uri !== campaign.eventTypeUri) problems.push("uri");
  if (live.slug !== campaign.slug) problems.push("slug");
  if (live.duration !== campaign.durationMinutes) problems.push("duration");
  if (live.active !== true) problems.push("active");
  if (live.scheduling_url !== campaign.schedulingUrl) problems.push("scheduling_url");
  if (live.name !== campaign.displayName) problems.push("name");
  if (kinds.length !== 1 || kinds[0] !== campaign.locationKind) problems.push("location");
  if (problems.length > 0) {
    throw new EventTypeDriftError(
      `${campaign.label} event type no longer matches the checked snapshot (${problems.join(", ")}). It was not modified.`,
    );
  }
}
