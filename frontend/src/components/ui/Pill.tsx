import type { ReactNode } from 'react';

export type PillTone = 'neutral' | 'lime' | 'coral' | 'amber' | 'muted';

const TONE_CLASSES: Record<PillTone, string> = {
  neutral: 'border-ink-600 bg-ink-800 text-ink-200',
  lime: 'border-lime-600/50 bg-lime-500/10 text-lime-400',
  coral: 'border-coral-500/50 bg-coral-500/10 text-coral-400',
  amber: 'border-amber-500/40 bg-amber-500/10 text-amber-400',
  muted: 'border-ink-700 bg-ink-850 text-ink-400',
};

interface Props {
  tone?: PillTone;
  children: ReactNode;
  className?: string;
}

export function Pill({ tone = 'neutral', children, className = '' }: Props): JSX.Element {
  return (
    <span
      className={[
        'inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-2xs uppercase tracking-wider',
        TONE_CLASSES[tone],
        className,
      ].join(' ')}
    >
      {children}
    </span>
  );
}
