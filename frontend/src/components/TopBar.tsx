import { useEditorStore } from '@/stores/editorStore';
import { Pill } from '@/components/ui/Pill';
import { Button } from '@/components/ui/Button';

export function TopBar(): JSX.Element {
  const projectId = useEditorStore((s) => s.projectId);
  const sourceFilename = useEditorStore((s) => s.sourceFilename);
  const imageWidth = useEditorStore((s) => s.imageWidth);
  const imageHeight = useEditorStore((s) => s.imageHeight);
  const reset = useEditorStore((s) => s.reset);

  return (
    <header className="flex h-12 shrink-0 items-center justify-between border-b border-ink-700 bg-ink-900 px-4">
      <div className="flex items-center gap-3">
        <span className="flex h-6 w-6 items-center justify-center rounded-sm bg-lime-500 text-ink-950">
          <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" aria-hidden>
            <circle cx="8" cy="8" r="6" fill="currentColor" />
            <circle cx="6" cy="6" r="2" fill="rgba(255,255,255,0.45)" />
          </svg>
        </span>
        <span className="text-sm font-semibold tracking-tight text-ink-100">HDRI Tool</span>
        {projectId ? (
          <>
            <span className="text-ink-600">/</span>
            <span className="font-mono text-xs text-ink-300">
              {sourceFilename ?? 'untitled.exr'}
            </span>
            {imageWidth && imageHeight ? (
              <Pill tone="muted">
                {imageWidth}×{imageHeight}
              </Pill>
            ) : null}
          </>
        ) : (
          <span className="text-2xs uppercase tracking-widest text-ink-500">
            Chrome ball → Equirect HDRI
          </span>
        )}
      </div>
      <div className="flex items-center gap-2">
        {projectId ? (
          <Button size="sm" variant="ghost" onClick={reset}>
            Reset
          </Button>
        ) : null}
      </div>
    </header>
  );
}
