import { useEffect, useMemo, useState } from 'react';
import './raise.css';
import {
  BEFORE_AFTER,
  CALENDLY_URL,
  CATEGORY_NOTES,
  COMPANY_FAQS,
  FOUNDER_EMAIL,
  FOUNDER_PHONE_DISPLAY,
  FOUNDER_PHONE_TEL,
  INDUSTRIES,
  INVESTING_FAQS,
  INVESTOR_OVERVIEW_URL,
  LAYERS,
  MODEL_STEPS,
  OFFERING_FACTS,
  OUTCOMES,
  PERK_LABELS,
  PROBLEM_POINTS,
  PROCEEDS,
  RISKS,
  SITE_URL,
  SOURCES,
  TAGLINE,
  TARGET_USD,
  TIERS,
  checksToFill,
  formatPortion,
  formatUsd,
  type FaqItem,
  type Tier,
} from './raiseData';
import { trackInvestorEvent } from '../../lib/investorAnalytics';

const NAV = [
  { href: '#opportunity', label: 'The opportunity' },
  { href: '#platform', label: 'Platform' },
  { href: '#participate', label: 'Participate' },
  { href: '#comparison', label: 'Comparison' },
  { href: '#financials', label: 'Financials' },
  { href: '#education', label: 'Investor education' },
];

function book(placement: string) {
  trackInvestorEvent('investor_cta_click', { placement: 'raise', raisePlacement: placement });
}

export function RaisePage() {
  const [tierId, setTierId] = useState(TIERS[3].id);
  const tier = TIERS.find((item) => item.id === tierId) ?? TIERS[0];

  const demoHref = import.meta.env.BASE_URL || '/';

  useEffect(() => {
    const previous = document.title;
    document.title = 'WisdomTwin | Proposed $1M SAFE briefing';
    return () => {
      document.title = previous;
    };
  }, []);

  return (
    <div className="raise-page min-h-[100dvh] pb-24 md:pb-0">
      <a
        href="#opportunity"
        className="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-50 focus:rounded-full focus:bg-[var(--cream)] focus:px-4 focus:py-2 focus:text-[var(--ink)]"
      >
        Skip to the opportunity
      </a>
      <Header />
      <main>
        <Hero tier={tier} demoHref={demoHref} />
        <Calculator tier={tier} onSelect={setTierId} />
        <Platform demoHref={demoHref} />
        <Problem />
        <Method />
        <Markets />
        <Participate selectedId={tier.id} onSelect={setTierId} />
        <Comparison />
        <Founder />
        <Financials />
        <Education />
        <Close />
      </main>
      <Footer />
      <MobileBar />
    </div>
  );
}

function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-[#0b1f3a]/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 md:px-6">
        <a href="#top" className="flex items-center gap-2 text-[var(--cream)] no-underline">
          <Mark />
          <span className="text-sm font-semibold tracking-[0.16em] uppercase">WisdomTwin</span>
        </a>
        <nav className="hidden items-center gap-5 lg:flex" aria-label="Page">
          {NAV.map((item) => (
            <a key={item.href} href={item.href} className="text-sm text-[var(--cream-dim)] no-underline hover:text-[var(--cream)]">
              {item.label}
            </a>
          ))}
        </nav>
        <a href={CALENDLY_URL} target="_blank" rel="noreferrer" className="raise-cta !px-4 !py-2 text-sm" onClick={() => book('header')}>
          Book 20 min
        </a>
      </div>
      <nav className="flex gap-4 overflow-x-auto px-4 pb-3 lg:hidden" aria-label="Page">
        {NAV.map((item) => (
          <a key={item.href} href={item.href} className="shrink-0 text-sm text-[var(--cream-dim)] no-underline">
            {item.label}
          </a>
        ))}
      </nav>
    </header>
  );
}

function Mark() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
      <circle cx="8" cy="11" r="6" fill="none" stroke="#C8A45D" strokeWidth="1.4" />
      <circle cx="14" cy="11" r="6" fill="none" stroke="#F37021" strokeWidth="1.4" />
    </svg>
  );
}

function Hero({ tier, demoHref }: { tier: Tier; demoHref: string }) {
  return (
    <section id="opportunity" className="scroll-mt-28 mx-auto grid max-w-6xl gap-8 px-4 py-12 md:px-6 md:py-16 lg:grid-cols-[1.15fr_0.85fr]">
      <div id="top">
        <p className="raise-kicker">Proposed angel round</p>
        <h1 className="raise-display mt-4 text-4xl leading-[1.05] text-[var(--cream)] md:text-6xl">
          Judgment, available when the decision cannot wait.
        </h1>
        <p className="mt-5 max-w-xl text-lg leading-relaxed text-[var(--cream-dim)]">
          WisdomTwin, Inc. is a Delaware company building a sovereign judgment layer for regulated enterprises.
          The published plan is a proposed {formatUsd(TARGET_USD)} post-money SAFE. The cap, the discount, and every
          other economic term are still to be agreed. This page is the briefing. It is not the offering.
        </p>
        <p className="mt-4 max-w-xl text-base leading-relaxed text-[var(--cream)]">{TAGLINE}</p>
        <dl className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            [formatUsd(TARGET_USD), 'Proposed SAFE target'],
            ['5', 'Synthetic demos'],
            ['$0', 'Product revenue'],
            ['0', 'Production users'],
          ].map(([value, label]) => (
            <div key={label} className="raise-card rounded-2xl p-3">
              <dt className="raise-display text-2xl text-[var(--cream)]">{value}</dt>
              <dd className="mt-1 text-xs leading-snug text-[var(--cream-dim)]">{label}</dd>
            </div>
          ))}
        </dl>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <a href={CALENDLY_URL} target="_blank" rel="noreferrer" className="raise-cta" onClick={() => book('hero')}>
            Book 20 min with Roman
          </a>
          <a href={demoHref} className="raise-cta-ghost">
            Watch the synthetic huddle
          </a>
        </div>
        <p className="mt-4 text-sm text-[var(--cream-dim)]">
          Text anytime{' '}
          <a className="text-[var(--cream)]" href={`tel:${FOUNDER_PHONE_TEL}`}>
            {FOUNDER_PHONE_DISPLAY}
          </a>
          {' · '}
          <a className="text-[var(--cream)]" href={`mailto:${FOUNDER_EMAIL}`}>
            {FOUNDER_EMAIL}
          </a>
        </p>
      </div>
      <aside className="raise-card h-fit rounded-3xl p-5 md:p-6" aria-label="Offering facts">
        <p className="raise-kicker">Live with founder Roman Bodnarchuk</p>
        <h2 className="raise-display mt-3 text-3xl">The round, as published</h2>
        <p className="mt-2 text-sm leading-relaxed text-[var(--cream-dim)]">
          Selected conversation: {tier.name} · {formatUsd(tier.amount)}. That selection is a calculator, not a commitment.
        </p>
        <dl className="mt-5 divide-y divide-white/10">
          {OFFERING_FACTS.map((fact) => (
            <div key={fact.label} className="grid grid-cols-[9.5rem_1fr] gap-3 py-3">
              <dt className="text-xs tracking-wide text-[var(--cream-dim)] uppercase">{fact.label}</dt>
              <dd>
                <p className="font-semibold text-[var(--cream)]">{fact.value}</p>
                {fact.note ? <p className="mt-1 text-xs leading-relaxed text-[var(--cream-dim)]">{fact.note}</p> : null}
              </dd>
            </div>
          ))}
        </dl>
        <div className="mt-2">
          <div className="mb-2 flex items-center justify-between text-xs text-[var(--cream-dim)]">
            <span>Funds accepted on this page</span>
            <span>$0 of {formatUsd(TARGET_USD)}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-white/10" role="img" aria-label="No funds accepted. Progress is zero.">
            <div className="h-full w-0 bg-[var(--brand-orange)]" />
          </div>
        </div>
        <a href="#calculator" className="raise-cta mt-5 w-full">
          See a check against the target
        </a>
      </aside>
    </section>
  );
}

function Calculator({ tier, onSelect }: { tier: Tier; onSelect: (id: string) => void }) {
  const fill = checksToFill(tier.amount);
  const fillLabel = Number.isInteger(fill) ? fill.toLocaleString('en-US') : fill.toFixed(1);

  return (
    <section id="calculator" className="scroll-mt-28 border-y border-white/10 bg-black/25">
      <div className="mx-auto max-w-6xl px-4 py-14 md:px-6">
        <p className="raise-kicker">Participation calculator</p>
        <h2 className="raise-display mt-3 max-w-3xl text-4xl">What a check is, against the published target.</h2>
        <p className="mt-4 max-w-3xl text-[var(--cream-dim)] leading-relaxed">
          The more you would be prepared to discuss, the more of the founder’s time the conversation can use. It does not
          unlock bonus shares, a lower valuation, or equity. Ownership cannot be calculated until a cap and a discount exist.
        </p>
        <div className="mt-8 flex flex-wrap gap-2" role="group" aria-label="Select a check size">
          {TIERS.map((item) => (
            <button
              key={item.id}
              type="button"
              className="raise-amount"
              aria-pressed={item.id === tier.id}
              onClick={() => onSelect(item.id)}
            >
              {formatUsd(item.amount)}
            </button>
          ))}
        </div>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <Result value={formatUsd(tier.amount)} label={`${tier.name} check`} />
          <Result value={formatPortion(tier.amount)} label="of the $1,000,000 target" />
          <Result value={fillLabel} label="checks of this size fill the target" />
        </div>
        <article className="raise-card mt-4 rounded-3xl p-5 md:p-6">
          <h3 className="raise-display text-2xl">{tier.name}</h3>
          <p className="mt-2 text-[var(--cream)]">{tier.summary}</p>
          <p className="mt-2 text-sm leading-relaxed text-[var(--cream-dim)]">{tier.detail}</p>
          <ul className="mt-4 grid gap-2 sm:grid-cols-2">
            {tier.perks.map((perk) => (
              <li key={perk} className="text-sm text-[var(--cream)]">
                <span className="mr-2 text-[var(--brand-gold)]" aria-hidden="true">
                  ✓
                </span>
                {PERK_LABELS[perk]}
                <span className="text-[var(--cream-dim)]"> — proposed</span>
              </li>
            ))}
          </ul>
          <div className="mt-5 flex flex-wrap gap-3">
            <a href={CALENDLY_URL} target="_blank" rel="noreferrer" className="raise-cta" onClick={() => book(`calculator-${tier.id}`)}>
              Discuss {formatUsd(tier.amount)}
            </a>
            <a href="#participate" className="raise-cta-ghost">
              Read every tier
            </a>
          </div>
        </article>
      </div>
    </section>
  );
}

function Result({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-5">
      <p className="raise-display text-4xl text-[var(--cream)]">{value}</p>
      <p className="mt-2 text-sm text-[var(--cream-dim)]">{label}</p>
    </div>
  );
}

function Platform({ demoHref }: { demoHref: string }) {
  return (
    <section id="platform" className="scroll-mt-28 mx-auto max-w-6xl px-4 py-16 md:px-6">
      <p className="raise-kicker">Meet WisdomTwin</p>
      <h2 className="raise-display mt-3 max-w-3xl text-4xl md:text-5xl">
        The market is pricing judgment as a function call. We are building the workflow where the data is allowed to live.
      </h2>
      <p className="mt-4 max-w-3xl leading-relaxed text-[var(--cream-dim)]">
        High-consequence decisions still queue behind calendars, inboxes, and a few people. WisdomTwin is being built so
        the right judgment, evidence, limits, and escalation path can travel with the decision, and a named human stays
        accountable. We do not sell autonomy.
      </p>
      <div className="mt-10 grid gap-4 md:grid-cols-2">
        {LAYERS.map((layer) => (
          <article key={layer.index} className="raise-card rounded-3xl p-5">
            <p className="raise-kicker">{layer.index}</p>
            <h3 className="raise-display mt-2 text-2xl">{layer.title}</h3>
            <p className="mt-3 text-sm leading-relaxed text-[var(--cream-dim)]">{layer.body}</p>
            <p className="mt-4 text-xs tracking-wide text-[var(--brand-gold)] uppercase">{layer.status}</p>
          </article>
        ))}
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-3">
        {OUTCOMES.map((item) => (
          <article key={item.title} className="rounded-3xl border border-[var(--brand-gold)]/30 p-5">
            <h3 className="text-lg font-semibold">{item.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-[var(--cream-dim)]">{item.body}</p>
          </article>
        ))}
      </div>
      <p className="mt-6 text-sm text-[var(--cream-dim)]">
        The huddle on this site is one of five founder-built synthetic demonstrations.{' '}
        <a href={demoHref} className="text-[var(--cream)] underline">
          Watch it
        </a>
        . It is not a customer result.
      </p>
    </section>
  );
}

function Problem() {
  return (
    <section id="problem" className="scroll-mt-28 border-y border-white/10 bg-black/20">
      <div className="mx-auto max-w-6xl px-4 py-16 md:px-6">
        <p className="raise-kicker">The wait</p>
        <h2 className="raise-display mt-3 max-w-3xl text-4xl">Important decisions still wait for people, calendars, and reconstructed context.</h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PROBLEM_POINTS.map((point) => (
            <article key={point.value} className="raise-card rounded-3xl p-5">
              <p className="raise-display text-3xl text-[var(--brand-gold)]">{point.value}</p>
              <p className="mt-3 text-sm leading-relaxed text-[var(--cream-dim)]">{point.label}</p>
            </article>
          ))}
        </div>
        <div className="mt-8 grid gap-6 md:grid-cols-2">
          <p className="leading-relaxed text-[var(--cream)]">
            The answer may already exist somewhere. The judgment does not. It is fragmented across senior people, meetings,
            policies, precedent, exceptions, inboxes, and documents.
          </p>
          <p className="leading-relaxed text-[var(--cream-dim)]">
            AI made fluent answers cheap. A regulated workflow still needs a typed decision: a bounded action, evidence,
            uncertainty, a policy result, authorization, and a named human release. A paragraph that sounds plausible is not
            that contract.
          </p>
        </div>
      </div>
    </section>
  );
}

function Method() {
  return (
    <section id="method" className="scroll-mt-28 mx-auto max-w-6xl px-4 py-16 md:px-6">
      <p className="raise-kicker">How the change is delivered</p>
      <h2 className="raise-display mt-3 text-4xl">Before the room. After the room.</h2>
      <div className="raise-table-wrap mt-8">
        <table className="raise-table min-w-[640px]">
          <thead>
            <tr>
              <th scope="col">Decision</th>
              <th scope="col">Before</th>
              <th scope="col">After</th>
            </tr>
          </thead>
          <tbody>
            {BEFORE_AFTER.map((row) => (
              <tr key={row.topic}>
                <th scope="row">{row.topic}</th>
                <td className="text-left text-[var(--cream-dim)]">{row.before}</td>
                <td className="text-left">{row.after}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h3 className="raise-display mt-14 text-3xl">Pilot one workflow. Expand with evidence.</h3>
      <ol className="mt-6 grid gap-4 md:grid-cols-2">
        {MODEL_STEPS.map((step) => (
          <li key={step.step} className="raise-card rounded-3xl p-5">
            <p className="raise-kicker">{step.step}</p>
            <h4 className="mt-2 text-xl font-semibold">{step.title}</h4>
            <p className="mt-2 text-sm leading-relaxed text-[var(--cream-dim)]">{step.body}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

function Markets() {
  return (
    <section id="markets" className="scroll-mt-28 border-y border-white/10 bg-black/20">
      <div className="mx-auto max-w-6xl px-4 py-16 md:px-6">
        <p className="raise-kicker">Where the wait costs the most</p>
        <h2 className="raise-display mt-3 max-w-3xl text-4xl">Regulated work first. No logos claimed.</h2>
        <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {INDUSTRIES.map((industry) => (
            <article key={industry.title} className="raise-card rounded-3xl p-5">
              <h3 className="text-xl font-semibold">{industry.title}</h3>
              <p className="mt-3 text-sm text-[var(--cream-dim)]">
                <span className="text-[var(--cream)]">Before. </span>
                {industry.before}
              </p>
              <p className="mt-2 text-sm text-[var(--cream-dim)]">
                <span className="text-[var(--cream)]">After. </span>
                {industry.after}
              </p>
            </article>
          ))}
        </div>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {CATEGORY_NOTES.map((note) => (
            <article key={note.title} className="rounded-3xl border border-white/10 p-5">
              <h3 className="text-lg font-semibold">{note.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-[var(--cream-dim)]">{note.body}</p>
            </article>
          ))}
        </div>
        <p className="mt-6 text-sm text-[var(--cream-dim)]">
          Adjacent financings are attributed on the{' '}
          <a href={INVESTOR_OVERVIEW_URL} className="text-[var(--cream)] underline">
            investor overview
          </a>
          . They are not WisdomTwin metrics.
        </p>
      </div>
    </section>
  );
}

function Participate({ selectedId, onSelect }: { selectedId: string; onSelect: (id: string) => void }) {
  return (
    <section id="participate" className="scroll-mt-28 mx-auto max-w-6xl px-4 py-16 md:px-6">
      <p className="raise-kicker">Angel and community interest</p>
      <h2 className="raise-display mt-3 max-w-3xl text-4xl">Choose a conversation. Not a share class.</h2>
      <p className="mt-4 max-w-3xl leading-relaxed text-[var(--cream-dim)]">
        Every check below is a proposed way to talk about the same unpublished SAFE. Higher amounts propose more access
        to the founders’ time. They do not propose more favorable securities terms. Those terms, when they exist, should
        be the same instrument for the round unless definitive documents say otherwise.
      </p>
      <div className="mt-8 grid gap-4 md:grid-cols-2">
        {TIERS.map((tier) => (
          <article key={tier.id} className="raise-card flex flex-col rounded-3xl p-5" id={`tier-${tier.id}`}>
            <div className="flex items-baseline justify-between gap-3">
              <h3 className="text-xl font-semibold">{tier.name}</h3>
              <p className="raise-display text-2xl">{formatUsd(tier.amount)}</p>
            </div>
            <p className="mt-1 text-xs tracking-wide text-[var(--brand-gold)] uppercase">
              {formatPortion(tier.amount)} of the target
            </p>
            <p className="mt-3 text-sm leading-relaxed text-[var(--cream)]">{tier.summary}</p>
            <p className="mt-2 text-sm leading-relaxed text-[var(--cream-dim)]">{tier.detail}</p>
            <ul className="mt-4 space-y-1.5 text-sm text-[var(--cream-dim)]">
              {tier.perks.map((perk) => (
                <li key={perk}>· {PERK_LABELS[perk]}</li>
              ))}
            </ul>
            <div className="mt-5 flex flex-wrap gap-2">
              <button
                type="button"
                className="raise-amount"
                aria-pressed={selectedId === tier.id}
                onClick={() => {
                  onSelect(tier.id);
                  document.getElementById('calculator')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }}
              >
                {selectedId === tier.id ? 'Showing in calculator' : 'Show in calculator'}
              </button>
              <a
                href={CALENDLY_URL}
                target="_blank"
                rel="noreferrer"
                className="raise-cta !py-2 text-sm"
                onClick={() => book(`tier-${tier.id}`)}
              >
                Book 20 min
              </a>
            </div>
          </article>
        ))}
      </div>
      <div className="mt-8 grid gap-4 md:grid-cols-2">
        <article className="rounded-3xl border border-white/10 p-5">
          <h3 className="text-lg font-semibold">Angel path</h3>
          <p className="mt-2 text-sm leading-relaxed text-[var(--cream-dim)]">
            A direct conversation toward the proposed post-money SAFE. Roman books 20 minutes at the link used across
            WisdomTwin. Larger checks can ask for the working sessions above. Nothing is funded in the meeting.
          </p>
        </article>
        <article className="rounded-3xl border border-white/10 p-5">
          <h3 className="text-lg font-semibold">Crowdfunding path</h3>
          <p className="mt-2 text-sm leading-relaxed text-[var(--cream-dim)]">
            A later Regulation Crowdfunding offer would need a registered funding portal, a Form C, educational
            materials delivered by that portal, investment limits, cancellation rights, and an escrow that WisdomTwin
            does not touch. This page is the reading order for that kind of campaign. It is not the campaign.
          </p>
        </article>
      </div>
    </section>
  );
}

function Comparison() {
  const rows = useMemo(
    () =>
      [
        { label: 'Check', cell: (tier: Tier) => formatUsd(tier.amount) },
        { label: 'Share of the $1M target', cell: (tier: Tier) => formatPortion(tier.amount) },
        {
          label: 'Checks that fill the target',
          cell: (tier: Tier) => checksToFill(tier.amount).toLocaleString('en-US'),
        },
        { label: 'Instrument', cell: () => 'Proposed SAFE' },
        { label: 'Ownership stated', cell: () => 'No' },
        { label: 'Bonus shares', cell: () => 'None' },
        ...Object.entries(PERK_LABELS).map(([id, label]) => ({
          label,
          cell: (tier: Tier) => (tier.perks.includes(id as Tier['perks'][number]) ? 'Proposed' : '—'),
        })),
      ] as const,
    [],
  );

  return (
    <section id="comparison" className="scroll-mt-28 border-y border-white/10 bg-black/20">
      <div className="mx-auto max-w-6xl px-4 py-16 md:px-6">
        <p className="raise-kicker">Comparison</p>
        <h2 className="raise-display mt-3 text-4xl">Same security. Different access.</h2>
        <p className="mt-4 max-w-3xl text-sm leading-relaxed text-[var(--cream-dim)]">
          “Proposed” means Roman can offer the time if a round is actually documented and capacity exists. It is not a
          contractual perk and not consideration for a security.
        </p>
        <div className="raise-table-wrap mt-8">
          <table className="raise-table raise-table-wide">
            <thead>
              <tr>
                <th scope="col">Perk</th>
                {TIERS.map((tier) => (
                  <th key={tier.id} scope="col">
                    {tier.name}
                    <span className="mt-1 block font-normal text-[var(--cream-dim)]">{formatUsd(tier.amount)}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.label}>
                  <th scope="row">{row.label}</th>
                  {TIERS.map((tier) => (
                    <td key={tier.id}>{row.cell(tier)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function Founder() {
  return (
    <section id="founder" className="scroll-mt-28 mx-auto grid max-w-6xl gap-8 px-4 py-16 md:grid-cols-[0.9fr_1.1fr] md:px-6">
      <div>
        <p className="raise-kicker">Message from the founder</p>
        <h2 className="raise-display mt-3 text-4xl">The work was ready Tuesday. The calendar said Thursday.</h2>
        <div className="mt-8 space-y-5">
          <Person
            initials="RB"
            name="Roman Bodnarchuk"
            role="Co-Founder and CEO"
            body="Roman founded N5R in 1998. His founder account spans twenty-eight years selling into P&G across 21 brands, Apple, Microsoft, General Motors, Marriott and Wave, across 15 countries and 5 continents. Those companies were his classrooms, not WisdomTwin deployments."
          />
          <Person
            initials="SC"
            name="Stella Cabrera"
            role="Co-Founder, Governance (Dubai)"
            body="Stella brings more than 20 years in financial services and technology. EDM Association lists her as Senior Advisor, Global Strategic Relations and MENA Lead, and as a former President and current Board Chair of RMA Toronto."
          />
        </div>
      </div>
      <blockquote className="raise-card rounded-3xl p-6 md:p-8">
        <p className="text-lg leading-relaxed text-[var(--cream)]">
          I spent twenty-eight years in enterprise rooms where Tuesday’s prepared work waited for Thursday’s meeting. I am
          building WisdomTwin so the decision can move with evidence, permissions, and human authority intact.
        </p>
        <p className="mt-4 leading-relaxed text-[var(--cream-dim)]">
          Meetings are the cage. WisdomTwin is the door. The cage is making a prepared decision wait for the room. It is
          not governance, the required approval, or the human who remains accountable.
        </p>
        <p className="mt-4 leading-relaxed text-[var(--cream-dim)]">
          We are pre-revenue. The demonstrations are synthetic and I built them. The round I am willing to discuss is a
          proposed one million dollar post-money SAFE, and the economic terms are not yet agreed. I would rather show you
          a governed refusal than a page that invents traction.
        </p>
        <footer className="mt-6 text-sm text-[var(--brand-gold)]">Roman Bodnarchuk, Co-Founder and CEO</footer>
        <a href={CALENDLY_URL} target="_blank" rel="noreferrer" className="raise-cta mt-6" onClick={() => book('founder')}>
          Book 20 min
        </a>
      </blockquote>
    </section>
  );
}

function Person({ initials, name, role, body }: { initials: string; name: string; role: string; body: string }) {
  return (
    <article className="flex gap-4">
      <div className="grid h-12 w-12 shrink-0 place-items-center rounded-full border border-[var(--brand-gold)]/50 text-sm text-[var(--brand-gold)]">
        {initials}
      </div>
      <div>
        <h3 className="font-semibold">{name}</h3>
        <p className="text-sm text-[var(--brand-gold)]">{role}</p>
        <p className="mt-2 text-sm leading-relaxed text-[var(--cream-dim)]">{body}</p>
      </div>
    </article>
  );
}

function Financials() {
  return (
    <section id="financials" className="scroll-mt-28 border-y border-white/10 bg-black/20">
      <div className="mx-auto max-w-6xl px-4 py-16 md:px-6">
        <p className="raise-kicker">Financials and details</p>
        <h2 className="raise-display mt-3 text-4xl">Illustrative use of a $1,000,000 raise.</h2>
        <p className="mt-4 max-w-3xl text-sm leading-relaxed text-[var(--cream-dim)]">
          WisdomTwin has published the target and the instrument, not a use-of-proceeds table filed with anyone. The
          split below is a planning view of that single target. There is no second “maximum offering” column, because no
          maximum has been authorized. Intermediary fees are zero here because no intermediary is selling securities.
        </p>
        <div className="raise-table-wrap mt-8">
          <table className="raise-table min-w-[680px]">
            <thead>
              <tr>
                <th scope="col">Use</th>
                <th scope="col">Share of target</th>
                <th scope="col">Amount</th>
                <th scope="col">What it is for</th>
              </tr>
            </thead>
            <tbody>
              {PROCEEDS.map((row) => (
                <tr key={row.use}>
                  <th scope="row">{row.use}</th>
                  <td>{row.pct}</td>
                  <td>{formatUsd(row.amount)}</td>
                  <td className="text-left text-[var(--cream-dim)]">{row.detail}</td>
                </tr>
              ))}
              <tr>
                <th scope="row">Total</th>
                <td>100%</td>
                <td>{formatUsd(TARGET_USD)}</td>
                <td className="text-left">Equals the published target. Not cash on hand.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <h3 className="raise-display mt-12 text-3xl">Risks, in plain language</h3>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {RISKS.map((risk) => (
            <article key={risk.title} className="raise-card rounded-3xl p-5">
              <h4 className="font-semibold">{risk.title}</h4>
              <p className="mt-2 text-sm leading-relaxed text-[var(--cream-dim)]">{risk.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function Education() {
  return (
    <section id="education" className="scroll-mt-28 mx-auto max-w-6xl px-4 py-16 md:px-6">
      <p className="raise-kicker">Investor education</p>
      <h2 className="raise-display mt-3 text-4xl">Read this before you treat any startup check as a plan.</h2>
      <p className="mt-4 max-w-3xl text-sm leading-relaxed text-[var(--cream-dim)]">
        Early-stage securities are speculative, illiquid, and can go to zero. Net worth, income, and how much you can
        afford to lose are questions for you and your advisor. This section is general education from the company. It is
        not a portal’s required educational materials, because no portal is involved.
      </p>
      <div className="mt-8 grid gap-8 md:grid-cols-2">
        <FaqGroup title="Investing questions" items={INVESTING_FAQS} />
        <FaqGroup title="WisdomTwin questions" items={COMPANY_FAQS} />
      </div>
      <h3 className="mt-12 text-lg font-semibold">Sources</h3>
      <ul className="mt-4 space-y-3">
        {SOURCES.map((source) => (
          <li key={source.href} className="text-sm leading-relaxed text-[var(--cream-dim)]">
            <a href={source.href} className="text-[var(--cream)] underline" target="_blank" rel="noreferrer">
              {source.label}
            </a>
            {' — '}
            {source.note}
          </li>
        ))}
      </ul>
    </section>
  );
}

function FaqGroup({ title, items }: { title: string; items: FaqItem[] }) {
  return (
    <div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <div className="mt-3 divide-y divide-white/10 rounded-3xl border border-white/10">
        {items.map((item) => (
          <details key={item.q} className="raise-faq group p-4">
            <summary className="flex items-start justify-between gap-4 font-medium">
              {item.q}
              <span className="text-[var(--brand-gold)] group-open:rotate-45" aria-hidden="true">
                +
              </span>
            </summary>
            <p className="mt-3 text-sm leading-relaxed text-[var(--cream-dim)]">{item.a}</p>
          </details>
        ))}
      </div>
    </div>
  );
}

function Close() {
  return (
    <section id="close" className="scroll-mt-28 mx-auto max-w-6xl px-4 py-16 md:px-6">
      <div className="raise-card rounded-[2rem] px-6 py-10 text-center md:px-12">
        <p className="raise-kicker">WisdomTwin preserves institutional judgment.</p>
        <h2 className="raise-display mt-4 text-4xl md:text-5xl">Discuss the proposed round. Do not send money to this page.</h2>
        <p className="mx-auto mt-4 max-w-2xl text-[var(--cream-dim)] leading-relaxed">
          Book twenty minutes. Bring the decision you would want governed, or the questions you would ask before a SAFE
          exists. The public product story lives at{' '}
          <a href={SITE_URL} className="text-[var(--cream)] underline">
            wisdomtwin.ai
          </a>
          .
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <a href={CALENDLY_URL} target="_blank" rel="noreferrer" className="raise-cta" onClick={() => book('close')}>
            Book 20 min
          </a>
          <a href={INVESTOR_OVERVIEW_URL} className="raise-cta-ghost" target="_blank" rel="noreferrer">
            Read the investor overview
          </a>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-white/10 px-4 py-10 md:px-6">
      <div className="mx-auto max-w-6xl space-y-4 text-xs leading-relaxed text-[var(--cream-dim)]">
        <p className="text-sm text-[var(--cream)]">{TAGLINE}</p>
        <p>
          WisdomTwin, Inc., a Delaware corporation, founder-built in Toronto. 90 Stadium Road, Suite 911, Toronto, ON
          M5V 3W5, Canada. {FOUNDER_EMAIL}. Text {FOUNDER_PHONE_DISPLAY}.
        </p>
        <p>
          This page is an informational briefing for prospective angels and for readers studying how a future exempt
          offering might be structured. It is not an offer to sell, or a solicitation of an offer to buy, any security.
          No money is being solicited or accepted through this page. No Form C has been filed for this briefing. If an
          offering is made, it will be made only through definitive documents and, if applicable, a registered funding
          portal or another available exemption. WisdomTwin does not provide investment, legal, or tax advice.
        </p>
        <p>
          Securities investments can result in the loss of the entire amount invested. Non-public securities are
          illiquid. Adjacent-company financings cited from WisdomTwin’s own investor overview are not WisdomTwin
          results. Demonstrations are synthetic. Design targets are targets.
        </p>
        <p>© {new Date().getFullYear()} WisdomTwin, Inc.</p>
      </div>
    </footer>
  );
}

function MobileBar() {
  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t border-white/10 bg-[#0b1f3a]/95 p-3 backdrop-blur md:hidden">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs leading-snug text-[var(--cream-dim)]">
          Proposed {formatUsd(TARGET_USD)} SAFE
          <span className="block text-[var(--cream)]">Not open for funds</span>
        </p>
        <a href={CALENDLY_URL} target="_blank" rel="noreferrer" className="raise-cta !py-2 text-sm" onClick={() => book('mobile-bar')}>
          Book 20 min
        </a>
      </div>
    </div>
  );
}
