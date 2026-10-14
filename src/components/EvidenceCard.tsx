import type { EvidenceCard as EvidenceCardType } from '../types/timeline';
import { SPEAKER_LABELS } from '../data/participants';

interface Props {
  card: EvidenceCardType;
  highlighted?: boolean;
}

/** Short values become a hero proof point; long values stay as compact rows. */
const HERO_MAX_CHARS = 12;

export function EvidenceCard({ card, highlighted = false }: Props) {
  const metrics = card.metrics ?? [];
  const heroIdx = metrics.findIndex((m) => m.value.length <= HERO_MAX_CHARS);
  const rows = metrics.filter((_, i) => i !== heroIdx);

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
          <h3 className="mt-0.5 text-[15px] font-medium text-[var(--cream)]">{card.title}</h3>
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
      <p className="mt-1 text-[13px] leading-snug text-[var(--cream)]">{card.finding}</p>

      {metrics.length > 0 && (
        <div className="mt-3 space-y-1.5">
          {heroIdx >= 0 && (
            <div className="rounded-lg border border-[var(--warm)]/25 bg-[var(--warm-soft)] px-3 py-2">
              <p className="text-[9px] tracking-[0.1em] text-[var(--cream-dim)] uppercase">
                {metrics[heroIdx].label}
              </p>
              <p className="text-2xl font-semibold leading-tight tabular-nums text-[var(--cream)]">
                {metrics[heroIdx].value}
              </p>
            </div>
          )}
          {rows.map((m) => (
            <div
              key={m.label}
              className="flex items-baseline justify-between gap-2 rounded-lg border border-white/5 bg-white/[0.03] px-3 py-1.5"
            >
              <p className="text-[9px] text-[var(--cream-dim)]">{m.label}</p>
              <p className="text-xs font-medium tabular-nums text-[var(--cream)]">{m.value}</p>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
