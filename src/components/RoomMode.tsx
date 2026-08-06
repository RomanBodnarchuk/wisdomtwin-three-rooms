import { AnimatePresence, motion } from 'framer-motion';
import type { RoomMode as RoomModeType } from '../types/timeline';
import { useReducedMotion } from '../hooks/useReducedMotion';

const LABELS: Record<string, string> = {
  dream: 'DREAM',
  'stress-test': 'STRESS-TEST',
  build: 'BUILD',
  complete: 'COMPLETE',
  idle: '',
};

interface Props {
  room: RoomModeType;
  overlay?: boolean;
}

export function RoomMode({ room, overlay = false }: Props) {
  const reduced = useReducedMotion();
  const label = LABELS[room] ?? '';

  if (!label || room === 'idle') return null;

  if (overlay) {
    return (
      <AnimatePresence>
        <motion.div
          key={room}
          className="pointer-events-none absolute inset-0 z-30 flex items-center justify-center"
          initial={reduced ? { opacity: 1 } : { opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reduced ? 0 : 0.6 }}
          data-testid={`room-overlay-${room}`}
        >
          <motion.div
            initial={reduced ? false : { opacity: 0, letterSpacing: '0.4em' }}
            animate={{ opacity: 1, letterSpacing: '0.35em' }}
            transition={{ duration: reduced ? 0 : 0.8 }}
            className="rounded-full border border-white/10 bg-black/50 px-8 py-3 backdrop-blur-md"
          >
            <p className="text-sm font-medium tracking-[0.35em] text-[var(--cream)] uppercase md:text-base">
              {label}
            </p>
          </motion.div>
        </motion.div>
      </AnimatePresence>
    );
  }

  return (
    <div
      className="chip border-[var(--warm)]/30 text-[var(--warm)]"
      data-testid={`room-chip-${room}`}
      aria-label={`Room mode: ${label}`}
    >
      {label}
    </div>
  );
}
