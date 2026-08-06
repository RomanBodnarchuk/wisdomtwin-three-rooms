import { motion } from 'framer-motion';
import type { EndCardEvent } from '../types/timeline';
import { SyntheticDataDisclosure } from './SyntheticDataDisclosure';
import { useReducedMotion } from '../hooks/useReducedMotion';

interface Props {
  endCard: EndCardEvent | null;
  investorMode: boolean;
  onReplay: () => void;
  onRestart: () => void;
}

export function EndCard({ endCard, investorMode, onReplay, onRestart }: Props) {
  const reduced = useReducedMotion();
  if (!endCard) return null;

  const showInvestor = investorMode || endCard.showInvestorContrast;

  return (
    <div
      className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-black px-6 text-center"
      data-testid="end-card"
      data-stage={endCard.stage}
    >
      <div className="max-w-xl space-y-5">
        {endCard.lines.map((line, i) => (
          <motion.p
            key={`${endCard.stage}-${i}-${line}`}
            initial={reduced ? false : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: reduced ? 0 : 0.6, delay: reduced ? 0 : i * 0.12 }}
            className={`leading-relaxed text-[var(--cream)] ${
              endCard.stage >= 5 && i === 0
                ? 'text-2xl font-semibold tracking-[0.2em] md:text-3xl'
                : endCard.stage >= 5
                  ? 'text-sm tracking-[0.12em] text-[var(--cream-dim)] uppercase'
                  : 'text-lg md:text-xl'
            }`}
            style={{ fontFamily: i === 0 && endCard.stage >= 5 ? 'var(--font-display)' : undefined }}
          >
            {line}
          </motion.p>
        ))}

        {showInvestor && endCard.stage >= 4 && (
          <motion.div
            initial={reduced ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mx-auto mt-6 max-w-sm rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-left"
            data-testid="investor-contrast"
          >
            <p className="text-[10px] tracking-[0.18em] text-[var(--cream-dim)] uppercase">
              Institutional judgment layer
            </p>
            <ul className="mt-2 space-y-1 text-sm text-[var(--cream)]">
              <li>Search finds documents</li>
              <li>Twins preserve people</li>
              <li className="font-medium text-[var(--warm)]">WisdomTwin preserves decisions</li>
            </ul>
          </motion.div>
        )}

        {endCard.stage >= 5 && (
          <div className="mx-auto mt-4 max-w-md space-y-4">
            <a
              href="https://calendly.com/romanbodnarchuk/20min"
              target="_blank"
              rel="noreferrer"
              data-testid="end-cta"
              className="block w-full rounded-2xl bg-[var(--cream)] px-6 py-4 text-sm font-semibold tracking-[0.12em] text-[var(--ink)] uppercase transition hover:bg-white"
            >
              Book Your Executive Huddle Demo
            </a>
            <p className="text-xs tracking-[0.08em] text-[var(--cream-dim)]">
              wisdomtwin.ai · Text anytime with questions or to book: 416 220 5314
            </p>
            <div className="flex flex-wrap justify-center gap-2 pt-2">
              <button
                type="button"
                onClick={onReplay}
                className="rounded-full border border-white/15 px-5 py-2 text-sm text-[var(--cream)]"
                data-testid="end-replay"
              >
                Replay
              </button>
              <button
                type="button"
                onClick={onRestart}
                className="rounded-full border border-white/15 px-5 py-2 text-sm text-[var(--cream-dim)]"
                data-testid="end-restart"
              >
                Restart
              </button>
            </div>
            <SyntheticDataDisclosure compact />
          </div>
        )}
      </div>
    </div>
  );
}
