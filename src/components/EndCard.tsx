import { motion } from 'framer-motion';
import type { EndCardEvent } from '../types/timeline';
import { SyntheticDataDisclosure } from './SyntheticDataDisclosure';
import { useReducedMotion } from '../hooks/useReducedMotion';
import { DecisionEconomicsCard } from './DecisionEconomicsCard';
import { trackInvestorEvent } from '../lib/investorAnalytics';

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
      className="absolute inset-0 z-50 flex flex-col items-center justify-start overflow-y-auto bg-black px-5 py-6 text-center md:justify-center md:px-6"
      data-testid="end-card"
      data-stage={endCard.stage}
    >
      <div className="w-full max-w-3xl space-y-5">
        {endCard.lines.map((line, i) => (
          <motion.p
            key={`${endCard.stage}-${i}-${line}`}
            initial={reduced ? false : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: reduced ? 0 : 0.6, delay: reduced ? 0 : i * 0.12 }}
            className={`leading-relaxed text-[var(--cream)] ${
              endCard.stage >= 5 && i === 0
                ? 'text-sm font-semibold tracking-[0.24em] text-[var(--brand-gold)] md:text-base'
                : endCard.stage >= 5 && i === 1
                  ? 'text-3xl leading-tight md:text-5xl'
                : endCard.stage >= 5
                  ? 'text-sm tracking-[0.08em] text-[var(--cream-dim)]'
                  : 'text-lg md:text-xl'
            }`}
            style={{ fontFamily: i === 1 && endCard.stage >= 5 ? 'var(--font-display)' : undefined }}
          >
            {line}
          </motion.p>
        ))}

        {showInvestor && endCard.stage >= 4 && (
          <motion.div
            initial={reduced ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mx-auto mt-6 grid max-w-2xl gap-3 md:grid-cols-2"
            data-testid="investor-contrast"
          >
            <DecisionEconomicsCard />
            <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left">
              <p className="text-[10px] font-semibold tracking-[0.18em] text-[var(--cream-dim)] uppercase">
                The compounding asset
              </p>
              <p className="mt-2 text-sm leading-relaxed text-[var(--cream)]">
                Every governed decision strengthens the enterprise judgment layer.
              </p>
              <ul className="mt-3 grid grid-cols-2 gap-2 text-xs text-[var(--cream-dim)]">
                <li className="rounded-lg border border-white/8 px-2 py-2">Policy memory</li>
                <li className="rounded-lg border border-white/8 px-2 py-2">Decision precedent</li>
                <li className="rounded-lg border border-white/8 px-2 py-2">Dissent history</li>
                <li className="rounded-lg border border-white/8 px-2 py-2">Escalation outcomes</li>
              </ul>
            </section>
          </motion.div>
        )}

        {endCard.stage >= 5 && (
          <div className="mx-auto mt-4 max-w-lg space-y-4">
            <a
              href="https://calendly.com/romanbodnarchuk/20min"
              target="_blank"
              rel="noreferrer"
              data-testid="end-cta"
              onClick={() => trackInvestorEvent('investor_cta_click', { placement: 'end-card' })}
              className="block w-full rounded-2xl bg-[var(--cream)] px-6 py-4 text-sm font-semibold tracking-[0.12em] text-[var(--ink)] uppercase transition hover:bg-white"
            >
              Book a 20-minute investor demo
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
