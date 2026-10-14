export function DecisionEconomicsCard() {
  return (
    <section
      className="rounded-2xl border border-[var(--brand-gold)]/25 bg-[var(--brand-gold)]/[0.07] p-4 text-left"
      data-testid="decision-economics"
      aria-label="The governed outcome"
    >
      <p className="text-[10px] font-semibold tracking-[0.18em] text-[var(--brand-gold)] uppercase">
        The governed outcome
      </p>
      <div className="mt-3 grid grid-cols-3 items-center gap-3">
        <div>
          <p className="text-xl font-semibold text-[var(--cream)]">8:42</p>
          <p className="text-[10px] text-[var(--cream-dim)]">governed huddle</p>
        </div>
        <div>
          <p className="text-xl font-semibold text-[var(--cream)]">4 of 5</p>
          <p className="text-[10px] text-[var(--cream-dim)]">blockers resolved</p>
        </div>
        <div>
          <p className="text-xl font-semibold text-[var(--cream)]">1</p>
          <p className="text-[10px] text-[var(--cream-dim)]">named human escalation</p>
        </div>
      </div>
      <p className="mt-3 border-t border-white/8 pt-3 text-xs leading-relaxed text-[var(--cream)]">
        Thursday morning, the CEO walks in with the board package.
      </p>
      <p className="mt-1 text-[9px] leading-relaxed text-[var(--cream-dim)]">
        Synthetic scenario. Fictional names and data. No customer deployment.
      </p>
    </section>
  );
}
