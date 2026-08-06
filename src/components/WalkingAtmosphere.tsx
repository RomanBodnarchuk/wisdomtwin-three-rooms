import { motion } from 'framer-motion';
import type { DemoSnapshot } from '../types/timeline';
import { useReducedMotion } from '../hooks/useReducedMotion';

interface Props {
  snapshot: DemoSnapshot;
  live: boolean;
}

/**
 * Over-the-shoulder night walk atmosphere — no face, no boardroom.
 * Phone remains the primary stage; this is depth and urgency only.
 */
export function WalkingAtmosphere({ snapshot, live }: Props) {
  const reduced = useReducedMotion();
  const { lighting, ceoPose, safeDeclineActive } = snapshot;

  const glow =
    lighting === 'pressure'
      ? 'from-[#1a1210] via-[#0c0a0c] to-[#050508]'
      : lighting === 'resolve'
        ? 'from-[#12141a] via-[#0e1014] to-[#08090c]'
        : 'from-[#0e1018] via-[#0a0b10] to-[#050508]';

  return (
    <div
      className={`pointer-events-none absolute inset-0 overflow-hidden bg-gradient-to-b ${glow}`}
      data-testid="walking-atmosphere"
      aria-hidden
    >
      {/* City glow horizon */}
      <div
        className="absolute inset-x-0 bottom-[18%] h-[40%] opacity-40"
        style={{
          background:
            'radial-gradient(ellipse 80% 50% at 50% 100%, rgba(120,140,180,0.12), transparent 70%)',
        }}
      />

      {/* Subtle street light wash */}
      <div
        className="absolute top-0 right-0 h-1/2 w-1/3 opacity-30"
        style={{
          background: 'radial-gradient(ellipse at 80% 20%, rgba(200,180,140,0.08), transparent 55%)',
        }}
      />

      {/* Walking parallax — phone hand-feel */}
      {!reduced && live && (
        <motion.div
          className="absolute inset-0"
          animate={{
            y: ceoPose === 'tired' ? [0, 3, 0, -2, 0] : [0, 2, 0, -1.5, 0],
            x: [0, 1.5, -1, 0],
          }}
          transition={{
            duration: safeDeclineActive ? 4.5 : 2.8,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      )}

      {/* Shadow / shoulder silhouette — no face */}
      <div className="absolute bottom-0 left-0 h-[28%] w-[22%] opacity-25">
        <div className="absolute bottom-0 left-[10%] h-full w-[70%] rounded-t-[40%] bg-black blur-sm" />
      </div>

      {/* Vignette */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_35%,rgba(0,0,0,0.65)_100%)]" />

      {live && (
        <div className="absolute top-5 left-5 z-[1] rounded-full border border-white/10 bg-black/40 px-3 py-1.5 backdrop-blur">
          <p className="text-[10px] tracking-[0.18em] text-[var(--cream-dim)] uppercase">
            Sunday 11:47 PM · Night walk
          </p>
        </div>
      )}
    </div>
  );
}
