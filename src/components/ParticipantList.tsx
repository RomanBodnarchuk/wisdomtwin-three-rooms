import type { ParticipantState, SpeakerId } from '../types/timeline';
import { PARTICIPANTS } from '../data/participants';
import { RoleParticipant } from './RoleParticipant';

interface Props {
  participants: Record<string, ParticipantState>;
}

export function ParticipantList({ participants }: Props) {
  return (
    <div className="space-y-1.5" data-testid="participant-list" role="list" aria-label="Huddle participants">
      {PARTICIPANTS.map((p) => (
        <div key={p.id} role="listitem">
          <RoleParticipant
            id={p.id as SpeakerId}
            state={participants[p.id] ?? 'offline'}
          />
        </div>
      ))}
    </div>
  );
}
