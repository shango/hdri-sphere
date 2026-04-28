const HINTS: { keys: string; label: string }[] = [
  { keys: '1–4', label: 'Switch view' },
  { keys: '\\', label: 'Hold for original' },
  { keys: 'X', label: 'Toggle brush' },
  { keys: '[ ]', label: 'Brush size' },
];

export function ShortcutHints(): JSX.Element {
  return (
    <div className="flex flex-wrap items-center gap-4 border-t border-ink-700 bg-ink-800/30 px-4 py-2 text-xs text-ink-300">
      {HINTS.map((h) => (
        <span key={h.keys} className="flex items-center gap-1">
          <kbd className="rounded border border-ink-600 bg-ink-900 px-1.5 py-0.5 font-mono text-[10px] text-ink-100">
            {h.keys}
          </kbd>
          <span>{h.label}</span>
        </span>
      ))}
    </div>
  );
}
