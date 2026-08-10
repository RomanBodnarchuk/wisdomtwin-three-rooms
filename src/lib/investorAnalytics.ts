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

declare global {
  interface Window {
    plausible?: (event: string, options?: { props?: InvestorEventProps }) => void;
    dataLayer?: Array<Record<string, unknown>>;
  }
}

/**
 * Privacy-friendly, vendor-neutral instrumentation. If Plausible or a dataLayer
 * is added later, the same four investor-funnel events begin flowing without a
 * component rewrite. No identity, transcript, or content data is collected.
 */
export function trackInvestorEvent(name: InvestorEventName, props: InvestorEventProps = {}): void {
  if (typeof window === 'undefined') return;

  window.dispatchEvent(new CustomEvent('wisdomtwin:investor-event', { detail: { name, props } }));
  window.plausible?.(name, { props });
  window.dataLayer?.push({ event: name, ...props });
}
