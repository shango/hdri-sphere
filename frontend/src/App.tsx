import { useEditorStore } from '@/stores/editorStore';
import { Uploader } from '@/components/Uploader';
import { Editor } from '@/components/Editor';
import { TopBar } from '@/components/TopBar';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { useShortcuts } from '@/hooks/useShortcuts';

export function App(): JSX.Element {
  const projectId = useEditorStore((s) => s.projectId);
  const reset = useEditorStore((s) => s.reset);
  useShortcuts();

  return (
    <div className="flex h-full flex-col bg-ink-950 text-ink-100">
      <TopBar />
      <main className="flex flex-1 overflow-hidden">
        <ErrorBoundary onReset={reset}>
          {projectId ? <Editor /> : <Uploader />}
        </ErrorBoundary>
      </main>
    </div>
  );
}
