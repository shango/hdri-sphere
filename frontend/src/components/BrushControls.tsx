import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useEditorStore } from '@/stores/editorStore';
import { setMask } from '@/lib/api';
import { Button } from '@/components/ui/Button';

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
      void queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      onResetStrokes();
    },
  });

  return (
    <div className="flex w-full max-w-3xl flex-wrap items-center gap-3 rounded-md border border-ink-700 bg-ink-850 px-4 py-2">
      <span className="text-2xs uppercase tracking-widest text-ink-400">Brush</span>

      <div className="flex overflow-hidden rounded border border-ink-600">
        <button
          type="button"
          onClick={() => setBrushMode('add')}
          className={[
            'px-3 py-1 text-xs transition',
            brushMode === 'add'
              ? 'bg-coral-500/20 text-coral-300'
              : 'text-ink-300 hover:bg-ink-800',
          ].join(' ')}
          title="Add to mask (X to toggle)"
        >
          Add +
        </button>
        <button
          type="button"
          onClick={() => setBrushMode('remove')}
          className={[
            'border-l border-ink-600 px-3 py-1 text-xs transition',
            brushMode === 'remove'
              ? 'bg-lime-500/20 text-lime-400'
              : 'text-ink-300 hover:bg-ink-800',
          ].join(' ')}
          title="Erase mask (X to toggle)"
        >
          Erase −
        </button>
      </div>

      <label htmlFor="brushSize" className="ml-2 text-2xs uppercase tracking-widest text-ink-400">
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
        className="w-40"
      />
      <span className="w-10 font-mono text-xs tabular-nums text-ink-200">{brushSize}px</span>

      <div className="ml-auto flex gap-2">
        <Button
          size="sm"
          variant="secondary"
          onClick={() => autoMask.mutate()}
          disabled={autoMask.isPending}
        >
          {autoMask.isPending ? 'Working…' : 'Auto-detect'}
        </Button>
        <Button size="sm" variant="ghost" onClick={onResetStrokes}>
          Clear strokes
        </Button>
      </div>
    </div>
  );
}
