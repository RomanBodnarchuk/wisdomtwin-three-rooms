import type { ActiveSpeakerState } from '../types/timeline';
import { SPEAKER_LABELS } from '../data/participants';
import { speakerColor } from '../lib/timelineEngine';

interface Props {
  active: ActiveSpeakerState | null;
}

export function ActiveSpeaker({ active }: Props) {
  if (!active?.speaker) {
    return (
      <div className="rounded-xl border border-dashed border-white/10 px-3 py-2.5" data-testid="active-speaker-idle">
        <p className="text-[10px] tracking-[0.16em] text-[var(--cream-dim)] uppercase">Active speaker</p>
        <p className="mt-1 text-xs text-[var(--cream-dim)]/70">Listening…</p>
      </div>
    );
  }

  return (
    <div
      className="rounded-xl border border-[var(--warm)]/30 bg-[var(--warm-soft)] px-3 py-2.5"
      data-testid="active-speaker"
      data-speaker={active.speaker}
    >
      <p
        className="text-[10px] font-medium tracking-[0.16em] uppercase"
        style={{ color: speakerColor(active.speaker) }}
      >
        {SPEAKER_LABELS[active.speaker]}
      </p>
      <p className="mt-1 line-clamp-3 text-xs leading-relaxed text-[var(--cream)]">{active.text}</p>
    </div>
  );
}
