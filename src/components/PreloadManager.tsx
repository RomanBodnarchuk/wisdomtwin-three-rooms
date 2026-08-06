import { useEffect, useState } from 'react';
import { LoadingState } from './LoadingState';

interface Props {
  children: React.ReactNode;
}

/**
 * Lightweight preload gate. Does not block on every secondary asset —
 * only ensures fonts/CSS paint and a minimum ready frame.
 */
export function PreloadManager({ children }: Props) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const done = () => {
      if (!cancelled) setReady(true);
    };

    // Allow first paint quickly; secondary assets load after start gesture.
    if (document.readyState === 'complete') {
      const t = window.setTimeout(done, 120);
      return () => {
        cancelled = true;
        window.clearTimeout(t);
      };
    }

    window.addEventListener('load', done, { once: true });
    const fallback = window.setTimeout(done, 800);
    return () => {
      cancelled = true;
      window.removeEventListener('load', done);
      window.clearTimeout(fallback);
    };
  }, []);

  if (!ready) return <LoadingState />;
  return <>{children}</>;
}
