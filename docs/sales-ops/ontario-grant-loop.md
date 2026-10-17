# Ontario Job Grant loop

Checked October 6, 2026. No prospect was dialed. The US Twilio number was not moved.

## Who owns the ElevenLabs agents

There is one workspace. Every agent listed in this run was created by `roman@n5r.com`, who is also the admin on this connector. A second session tagged `owner-claude-cowork-2026-10-06` edited some of the same agents today. That is the same account, not a second owner. This Cursor session can read and update those agents because the connector is signed in as that workspace.

## The path

HubSpot portal `66868` holds the Ontario business contacts. This loop does not dial them yet.

1. Outbound voice, not released: `agent_3101m49jjdyafkebpbjszn024fs1`, "N5R Ontario Job Grant Hook v3". No phone number. Voice `OtTgp0gIgmfhqSXfyakl`. The hook script was updated in this pass. Version `agtvrsn_1801m49jpeh9e3x9s0d5bexjhby3`.
2. Do not use `agent_9601m3zbep94f1rbt80q1298qed4` for this campaign. It still holds the only number, a US Twilio number.
3. Booking page, fifteen minutes: `https://calendly.com/romanbodnarchuk/roman-bodnarchuk-n5r-ai-15-minute-business-call`.
4. One meeting twin: N5R PAL `pce648b51455`, username `n5r-roman`. Do not also invite `wisdomtwin-roman`. The worker in `services/salesperson-worker/src/singleJoin.ts` blocks a second join on the same Meet link.

## The hook

Official page checked October 6, 2026: https://www.ontario.ca/page/ontario-job-grant (page updated August 31, 2026).

The offer is a free fifteen minute fit check with Roman. Eligible training can be supported up to $10,000 per trainee. Under 100 employees, the company pays at least one sixth. At 100 or more, the company pays half. A small employer training a previously unemployed new hire may qualify for up to $15,000 per trainee without a minimum contribution. That is not free training for the current team. The province decides. A fixed budget means eligibility is not approval. N5R is not claimed as an approved provider. N5R training, if purchased, starts at USD $15,000.

The call qualifies an Ontario location of at least one year, a real task, a named signer, and a way to pay the company's share. Then it offers the booking page. It does not claim the meeting is booked.

## Still blocked

A Canadian calling number is not on the unreleased agent. Outbound to the HubSpot list stays off until that number is assigned and a campaign batch is approved.
