import { getTranscript } from '../data/transcript';
import type { CutId } from '../types/timeline';
import { formatTime } from '../lib/timelineEngine';

interface Props {
  open: boolean;
  cutId: CutId;
  timeMs: number;
  onClose: () => void;
  onSeek: (ms: number) => void;
}

export function LiveTranscript({ open, cutId, timeMs, onClose, onSeek }: Props) {
  if (!open) return null;
  const lines = getTranscript(cutId);

  return (
    <div
      className="absolute inset-0 z-40 flex flex-col bg-[var(--ink)]/95 backdrop-blur-md"
      role="dialog"
      aria-modal="true"
      aria-label="Live transcript"
      data-testid="live-transcript"
    >
      <div className="flex items-center justify-between border-b border-[var(--ink-border)] px-4 py-3">
        <h2 className="text-xs font-semibold tracking-[0.2em] text-[var(--cream)] uppercase">
          Transcript
        </h2>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg px-2 py-1 text-xs text-[var(--cream-dim)] hover:bg-white/5"
        >
          Close
        </button>
      </div>
      <div className="drawer-scroll flex-1 space-y-3 overflow-y-auto p-4">
        {lines.map((line) => {
          const active = timeMs >= line.startMs && timeMs < line.endMs;
          return (
            <button
              key={line.id}
              type="button"
              onClick={() => onSeek(line.startMs)}
              className={`w-full rounded-xl border px-3 py-2.5 text-left transition ${
                active
                  ? 'border-[var(--warm)]/40 bg-[var(--warm-soft)]'
                  : 'border-transparent hover:border-[var(--ink-border)] hover:bg-white/[0.03]'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] tracking-[0.14em] text-[var(--cream-dim)] uppercase">
                  {line.speakerLabel}
                </span>
                <span className="font-mono text-[10px] text-[var(--cream-dim)]/70">
                  {formatTime(line.startMs)}
                </span>
              </div>
              <p className="mt-1 text-sm leading-snug text-[var(--cream)]">{line.text}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
