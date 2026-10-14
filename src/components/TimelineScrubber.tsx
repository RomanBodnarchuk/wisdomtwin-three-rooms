import { formatTime } from '../lib/timelineEngine';

export interface ScrubberChapter {
  ms: number;
  label: string;
}

interface Props {
  timeMs: number;
  durationMs: number;
  startMs?: number;
  chapters?: ScrubberChapter[];
  onSeek: (ms: number) => void;
  disabled?: boolean;
}

/**
 * Seek bar with room chapter markers. Skippable beats convert better than
 * imprisoning ones: a CRO can jump straight to the dissent-preserved build.
 */
export function TimelineScrubber({
  timeMs,
  durationMs,
  startMs = 0,
  chapters = [],
  onSeek,
  disabled,
}: Props) {
  const displayTimeMs = Math.max(0, timeMs - startMs);
  const displayDurationMs = Math.max(0, durationMs - startMs);
  const span = Math.max(1, durationMs - startMs);

  return (
    <div data-testid="timeline-scrubber">
      {chapters.length > 0 && (
        <div className="relative mb-1.5 hidden h-4 sm:block" data-testid="timeline-chapters">
          {chapters.map((ch) => {
            const rawPct = ((ch.ms - startMs) / span) * 100;
            const pct = Math.min(96, Math.max(3, rawPct));
            const active = timeMs >= ch.ms;
            return (
              <button
                key={ch.label}
                type="button"
                disabled={disabled}
                onClick={() => onSeek(ch.ms)}
                title={`Jump to ${ch.label}`}
                aria-label={`Jump to ${ch.label}`}
                className={`absolute top-0 -translate-x-1/2 rounded px-1 text-[7px] font-semibold tracking-[0.12em] uppercase transition ${
                  active
                    ? 'text-[var(--warm)]'
                    : 'text-[var(--cream-dim)]/60 hover:text-[var(--cream-dim)]'
                }`}
                style={{ left: `${pct}%` }}
              >
                {ch.label}
              </button>
            );
          })}
        </div>
      )}
      <div className="flex items-center gap-3">
        <span className="w-10 shrink-0 font-mono text-[11px] tabular-nums text-[var(--cream-dim)]">
          {formatTime(displayTimeMs)}
        </span>
        <input
          type="range"
          className="scrubber w-full"
          min={startMs}
          max={durationMs}
          step={100}
          value={Math.max(startMs, Math.min(timeMs, durationMs))}
          disabled={disabled}
          aria-label="Seek timeline"
          aria-valuetext={`${formatTime(displayTimeMs)} of ${formatTime(displayDurationMs)}`}
          onChange={(e) => onSeek(Number(e.target.value))}
        />
        <span className="w-10 shrink-0 text-right font-mono text-[11px] tabular-nums text-[var(--cream-dim)]">
          {formatTime(displayDurationMs)}
        </span>
      </div>
    </div>
  );
}
