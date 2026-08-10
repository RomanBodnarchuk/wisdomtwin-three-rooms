import { useEffect, useRef } from 'react';
import type { DemoPhase } from '../types/timeline';
import { trackInvestorEvent } from '../lib/investorAnalytics';

interface Options {
  cutId: string;
  durationMs: number;
  phase: DemoPhase;
  timeMs: number;
}

const MILESTONES = [25, 50, 75] as const;

export function useInvestorAnalytics({ cutId, durationMs, phase, timeMs }: Options): void {
  const tracked = useRef(new Set<string>());

  useEffect(() => {
    if (phase !== 'playing' && phase !== 'paused' && phase !== 'complete') return;

    if (!tracked.current.has('start')) {
      tracked.current.add('start');
      trackInvestorEvent('investor_film_start', { cut: cutId });
    }

    const progress = durationMs > 0 ? (timeMs / durationMs) * 100 : 0;
    for (const milestone of MILESTONES) {
      const key = `progress-${milestone}`;
      if (progress >= milestone && !tracked.current.has(key)) {
        tracked.current.add(key);
        trackInvestorEvent('investor_film_progress', { cut: cutId, milestone });
      }
    }

    if (phase === 'complete' && !tracked.current.has('complete')) {
      tracked.current.add('complete');
      trackInvestorEvent('investor_film_complete', { cut: cutId, milestone: 100 });
    }
  }, [cutId, durationMs, phase, timeMs]);
}
