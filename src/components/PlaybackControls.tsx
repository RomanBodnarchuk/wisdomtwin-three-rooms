import type { DemoPhase } from '../types/timeline';
import { TimelineScrubber } from './TimelineScrubber';

interface Props {
  phase: DemoPhase;
  timeMs: number;
  durationMs: number;
  timelineStartMs?: number;
  muted: boolean;
  captionsOn: boolean;
  onTogglePlay: () => void;
  onRestart: () => void;
  onToggleMute: () => void;
  onToggleCaptions: () => void;
  onSeek: (ms: number) => void;
  onOpenEvidence: () => void;
  onOpenBlockers: () => void;
  onOpenEscalations: () => void;
  onOpenTranscript: () => void;
}

export function PlaybackControls({
  phase,
  timeMs,
  durationMs,
  timelineStartMs = 0,
  muted,
  captionsOn,
  onTogglePlay,
  onRestart,
  onToggleMute,
  onToggleCaptions,
  onSeek,
  onOpenEvidence,
  onOpenBlockers,
  onOpenEscalations,
  onOpenTranscript,
}: Props) {
  const playing = phase === 'playing';
  const started = phase === 'playing' || phase === 'paused' || phase === 'complete';

  return (
    <div
      className="border-t border-[var(--ink-border)] bg-black/40 px-3 py-2.5 backdrop-blur-md"
      data-testid="playback-controls"
    >
      <TimelineScrubber
        timeMs={timeMs}
        durationMs={durationMs}
        startMs={timelineStartMs}
        onSeek={onSeek}
        disabled={!started}
      />

      <div className="mt-2.5 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-1">
          <ControlButton
            label={playing ? 'Pause' : phase === 'complete' ? 'Replay' : 'Play'}
            onClick={onTogglePlay}
            primary
            testId="btn-play"
          />
          <ControlButton label="Restart" onClick={onRestart} testId="btn-restart" />
          <ControlButton
            label={muted ? 'Unmute' : 'Mute'}
            onClick={onToggleMute}
            testId="btn-mute"
            pressed={muted}
          />
          <ControlButton
            label="CC"
            onClick={onToggleCaptions}
            testId="btn-captions"
            pressed={captionsOn}
          />
        </div>
        <div className="hidden items-center gap-1 sm:flex">
          <ControlButton label="Evidence" onClick={onOpenEvidence} testId="btn-evidence" />
          <ControlButton label="Blockers" onClick={onOpenBlockers} testId="btn-blockers" />
          <ControlButton label="Escalate" onClick={onOpenEscalations} testId="btn-escalations" />
          <ControlButton label="Script" onClick={onOpenTranscript} testId="btn-transcript" />
        </div>
      </div>
    </div>
  );
}

function ControlButton({
  label,
  onClick,
  primary,
  pressed,
  testId,
}: {
  label: string;
  onClick: () => void;
  primary?: boolean;
  pressed?: boolean;
  testId?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={testId}
      aria-pressed={pressed}
      className={`rounded-lg px-2.5 py-1.5 text-[11px] font-medium tracking-wide transition ${
        primary
          ? 'bg-[var(--cream)] text-[var(--ink)] hover:bg-white'
          : pressed
            ? 'bg-white/15 text-[var(--cream)]'
            : 'text-[var(--cream-dim)] hover:bg-white/8 hover:text-[var(--cream)]'
      }`}
    >
      {label}
    </button>
  );
}
