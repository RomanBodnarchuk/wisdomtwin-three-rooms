export function LoadingState({ label = 'Preparing executive environment…' }: { label?: string }) {
  return (
    <div
      className="flex min-h-[100dvh] flex-col items-center justify-center bg-[var(--ink)] px-6 text-center"
      role="status"
      aria-live="polite"
    >
      <div className="mb-6 h-10 w-10 animate-pulse rounded-full border border-[var(--warm)]/40 bg-[var(--warm-soft)]" />
      <p className="text-sm tracking-[0.2em] text-[var(--cream-dim)] uppercase">{label}</p>
    </div>
  );
}
