# Ontario Job Grant readiness

Decision date: October 6, 2026. HubSpot portal `66868`. Recorded October 8, 2026.

We are not ready to call all Ontario businesses in HubSpot with a script that says "up to $10,000 in AI training for every employee in Ontario."

Outbound stays off. The kill switch, owner-test mode, the claims guardrail, and the no-funding-claims rule stay on.

No call, email, or text was sent to record this decision.

## Blocker 1. There is nothing to dial

A sample of 100 of 75,751 contacts had email on all of them, a name on 1, and phone, company, website, city, state, and country on 0.

## Blocker 2. The list is not Ontario

The sample is a global professional-services directory, not an Ontario list. Country and state are empty, so Ontario cannot be filtered.

## Blocker 3. The claim is false

Official page: https://www.ontario.ca/page/ontario-job-grant (updated August 31, 2026).

The program can support up to $10,000 per trainee for approved training. It does not pay that amount for every employee. Employers with 100 or more employees pay half. Employers with fewer than 100 pay at least one sixth. A small employer training a previously unemployed new hire may qualify for up to $15,000 without a minimum contribution. Training cannot start before approval. An eligible provider is required. Vendor product training and business consulting are excluded. Meeting the rules does not guarantee funding.

Whether N5R is an eligible provider is unverified.

## Blocker 4. Consent and disclosure are not implemented

CASL, CRTC unsolicited telecommunications rules and the National Do Not Call List, and AI-voice disclosure are not implemented.

## Recommended path

1. Answer provider eligibility first. Whether N5R is an eligible provider is still unverified.
2. Keep the honest claim: up to $10,000 per trainee for approved training, with the employer share, the small-employer new-hire exception, approval before training starts, an eligible provider, and no guarantee of funding.
3. Rebuild an Ontario list with names and direct lines.
4. Add consent and suppression.
5. Then run a 25-contact owner-reviewed batch.

Until that path is finished, outbound stays off.

## Installed scripts

Checked on October 8, 2026:

- `docs/sales-ops/prompts/live/n5r-grant-hook-voice.md`
- `docs/sales-ops/prompts/live/n5r-grant-hook-meeting.md`

Both already match the verified facts. They limit the offer to eligible training, up to $10,000 per trainee, with the employer share and the new-hire exception. They state that meeting the rules does not guarantee funding. They forbid saying the grant is for every employee, that it is guaranteed or free for the current team, and that N5R is an approved provider. No sentence was changed.

## Contact total

The sample of 100 of 75,751 is from the October 6, 2026 assessment. A read-only check on October 8, 2026 confirmed portal `66868` and a contact total of 75,755. That check did not export contact records and did not repeat the field sample. The higher total does not add phone numbers, names, or an Ontario filter.
