export function DecisionEconomicsCard() {
  return (
    <section
      className="rounded-2xl border border-[var(--brand-gold)]/25 bg-[var(--brand-gold)]/[0.07] p-4 text-left"
      data-testid="decision-economics"
      aria-label="Illustrative decision economics"
    >
      <p className="text-[10px] font-semibold tracking-[0.18em] text-[var(--brand-gold)] uppercase">
        Illustrative decision economics
      </p>
      <div className="mt-3 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
        <div>
          <p className="text-xl font-semibold text-[var(--cream)]">19 days</p>
          <p className="text-[10px] text-[var(--cream-dim)]">executive waiting</p>
        </div>
        <span className="text-lg text-[var(--brand-gold)]" aria-hidden>→</span>
        <div>
          <p className="text-xl font-semibold text-[var(--cream)]">8:42</p>
          <p className="text-[10px] text-[var(--cream-dim)]">governed huddle</p>
        </div>
      </div>
      <p className="mt-3 border-t border-white/8 pt-3 text-xs leading-relaxed text-[var(--cream)]">
        ≈$400K in delayed execution compressed into one decision cycle.
      </p>
      <p className="mt-2 text-xs leading-relaxed text-[var(--cream)]">
        Thursday morning, the CEO walks in with the board package.
      </p>
      <p className="mt-1 text-[9px] leading-relaxed text-[var(--cream-dim)]">
        Illustrative scenario estimate; economics vary by organization.
      </p>
    </section>
  );
}
