import { useEquirectPreview } from '@/hooks/usePreview';
import { Spinner } from '@/components/Spinner';

export function EquirectStrip(): JSX.Element {
  const preview = useEquirectPreview(1024);

  return (
    <div className="border-t border-ink-700 bg-ink-800/40 px-4 py-3">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider text-ink-300">Equirect preview</span>
      </div>
      <div className="aspect-[2/1] w-full overflow-hidden rounded bg-ink-900">
        {preview.isPending ? (
          <Spinner />
        ) : preview.isError ? (
          <div className="flex h-full w-full items-center justify-center text-sm text-red-400">
            {preview.error.message}
          </div>
        ) : (
          <img src={preview.data} alt="Equirect preview" className="h-full w-full object-cover" />
        )}
      </div>
    </div>
  );
}
