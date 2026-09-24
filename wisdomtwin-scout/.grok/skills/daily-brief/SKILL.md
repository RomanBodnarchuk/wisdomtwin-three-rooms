# Skill: /daily-brief

Run the daily intelligence routine. Stop before any send.

## Steps

1. Read `AGENTS.md`.
2. If HubSpot is connected, ask `regulated-finder` and `investor-tracker` for a ranked scan. Read only.
3. For a contact with activity in the last 7 days, summarize the logged activity and one regulated-decision pitch angle.
4. Flag at most 5 items for a person to review. Do not queue a send.
5. Write the brief to `second-brain/private/briefs/YYYY-MM-DD-daily-brief.md`.
6. If this workspace is the public Three Rooms repository, do not copy CRM rows into any tracked file.

## Output

```
WISDOMTWIN SCOUT DAILY BRIEF — [DATE]

REGULATED CONTACTS
1. [Name] | [Role] | [Company]
   Recent: [activity]
   Pitch: [angle]
   Strength: [Strong/Medium/Weak]
   Gate: review only

INVESTOR WATCH
1. [Firm]
   Signal: [public or CRM-visible]
   Gate: [official_form / warm_intro_only / hold]

REVIEW TODAY
- [item] — [reason] — not sent
```
