export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div
      className="flex min-h-[100dvh] flex-col items-center justify-center bg-[var(--ink)] px-6 text-center"
      role="alert"
    >
      <p className="mb-2 text-xs tracking-[0.25em] text-red-300/80 uppercase">Unable to start</p>
      <p className="max-w-md text-[var(--cream)]">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-8 rounded-full border border-[var(--ink-border)] bg-white/5 px-6 py-2.5 text-sm text-[var(--cream)] transition hover:bg-white/10"
        >
          Try again
        </button>
      )}
    </div>
  );
}
