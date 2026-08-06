import type { ParticipantState, SpeakerId } from '../types/timeline';
import { getParticipant } from '../data/participants';

interface Props {
  id: SpeakerId;
  state: ParticipantState;
}

const STATE_LABEL: Record<ParticipantState, string> = {
  offline: 'Offline',
  joining: 'Joining',
  present: 'Present',
  speaking: 'Speaking',
  thinking: 'Thinking',
  'finding-evidence': 'Finding evidence',
  declining: 'Declining',
  escalating: 'Escalating',
  consensus: 'Consensus',
};

export function RoleParticipant({ id, state }: Props) {
  const meta = getParticipant(id);
  if (!meta) return null;

  const active = state === 'speaking';
  const dim = state === 'offline';
  const alert = state === 'declining' || state === 'escalating';
  const evidence = state === 'finding-evidence';
  const consensus = state === 'consensus';

  return (
    <div
      className={`flex items-center gap-2.5 rounded-xl border px-2.5 py-2 transition-colors duration-300 ${
        dim
          ? 'border-transparent opacity-30'
          : active
            ? 'border-[var(--warm)]/40 bg-[var(--warm-soft)]'
            : alert
              ? 'border-amber-400/30 bg-[var(--danger-soft)]'
              : consensus
                ? 'border-[var(--secure)]/30 bg-[var(--secure-dim)]'
                : 'border-[var(--ink-border)] bg-white/[0.02]'
      }`}
      data-testid={`participant-${id}`}
      data-state={state}
      aria-label={`${meta.label}: ${STATE_LABEL[state]}`}
    >
      <div
        className={`relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full border text-[11px] font-semibold tracking-wide ${
          active
            ? 'border-[var(--warm)] text-[var(--cream)]'
            : alert
              ? 'border-amber-400/50 text-amber-100'
              : 'border-white/15 text-[var(--cream-dim)]'
        }`}
      >
        <span aria-hidden>{meta.initials}</span>
        {active && (
          <span className="absolute -right-0.5 -bottom-0.5 h-2.5 w-2.5 rounded-full bg-[var(--warm)] shadow-[0_0_8px_var(--warm)]" />
        )}
        {evidence && !active && (
          <span className="absolute -right-0.5 -bottom-0.5 h-2 w-2 rounded-full bg-sky-400/90" />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-xs font-medium text-[var(--cream)]">{meta.label}</p>
        <p className="truncate text-[10px] text-[var(--cream-dim)]">{STATE_LABEL[state]}</p>
      </div>
      <span className="text-sm text-[var(--cream-dim)]/50" aria-hidden>
        {meta.glyph}
      </span>
    </div>
  );
}
