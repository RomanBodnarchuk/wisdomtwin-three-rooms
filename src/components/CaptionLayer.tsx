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

const HIGHLIGHT_PHRASES = [
  'sixty-two to ninety-one percent',
  'seven point four million dollars',
  'eleven million dollars',
  'eight minutes, forty-two seconds',
  'declining to answer',
  'thirty-eight minutes',
  'ninety-four percent',
  'ninety-one percent',
  'fourteen days to one',
  'dissent preserved',
  'dissent notes',
  'seven to two',
  'nineteen days',
  'three weeks',
  'one button',
  '12,400',
  'nine percent',
] as const;

const HIGHLIGHT_LOOKUP = new Set<string>(HIGHLIGHT_PHRASES);
const HIGHLIGHT_PATTERN = new RegExp(
  `(${[...HIGHLIGHT_PHRASES]
    .sort((a, b) => b.length - a.length)
    .map((phrase) => phrase.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    .join('|')})`,
  'gi',
);

function highlightCaption(text: string) {
  return text.split(HIGHLIGHT_PATTERN).map((part, index) =>
    HIGHLIGHT_LOOKUP.has(part.toLowerCase()) ? (
      <mark
        key={`${part}-${index}`}
        className="rounded bg-[var(--brand-gold)]/15 px-0.5 font-semibold text-[var(--brand-gold)]"
      >
        {part}
      </mark>
    ) : (
      part
    ),
  );
}

export function CaptionLayer({ visible, speaker, text }: Props) {
  const reduced = useReducedMotion();
  if (!visible || !text || !speaker) return null;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={`${speaker}-${text}`}
        initial={reduced ? false : { opacity: 0, y: 10, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={reduced ? undefined : { opacity: 0, y: -6 }}
        transition={{ duration: reduced ? 0 : 0.28, ease: 'easeOut' }}
        className="pointer-events-none absolute inset-x-0 bottom-[72px] z-30 flex justify-center px-4 md:bottom-24 md:right-[40%]"
        data-testid="caption-layer"
        role="status"
        aria-live="polite"
      >
        <div className="max-w-3xl rounded-2xl border border-white/12 bg-black/80 px-5 py-3.5 shadow-2xl backdrop-blur-md">
          <p
            className="text-[10px] font-semibold tracking-[0.16em] uppercase md:text-[11px]"
            style={{ color: speakerColor(speaker) }}
          >
            {SPEAKER_LABELS[speaker]}
          </p>
          <p className="mt-1 text-base leading-relaxed text-[var(--cream)] md:text-xl md:leading-relaxed">
            {highlightCaption(text)}
          </p>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
