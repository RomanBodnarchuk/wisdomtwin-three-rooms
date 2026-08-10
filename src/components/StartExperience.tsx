import { SyntheticDataDisclosure } from './SyntheticDataDisclosure';
import { InvestorModeToggle } from './InvestorModeToggle';

interface Props {
  investorMode: boolean;
  showInvestorToggle?: boolean;
  onInvestorModeChange: (on: boolean) => void;
  onStart: () => void;
}

const PROOF_METRICS = [
  { value: '12,400', label: 'decisions reviewed' },
  { value: '91 / 9', label: 'policy / human split' },
  { value: '62→91%', label: 'confidence lift' },
  { value: '$7.4M', label: 'governed phase one' },
];

const OUTCOME_LINES = [
  'Five executive perspectives convened with policy and precedent attached',
  'Low-confidence judgment withheld and routed to a named human',
  'Board package, citations, dissent, objections, and audit record completed',
];

export function StartExperience({
  investorMode,
  showInvestorToggle = false,
  onInvestorModeChange,
  onStart,
}: Props) {
  return (
    <div
      className="absolute inset-0 z-40 flex items-start justify-center overflow-y-auto bg-black/80 px-5 py-4 backdrop-blur-sm md:items-center"
      data-testid="start-experience"
    >
      <div className="relative w-full max-w-2xl overflow-hidden rounded-3xl border border-white/10 bg-[var(--ink-elevated)] p-6 shadow-2xl md:p-8">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[var(--brand-gold)]/70 to-transparent" />
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-[11px] font-semibold tracking-[0.28em] text-[var(--brand-gold)] uppercase">
            WisdomTwin
          </p>
          <p className="text-[10px] tracking-[0.16em] text-[var(--cream-dim)] uppercase">
            Investor film · 2:54
          </p>
        </div>
        <h1
          className="mt-4 text-3xl leading-[1.05] text-[var(--cream)] md:text-5xl"
          style={{ fontFamily: 'var(--font-display)' }}
        >
          Three weeks of executive coordination. One governed decision in 8:42.
        </h1>
        <p
          className="mt-2 text-sm text-[var(--warm)] italic md:text-base"
          style={{ fontFamily: 'var(--font-display)' }}
        >
          WisdomTwin preserves institutional judgment.
        </p>
        <p className="mt-3 max-w-xl text-sm leading-relaxed text-[var(--cream)] md:text-base">
          Sunday, 9:40 p.m. The board packet locks tomorrow. Watch WisdomTwin turn institutional
          memory into a board-ready decision—without erasing evidence, dissent, or human judgment.
        </p>
        <p className="mt-2 text-[11px] leading-relaxed text-[var(--cream-dim)]">
          Wisdom Twins join any huddle surface—Teams, Zoom, Slack—or the one-press WisdomTwin app.
        </p>

        <dl className="mt-6 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 sm:grid-cols-4">
          {PROOF_METRICS.map((metric) => (
            <div key={metric.label} className="bg-[var(--ink-panel)] px-3 py-3">
              <dd className="text-lg font-semibold tabular-nums text-[var(--cream)]">{metric.value}</dd>
              <dt className="mt-1 text-[9px] leading-tight tracking-[0.1em] text-[var(--cream-dim)] uppercase">
                {metric.label}
              </dt>
            </div>
          ))}
        </dl>

        <div className="mt-5 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
          <p className="text-[10px] tracking-[0.18em] text-[var(--cream-dim)] uppercase">
            What investors should watch for
          </p>
          <ul className="mt-2 grid gap-2 text-sm leading-snug text-[var(--cream)] md:grid-cols-3">
            {OUTCOME_LINES.map((line) => (
              <li key={line} className="flex gap-2">
                <span className="mt-0.5 text-[var(--secure)]">✓</span>
                <span>{line}</span>
              </li>
            ))}
          </ul>
        </div>

        <button
          type="button"
          onClick={onStart}
          data-testid="btn-start"
          className="mt-6 w-full rounded-2xl bg-[var(--cream)] px-4 py-4 text-sm font-semibold tracking-[0.12em] text-[var(--ink)] uppercase transition hover:bg-white"
        >
          Watch the 2:54 investor film
        </button>

        <p className="mt-3 text-center text-[11px] text-[var(--cream-dim)]">
          Captions on · Space to pause · M mute · C captions
        </p>

        {showInvestorToggle && (
          <div className="mt-5 space-y-3 border-t border-white/5 pt-4">
            <InvestorModeToggle on={investorMode} onChange={onInvestorModeChange} />
          </div>
        )}

        <div className="mt-4 text-center">
          <SyntheticDataDisclosure compact />
        </div>
      </div>
    </div>
  );
}
