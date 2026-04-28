import { ViewModeSelector } from '@/components/ViewModeSelector';
import { PreviewPanel } from '@/components/PreviewPanel';
import { ShortcutHints } from '@/components/ShortcutHints';
import { WorkflowRail } from '@/components/WorkflowRail';
import { InspectorPanel } from '@/components/InspectorPanel';

export function Editor(): JSX.Element {
  return (
    <div className="flex h-full w-full">
      <WorkflowRail />
      <section className="flex flex-1 flex-col overflow-hidden">
        <ViewModeSelector />
        <div className="flex-1 overflow-hidden bg-ink-950">
          <PreviewPanel />
        </div>
        <ShortcutHints />
      </section>
      <InspectorPanel />
    </div>
  );
}
