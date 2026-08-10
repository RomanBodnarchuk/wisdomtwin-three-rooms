import { AnimatePresence, motion } from 'framer-motion';
import type { SpeakerId } from '../types/timeline';
import { SPEAKER_LABELS } from '../data/participants';
import { speakerColor } from '../lib/timelineEngine';
import { useReducedMotion } from '../hooks/useReducedMotion';

interface Props {
  visible: boolean;
  speaker: SpeakerId | null;
  text: string | null;
}

/**
 * Money phrases — the beats an investor must not miss — highlighted in warm gold.
 * Longest alternatives first so "ninety-one percent" beats "nine percent".
 */
const MONEY_PHRASES = [
  'sixty-two to ninety-one percent',
  'seven point four million dollars',
  'eleven million dollars',
  'eight minutes, forty-two seconds',
  'declining to answer',
  'thirty-eight minutes',
  'ninety-four percent',
  'ninety-one percent',
  'fourteen days to one',
  'seven to two',
  'nineteen days',
  'three weeks',
  '12,400',
  'nine percent',
];

const MONEY_RE = new RegExp(
  `(${MONEY_PHRASES.map((p) => p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`,
  'gi',
);

function renderHighlighted(text: string) {
  const parts = text.split(MONEY_RE);
  return parts.map((part, i) =>
    i % 2 === 1 ? (
      <span key={i} className="font-semibold text-[var(--warm)]">
        {part}
      </span>
    ) : (
      <span key={i}>{part}</span>
    ),
  );
}

export function CaptionLayer({ visible, speaker, text }: Props) {
  const reduced = useReducedMotion();
  if (!visible || !text || !speaker) return null;

  return (
    <div
      className="pointer-events-none absolute inset-x-0 bottom-[72px] z-20 flex justify-center px-4 md:bottom-24"
      data-testid="caption-layer"
      aria-live="polite"
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={text}
          initial={reduced ? false : { opacity: 0, y: 10, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={reduced ? undefined : { opacity: 0, y: -6 }}
          transition={{ duration: reduced ? 0 : 0.28, ease: 'easeOut' }}
          className="max-w-2xl rounded-2xl border border-white/10 bg-black/75 px-5 py-3.5 shadow-2xl backdrop-blur-md"
        >
          <p
            className="text-[10px] font-medium tracking-[0.16em] uppercase md:text-[11px]"
            style={{ color: speakerColor(speaker) }}
          >
            {SPEAKER_LABELS[speaker]}
          </p>
          <p className="mt-1 text-base leading-relaxed text-[var(--cream)] md:text-xl md:leading-relaxed">
            {renderHighlighted(text)}
          </p>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
