import type { ReactNode } from 'react';

interface Props {
  title: string;
  aside?: ReactNode;
  children: ReactNode;
  dense?: boolean;
}

export function Section({ title, aside, children, dense = false }: Props): JSX.Element {
  return (
    <section className="border-b border-ink-700/70 last:border-b-0">
      <header className="flex items-center justify-between px-4 pt-4 pb-2">
        <h3 className="text-2xs font-semibold uppercase tracking-widest text-ink-400">
          {title}
        </h3>
        {aside ? <div className="text-2xs text-ink-400">{aside}</div> : null}
      </header>
      <div className={dense ? 'px-4 pb-3' : 'px-4 pb-4'}>{children}</div>
    </section>
  );
}
