interface Props {
  on: boolean;
  onChange: (on: boolean) => void;
}

export function InvestorModeToggle({ on, onChange }: Props) {
  return (
    <label className="flex cursor-pointer items-center gap-2 text-[11px] text-[var(--cream-dim)]" data-testid="investor-mode-toggle">
      <input
        type="checkbox"
        checked={on}
        onChange={(e) => onChange(e.target.checked)}
        className="h-3.5 w-3.5 rounded border-white/20 bg-transparent"
        aria-label="Detail mode"
      />
      Detail mode
    </label>
  );
}
