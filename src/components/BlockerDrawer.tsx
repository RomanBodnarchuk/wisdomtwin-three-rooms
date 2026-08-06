import type { BlockerStatus } from '../types/timeline';
import { BlockerRegister } from './BlockerRegister';

interface Props {
  open: boolean;
  blockers: Record<string, BlockerStatus>;
  onClose: () => void;
}

export function BlockerDrawer({ open, blockers, onClose }: Props) {
  if (!open) return null;

  return (
    <div
      className="absolute inset-0 z-40 flex flex-col bg-[var(--ink)]/95 backdrop-blur-md"
      role="dialog"
      aria-modal="true"
      aria-label="Blockers drawer"
      data-testid="blocker-drawer"
    >
      <div className="flex items-center justify-between border-b border-[var(--ink-border)] px-4 py-3">
        <h2 className="text-xs font-semibold tracking-[0.2em] text-[var(--cream)] uppercase">
          Blockers
        </h2>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg px-2 py-1 text-xs text-[var(--cream-dim)] hover:bg-white/5"
        >
          Close
        </button>
      </div>
      <div className="drawer-scroll flex-1 overflow-y-auto p-4">
        <BlockerRegister blockers={blockers} />
      </div>
    </div>
  );
}
