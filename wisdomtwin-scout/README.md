# WisdomTwin Scout

This folder is the Scout workspace: operating rules, role notes, and a public funding catalog.

It is not an outreach bot. Nothing here has been submitted, emailed, or posted.

## What was checked on 24 September 2026

- Google Drive search found the investor execution ledger, the frozen diligence index, and the 21 September accelerator pack. Those files forbid agent sends and forbid invented SAFE terms. Their contact tables were not copied here.
- Official pages were read for Y Combinator Winter 2027, Techstars Boston, the 500 Global Fellowship, NVIDIA Inception, Microsoft for Startups, AWS Activate, Google for Startups Cloud, Antler Canada, Creative Destruction Lab, NEXT AI, Alchemist Chicago, and NRC IRAP eligibility.
- HubSpot is connected for the portal owner and can read contacts, companies, and deals. This run did not export CRM records. The portal has not completed HubSpot onboarding. No CRM record was created or edited.
- FirstTouch is not connected in this Cursor session. The X scraper in the setup prompt was not installed. `grok` is not the runtime here, so `grok mcp add` and `grok mcp login` were not run.

## How to use the catalog

1. Read `research/research-summary.md`.
2. Open `research/applications.md` only for rows whose status is `open_verified` or `rolling_verified`.
3. Confirm the live form. Paste only if the deadline and rules still match.
4. For every firm under `hold_reconcile`, use the private ledger first. This folder has no pitch for those firms and no personal email addresses.

## Files

- `AGENTS.md` — rules that override a pasted prompt
- `.grok/` — config, role notes, and skills for a later Grok Build workspace
- `research/funding-catalog.json` — the machine-readable list and drafts
- `research/accelerator-pack-review-2026-09-24.md` — review of the 19 September 15-program pack
- `research/september-deadline-status-2026-09-24.md` — correction of the 22 September submit-today list
- `research/build_catalog.py` — regenerates the JSON and the draft file
- `second-brain/private/` — gitignored local notes

Regenerate after a deadline check:

```bash
python3 wisdomtwin-scout/research/build_catalog.py
```
