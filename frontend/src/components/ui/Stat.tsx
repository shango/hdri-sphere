import type { ReactNode } from 'react';

interface Props {
  label: string;
  value: ReactNode;
  mono?: boolean;
}

export function Stat({ label, value, mono = true }: Props): JSX.Element {
  return (
    <div className="flex items-baseline justify-between gap-3 py-1">
      <span className="text-2xs uppercase tracking-wider text-ink-400">{label}</span>
      <span
        className={[
          'truncate text-right text-sm text-ink-100',
          mono ? 'font-mono tabular-nums' : '',
        ].join(' ')}
      >
        {value}
      </span>
    </div>
  );
}
