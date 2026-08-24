import { SyntheticDataDisclosure } from './SyntheticDataDisclosure';
import { InvestorModeToggle } from './InvestorModeToggle';

interface Props {
  investorMode: boolean;
  showInvestorToggle?: boolean;
  onInvestorModeChange: (on: boolean) => void;
  onStart: () => void;
}

const DEMO_SIGNALS = [
  { value: 'Linked', label: 'source evidence' },
  { value: 'Checked', label: 'policy gates' },
  { value: 'Named', label: 'human escalation' },
  { value: 'Logged', label: 'audit trail' },
];

const OUTCOME_LINES = [
  'Relevant role perspectives assembled without waiting for another calendar cycle',
  'Evidence, policy context, dissent, and uncertainty remain visible',
  'The workflow resolves to accountable action, escalation, or safe decline',
];

export function StartExperience({
  investorMode,
  showInvestorToggle = false,
  onInvestorModeChange,
  onStart,
}: Props) {
  return (
    <div
      className="absolute inset-0 z-40 flex flex-col bg-black/80 backdrop-blur-sm"
      data-testid="start-experience"
    >
      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4 md:flex md:items-center md:justify-center">
      <div className="relative w-full max-w-2xl overflow-hidden rounded-3xl border border-white/10 bg-[var(--ink-elevated)] p-5 shadow-2xl md:p-8">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[var(--brand-gold)]/70 to-transparent" />
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-[11px] font-semibold tracking-[0.28em] text-[var(--brand-gold)] uppercase">
            WisdomTwin
          </p>
          <p className="text-[10px] tracking-[0.16em] text-[var(--cream-dim)] uppercase">
            Synthetic demo film · 2:54
          </p>
        </div>
        <h1
          className="mt-4 text-3xl leading-[1.05] text-[var(--cream)] md:text-5xl"
          style={{ fontFamily: 'var(--font-display)' }}
        >
          Stop waiting for judgment. Start moving at AI-native speed.
        </h1>
        <p
          className="mt-2 text-sm text-[var(--warm)] italic md:text-base"
          style={{ fontFamily: 'var(--font-display)' }}
        >
          From meeting-speed coordination to a governed decision workflow while the question is still live.
        </p>
        <p className="mt-3 max-w-xl text-sm leading-relaxed text-[var(--cream)] md:text-base">
          Sunday, 9:40 p.m. The board packet locks tomorrow. The evidence is scattered, the relevant
          executives are not all available, and the decision cannot wait for another meeting. Watch the
          workflow assemble role-specific judgment, precedent, policy context, dissent, escalation, and
          accountable human authority so the decision can move forward without hiding uncertainty.
        </p>
        <p className="mt-2 text-[11px] leading-relaxed text-[var(--cream-dim)]">
          WisdomTwin is the mechanism behind the change: role-specific Wisdom Twins, governed huddles,
          evidence-linked reasoning, and explicit human escalation.
        </p>

        <dl className="mt-6 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 sm:grid-cols-4">
          {DEMO_SIGNALS.map((metric) => (
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
            What changes
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
          className="mt-5 w-full rounded-2xl bg-[var(--cream)] px-4 py-4 text-sm font-semibold tracking-[0.12em] text-[var(--ink)] uppercase transition hover:bg-white"
        >
          Watch the 2:54 synthetic demo
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
      <div className="shrink-0 border-t border-white/10 bg-black/70 px-4 py-3 md:hidden">
        <button
          type="button"
          onClick={onStart}
          className="w-full rounded-2xl bg-[var(--cream)] px-4 py-3 text-sm font-semibold tracking-[0.12em] text-[var(--ink)] uppercase"
        >
          Watch the 2:54 synthetic demo
        </button>
      </div>
    </div>
  );
}
