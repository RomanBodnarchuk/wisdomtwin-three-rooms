import {
  CalendlyHttpError,
  CalendlyTimeoutError,
  CalendlyUncertainError,
  redactSecrets,
  WorkerError,
} from "./errors.ts";

export interface ScheduledEvent {
  uri: string;
  eventType: string;
  startTime: string;
  endTime: string;
  status: string;
  name: string | null;
}

export interface InviteeRecord {
  uri: string;
  email: string;
  name: string;
  status: string;
  timezone: string | null;
}

export interface CreatedInvitee {
  eventUri: string;
  inviteeUri: string;
  status: string;
  email: string;
  timezone: string | null;
}

export interface CreateInviteeInput {
  eventTypeUri: string;
  startTime: string;
  name: string;
  email: string;
  timezone: string;
  locationKind: "google_conference";
}

export interface ListEventsQuery {
  user: string;
  inviteeEmail: string;
  status: "active" | "canceled";
  minStartTime: string;
  maxStartTime: string;
}

export interface CalendlyUser {
  uri: string;
  name: string;
  email: string;
  timezone: string;
  schedulingUrl: string;
  slug: string;
  currentOrganization: string;
}

export interface CalendlyClient {
  getCurrentUser(): Promise<CalendlyUser>;
  getOrganization(organizationUri: string): Promise<Record<string, unknown>>;
  getEventType(eventTypeUri: string): Promise<Record<string, unknown>>;
  listAvailableTimes(eventTypeUri: string, startTime: string, endTime: string): Promise<string[]>;
  listScheduledEvents(query: ListEventsQuery): Promise<ScheduledEvent[]>;
  getScheduledEvent(eventUri: string): Promise<ScheduledEvent>;
  listInvitees(eventUri: string): Promise<InviteeRecord[]>;
  createInvitee(input: CreateInviteeInput): Promise<CreatedInvitee>;
  cancelEvent(eventUri: string, reason: string): Promise<void>;
}

const API_ORIGIN = "https://api.calendly.com";

function isTimeout(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const name = "name" in error ? String(error.name) : "";
  return name === "TimeoutError" || name === "AbortError";
}

function eventUuid(eventUri: string): string {
  const match = /^https:\/\/api\.calendly\.com\/scheduled_events\/([^/]+)$/.exec(eventUri);
  if (!match) {
    throw new WorkerError("calendly_http", "Scheduled event URI is not recognized.");
  }
  return match[1];
}

function asRecord(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object") return {};
  return value as Record<string, unknown>;
}

function parseEvent(value: unknown): ScheduledEvent {
  const record = asRecord(value);
  const uri = String(record.uri ?? "");
  const eventType = String(record.event_type ?? "");
  const startTime = String(record.start_time ?? "");
  const endTime = String(record.end_time ?? "");
  const status = String(record.status ?? "");
  if (!uri || !eventType || !startTime || !status) {
    throw new CalendlyUncertainError(200, "Calendly returned an event without the fields needed to confirm it.");
  }
  return {
    uri,
    eventType,
    startTime,
    endTime,
    status,
    name: record.name == null ? null : String(record.name),
  };
}

function parseInvitee(value: unknown): InviteeRecord {
  const record = asRecord(value);
  return {
    uri: String(record.uri ?? ""),
    email: String(record.email ?? ""),
    name: String(record.name ?? ""),
    status: String(record.status ?? ""),
    timezone: record.timezone == null ? null : String(record.timezone),
  };
}

export class HttpCalendlyClient implements CalendlyClient {
  private readonly token: string;
  private readonly fetchImpl: typeof fetch;
  private readonly timeoutMs: number;

  constructor(token: string, fetchImpl: typeof fetch = fetch, timeoutMs = 20_000) {
    if (!token.trim()) {
      throw new Error("Calendly token is not configured.");
    }
    this.token = token;
    this.fetchImpl = fetchImpl;
    this.timeoutMs = timeoutMs;
  }

  getCurrentUser(): Promise<CalendlyUser> {
    return this.request("GET", "/users/me").then((body) => {
      const resource = asRecord(asRecord(body).resource);
      return {
        uri: String(resource.uri ?? ""),
        name: String(resource.name ?? ""),
        email: String(resource.email ?? ""),
        timezone: String(resource.timezone ?? ""),
        schedulingUrl: String(resource.scheduling_url ?? ""),
        slug: String(resource.slug ?? ""),
        currentOrganization: String(resource.current_organization ?? ""),
      };
    });
  }

  getOrganization(organizationUri: string): Promise<Record<string, unknown>> {
    const uuid = organizationUri.split("/").pop();
    if (!uuid || organizationUri !== `${API_ORIGIN}/organizations/${uuid}`) {
      throw new WorkerError("calendly_http", "Organization URI is not recognized.");
    }
    return this.request("GET", `/organizations/${encodeURIComponent(uuid)}`).then((body) =>
      asRecord(asRecord(body).resource),
    );
  }

  getEventType(eventTypeUri: string): Promise<Record<string, unknown>> {
    const uuid = eventTypeUri.split("/").pop();
    if (!uuid || eventTypeUri !== `${API_ORIGIN}/event_types/${uuid}`) {
      throw new WorkerError("calendly_http", "Event type URI is not recognized.");
    }
    return this.request("GET", `/event_types/${encodeURIComponent(uuid)}`).then((body) =>
      asRecord(asRecord(body).resource),
    );
  }

  async listAvailableTimes(eventTypeUri: string, startTime: string, endTime: string): Promise<string[]> {
    const body = await this.request("GET", "/event_type_available_times", {
      query: { event_type: eventTypeUri, start_time: startTime, end_time: endTime },
    });
    const collection = asRecord(body).collection;
    if (!Array.isArray(collection)) return [];
    const slots: string[] = [];
    for (const item of collection) {
      const record = asRecord(item);
      if (record.status && record.status !== "available") continue;
      const start = String(record.start_time ?? "");
      if (start) slots.push(start);
    }
    return slots;
  }

  listScheduledEvents(query: ListEventsQuery): Promise<ScheduledEvent[]> {
    return this.collectPages("/scheduled_events", {
      user: query.user,
      invitee_email: query.inviteeEmail,
      status: query.status,
      min_start_time: query.minStartTime,
      max_start_time: query.maxStartTime,
      count: "100",
      sort: "start_time:asc",
    }).then((items) => items.map(parseEvent));
  }

  getScheduledEvent(eventUri: string): Promise<ScheduledEvent> {
    return this.request("GET", `/scheduled_events/${encodeURIComponent(eventUuid(eventUri))}`).then((body) =>
      parseEvent(asRecord(body).resource),
    );
  }

  listInvitees(eventUri: string): Promise<InviteeRecord[]> {
    return this.collectPages(`/scheduled_events/${encodeURIComponent(eventUuid(eventUri))}/invitees`, {
      count: "100",
      status: "active",
    }).then((items) => items.map(parseInvitee));
  }

  async createInvitee(input: CreateInviteeInput): Promise<CreatedInvitee> {
    const body = await this.request("POST", "/invitees", {
      json: {
        event_type: input.eventTypeUri,
        start_time: input.startTime,
        invitee: {
          name: input.name,
          email: input.email,
          timezone: input.timezone,
        },
        location: { kind: input.locationKind },
      },
    });
    const resource = asRecord(asRecord(body).resource);
    const eventUri = String(resource.event ?? "");
    const status = String(resource.status ?? "");
    const email = String(resource.email ?? "");
    if (!eventUri || status !== "active" || !email) {
      throw new CalendlyUncertainError(201, "Calendly did not return an active invitee.");
    }
    return {
      eventUri,
      inviteeUri: String(resource.uri ?? ""),
      status,
      email,
      timezone: resource.timezone == null ? null : String(resource.timezone),
    };
  }

  async cancelEvent(eventUri: string, reason: string): Promise<void> {
    await this.request("POST", `/scheduled_events/${encodeURIComponent(eventUuid(eventUri))}/cancellation`, {
      json: { reason },
    });
  }

  private async collectPages(path: string, query: Record<string, string>): Promise<unknown[]> {
    const items: unknown[] = [];
    let pageToken = "";
    for (let page = 0; page < 5; page += 1) {
      const body = await this.request("GET", path, {
        query: pageToken ? { ...query, page_token: pageToken } : query,
      });
      const record = asRecord(body);
      const collection = record.collection;
      if (Array.isArray(collection)) items.push(...collection);
      const token = asRecord(record.pagination).next_page_token;
      if (typeof token !== "string" || token.length === 0) break;
      pageToken = token;
    }
    return items;
  }

  private async request(
    method: string,
    path: string,
    options: { query?: Record<string, string>; json?: unknown } = {},
  ): Promise<unknown> {
    const url = new URL(path, API_ORIGIN);
    for (const [key, value] of Object.entries(options.query ?? {})) {
      url.searchParams.set(key, value);
    }
    let response: Response;
    try {
      response = await this.fetchImpl(url, {
        method,
        headers: {
          Authorization: `Bearer ${this.token}`,
          Accept: "application/json",
          "Content-Type": "application/json",
          "User-Agent": "wisdomtwin-salesperson-worker/0.1",
        },
        body: options.json === undefined ? undefined : JSON.stringify(options.json),
        signal: AbortSignal.timeout(this.timeoutMs),
      });
    } catch (error) {
      if (isTimeout(error)) throw new CalendlyTimeoutError();
      const message = error instanceof Error ? error.message : "Calendly request failed.";
      throw new CalendlyHttpError(0, redactSecrets(message));
    }
    const text = await response.text();
    const safe = redactSecrets(text).slice(0, 500);
    if (response.status >= 500) throw new CalendlyUncertainError(response.status, safe);
    if (!response.ok) throw new CalendlyHttpError(response.status, safe);
    if (!text) return {};
    try {
      return JSON.parse(text) as unknown;
    } catch {
      throw new CalendlyUncertainError(response.status, "Calendly returned a response that was not JSON.");
    }
  }
}
