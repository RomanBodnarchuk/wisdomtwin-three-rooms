import { INITIAL_ESCALATION } from '../data/blockers';

interface Props {
  activeIds: string[];
  highlighted?: boolean;
}

export function EscalationCard({ activeIds, highlighted = false }: Props) {
  if (!activeIds.includes(INITIAL_ESCALATION.id)) return null;

  const esc = INITIAL_ESCALATION;

  return (
    <article
      className={`rounded-xl border p-3 ${
        highlighted
          ? 'border-amber-400/40 bg-[var(--danger-soft)]'
          : 'border-amber-400/25 bg-black/30'
      }`}
      data-testid="escalation-card"
      aria-label="Human escalation"
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="text-[10px] tracking-[0.16em] text-amber-200/90 uppercase">
          Human escalation
        </p>
        <span className="chip border-amber-400/30 text-amber-100">Unresolved</span>
      </div>
      <h3 className="text-sm font-medium text-[var(--cream)]">{esc.title}</h3>
      <p className="mt-1.5 text-xs leading-relaxed text-[var(--cream-dim)]">{esc.reason}</p>
      <dl className="mt-3 grid grid-cols-1 gap-1.5 text-xs">
        <div className="flex justify-between gap-2">
          <dt className="text-[var(--cream-dim)]">Reviewer</dt>
          <dd className="text-right text-[var(--cream)]">{esc.reviewer}</dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt className="text-[var(--cream-dim)]">Est. review time</dt>
          <dd className="tabular-nums text-[var(--cream)]">{esc.estimatedMinutes} min</dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt className="text-[var(--cream-dim)]">Audit</dt>
          <dd className="text-[var(--secure)]">Recorded</dd>
        </div>
      </dl>
      <p className="mt-3 text-[10px] leading-snug text-[var(--cream-dim)]/90">
        WisdomTwin knows when not to answer. This remains open for a named human.
      </p>
    </article>
  );
}
