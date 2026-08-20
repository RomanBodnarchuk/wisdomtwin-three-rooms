export type InvestorEventName =
  | 'investor_film_start'
  | 'investor_film_progress'
  | 'investor_film_complete'
  | 'investor_cta_click';

export interface InvestorEventProps {
  cut?: string;
  milestone?: number;
  placement?: 'live' | 'end-card';
}

type PlausibleFn = ((event: string, options?: { props?: InvestorEventProps }) => void) & {
  q?: unknown[];
};

declare global {
  interface Window {
    plausible?: PlausibleFn;
    dataLayer?: Array<Record<string, unknown>>;
  }
}

const PLAUSIBLE_DOMAIN = 'romanbodnarchuk.github.io';
const PLAUSIBLE_SCRIPT_ID = 'wisdomtwin-plausible';
const PLAUSIBLE_SRC = 'https://plausible.io/js/script.outbound-links.js';

/**
 * Privacy-friendly analytics. Plausible is the chosen provider: no cookies,
 * no identity, no transcript. dataLayer is initialized so a tag manager can
 * subscribe later without a rewrite.
 */
export function installAnalytics(): void {
  if (typeof window === 'undefined' || typeof document === 'undefined') return;

  window.dataLayer = window.dataLayer ?? [];

  if (typeof window.plausible !== 'function') {
    const fn = ((...args: unknown[]) => {
      (fn.q = fn.q ?? []).push(args);
    }) as PlausibleFn;
    fn.q = [];
    window.plausible = fn;
  }

  if (document.getElementById(PLAUSIBLE_SCRIPT_ID)) return;

  const script = document.createElement('script');
  script.id = PLAUSIBLE_SCRIPT_ID;
  script.defer = true;
  script.setAttribute('data-domain', PLAUSIBLE_DOMAIN);
  script.src = PLAUSIBLE_SRC;
  document.head.appendChild(script);
}

/**
 * Funnel events leave the browser via Plausible custom events and dataLayer.
 * No identity, transcript, or content data is collected.
 */
export function trackInvestorEvent(name: InvestorEventName, props: InvestorEventProps = {}): void {
  if (typeof window === 'undefined') return;

  installAnalytics();

  window.dispatchEvent(new CustomEvent('wisdomtwin:investor-event', { detail: { name, props } }));
  window.plausible?.(name, { props });
  window.dataLayer?.push({ event: name, ...props });
}
