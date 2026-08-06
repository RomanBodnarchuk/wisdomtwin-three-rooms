import type { EvidenceCard as EvidenceCardType } from '../types/timeline';
import { SPEAKER_LABELS } from '../data/participants';

interface Props {
  card: EvidenceCardType;
  highlighted?: boolean;
}

export function EvidenceCard({ card, highlighted = false }: Props) {
  return (
    <article
      className={`rounded-xl border p-3 transition ${
        highlighted
          ? 'border-[var(--warm)]/40 bg-[var(--warm-soft)]'
          : 'border-[var(--ink-border)] bg-black/25'
      }`}
      data-testid={`evidence-card-${card.id}`}
      aria-label={`Evidence: ${card.title}`}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <div>
          <p className="text-[10px] tracking-[0.16em] text-[var(--cream-dim)] uppercase">
            {SPEAKER_LABELS[card.role] ?? card.role}
          </p>
          <h3 className="mt-0.5 text-sm font-medium text-[var(--cream)]">{card.title}</h3>
        </div>
        <span className="chip">Source-backed</span>
      </div>

      <p className="text-[10px] tracking-[0.12em] text-[var(--cream-dim)] uppercase">Sources reviewed</p>
      <ul className="mt-1 space-y-0.5">
        {card.sources.map((s) => (
          <li key={s} className="text-xs text-[var(--cream-dim)]">
            · {s}
          </li>
        ))}
      </ul>

      <p className="mt-2 text-[10px] tracking-[0.12em] text-[var(--cream-dim)] uppercase">Finding</p>
      <p className="mt-1 text-sm leading-snug text-[var(--cream)]">{card.finding}</p>

      {card.metrics && card.metrics.length > 0 && (
        <div className="mt-3 grid grid-cols-2 gap-2">
          {card.metrics.map((m) => (
            <div key={m.label} className="rounded-lg border border-white/5 bg-white/[0.03] px-2 py-1.5">
              <p className="text-[9px] text-[var(--cream-dim)]">{m.label}</p>
              <p className="text-sm font-medium tabular-nums text-[var(--cream)]">{m.value}</p>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
