import type { CutId } from '../types/timeline';

const OPTIONS: Array<{ id: CutId; label: string }> = [
  { id: 'outreach45', label: '45s outreach' },
  { id: 'investor60', label: '60s investor' },
  { id: 'full', label: 'Full (~3 min)' },
];

interface Props {
  value: CutId;
  onChange: (cut: CutId) => void;
  disabled?: boolean;
}

export function CutSelector({ value, onChange, disabled }: Props) {
  return (
    <div className="flex flex-wrap gap-1.5" data-testid="cut-selector" role="group" aria-label="Demo cut">
      {OPTIONS.map((o) => (
        <button
          key={o.id}
          type="button"
          disabled={disabled}
          onClick={() => onChange(o.id)}
          aria-pressed={value === o.id}
          data-testid={`cut-${o.id}`}
          className={`rounded-full border px-3 py-1 text-[11px] transition ${
            value === o.id
              ? 'border-[var(--warm)]/50 bg-[var(--warm-soft)] text-[var(--cream)]'
              : 'border-[var(--ink-border)] text-[var(--cream-dim)] hover:border-white/20'
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
