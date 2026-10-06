export class WorkerError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = new.target.name;
    this.code = code;
  }
}

export class CampaignIsolationError extends WorkerError {
  constructor(message = "This campaign cannot use that event type.") {
    super("campaign_isolation", message);
  }
}

export class UnverifiedContactError extends WorkerError {
  constructor(message = "This contact is not verified.") {
    super("unverified_contact", message);
  }
}

export class ProspectBookingBlockedError extends WorkerError {
  constructor(
    message = "Bookings that would email anyone other than the owner test contact are blocked.",
  ) {
    super("prospect_booking_blocked", message);
  }
}

export class ConfirmationRequiredError extends WorkerError {
  constructor(message = "Confirm name, email, date, time, and timezone before booking.") {
    super("confirmation_required", message);
  }
}

export class SlotUnavailableError extends WorkerError {
  constructor(message = "That time is not an open slot for this event type.") {
    super("slot_unavailable", message);
  }
}

export class AmbiguousBookingsError extends WorkerError {
  constructor(message = "More than one active appointment matches this request. No new appointment was created.") {
    super("ambiguous_bookings", message);
  }
}

export class ReconciliationRequiredError extends WorkerError {
  constructor(
    message = "Calendly did not confirm the booking. Reconcile the schedule before retrying so a second appointment is not created.",
  ) {
    super("reconciliation_required", message);
  }
}

export class CalendlyTimeoutError extends WorkerError {
  constructor(message = "The Calendly request timed out.") {
    super("calendly_timeout", message);
  }
}

export class CalendlyUncertainError extends WorkerError {
  readonly status: number;

  constructor(status: number, message: string) {
    super("calendly_uncertain", message);
    this.status = status;
  }
}

export class CalendlyHttpError extends WorkerError {
  readonly status: number;

  constructor(status: number, message: string) {
    super("calendly_http", message);
    this.status = status;
  }
}

export class EventTypeDriftError extends WorkerError {
  constructor(message: string) {
    super("event_type_drift", message);
  }
}

/** Remove credential-shaped strings from text that might be logged. */
export function redactSecrets(text: string): string {
  return text
    .replace(/Bearer\s+\S+/gi, "Bearer [redacted]")
    .replace(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g, "[redacted]");
}
