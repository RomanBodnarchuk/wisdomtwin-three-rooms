export const OWNER_EMAIL = "roman@n5r.com";
export const OWNER_NAME = "Roman Bodnarchuk";
export const OWNER_HUBSPOT_CONTACT_ID = "143893597452";
export const OWNER_TIMEZONE = "America/Toronto";
export const CALENDLY_USER_URI = "https://api.calendly.com/users/DBHDBPAOK4RMWSRQ";
export const CALENDLY_USER_TIMEZONE = "America/New_York";

export type CampaignId = "wisdomtwin" | "n5r";

export interface Campaign {
  readonly id: CampaignId;
  readonly label: string;
  readonly eventTypeUri: string;
  readonly schedulingUrl: string;
  readonly slug: string;
  readonly durationMinutes: 15;
  readonly locationKind: "google_conference";
  readonly displayName: string;
}

export const CAMPAIGNS: Record<CampaignId, Campaign> = {
  wisdomtwin: {
    id: "wisdomtwin",
    label: "WisdomTwin",
    eventTypeUri: "https://api.calendly.com/event_types/DGDHPUSUU24UVHEM",
    schedulingUrl: "https://calendly.com/romanbodnarchuk/20min",
    slug: "20min",
    durationMinutes: 15,
    locationKind: "google_conference",
    displayName: "15-Min Intro: WisdomTwin.ai",
  },
  n5r: {
    id: "n5r",
    label: "N5R",
    eventTypeUri: "https://api.calendly.com/event_types/803240ac-719e-4b20-a346-e8bc5b167262",
    schedulingUrl: "https://calendly.com/romanbodnarchuk/roman-bodnarchuk-n5r-ai-15-minute-business-call",
    slug: "roman-bodnarchuk-n5r-ai-15-minute-business-call",
    durationMinutes: 15,
    locationKind: "google_conference",
    displayName: "Roman Bodnarchuk | N5R.ai | 15-Minute Business Call",
  },
};

export const CAMPAIGN_IDS = Object.keys(CAMPAIGNS) as CampaignId[];

export function otherCampaign(id: CampaignId): CampaignId {
  return id === "wisdomtwin" ? "n5r" : "wisdomtwin";
}
