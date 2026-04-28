import { ViewModeSelector } from '@/components/ViewModeSelector';
import { PreviewPanel } from '@/components/PreviewPanel';
import { ExposureSlider } from '@/components/ExposureSlider';
import { TechniquePanel } from '@/components/TechniquePanel';
import { ExportButton } from '@/components/ExportButton';
import { EquirectStrip } from '@/components/EquirectStrip';
import { ShortcutHints } from '@/components/ShortcutHints';
import { useEditorStore } from '@/stores/editorStore';

export function Editor(): JSX.Element {
  const sourceFilename = useEditorStore((s) => s.sourceFilename);

  return (
    <div className="flex h-full w-full">
      <section className="flex flex-1 flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b border-ink-700 px-4 py-2 text-sm text-ink-200">
          <span className="font-mono text-ink-300">{sourceFilename}</span>
        </div>
        <ViewModeSelector />
        <div className="flex-1 overflow-hidden">
          <PreviewPanel />
        </div>
        <ShortcutHints />
      </section>
      <aside className="flex w-80 flex-col border-l border-ink-700 bg-ink-800/30">
        <ExposureSlider />
        <TechniquePanel />
        <EquirectStrip />
        <ExportButton />
      </aside>
    </div>
  );
}
