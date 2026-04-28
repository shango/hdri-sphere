import type { ButtonHTMLAttributes, ReactNode } from 'react';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';
type Size = 'sm' | 'md';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  children: ReactNode;
}

const VARIANT: Record<Variant, string> = {
  primary:
    'bg-lime-500 text-ink-950 hover:bg-lime-400 disabled:bg-lime-700 disabled:text-ink-300',
  secondary:
    'border border-ink-600 bg-ink-800 text-ink-100 hover:bg-ink-750 hover:border-ink-500',
  ghost: 'text-ink-300 hover:bg-ink-800 hover:text-ink-100',
  danger:
    'border border-coral-500/40 bg-coral-500/10 text-coral-400 hover:bg-coral-500/20 hover:text-coral-300',
};

const SIZE: Record<Size, string> = {
  sm: 'px-2.5 py-1 text-xs',
  md: 'px-3.5 py-1.5 text-sm',
};

export function Button({
  variant = 'secondary',
  size = 'md',
  className = '',
  children,
  ...rest
}: Props): JSX.Element {
  return (
    <button
      type="button"
      className={[
        'inline-flex items-center justify-center gap-2 rounded font-medium transition disabled:cursor-not-allowed disabled:opacity-60',
        VARIANT[variant],
        SIZE[size],
        className,
      ].join(' ')}
      {...rest}
    >
      {children}
    </button>
  );
}
