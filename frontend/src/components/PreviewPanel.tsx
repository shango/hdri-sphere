import { useEditorStore } from '@/stores/editorStore';
import { useBallPreview } from '@/hooks/usePreview';
import { CompareView } from '@/components/CompareView';
import { MaskEditor } from '@/components/MaskEditor';
import { Spinner } from '@/components/Spinner';

export function PreviewPanel(): JSX.Element {
  const viewMode = useEditorStore((s) => s.viewMode);

  if (viewMode === 'mask') return <MaskEditor />;
  if (viewMode === 'compare') return <CompareView />;
  return <SimplePreview viewMode={viewMode} />;
}

function SimplePreview({
  viewMode,
}: {
  viewMode: 'original' | 'inpainted';
}): JSX.Element {
  const preview = useBallPreview(viewMode);

  if (preview.isPending) return <Spinner label="Rendering" />;
  if (preview.isError)
    return (
      <div className="flex h-full w-full items-center justify-center text-sm text-red-400">
        {preview.error.message}
      </div>
    );

  return (
    <div className="flex h-full w-full items-center justify-center p-4">
      <img
        src={preview.data}
        alt={viewMode}
        className="max-h-full max-w-full rounded border border-ink-700 object-contain"
      />
    </div>
  );
}
