const HINTS: { keys: string; label: string }[] = [
  { keys: '1–4', label: 'Switch view' },
  { keys: '\\', label: 'Hold for original' },
  { keys: 'X', label: 'Toggle brush' },
  { keys: '[ ]', label: 'Brush size' },
];

export function ShortcutHints(): JSX.Element {
  return (
    <div className="flex flex-wrap items-center gap-5 border-t border-ink-700 bg-ink-900 px-5 py-2 text-2xs text-ink-500">
      {HINTS.map((h) => (
        <span key={h.keys} className="flex items-center gap-1.5">
          <kbd className="rounded border border-ink-600 bg-ink-850 px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-ink-200">
            {h.keys}
          </kbd>
          <span>{h.label}</span>
        </span>
      ))}
    </div>
  );
}
