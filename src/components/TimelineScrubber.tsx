import { formatTime } from '../lib/timelineEngine';

interface Props {
  timeMs: number;
  durationMs: number;
  startMs?: number;
  onSeek: (ms: number) => void;
  disabled?: boolean;
}

export function TimelineScrubber({
  timeMs,
  durationMs,
  startMs = 0,
  onSeek,
  disabled,
}: Props) {
  const displayTimeMs = Math.max(0, timeMs - startMs);
  const displayDurationMs = Math.max(0, durationMs - startMs);

  return (
    <div className="flex items-center gap-3" data-testid="timeline-scrubber">
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
  );
}
