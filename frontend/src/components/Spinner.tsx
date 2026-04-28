interface Props {
  label?: string;
}

export function Spinner({ label }: Props): JSX.Element {
  return (
    <div className="flex h-full w-full items-center justify-center gap-3 text-ink-300">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-ink-500 border-t-accent-500" />
      {label ? <span className="text-sm">{label}</span> : null}
    </div>
  );
}
