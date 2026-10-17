import {
  OWNER_EMAIL,
  OWNER_HUBSPOT_CONTACT_ID,
  OWNER_NAME,
} from "./campaigns.ts";
import { ProspectBookingBlockedError, UnverifiedContactError } from "./errors.ts";

export interface VerifiedContact {
  readonly email: typeof OWNER_EMAIL;
  readonly name: typeof OWNER_NAME;
  readonly hubspotContactId: typeof OWNER_HUBSPOT_CONTACT_ID;
  readonly verification: "owner-test";
}

export interface ContactClaim {
  email: string;
  name: string;
  hubspotContactId: string;
}

/**
 * The only verified contact this worker will book, list, or cancel.
 * A self-asserted email is not enough. HubSpot id and name must match the owner record.
 */
export function verifyOwnerTestContact(claim: ContactClaim): VerifiedContact {
  const email = claim.email.trim().toLowerCase();
  if (email !== OWNER_EMAIL) {
    throw new ProspectBookingBlockedError();
  }
  if (claim.hubspotContactId !== OWNER_HUBSPOT_CONTACT_ID || claim.name.trim() !== OWNER_NAME) {
    throw new UnverifiedContactError(
      "The owner test contact must match the verified HubSpot record for roman@n5r.com.",
    );
  }
  return {
    email: OWNER_EMAIL,
    name: OWNER_NAME,
    hubspotContactId: OWNER_HUBSPOT_CONTACT_ID,
    verification: "owner-test",
  };
}

export function assertVerifiedContact(contact: VerifiedContact): VerifiedContact {
  if (
    contact.verification !== "owner-test" ||
    contact.email !== OWNER_EMAIL ||
    contact.name !== OWNER_NAME ||
    contact.hubspotContactId !== OWNER_HUBSPOT_CONTACT_ID
  ) {
    if (contact.email && contact.email !== OWNER_EMAIL) {
      throw new ProspectBookingBlockedError();
    }
    throw new UnverifiedContactError();
  }
  return verifyOwnerTestContact(contact);
}
