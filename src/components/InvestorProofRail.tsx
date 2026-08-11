import { AnimatePresence, motion } from 'framer-motion';
import { getInvestorChapter } from '../data/investorNarrative';
import { useReducedMotion } from '../hooks/useReducedMotion';

interface Props {
  timeMs: number;
}

export function InvestorProofRail({ timeMs }: Props) {
  const reduced = useReducedMotion();
  const chapter = getInvestorChapter(timeMs);

  return (
    <AnimatePresence mode="wait">
      <motion.aside
        key={chapter.id}
        initial={reduced ? false : { opacity: 0, x: -12 }}
        animate={{ opacity: 1, x: 0 }}
        exit={reduced ? undefined : { opacity: 0, x: 8 }}
        transition={{ duration: reduced ? 0 : 0.35 }}
        className="pointer-events-none absolute top-20 left-5 z-20 hidden w-[min(31vw,360px)] rounded-2xl border border-white/10 bg-black/65 p-4 shadow-2xl backdrop-blur-md lg:block"
        data-testid="investor-proof-rail"
        aria-label={`Demo narrative: ${chapter.headline}`}
      >
        <p className="text-[10px] font-semibold tracking-[0.2em] text-[var(--brand-gold)] uppercase">
          {chapter.eyebrow}
        </p>
        <h2 className="mt-2 text-xl leading-tight text-[var(--cream)]" style={{ fontFamily: 'var(--font-display)' }}>
          {chapter.headline}
        </h2>
        <p className="mt-2 text-xs leading-relaxed text-[var(--cream-dim)]">{chapter.detail}</p>
        <dl className="mt-4 grid grid-cols-3 gap-2 border-t border-white/8 pt-3">
          {chapter.metrics.map((metric) => (
            <div key={metric.label}>
              <dd className="text-sm font-semibold tabular-nums text-[var(--cream)]">{metric.value}</dd>
              <dt className="mt-0.5 text-[9px] leading-tight tracking-wide text-[var(--cream-dim)] uppercase">
                {metric.label}
              </dt>
            </div>
          ))}
        </dl>
      </motion.aside>

      <motion.div
        key={`${chapter.id}-compact`}
        initial={reduced ? false : { opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={reduced ? undefined : { opacity: 0 }}
        className="pointer-events-none absolute top-14 right-3 left-3 z-20 rounded-xl border border-white/10 bg-black/70 px-3 py-2.5 backdrop-blur-md lg:hidden"
        data-testid="investor-proof-compact"
      >
        <div className="flex items-center justify-between gap-3">
          <p className="text-[9px] font-semibold tracking-[0.16em] text-[var(--brand-gold)] uppercase">
            {chapter.eyebrow}
          </p>
          <p className="shrink-0 text-[9px] tabular-nums text-[var(--cream-dim)]">
            {chapter.metrics[0].value}
          </p>
        </div>
        <p className="mt-1 text-xs font-medium leading-snug text-[var(--cream)]">{chapter.headline}</p>
      </motion.div>
    </AnimatePresence>
  );
}
