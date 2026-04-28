export type DotTone = 'lime' | 'coral' | 'amber' | 'muted' | 'neutral';

const TONE: Record<DotTone, string> = {
  lime: 'bg-lime-500 shadow-[0_0_8px] shadow-lime-500/60',
  coral: 'bg-coral-500 shadow-[0_0_8px] shadow-coral-500/60',
  amber: 'bg-amber-500 shadow-[0_0_8px] shadow-amber-500/60',
  muted: 'bg-ink-500',
  neutral: 'bg-ink-300',
};

interface Props {
  tone?: DotTone;
  pulse?: boolean;
  size?: number;
}

export function StatusDot({ tone = 'neutral', pulse = false, size = 8 }: Props): JSX.Element {
  return (
    <span
      className={['inline-block rounded-full', TONE[tone], pulse ? 'animate-pulse' : ''].join(' ')}
      style={{ width: size, height: size }}
      aria-hidden
    />
  );
}
