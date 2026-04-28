import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useEditorStore } from '@/stores/editorStore';
import { setMask } from '@/lib/api';

interface Props {
  onResetStrokes: () => void;
}

export function BrushControls({ onResetStrokes }: Props): JSX.Element {
  const projectId = useEditorStore((s) => s.projectId);
  const brushMode = useEditorStore((s) => s.brushMode);
  const setBrushMode = useEditorStore((s) => s.setBrushMode);
  const brushSize = useEditorStore((s) => s.brushSize);
  const setBrushSize = useEditorStore((s) => s.setBrushSize);

  const queryClient = useQueryClient();
  const autoMask = useMutation({
    mutationFn: async () => {
      if (!projectId) return;
      await setMask(projectId, { auto: true });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['preview', projectId] });
      onResetStrokes();
    },
  });

  return (
    <div className="flex w-full max-w-3xl flex-wrap items-center gap-3 rounded border border-ink-700 bg-ink-800/50 px-4 py-2">
      <span className="text-xs uppercase tracking-wider text-ink-300">Brush</span>
      <button
        type="button"
        onClick={() => setBrushMode('add')}
        className={[
          'rounded px-3 py-1 text-sm transition',
          brushMode === 'add'
            ? 'bg-red-500/80 text-white'
            : 'border border-ink-600 text-ink-200 hover:bg-ink-700',
        ].join(' ')}
        title="Add to mask (X to toggle)"
      >
        Add +
      </button>
      <button
        type="button"
        onClick={() => setBrushMode('remove')}
        className={[
          'rounded px-3 py-1 text-sm transition',
          brushMode === 'remove'
            ? 'bg-accent-500 text-ink-900'
            : 'border border-ink-600 text-ink-200 hover:bg-ink-700',
        ].join(' ')}
        title="Erase mask (X to toggle)"
      >
        Erase −
      </button>

      <label htmlFor="brushSize" className="ml-2 text-xs uppercase tracking-wider text-ink-300">
        Size
      </label>
      <input
        id="brushSize"
        type="range"
        min={2}
        max={200}
        step={1}
        value={brushSize}
        onChange={(e) => setBrushSize(parseInt(e.target.value, 10))}
        className="w-40 accent-accent-500"
      />
      <span className="w-10 font-mono text-sm tabular-nums">{brushSize}px</span>

      <div className="ml-auto flex gap-2">
        <button
          type="button"
          onClick={() => autoMask.mutate()}
          disabled={autoMask.isPending}
          className="rounded border border-ink-600 px-3 py-1 text-sm hover:bg-ink-700 disabled:opacity-60"
        >
          {autoMask.isPending ? 'Working…' : 'Auto-detect'}
        </button>
        <button
          type="button"
          onClick={onResetStrokes}
          className="rounded border border-ink-600 px-3 py-1 text-sm hover:bg-ink-700"
        >
          Clear strokes
        </button>
      </div>
    </div>
  );
}
