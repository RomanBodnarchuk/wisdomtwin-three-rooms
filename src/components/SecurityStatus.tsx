interface Props {
  live?: boolean;
  compact?: boolean;
}

const CHIPS = [
  { id: 'onprem', label: 'On-premise' },
  { id: 'zero', label: 'Zero external calls' },
  { id: 'audit', label: 'Audit active' },
  { id: 'human', label: 'Human governed' },
] as const;

export function SecurityStatus({ live = false, compact = false }: Props) {
  if (!live) {
    return (
      <div className="chip chip-secure" data-testid="security-pre">
        Private enterprise environment
      </div>
    );
  }

  return (
    <div
      className={`flex flex-wrap gap-1.5 ${compact ? 'justify-center' : ''}`}
      data-testid="security-live"
      aria-label="Security status"
    >
      {CHIPS.map((c) => (
        <span key={c.id} className="chip chip-secure">
          <span className="h-1 w-1 rounded-full bg-[var(--secure)]" aria-hidden />
          {c.label}
        </span>
      ))}
    </div>
  );
}
