interface Props {
  active: boolean;
}

/** Governed answer-withheld state — silence is the feature. */
export function SafeDeclineBanner({ active }: Props) {
  if (!active) return null;

  return (
    <div
      className="rounded-xl border border-amber-400/35 bg-amber-500/[0.08] px-3 py-3"
      data-testid="safe-decline-banner"
      role="status"
      aria-live="polite"
    >
      <p className="text-[10px] font-semibold tracking-[0.2em] text-amber-200 uppercase">
        Answer withheld
      </p>
      <p className="mt-1 text-xs text-[var(--cream)]">Insufficient precedent</p>
      <p className="mt-0.5 text-[10px] text-[var(--cream-dim)]">Audit event created · Human escalation required</p>
    </div>
  );
}
