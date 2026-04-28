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
    <div className="flex items-center gap-6 border-b border-ink-700 bg-ink-900 px-5">
      {MODES.map((m) => {
        const active = viewMode === m.value;
        return (
          <button
            key={m.value}
            type="button"
            onClick={() => setViewMode(m.value)}
            className={[
              'group relative flex items-center gap-2 py-3 text-sm transition',
              active ? 'text-ink-100' : 'text-ink-400 hover:text-ink-200',
            ].join(' ')}
            title={`Press ${m.key}`}
          >
            <span className="font-mono text-2xs uppercase tracking-widest text-ink-500">
              {m.key}
            </span>
            <span>{m.label}</span>
            {active ? (
              <span className="absolute inset-x-0 -bottom-px h-[2px] bg-lime-500" />
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
