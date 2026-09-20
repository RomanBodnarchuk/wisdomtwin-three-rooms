export const SYNTHETIC_DISCLOSURE =
  'Synthetic demonstration. Fictional names and data. No customer deployment.';

export function SyntheticDataDisclosure({ compact = false }: { compact?: boolean }) {
  if (compact) {
    return (
      <p className="text-[10px] leading-relaxed tracking-wide text-[var(--cream-dim)]/70">
        {SYNTHETIC_DISCLOSURE}
      </p>
    );
  }

  return (
    <aside
      className="rounded-xl border border-[var(--ink-border)] bg-black/30 px-4 py-3 text-left"
      aria-label="Synthetic data disclosure"
    >
      <p className="text-xs leading-relaxed text-[var(--cream-dim)]/90">{SYNTHETIC_DISCLOSURE}</p>
    </aside>
  );
}
