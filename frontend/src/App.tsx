import { useEditorStore } from '@/stores/editorStore';
import { Uploader } from '@/components/Uploader';
import { Editor } from '@/components/Editor';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { useShortcuts } from '@/hooks/useShortcuts';

export function App(): JSX.Element {
  const projectId = useEditorStore((s) => s.projectId);
  const reset = useEditorStore((s) => s.reset);
  useShortcuts();

  return (
    <div className="flex h-full flex-col bg-ink-900 text-ink-100">
      <header className="flex items-center justify-between border-b border-ink-700 px-6 py-3">
        <h1 className="text-lg font-semibold tracking-tight">HDRI Tool</h1>
        {projectId ? (
          <button
            type="button"
            onClick={reset}
            className="rounded border border-ink-600 px-3 py-1 text-sm text-ink-200 hover:bg-ink-800"
          >
            Reset
          </button>
        ) : null}
      </header>
      <main className="flex flex-1 overflow-hidden">
        <ErrorBoundary onReset={reset}>
          {projectId ? <Editor /> : <Uploader />}
        </ErrorBoundary>
      </main>
    </div>
  );
}
