interface Props {
  value: number | null;
  visible: boolean;
}

export function ConsensusMeter({ value, visible }: Props) {
  if (!visible || value === null) return null;

  return (
    <div
      className="rounded-xl border border-[var(--ink-border)] bg-black/30 p-3"
      data-testid="consensus-meter"
      aria-label={`Consensus confidence ${value} percent, based on available precedent and policy`}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="text-[10px] tracking-[0.16em] text-[var(--cream-dim)] uppercase">
          Consensus confidence
        </p>
        <p className="text-lg font-semibold tabular-nums text-[var(--cream)]">{value}%</p>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-gradient-to-r from-[var(--warm)] to-[var(--secure)] transition-[width] duration-700"
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
      <p className="mt-2 text-[10px] leading-snug text-[var(--cream-dim)]">
        Based on available precedent and policy
      </p>
    </div>
  );
}
