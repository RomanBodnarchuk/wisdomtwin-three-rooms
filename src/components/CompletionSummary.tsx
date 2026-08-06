import { COMPLETION_SUMMARY } from '../data/blockers';

export function CompletionSummary() {
  const rows = [
    { label: 'Duration', value: COMPLETION_SUMMARY.durationLabel },
    { label: 'Blockers resolved', value: COMPLETION_SUMMARY.blockersResolved },
    { label: 'Human escalation created', value: String(COMPLETION_SUMMARY.humanEscalation) },
    { label: 'Board memo', value: COMPLETION_SUMMARY.boardMemo },
    { label: 'Supporting citations', value: COMPLETION_SUMMARY.citations },
    { label: 'Dissent', value: COMPLETION_SUMMARY.dissent },
    { label: 'Audit record', value: COMPLETION_SUMMARY.auditRecord },
  ];

  return (
    <section
      className="rounded-xl border border-[var(--ink-border)] bg-black/30 p-3"
      data-testid="completion-summary"
      aria-label="Huddle complete summary"
    >
      <p className="text-[10px] tracking-[0.2em] text-[var(--warm)] uppercase">Huddle complete</p>
      <dl className="mt-3 space-y-2">
        {rows.map((r) => (
          <div key={r.label} className="flex items-center justify-between gap-3 text-xs">
            <dt className="text-[var(--cream-dim)]">{r.label}</dt>
            <dd className="font-medium text-[var(--cream)]">{r.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
