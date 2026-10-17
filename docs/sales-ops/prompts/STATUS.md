# PAL prompt status

Checked October 5, 2026. These files are stored source. They are not installed.

The kit README (`kit-readme.md`, version 0.1.0, built 2026-10-04) says the PAL prompts were written, checked against canon, and are ready to apply. The same README says nothing in the kit has been applied, every script defaults to a dry run, and live owner tests have not started because they are blocked. The apply scripts, objectives, guardrails, knowledge files, `config/campaigns.json`, and `ROMAN-ACTIONS.md` were not in this upload.

This review does not treat either prompt as approved source for an ElevenLabs branch or a Tavus PAL.

## Where these files live

The kit folder map names `tavus/prompts/` for the system prompts. These copies live under `docs/sales-ops/prompts/` so they stay separate from `docs/two-company-salesperson-step1-inventory.md`.

| File | What it is |
| --- | --- |
| `kit-readme.md` | Uploaded kit README, verbatim |
| `wisdomtwin.system-prompt.md` | Uploaded WisdomTwin PAL system prompt, verbatim |
| `n5r.system-prompt.md` | Uploaded N5R PAL system prompt, verbatim |
| `STATUS.md` | This review |

## Verdict

Both prompts are drafts. Do not install them on a live branch, a 0 percent traffic branch, or a Tavus PAL until Roman approves the price language and the `/20min` routing conflict below.

Not installed, because:

- The README does not require an apply in this state. Owner tests are blocked, and the provisioning scripts are absent.
- Step 1 inventory: no trained Roman face, and the two Roman-named PALs are stock faces. Do not reuse them and do not create a new PAL from this draft.
- These prompts are video PAL instructions. The existing 0 percent branches are phone qualification prompts. Copying this text onto those branches would change channel, pricing, and booking behavior.
- Tavus guardrails on the account defer price quotes and do not state an approved price. The Step 1 inventory does not adopt a draft pricing ladder as an authorized offer.

No ElevenLabs branch, Tavus PAL, HubSpot record, Calendly event, or outbound message was changed.

## Canon check

Shared checks that pass:

- Each prompt discloses that the speaker is an AI twin in the first spoken sentence, and again if asked whether it is Roman.
- Neither prompt uses an em dash.
- The spoken prompts use American spelling, including "judgment".
- WisdomTwin does not pitch fundraising, a SAFE, or a valuation. N5R does not mention WisdomTwin in the offer, and it does not guarantee a grant or funding.
- The Talent Lab sentence attributes USD $5.5 million to Talent Lab's CEO for 2025 and says it is not WisdomTwin revenue.

WisdomTwin draft, not approved:

- The headline ladder matches the locked figures: no-cost Judgment Assessment, Concept Validation at USD $50,000, Structured Pilot at USD $250,000, Commercial at USD $500,000 or more per year.
- It then adds prices that are not in that ladder: USD $5,000 one-time setup plus USD $500 per month for each role beyond the included roles. Those figures are not approved.
- It also adds package terms the locked ladder does not state: two months and ten roles, six months and fifty roles, and five hundred roles on the commercial tier.
- If asked about stage, it says the company is pre-revenue, the product is built, and it is selecting first pilot partners. It does not state the rest of the truth baseline: zero production users, zero paying customers, USD $0 product revenue, and five synthetic demos. The board-packet demonstration is labeled synthetic.
- Investment, fundraising, valuation, and financing are named only as topics to refuse, with a redirect to Roman. That is a refusal, not an offer. Buyer outreach should not grow that into investor content.
- A reimbursement question is deferred. The prompt does not promise government reimbursement.

N5R draft, not approved:

- It states that engagements start at USD $15,000. That price is not in the locked WisdomTwin ladder, not in the kit README, and not adopted by the Step 1 inventory.
- Ontario Job Grant language does not say the grant is guaranteed, automatic, free, or already approved for N5R. It limits itself to program facts: support up to ten thousand dollars per trainee, half of the training cost paid by employers with one hundred or more employees, and at least one sixth paid by smaller employers. The prompt does not say whether those dollars are CAD or USD. The official program name is the Canada-Ontario Job Grant. The prompt shortens that to Ontario Job Grant.
- Fit requires an Ontario business and a team to train. WisdomTwin and fundraising are prohibited topics.

Kit README conflicts to resolve before any apply:

- It says the investor `/20min` event is excluded so a PAL can never join it. The Step 1 inventory shows that `https://calendly.com/romanbodnarchuk/20min` is the WisdomTwin buyer intro, 15 minutes, not a separate investor event. Applying that exclude rule would block the only WisdomTwin buyer booking.
- It describes a 12-to-15-minute PAL session. Both live Calendly events are 15 minutes, a PAL can join about one minute early, and this Tavus account's conversation cap is still unknown. Do not shorten the events and do not buy a Tavus plan from this file.
- The README uses British spellings ("behaviour", "labelled"). The spoken prompts do not.

## Next gate

Roman decides whether the WisdomTwin overage prices and the N5R USD $15,000 floor stay, change, or come out. Until that decision, these files stay in the repo as drafts and stay off every agent and PAL.
