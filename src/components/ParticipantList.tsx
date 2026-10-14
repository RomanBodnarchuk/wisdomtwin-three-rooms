import type { ParticipantState } from '../types/timeline';
import { PARTICIPANTS } from '../data/participants';

interface Props {
  participants: Record<string, ParticipantState>;
}

const STATE_DOT: Record<string, string> = {
  present: 'bg-[var(--secure)]',
  joining: 'bg-[var(--warm)]',
  speaking: 'bg-[var(--warm)] animate-pulse',
  'finding-evidence': 'bg-sky-300',
  escalating: 'bg-[var(--stress)]',
  declining: 'bg-[var(--stress)]',
  consensus: 'bg-[var(--secure)]',
  offline: 'bg-white/20',
};

/** Compact chip row: one line for the whole bench instead of five stacked rows. */
export function ParticipantList({ participants }: Props) {
  return (
    <div
      className="flex flex-wrap gap-1.5"
      data-testid="participant-list"
      role="list"
      aria-label="Huddle participants"
    >
      {PARTICIPANTS.map((p) => {
        const state = participants[p.id] ?? 'offline';
        return (
          <span
            key={p.id}
            role="listitem"
            title={`${p.label}: ${state}`}
            className="flex items-center gap-1.5 rounded-full border border-white/10 bg-black/30 px-2 py-1"
            data-testid={`participant-${p.id}`}
            data-state={state}
          >
            <span className={`h-1.5 w-1.5 rounded-full ${STATE_DOT[state] ?? 'bg-white/20'}`} aria-hidden />
            <span className="text-[10px] font-medium text-[var(--cream)]">{p.shortLabel}</span>
          </span>
        );
      })}
    </div>
  );
}
