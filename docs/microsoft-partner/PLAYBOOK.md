# WisdomTwin — Microsoft Startup, Partner Center & Design Partner GTM Playbook

**Tagline:** *WisdomTwin preserves institutional judgment.*  
**Core Microsoft Positioning:** *Copilot answers from what you can see; WisdomTwin answers from what the role knows.*

---

## 1. Microsoft for Startups (Founders Hub) — Copy-Paste Application

**Apply URL:** `https://startups.microsoft.com`  
**Critical Sign-Up Rules:**
1. Sign in with a **personal Microsoft account** (do **not** use a work or school email, and make sure that personal account has no existing Azure subscription).
2. Choose **Continue without a code** (or enter your 10-character investor/accelerator referral code if available).
3. Verify identity with your **personal LinkedIn profile**.
4. **Activate your initial $200–$1,000 Azure credits within 90 days** so they do not expire.
5. **Credit Progression Ladder:**
   - Day 1 (LinkedIn verification): **$200–$1,000** immediate Azure credits + 50 seats of M365 Business Premium for sandbox testing.
   - Stage 2 (Business entity verification — `WisdomTwin, Inc.`): **$5,000** Azure credits.
   - Stage 3 (5 active Azure workloads): **$25,000** Azure credits.
   - Stage 4 (7 active Azure workloads): **$50,000** Azure credits.
   - Stage 5 (10 active Azure workloads + ~$3,000/mo usage): **$150,000** Azure credits.
   - *Stack Note:* Credits cover Azure services and models billed directly by Azure (Azure OpenAI / Microsoft Foundry models, Azure AI Speech, Azure Container Apps, Azure Database for PostgreSQL + pgvector).

### Exact Application Fields to Paste:
- **Registered Startup Name:** `WisdomTwin, Inc.`
- **Primary Industry:** `Software and Technology` / `B2B SaaS`
- **Website:** `https://wisdomtwin.ai`
- **Description of Solution:**
  > WisdomTwin.ai is a business-to-business software platform that acts as a judgment layer for Microsoft 365 Copilot. While Copilot surfaces information an individual employee can see, WisdomTwin aggregates and synthesizes the complete history of every person who has ever held a given role, turning institutional knowledge into role-specific judgment. Our solution is built on Azure, integrates directly with Microsoft Copilot through plugins and connectors, and is designed for Microsoft shops with under 100 employees, helping them preserve expertise and accelerate decision-making.

---

## 2. Microsoft AI Cloud Partner Program — ISV Success Enrollment Copy

**Portal:** Microsoft Partner Center (`https://partner.microsoft.com`) -> Software Development Company Hub -> **ISV Success**  
**Benefits Unlocked (~$126,000 value, free Year 1):** $5,000 Azure sponsorship, M365 E5 Developer subscription (25 seats), Copilot Studio & user licenses, GitHub Enterprise, and up to 50 hours of 1-on-1 Microsoft technical architecture consultations.

### Exact ISV Success Form Fields to Paste:
- **Application Use Scenario:**
  > WisdomTwin.ai is a business-to-business software platform that serves as a judgment layer for Microsoft 365 Copilot. It aggregates the complete history of every employee who has ever held a given role and synthesizes it into role-specific judgment for the person currently in that position. Our solution is built on Azure and integrates directly with Microsoft Copilot through plugins and connectors, allowing Copilot to surface institutional knowledge beyond what any single employee can see.
- **App Features:**
  > Role-based knowledge aggregation across all prior role holders, integration with Microsoft Copilot via plugins and connectors, Azure-hosted data storage and processing, and role-specific prompt engineering that turns historical expertise into actionable judgment.
- **Company Size:** `1–10 employees`
- **Cloud Integration:**
  > Built on Azure, integrated with Microsoft 365 Copilot through the Microsoft Copilot extensibility framework.
- **Timeline Commitments:** Start development within 3 months, complete within 12 months, and publish to Microsoft Commercial Marketplace.

---

## 3. Microsoft Commercial Marketplace Listing Copy

- **Offer Title:** `WisdomTwin — Role-Specific Institutional Judgment for Microsoft 365 Copilot`
- **Search Results Summary (100 chars):**
  > Role-specific digital twins and governed Audio Executive Huddles inside Microsoft 365 Copilot.
- **Short Description:**
  > Copilot answers from what you can see; WisdomTwin answers from what the role knows. WisdomTwin builds a temporal context graph of Decision Episodes across every executive who has held a role (CFO, CTO, CRO, CMO, Chief Legal Officer) and delivers precedent-backed recommendations, dissent notes, and governed safe-declines directly inside Microsoft 365 Copilot and the Audio Executive Huddle.

---

## 4. Partner Center Submission Checklist (`Apps and Agents for M365 and Copilot`)

- [ ] **1. Partner Center Seller Account & Business Verification**: Complete domain ownership (`wisdomtwin.ai`), D-U-N-S / Delaware incorporation verification (`WisdomTwin, Inc.`), and obtain verified publisher badge (`mpnId`).
- [ ] **2. Program Enrollment**: Enroll in the **Microsoft 365 and Copilot** program inside Partner Center (zero registration/certification fee for independent publishers).
- [ ] **3. Multitenant Entra App Registration**:
  - Register app in the seller-associated Entra tenant.
  - Configure On-Behalf-Of (OBO) OAuth 2.0 flow (`api://wisdomtwin.ai/Twin.Query`).
  - Declare least-privilege Graph application scopes for customer tenant admin consent: `Mail.Read`, `Sites.Read.All`, `Files.Read.All`, `ChannelMessage.Read.All`, `OnlineMeetingTranscript.Read.All`, `InformationProtectionPolicy.Read.All`, `GroupMember.Read.All`.
- [ ] **4. Declarative Agent Package (`copilot/`)**:
  - `copilot/manifest.json` (Teams / M365 schema v1.19)
  - `copilot/declarativeAgent.json` (Declarative Agent v1.2 with conversation starters)
  - `copilot/ai-plugin.json` (Plugin manifest v2.1 with Adaptive Card response semantics)
  - `copilot/openapi.yaml` (OpenAPI 3.1 spec with `queryTwin`, `listRoles`, `getJudgment`, `startHuddle` and `x-openai-isConsequential: false` read-only annotations)
  - Color (`192x192`) and Outline (`32x32`) PNG icons
- [ ] **5. Compliance & Support Artifacts**:
  - Public Privacy Policy URL (`https://wisdomtwin.ai/privacy`)
  - Terms of Use URL (`https://wisdomtwin.ai/terms`)
  - Support documentation & test tenant credentials for Microsoft certification reviewers
- [ ] **6. Publisher Attestation & M365 Certification**:
  - Complete **Publisher Attestation** self-assessment first to unlock the *Microsoft 365 Certified* trust badge (accelerates enterprise security reviews from 2 months to 2 weeks).
  - After landing 5 net-new Copilot customers and 1,000 MAU, apply for the **Microsoft Copilot Specialization** (supported by MS-102, SC-401 / APL-4002, and APL-7008 certifications) and **Solutions Partner for Industry AI**.

---

## 5. One-Page 90-Day CFO Design Partner Pilot Proposal

**Subject:** 90-Day Governed Judgment Pilot — Preserving CFO & Executive Decision Precedent in Microsoft 365

### The Problem
When a senior financial or legal officer leaves—or when five executives are booked across three weeks of calendars—critical decisions wait. Microsoft 365 Copilot is great at finding documents *one user can see*, but it cannot reconstruct **how the CFO role itself decides**: the budget caps, the 7–2 board votes, the preserved dissent notes, and the non-negotiable "never-do" boundaries across everyone who has held the seat.

### The 60–90 Day Design Partner Pilot
WisdomTwin connects read-only to your Microsoft 365 environment (Exchange Mail, SharePoint, OneDrive, and Teams transcripts) while strictly inheriting **Microsoft Entra ID permissions** and **Microsoft Purview sensitivity labels** within your tenant control boundary.
1. **Weeks 1–2 (Ingestion & Temporal Context Graph):** Index historical CFO, CTO, and Legal decision episodes into an isolated Azure tenant graph.
2. **Weeks 3–6 (Validation & Copilot Integration):** Surface the CFO Twin directly inside Microsoft 365 Copilot Chat and the one-press Audio Executive Huddle.
3. **Weeks 7–12 (Measured Evaluation):** Measure precedent retrieval accuracy, review time saved, and governed safe-decline escalations against your current CFO's judgment.

### Success Metric (Agreed Up Front in Writing)
In a live Executive Huddle, the CEO's CFO Twin accurately answers **3 complex historical precedent and threshold questions**—citing verbatim board motions, vote splits, and rejected alternatives—and properly triggers a **Safe Decline** when precedent is missing.

### The Exchange
- **Our Commitment:** Free/discounted pilot access, direct founder engineering support from Roman Bodnarchuk, roadmap priority, and locked-in preferred launch pricing. All data remains strictly inside your Canadian/enterprise tenant boundary.
- **Your Commitment:** Read-only M365 sandbox/scoped connector access, 30 minutes of weekly feedback from the CFO office, and a joint case study if the agreed success metric is hit.

---

## 6. Design Partner Outreach Scripts (Warm Intro & Targeted LinkedIn)

### Script A: Warm Intro (Former Colleagues / Trusted Network — 60–80% Conversion)
> **Subject:** Quick question on CFO transition / institutional memory at [Company]
>
> Hi [First Name],
>
> Hope you're doing well. I'm building **WisdomTwin.ai** here in Toronto—we're solving a specific gap inside Microsoft 365 shops: **Copilot answers from what one person can see, but it doesn't know why past leaders made the decisions they made.**
>
> We build a role-specific judgment graph across every CFO, CTO, and Legal officer who has held the seat—capturing the budget caps, the board dissent notes, and the "never-do" rules—and plug it straight into Microsoft Copilot and a live Audio Executive Huddle, with all data staying inside the customer's own Microsoft tenant and Purview controls.
>
> We're selecting 3–5 Microsoft-first companies for a 6-to-8-week design partner pilot where we prove one concrete metric: the CFO Twin answers 3 historical threshold/exception questions accurately in a live huddle with verbatim citations.
>
> Would you be open to a 20-minute look at our 2:54 healthcare boardroom huddle (`https://wisdomtwin.ai`) this week to see if this fits [Company] (or a CFO in your network who's lived the pain of reconstructing past decisions)?
>
> Best,  
> **Roman Bodnarchuk**  
> Co-Founder & CEO, WisdomTwin, Inc.  
> `roman@wisdomtwin.ai` | `416 220 5314` | `https://calendly.com/romanbodnarchuk/20min`

### Script B: Targeted LinkedIn Outreach (Mid-Size Canadian / Regulated Enterprise CFOs)
> Hi [First Name] — noticed [Company] runs on the Microsoft 365 stack. When a finance or legal leader transitions, their inbox stays behind, but the *judgment layer*—why an exception was approved in 2022, why a vendor was rejected, or what the board's real threshold is—walks out the door.
>
> We built WisdomTwin to sit inside Microsoft Copilot and preserve role-level decisions (with full Canadian tenant control and Purview label enforcement). We're onboarding 3 design partners for a 6-week pilot. Open to a brief 15-min chat after watching our 2:54 demo at `wisdomtwin.ai`?

---

## 7. Microsoft Copilot Specialization Case Study Template

- **Customer Profile:** `[Company Name]`, `[Industry: Healthcare / Banking / Insurance]`, `[<100 / Mid-Market Microsoft 365 E5 Shop]`
- **Challenge:** Reconstructing multi-year executive precedent across Mail, SharePoint, and Teams took weeks of calendar coordination and manual offboarding audits.
- **Microsoft Stack Used:** Microsoft 365 Copilot Declarative Agent, Microsoft Graph Delta API, Microsoft Entra ID (OBO Auth), Microsoft Purview Sensitivity Labels, Azure OpenAI, Azure AI Speech.
- **Measured Pilot Results (30–90 Days):**
  - **Decisions Evaluated:** `[e.g., 12,400 historical decisions indexed; X live executive queries]`
  - **Precedent Hit Rate:** `[X%]` verified by current role holder
  - **Governed Safe-Declines:** `[100%]` of low-confidence queries withheld and routed to named human reviewers (`[38 min]` average review)
  - **Copilot Seat Adoption Impact:** `[X]` net-new M365 Copilot seats activated
- **Executive Quote:** *"[CFO / CEO Quote on preserving institutional judgment without sacrificing governance.]"*
