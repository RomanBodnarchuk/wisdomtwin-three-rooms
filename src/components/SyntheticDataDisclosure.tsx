export function SyntheticDataDisclosure({ compact = false }: { compact?: boolean }) {
  if (compact) {
    return (
      <p className="text-[10px] leading-relaxed tracking-wide text-[var(--cream-dim)]/70">
        Synthetic demo data · No real customers, patients, or board records
      </p>
    );
  }

  return (
    <aside
      className="rounded-xl border border-[var(--ink-border)] bg-black/30 px-4 py-3 text-left"
      aria-label="Synthetic data disclosure"
    >
      <p className="text-[10px] font-medium tracking-[0.18em] text-[var(--cream-dim)] uppercase">
        Synthetic demonstration
      </p>
      <p className="mt-1.5 text-xs leading-relaxed text-[var(--cream-dim)]/90">
        All organizations, people, records, policies, financial figures, and operating data depicted
        are synthetic. No real customer, patient, or board record is implied.
      </p>
    </aside>
  );
}
