import { SecurityStatus } from './SecurityStatus';
import { RoomMode } from './RoomMode';
import type { RoomMode as RoomModeType } from '../types/timeline';

interface Props {
  live: boolean;
  room: RoomModeType;
}

export function HuddleHeader({ live, room }: Props) {
  return (
    <header className="space-y-2 border-b border-[var(--ink-border)] px-4 pt-1 pb-2.5" data-testid="huddle-header">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-semibold tracking-[0.22em] text-[var(--cream)]">WISDOMTWIN</span>
          {live && (
            <span className="flex items-center gap-1 text-[10px] tracking-[0.16em] text-red-300 uppercase">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-red-400" aria-hidden />
              Live
            </span>
          )}
        </div>
        {live && <RoomMode room={room} />}
      </div>
      {live ? (
        <>
          <p className="text-[10px] tracking-[0.2em] text-[var(--cream-dim)] uppercase">
            Executive Huddle · Judgment in motion
          </p>
          <SecurityStatus live />
        </>
      ) : (
        <SecurityStatus live={false} />
      )}
    </header>
  );
}
