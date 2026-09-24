# Skill: /daily-brief

Run the full daily intelligence routine.

## Steps
1. Spawn subagent `regulated-finder` — scan HubSpot + X + FirstTouch
2. Spawn subagent `investor-tracker` — scan HubSpot + X + FirstTouch
3. For each contact with activity in last 7 days:
   - Pull HubSpot history
   - Pull X posts/mentions (last 7 days)
   - Search web: "[name] [company] news" (last 30 days)
   - Summarize: recent posts/emails/deals
   - Infer needs: compliance AI, auditable decision trails, data sovereignty
   - Generate WisdomTwin pitch angle
4. Flag 3-5 for outreach today (rank by recency × strength × fit)
5. File to /second-brain/wisdomtwin-scout/[date]-daily-brief.md
6. File per-contact notes to /second-brain/contacts/regulated/[name].md
7. File per-investor notes to /second-brain/investors/[name].md

## Output format

═══════════════════════════════════════════
WISDOMTWIN SCOUT DAILY BRIEF — [DATE]
═══════════════════════════════════════════

📋 REGULATED CONTACTS — HIGH PRIORITY
1. [Name] | [Role] | [Company]
   Recent: [activity]
   Need: [inferred need]
   Pitch: [angle]
   Strength: [Strong/Medium/Weak]

💰 INVESTOR WATCH — NEW SIGNALS
1. [Name] | [Firm]
   New: [activity]
   Opportunity: [outreach trigger]
   Pitch: [angle]

🎯 FLAGGED FOR OUTREACH TODAY (3-5)
→ [Name] — [reason] — [channel]
