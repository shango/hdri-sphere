import { useEditorStore } from '@/stores/editorStore';
import { StatusDot } from '@/components/ui/StatusDot';
import type { ViewMode } from '@/types/api';

interface Stage {
  id: string;
  label: string;
  hint: string;
  view?: ViewMode;
}

const STAGES: Stage[] = [
  { id: 'upload', label: '01  Upload', hint: 'Source plate', view: 'original' },
  { id: 'detect', label: '02  Detect', hint: 'Ball geometry', view: 'original' },
  { id: 'mask', label: '03  Mask', hint: 'Photographer', view: 'mask' },
  { id: 'inpaint', label: '04  Inpaint', hint: 'Fill the mask', view: 'inpainted' },
  { id: 'export', label: '05  Export', hint: 'Equirect EXR', view: 'compare' },
];

export function WorkflowRail(): JSX.Element {
  const projectId = useEditorStore((s) => s.projectId);
  const ballRadius = useEditorStore((s) => s.ballRadius);
  const viewMode = useEditorStore((s) => s.viewMode);
  const setViewMode = useEditorStore((s) => s.setViewMode);

  const completed: Record<string, boolean> = {
    upload: !!projectId,
    detect: !!projectId && ballRadius > 0,
    mask: !!projectId,
    inpaint: !!projectId,
    export: false,
  };

  return (
    <nav className="flex w-56 shrink-0 flex-col border-r border-ink-700 bg-ink-900/80">
      <div className="px-4 py-3 text-2xs font-semibold uppercase tracking-widest text-ink-400">
        Workflow
      </div>
      <ol className="flex flex-col gap-0.5 px-2">
        {STAGES.map((s, i) => {
          const isCurrentView = !!s.view && viewMode === s.view;
          const isDone = completed[s.id];
          return (
            <li key={s.id}>
              <button
                type="button"
                disabled={!projectId && s.id !== 'upload'}
                onClick={() => {
                  if (s.view) setViewMode(s.view);
                }}
                className={[
                  'group flex w-full items-center gap-3 rounded px-2 py-2 text-left transition',
                  isCurrentView
                    ? 'bg-ink-800 ring-1 ring-lime-500/40'
                    : 'hover:bg-ink-800/60',
                  !projectId && s.id !== 'upload' ? 'opacity-40' : '',
                ].join(' ')}
              >
                <StatusDot
                  tone={isCurrentView ? 'lime' : isDone ? 'lime' : 'muted'}
                  pulse={isCurrentView}
                />
                <span className="flex flex-1 flex-col">
                  <span
                    className={[
                      'font-mono text-xs uppercase tracking-wider',
                      isCurrentView ? 'text-lime-400' : 'text-ink-300',
                    ].join(' ')}
                  >
                    {s.label}
                  </span>
                  <span className="text-2xs text-ink-500">{s.hint}</span>
                </span>
                {i < STAGES.length - 1 ? null : null}
              </button>
            </li>
          );
        })}
      </ol>
      <div className="mt-auto border-t border-ink-700 px-4 py-3 text-2xs leading-relaxed text-ink-500">
        Each stage is non-destructive — you can revisit any step without
        losing work.
      </div>
    </nav>
  );
}
