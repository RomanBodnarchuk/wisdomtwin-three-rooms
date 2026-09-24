export const CALENDLY_URL = 'https://calendly.com/romanbodnarchuk/20min';
export const FOUNDER_EMAIL = 'roman@wisdomtwin.ai';
export const FOUNDER_PHONE_DISPLAY = '416 220 5314';
export const FOUNDER_PHONE_TEL = '+14162205314';
export const INVESTOR_OVERVIEW_URL = 'https://wisdomtwin.ai/invest';
export const COMPANY_URL = 'https://wisdomtwin.ai/company';
export const SITE_URL = 'https://wisdomtwin.ai/';

export const TARGET_USD = 1_000_000;

export const TAGLINE = 'WisdomTwin preserves institutional judgment.';

export function formatUsd(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(amount);
}

export function portionOfTarget(amount: number): number {
  return amount / TARGET_USD;
}

export function formatPortion(amount: number): string {
  const pct = portionOfTarget(amount) * 100;
  if (pct >= 1) {
    return `${pct.toLocaleString('en-US', { maximumFractionDigits: 1 })}%`;
  }
  return `${pct.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
}

export function checksToFill(amount: number): number {
  return TARGET_USD / amount;
}

export type PerkId =
  | 'updates'
  | 'demos'
  | 'booking'
  | 'briefing'
  | 'session'
  | 'quarterly'
  | 'scoping'
  | 'governance'
  | 'designPartner'
  | 'founderDay';

export interface Tier {
  id: string;
  name: string;
  amount: number;
  summary: string;
  detail: string;
  perks: PerkId[];
}

const BASE_PERKS: PerkId[] = ['updates', 'demos', 'booking'];

export const TIERS: Tier[] = [
  {
    id: 'briefing',
    name: 'Briefing',
    amount: 1_000,
    summary: 'Follow the round and read the evidence as it is.',
    detail:
      'A proposed community-sized check. It opens the same unpublished SAFE conversation as every other check. It does not buy shares, bonus equity, or a customer pilot.',
    perks: BASE_PERKS,
  },
  {
    id: 'observer',
    name: 'Observer',
    amount: 2_500,
    summary: 'A longer founder briefing, still on unpublished terms.',
    detail:
      'For people who want more than the public 20-minute booking before deciding whether a proposed SAFE is even the right conversation.',
    perks: [...BASE_PERKS, 'briefing'],
  },
  {
    id: 'session',
    name: 'Working session',
    amount: 5_000,
    summary: 'Map one recurring decision that waits today.',
    detail:
      'The commercial product has a separate USD $5,000, two-week, read-only buyer evaluation. This tier is not that contract. It is a proposed investor working session on one decision loop.',
    perks: [...BASE_PERKS, 'briefing', 'session'],
  },
  {
    id: 'circle',
    name: 'Founder circle',
    amount: 10_000,
    summary: 'Stay close to the work while the round is being documented.',
    detail:
      'A proposed year of quarterly small-group updates with Roman, alongside the same SAFE economics everyone else would receive once terms exist.',
    perks: [...BASE_PERKS, 'briefing', 'session', 'quarterly'],
  },
  {
    id: 'scoping',
    name: 'Scoping',
    amount: 25_000,
    summary: 'One workflow, mapped with the people who would have to live with it.',
    detail:
      'A proposed scoping workshop for a single regulated decision. Capacity is limited. It is not a signed pilot and not a promise of deployment.',
    perks: [...BASE_PERKS, 'briefing', 'session', 'quarterly', 'scoping'],
  },
  {
    id: 'governance',
    name: 'Governance',
    amount: 50_000,
    summary: 'Spend the time on authority, evidence, and refusal.',
    detail:
      'A proposed governance session with Roman and, subject to her schedule, Stella Cabrera. The point of the session is the trust layer, not a pitch.',
    perks: [...BASE_PERKS, 'briefing', 'session', 'quarterly', 'scoping', 'governance'],
  },
  {
    id: 'path',
    name: 'Design path',
    amount: 100_000,
    summary: 'A serious conversation about becoming a design partner later.',
    detail:
      'Ten percent of the published target. This opens a proposed design-partner discussion. It does not create a pilot, a customer, or a production deployment.',
    perks: [...BASE_PERKS, 'briefing', 'session', 'quarterly', 'scoping', 'governance', 'designPartner'],
  },
  {
    id: 'day',
    name: 'Founder day',
    amount: 200_000,
    summary: 'One working day with Roman. Twenty percent of the target.',
    detail:
      'A proposed private working day, in Toronto or remote, by arrangement. Only a few can exist in a year. It includes the design-path conversation. It still does not set a valuation cap.',
    perks: [
      ...BASE_PERKS,
      'briefing',
      'session',
      'quarterly',
      'scoping',
      'governance',
      'designPartner',
      'founderDay',
    ],
  },
];

export const PERK_LABELS: Record<PerkId, string> = {
  updates: 'Written investor updates while the round is in discussion',
  demos: 'The public synthetic demonstrations',
  booking: 'The public 20-minute founder booking',
  briefing: 'Extended founder briefing',
  session: 'Working session on one decision loop',
  quarterly: 'Quarterly small-group update for one year',
  scoping: 'Workflow scoping workshop',
  governance: 'Governance session',
  designPartner: 'Design-partner conversation',
  founderDay: 'Private working day with Roman',
};

export const OFFERING_FACTS: Array<{ label: string; value: string; note?: string }> = [
  { label: 'Status', value: 'Proposed', note: 'Not open. This page accepts no funds.' },
  { label: 'Target raise', value: formatUsd(TARGET_USD), note: 'Published figure. Not a minimum or a cap on the company.' },
  { label: 'Instrument', value: 'Post-money SAFE', note: 'Proposed. The document is not yet the offering.' },
  { label: 'Valuation cap & discount', value: 'Not documented', note: 'Specific economic terms remain to be agreed.' },
  { label: 'Share price', value: 'None', note: 'A SAFE is not priced common stock.' },
  { label: 'Ownership from a check', value: 'Cannot be stated', note: 'Ownership waits on the cap, the discount, and a conversion.' },
  { label: 'Company', value: 'WisdomTwin, Inc.', note: 'A Delaware corporation. Founder-built in Toronto.' },
  { label: 'Stage', value: 'Pre-revenue', note: '0 production users. 0 paying customers. USD $0 product revenue.' },
  { label: 'Product evidence', value: '5 synthetic demos', note: 'Founder-built. Not customers, pilots, or measured results.' },
  { label: 'Funds via this page', value: formatUsd(0), note: 'There is no escrow, portal, or subscription flow here.' },
];

export interface Layer {
  index: string;
  title: string;
  body: string;
  status: string;
}

export const LAYERS: Layer[] = [
  {
    index: '01',
    title: 'Ingest',
    body: 'Bring authorized evidence into the customer boundary with source and permission context. Nothing is ingested before those boundaries are agreed.',
    status: 'Design, shown in synthetic demos',
  },
  {
    index: '02',
    title: 'Judgment Twin',
    body: 'Structure how a role decides: principles, thresholds, exceptions, and escalation. We model the role. We do not clone people, and we do not replace the person accountable for the outcome.',
    status: 'Design, shown in synthetic demos',
  },
  {
    index: '03',
    title: 'Trust Layer',
    body: 'Provenance, role-based access, version history, human review, escalation, and audit records sit in the path of the answer. Safe decline is part of the product.',
    status: 'Design, shown in synthetic demos',
  },
  {
    index: '04',
    title: 'One-Press Huddle',
    body: 'Open the decision when it arises and convene the roles it needs, without creating another calendar dependency. The output is a typed recommendation for a named human to release.',
    status: 'Synthetic demonstration',
  },
];

export const OUTCOMES = [
  { title: 'Recommend', body: 'The model proposes a bounded action the policy layer can inspect.' },
  { title: 'Escalate', body: 'When authority or evidence runs out, the question routes to the role that can decide it.' },
  { title: 'Safe decline', body: 'Low support, missing permission, or a conflict blocks release. Completeness is not permission.' },
];

export const PROBLEM_POINTS = [
  { value: 'Days', label: 'A CEO decision waits for the person who holds the judgment.' },
  { value: 'Weeks', label: 'A bank exception waits for committee availability.' },
  { value: 'Months', label: 'A procurement determination waits between reviewers.' },
  { value: 'Walks out', label: 'When the expert leaves, the way they decide leaves with them.' },
];

export const BEFORE_AFTER: Array<{ topic: string; before: string; after: string }> = [
  {
    topic: 'Timing',
    before: 'The prepared work waits for the next meeting.',
    after: 'The question moves while it is live.',
  },
  {
    topic: 'Evidence',
    before: 'Each reviewer rebuilds context from inboxes and decks.',
    after: 'Authorized sources arrive with the question.',
  },
  {
    topic: 'Limits',
    before: 'Thresholds and exceptions are assumed in the room.',
    after: 'Limits are stated with the answer.',
  },
  {
    topic: 'Authority',
    before: 'It is unclear who is allowed to release the decision.',
    after: 'A named human reviews, approves, or declines on the record.',
  },
  {
    topic: 'Gaps',
    before: 'The room fills missing evidence with confidence.',
    after: 'Missing, stale, or conflicting evidence blocks the next action.',
  },
];

export const INDUSTRIES = [
  {
    title: 'Banking',
    before: 'Credit exceptions wait for committee availability.',
    after: 'The decision package is assembled while the question is live.',
  },
  {
    title: 'Insurance',
    before: 'Claims wait while context and policy limits are reconstructed.',
    after: 'Claims move with evidence, limits, and escalation attached.',
  },
  {
    title: 'Healthcare',
    before: 'Policy interpretation waits for the next governance meeting.',
    after: 'Governance context is present when the question is asked.',
  },
  {
    title: 'Government',
    before: 'Procurement determinations wait between reviewers.',
    after: 'Decision support starts immediately, with authority still named.',
  },
  {
    title: 'Legal',
    before: 'Partners become the bottleneck on recurring determinations.',
    after: 'Institutional judgment is available, and exceptions reach a human.',
  },
];

export const MODEL_STEPS = [
  {
    step: '01',
    title: 'Pilot one workflow',
    body: 'Begin with a bounded regulated decision and an accountable buyer. The first ten pilots are a target, not signed business.',
  },
  {
    step: '02',
    title: 'Measure before claiming',
    body: 'The customer names the reviewer, the limits, and the acceptance criteria. Critical misses, source checks, review time, latency, and data egress are the tests. None are achieved results yet.',
  },
  {
    step: '03',
    title: 'Expand with evidence',
    body: 'A second workflow waits on measured acceptance. Pricing and packaging are not final.',
  },
  {
    step: '04',
    title: 'Contract the operating change',
    body: 'The planned model is an annual subscription plus implementation and private-deployment services. Pilot fees stay separate from any future investment.',
  },
];

export const PROCEEDS: Array<{ use: string; pct: string; amount: number; detail: string }> = [
  {
    use: 'Product hardening',
    pct: '40%',
    amount: 400_000,
    detail: 'Turn the synthetic decision contract into software a pilot could actually evaluate.',
  },
  {
    use: 'Pilot evaluation',
    pct: '25%',
    amount: 250_000,
    detail: 'Customer discovery and controlled evaluations. Not a claim that pilots are signed.',
  },
  {
    use: 'Deployment acceptance',
    pct: '15%',
    amount: 150_000,
    detail: 'Test retrieval, inference, logs, telemetry, backups, and support access against the deployment thesis.',
  },
  {
    use: 'Counsel and governance',
    pct: '12%',
    amount: 120_000,
    detail: 'SAFE documentation, corporate housekeeping, and any later exemption work. This page is not that work.',
  },
  {
    use: 'Operating reserve',
    pct: '8%',
    amount: 80_000,
    detail: 'Founder-built company. Reserve for the work between a conversation and a contract.',
  },
];

const proceedsTotal = PROCEEDS.reduce((sum, row) => sum + row.amount, 0);
if (proceedsTotal !== TARGET_USD) {
  throw new Error(`Use of proceeds must equal ${TARGET_USD}, got ${proceedsTotal}`);
}

export const RISKS: Array<{ title: string; body: string }> = [
  {
    title: 'You can lose the entire amount',
    body: 'WisdomTwin is an early-stage, pre-revenue company. An investment, if one is later offered, could become worthless. Nothing on this page is a forecast.',
  },
  {
    title: 'There are no customers yet',
    body: 'Zero production users, zero paying customers, and USD $0 in product revenue. Five demonstrations are synthetic and founder-built. They are not case studies.',
  },
  {
    title: 'The round is not open',
    body: 'The published plan is a proposed post-money SAFE for USD $1,000,000. The cap, discount, and other economics are not agreed. This page is not a subscription document.',
  },
  {
    title: 'A SAFE is not shares',
    body: 'Until a SAFE converts, the holder generally does not own stock, does not vote as a stockholder, and cannot point to a share price. Conversion depends on events that may never happen.',
  },
  {
    title: 'Illiquid by design',
    body: 'There is no public market for a WisdomTwin SAFE or for shares that might later be issued. A holder should expect to be unable to sell.',
  },
  {
    title: 'Dilution is unknown',
    body: 'Future financings, a larger round, or a conversion can change what any check represents. Because the cap is undocumented, this page refuses to state an ownership percentage.',
  },
  {
    title: 'The product is not production-validated',
    body: 'Private cloud, on-premises, on-device, and air-gapped patterns are deployment theses for pilot scoping. None is a certified production installation today.',
  },
  {
    title: 'Pilots may not happen',
    body: 'Buyer evaluations and the first ten regulated-industry pilots are targets. Scope, evidence rights, capacity, and start dates have to be confirmed before any contract.',
  },
  {
    title: 'Key-person company',
    body: 'The product demonstrations are founder-built. Roman Bodnarchuk leads the company. Losing that concentration of context would slow the work.',
  },
  {
    title: 'This page is not a funding portal',
    body: 'No intermediary is offering securities here. No Form C is filed for this briefing. A later Regulation Crowdfunding round, if any, would require a registered portal, escrow, and definitive disclosure. None of that exists on this page.',
  },
];

export interface FaqItem {
  q: string;
  a: string;
}

export const INVESTING_FAQS: FaqItem[] = [
  {
    q: 'Is this an offer to sell securities?',
    a: 'No. WisdomTwin is describing a proposed post-money SAFE. Specific economic terms remain to be agreed and documented. Booking a call or selecting a check size does not create an investment, a subscription, or an obligation to fund.',
  },
  {
    q: 'Why is there no share price and no bonus shares?',
    a: 'Priced stock and bonus-share schedules belong to offerings that have a price and a filed disclosure. WisdomTwin has published a target and an instrument, not a price. Stating bonus shares here would invent economics the company has not set.',
  },
  {
    q: 'How is this different from Regulation Crowdfunding?',
    a: 'A Regulation Crowdfunding offer is made through a registered intermediary, with a Form C, investment limits, cancellation rights, and escrow. This briefing is not that. It is a founder conversation about a proposed angel SAFE, plus a map of how a later community round would have to be built before anyone could use it.',
  },
  {
    q: 'How much can I invest?',
    a: 'Nothing, through this page. If a SAFE is later offered, the check size would be agreed in the documents. Crowdfunding investment limits do not apply here because no crowdfunding offering is open. They would apply only to a future offering made under those rules.',
  },
  {
    q: 'What is a post-money SAFE?',
    a: 'A SAFE is a contract that may convert into stock if a later triggering event happens, such as a priced round. “Post-money” describes how the valuation cap, if one is agreed, counts the money from the round. Until those terms are written down, there is nothing to calculate.',
  },
  {
    q: 'When would I get money back?',
    a: 'There is no schedule, dividend, or redemption right described here. Early-stage investments are illiquid. A return, if any, would depend on a later event that may never occur. Many early-stage investments return nothing.',
  },
  {
    q: 'Can I sell the SAFE or the shares?',
    a: 'Assume no. There is no market. Transfer restrictions would be in the definitive documents, which do not exist yet. A crowdfunding security, if one were ever issued, would also face statutory resale limits.',
  },
  {
    q: 'What if the company never raises the $1,000,000?',
    a: 'Then this proposed round does not close. Because this page is not taking money, there is no refund to process and no escrow to release. The company can keep building, change the plan, or not raise at all.',
  },
  {
    q: 'What if I change my mind after a conversation?',
    a: 'A conversation is not a commitment. Do not send money to a personal account, a link in email, or anyone who treats this page as a live subscribe button. If a real offering opens later, its cancellation rules will be in the offering documents, not here.',
  },
  {
    q: 'What are the tax consequences?',
    a: 'This page is not tax advice. SAFE treatment, qualified small business stock, and cross-border questions depend on your facts. Ask your own advisor before relying on any structure.',
  },
];

export const COMPANY_FAQS: FaqItem[] = [
  {
    q: 'What does WisdomTwin actually sell?',
    a: 'A governed way to move one high-consequence decision without waiting for the next meeting. The planned commercial form is an enterprise subscription plus implementation and private-deployment services. Pricing is not final. A separate buyer evaluation is USD $5,000 for two weeks, read-only, on one decision type. That fee is not an investment.',
  },
  {
    q: 'Does a Judgment Twin stand in for a person?',
    a: 'We model how a role decides, from authorized evidence. We do not clone people, and we do not replace the person accountable for the outcome. The brand line is the product constraint: WisdomTwin preserves institutional judgment.',
  },
  {
    q: 'What is true today?',
    a: 'Roman Bodnarchuk is Co-Founder and CEO. Stella Cabrera is Co-Founder, Governance, in Dubai. The company is pre-revenue, with five founder-built synthetic demonstrations, and is raising a proposed USD $1,000,000 post-money SAFE. Pilot starts and the first ten regulated pilots are targets, not signed logos.',
  },
  {
    q: 'Where does the decision run?',
    a: 'The deployment thesis is on-premises, on-device, or the customer’s private cloud, with no required third-party model egress. Each environment has to pass pilot acceptance tests before that boundary can be claimed. Air-gap is a separate, unverified profile.',
  },
  {
    q: 'How do I follow the company without investing?',
    a: 'Read wisdomtwin.ai, watch the synthetic huddle, and book 20 minutes. Investor updates described in the tiers are proposed for people in a documented round. They are not a newsletter you can buy on this page.',
  },
];

export const SOURCES: Array<{ label: string; href: string; note: string }> = [
  {
    label: 'WisdomTwin investor overview',
    href: INVESTOR_OVERVIEW_URL,
    note: 'Source for the proposed SAFE, the pre-revenue statement, and the team facts used on this page.',
  },
  {
    label: 'WisdomTwin company',
    href: COMPANY_URL,
    note: 'Source for how the company describes the work and the people.',
  },
  {
    label: 'Investor.gov',
    href: 'https://www.investor.gov/',
    note: 'U.S. Securities and Exchange Commission education for people considering any investment.',
  },
  {
    label: 'Regulation Crowdfunding, 17 CFR Part 227',
    href: 'https://www.ecfr.gov/current/title-17/chapter-II/part-227',
    note: 'The rule set a future crowdfunding offering would have to follow. It is not in effect for this briefing.',
  },
];

export const CATEGORY_NOTES = [
  {
    title: 'Typed decisions, not chat',
    body: 'WisdomTwin’s investor overview points to TypeSafe / Jev, a vendor-reported seed of about USD $40 million led by DCVC and announced around 15 September 2026, as category proof that capital is funding typed decisions. That figure is theirs, not a WisdomTwin metric. There is no partnership and no shared customer data.',
  },
  {
    title: 'Person-scale twins are a different product',
    body: 'The same overview cites Viven at about USD $35 million and Twin1 at about USD $20 million as companies that scale the person. WisdomTwin governs the decision. Those rounds are not WisdomTwin revenue, traction, or a comparable valuation.',
  },
  {
    title: 'The data has to be allowed to live there',
    body: 'Regulated buyers often cannot place judgment data on a multi-tenant decision API. On-premises, on-device, and customer private cloud are the deployment thesis. They are design intent for pilot scoping, not a live certification.',
  },
];
