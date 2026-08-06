import { formatTime } from '../lib/timelineEngine';

interface Props {
  timeMs: number;
  durationMs: number;
  onSeek: (ms: number) => void;
  disabled?: boolean;
}

export function TimelineScrubber({ timeMs, durationMs, onSeek, disabled }: Props) {
  return (
    <div className="flex items-center gap-3" data-testid="timeline-scrubber">
      <span className="w-10 shrink-0 font-mono text-[11px] tabular-nums text-[var(--cream-dim)]">
        {formatTime(timeMs)}
      </span>
      <input
        type="range"
        className="scrubber w-full"
        min={0}
        max={durationMs}
        step={100}
        value={Math.min(timeMs, durationMs)}
        disabled={disabled}
        aria-label="Seek timeline"
        onChange={(e) => onSeek(Number(e.target.value))}
      />
      <span className="w-10 shrink-0 text-right font-mono text-[11px] tabular-nums text-[var(--cream-dim)]">
        {formatTime(durationMs)}
      </span>
    </div>
  );
}
