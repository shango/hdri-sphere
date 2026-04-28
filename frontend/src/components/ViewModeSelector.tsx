import { useEditorStore } from '@/stores/editorStore';
import type { ViewMode } from '@/types/api';

const MODES: { value: ViewMode; label: string; key: string }[] = [
  { value: 'original', label: 'Original', key: '1' },
  { value: 'mask', label: 'Mask', key: '2' },
  { value: 'inpainted', label: 'Inpainted', key: '3' },
  { value: 'compare', label: 'Compare', key: '4' },
];

export function ViewModeSelector(): JSX.Element {
  const viewMode = useEditorStore((s) => s.viewMode);
  const setViewMode = useEditorStore((s) => s.setViewMode);

  return (
    <div className="flex items-center gap-1 border-b border-ink-700 bg-ink-800/50 px-4 py-2">
      <span className="mr-2 text-xs uppercase tracking-wider text-ink-300">View</span>
      {MODES.map((m) => (
        <button
          key={m.value}
          type="button"
          onClick={() => setViewMode(m.value)}
          className={[
            'rounded px-3 py-1 text-sm transition',
            viewMode === m.value
              ? 'bg-accent-500 text-ink-900'
              : 'text-ink-200 hover:bg-ink-700',
          ].join(' ')}
          title={`Shortcut: ${m.key}`}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
}
