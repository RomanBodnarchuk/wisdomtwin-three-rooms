import type { SpeakerId } from '../types/timeline';
import { SPEAKER_LABELS } from '../data/participants';
import { speakerColor } from '../lib/timelineEngine';

interface Props {
  visible: boolean;
  speaker: SpeakerId | null;
  text: string | null;
}

export function CaptionLayer({ visible, speaker, text }: Props) {
  if (!visible || !text || !speaker) return null;

  return (
    <div
      className="pointer-events-none absolute inset-x-0 bottom-[72px] z-20 flex justify-center px-4 md:bottom-24"
      data-testid="caption-layer"
      aria-live="polite"
    >
      <div className="max-w-2xl rounded-2xl border border-white/10 bg-black/70 px-4 py-3 shadow-2xl backdrop-blur-md">
        <p
          className="text-[10px] font-medium tracking-[0.16em] uppercase"
          style={{ color: speakerColor(speaker) }}
        >
          {SPEAKER_LABELS[speaker]}
        </p>
        <p className="mt-1 text-sm leading-relaxed text-[var(--cream)] md:text-[15px]">{text}</p>
      </div>
    </div>
  );
}
