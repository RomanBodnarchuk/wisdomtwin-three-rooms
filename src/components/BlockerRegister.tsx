import type { BlockerStatus } from '../types/timeline';
import { INITIAL_BLOCKERS } from '../data/blockers';

interface Props {
  blockers: Record<string, BlockerStatus>;
  compact?: boolean;
}

const STATUS_STYLE: Record<BlockerStatus, string> = {
  open: 'text-amber-200 border-amber-400/30',
  resolved: 'text-[var(--secure)] border-[var(--secure)]/30',
  mitigated: 'text-sky-200 border-sky-400/30',
  escalated: 'text-orange-200 border-orange-400/40',
};

export function BlockerRegister({ blockers, compact = false }: Props) {
  const items = INITIAL_BLOCKERS.map((b) => ({
    ...b,
    status: blockers[b.id] ?? b.status,
  })).filter((b) => blockers[b.id] !== undefined);

  if (items.length === 0) {
    return (
      <p className="text-xs text-[var(--cream-dim)]" data-testid="blocker-register-empty">
        No blockers registered yet.
      </p>
    );
  }

  return (
    <div className="space-y-2" data-testid="blocker-register" aria-label="Blocker register">
      {items.map((b) => (
        <article
          key={b.id}
          className={`rounded-xl border bg-black/20 p-3 ${STATUS_STYLE[b.status]}`}
          data-testid={`blocker-${b.id}`}
          data-status={b.status}
        >
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-sm font-medium text-[var(--cream)]">{b.title}</h3>
            <span className="chip shrink-0 capitalize">{b.status}</span>
          </div>
          {!compact && (
            <>
              <p className="mt-1.5 text-xs text-[var(--cream-dim)]">
                <span className="text-[var(--cream)]/70">Policy: </span>
                {b.policy}
              </p>
              <p className="mt-1 text-xs text-[var(--cream-dim)]">
                <span className="text-[var(--cream)]/70">Precedent: </span>
                {b.precedent}
              </p>
              <p className="mt-1 text-xs text-[var(--cream-dim)]">
                <span className="text-[var(--cream)]/70">Owner: </span>
                {b.owner}
              </p>
              <p className="mt-1 text-xs text-[var(--cream-dim)]">
                <span className="text-[var(--cream)]/70">Decision: </span>
                {b.decision}
              </p>
            </>
          )}
        </article>
      ))}
    </div>
  );
}
