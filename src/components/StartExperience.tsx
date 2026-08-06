import { SyntheticDataDisclosure } from './SyntheticDataDisclosure';
import { CutSelector } from './CutSelector';
import { InvestorModeToggle } from './InvestorModeToggle';
import type { CutId } from '../types/timeline';

interface Props {
  cutId: CutId;
  investorMode: boolean;
  showInvestorToggle?: boolean;
  onCutChange: (cut: CutId) => void;
  onInvestorModeChange: (on: boolean) => void;
  onStart: () => void;
}

const OUTCOME_LINES = [
  'Board package complete — slide 14 updated, financial appendix regenerated',
  'Dissent preserved · legal citations attached · 3 objections pre-answered',
  'Consensus confidence 94% — with a full audit trail',
];

export function StartExperience({
  cutId,
  investorMode,
  showInvestorToggle = false,
  onCutChange,
  onInvestorModeChange,
  onStart,
}: Props) {
  return (
    <div
      className="absolute inset-0 z-40 flex items-center justify-center bg-black/80 px-5 backdrop-blur-sm"
      data-testid="start-experience"
    >
      <div className="w-full max-w-md rounded-3xl border border-white/10 bg-[var(--ink-elevated)] p-6 shadow-2xl md:p-8">
        <p className="text-[11px] font-medium tracking-[0.28em] text-[var(--warm)] uppercase">
          WisdomTwin
        </p>
        <h1
          className="mt-3 text-2xl leading-tight text-[var(--cream)] md:text-3xl"
          style={{ fontFamily: 'var(--font-display)' }}
        >
          Watch a CEO get board-ready in one night.
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-[var(--cream-dim)]">
          Sunday, 9:40 p.m. Board packet locks tomorrow. His five senior officers take three weeks
          to convene. He has one button.
        </p>

        {/* Outcome first — the artifact, before the mechanism */}
        <div className="mt-5 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3">
          <p className="text-[10px] tracking-[0.18em] text-[var(--cream-dim)] uppercase">
            What Sunday night produces for Thursday morning
          </p>
          <ul className="mt-2 space-y-1.5 text-sm leading-snug text-[var(--cream)]">
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
          className="mt-6 w-full rounded-2xl bg-[var(--cream)] px-4 py-3.5 text-sm font-semibold tracking-[0.12em] text-[var(--ink)] uppercase transition hover:bg-white"
        >
          Watch how it happens
        </button>

        <p className="mt-3 text-center text-[11px] text-[var(--cream-dim)]">
          Audio begins only after you press start. Space to pause · M mute · C captions
        </p>

        <div className="mt-5 space-y-3 border-t border-white/5 pt-4">
          <p className="text-[10px] tracking-[0.16em] text-[var(--cream-dim)] uppercase">Cut length</p>
          <CutSelector value={cutId} onChange={onCutChange} />
          {showInvestorToggle && (
            <InvestorModeToggle on={investorMode} onChange={onInvestorModeChange} />
          )}
        </div>

        {/* Compliance footer — small, last, out of the way of the story */}
        <div className="mt-4 text-center">
          <SyntheticDataDisclosure compact />
        </div>
      </div>
    </div>
  );
}
