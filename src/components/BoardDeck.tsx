import type { RoomMode } from '../types/timeline';

interface Props {
  confidence: number | null;
  room: RoomMode;
}

export function BoardDeck({ confidence, room }: Props) {
  const sequence =
    room === 'build' || room === 'complete'
      ? ['1. Risk', '2. Governance', '3. Human control', '4. Revenue']
      : ['Enterprise AI', 'Prior-auth speed', 'Open questions'];

  return (
    <div
      className="relative aspect-[16/10] w-full overflow-hidden rounded-t-md border border-white/15 bg-[#0d1118] shadow-2xl"
      data-testid="board-deck"
      aria-label="Board deck on laptop"
    >
      {/* Laptop bezel top */}
      <div className="absolute inset-x-0 top-0 h-2 bg-[#1a1d24]" />
      <div className="absolute top-0.5 left-1/2 h-1 w-6 -translate-x-1/2 rounded-full bg-black/50" />

      <div className="flex h-full flex-col p-2.5 pt-3.5">
        <div className="mb-1.5 flex items-center justify-between">
          <p className="text-[7px] font-medium tracking-[0.14em] text-[var(--cream-dim)] uppercase">
            Board package
          </p>
          {confidence !== null && (
            <span className="text-[7px] tabular-nums text-[var(--secure)]">{confidence}%</span>
          )}
        </div>
        <p className="text-[9px] font-semibold text-[var(--cream)]">Enterprise AI Strategy</p>
        <p className="mt-0.5 text-[7px] text-[var(--cream-dim)]">Thursday strategy session</p>

        <ul className="mt-2 space-y-1">
          {sequence.map((line) => (
            <li
              key={line}
              className="flex items-center gap-1.5 text-[7px] text-[var(--cream-dim)]"
            >
              <span className="h-1 w-1 rounded-full bg-[var(--warm)]/70" />
              {line}
            </li>
          ))}
        </ul>

        {(room === 'build' || room === 'complete') && (
          <div className="mt-auto rounded border border-[var(--secure)]/20 bg-[var(--secure-dim)] px-1.5 py-1">
            <p className="text-[6px] tracking-wide text-[var(--secure)] uppercase">Governed plan ready</p>
          </div>
        )}
      </div>
    </div>
  );
}
