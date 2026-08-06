import { motion } from 'framer-motion';
import { useReducedMotion } from '../hooks/useReducedMotion';

interface Props {
  visible: boolean;
  timeLabel?: string;
}

/**
 * iPhone lock screen cold open — Sunday 11:47 PM board crisis notifications.
 */
export function LockScreen({ visible, timeLabel = '11:47' }: Props) {
  const reduced = useReducedMotion();
  if (!visible) return null;

  return (
    <div
      className="absolute inset-0 z-10 flex flex-col bg-gradient-to-b from-[#0a0c14] via-[#12151f] to-[#0a0b0d]"
      data-testid="lock-screen"
      aria-label="iPhone lock screen. Sunday 11:47 PM. Board notifications."
    >
      <div className="flex flex-1 flex-col items-center justify-center px-6 pb-16 pt-10">
        <motion.p
          initial={reduced ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-[11px] tracking-[0.22em] text-[var(--cream-dim)] uppercase"
        >
          Sunday
        </motion.p>
        <motion.p
          initial={reduced ? false : { opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: reduced ? 0 : 0.15 }}
          className="mt-1 font-light tabular-nums tracking-tight text-[var(--cream)]"
          style={{ fontSize: 'clamp(3.5rem, 18vw, 5.5rem)', lineHeight: 1 }}
        >
          {timeLabel}
        </motion.p>

        <div className="mt-10 w-full max-w-[320px] space-y-2.5">
          <motion.div
            initial={reduced ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: reduced ? 0 : 0.35 }}
            className="rounded-2xl border border-white/10 bg-white/[0.07] px-3.5 py-3 backdrop-blur-md"
            data-testid="lock-notif-board"
          >
            <div className="flex items-start gap-2.5">
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--warm)]/20 text-[10px] font-bold tracking-wide text-[var(--warm)]">
                CAL
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[11px] font-semibold tracking-[0.08em] text-[var(--cream)] uppercase">
                    Board Strategy Session
                  </p>
                  <span className="text-[10px] text-[var(--cream-dim)]">now</span>
                </div>
                <p className="mt-0.5 text-xs text-[var(--cream-dim)]">Thursday, 9:00 AM</p>
                <p className="mt-1 text-xs leading-snug text-[var(--cream)]">
                  Enterprise AI Strategy Required
                </p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={reduced ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: reduced ? 0 : 0.55 }}
            className="rounded-2xl border border-red-400/20 bg-red-500/[0.08] px-3.5 py-3 backdrop-blur-md"
            data-testid="lock-notif-packet"
          >
            <div className="flex items-start gap-2.5">
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-red-400/15 text-[10px] font-bold tracking-wide text-red-300">
                DOC
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[11px] font-semibold tracking-[0.08em] text-red-200 uppercase">
                    Board Packet Locks
                  </p>
                  <span className="text-[10px] text-red-300/70">8h</span>
                </div>
                <p className="mt-0.5 text-xs text-red-200/80">Monday, 8:00 AM</p>
                <p className="mt-1 text-xs leading-snug text-[var(--cream)]">
                  Final materials due before market open
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      <p className="pb-8 text-center text-[10px] tracking-[0.2em] text-[var(--cream-dim)]/50 uppercase">
        Swipe to unlock
      </p>
    </div>
  );
}
