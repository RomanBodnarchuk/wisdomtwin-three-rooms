import type { BoardArtifact } from '../types/timeline';

interface Props {
  artifacts: BoardArtifact[];
}

export function BoardOutputPanel({ artifacts }: Props) {
  const ready = artifacts.filter((a) => a.status === 'ready');
  if (ready.length === 0) return null;

  return (
    <section
      className="rounded-xl border border-[var(--secure)]/20 bg-[var(--secure-dim)]/40 p-3"
      data-testid="board-output-panel"
      aria-label="Board package outputs"
    >
      <p className="text-[10px] tracking-[0.16em] text-[var(--secure)] uppercase">Board package</p>
      <ul className="mt-2 space-y-1.5">
        {ready.map((a) => (
          <li key={a.id} className="flex items-start gap-2 text-xs text-[var(--cream)]">
            <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--secure)]" aria-hidden />
            <span>
              <span className="font-medium">{a.title}</span>
              {a.detail && (
                <span className="mt-0.5 block text-[var(--cream-dim)]">{a.detail}</span>
              )}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
