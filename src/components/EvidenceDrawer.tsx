import { EVIDENCE_CARDS } from '../data/evidence';
import { EvidenceCard } from './EvidenceCard';

interface Props {
  open: boolean;
  visibleIds: string[];
  onClose: () => void;
}

export function EvidenceDrawer({ open, visibleIds, onClose }: Props) {
  if (!open) return null;

  const cards = visibleIds
    .map((id) => EVIDENCE_CARDS[id])
    .filter(Boolean)
    .reverse();

  return (
    <div
      className="absolute inset-0 z-40 flex flex-col bg-[var(--ink)]/95 backdrop-blur-md"
      role="dialog"
      aria-modal="true"
      aria-label="Evidence drawer"
      data-testid="evidence-drawer"
    >
      <div className="flex items-center justify-between border-b border-[var(--ink-border)] px-4 py-3">
        <h2 className="text-xs font-semibold tracking-[0.2em] text-[var(--cream)] uppercase">
          Evidence
        </h2>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg px-2 py-1 text-xs text-[var(--cream-dim)] hover:bg-white/5"
          aria-label="Close evidence drawer"
        >
          Close
        </button>
      </div>
      <div className="drawer-scroll flex-1 space-y-3 overflow-y-auto p-4">
        {cards.length === 0 ? (
          <p className="text-sm text-[var(--cream-dim)]">No evidence cards yet in this moment.</p>
        ) : (
          cards.map((c) => <EvidenceCard key={c.id} card={c} highlighted />)
        )}
      </div>
    </div>
  );
}
