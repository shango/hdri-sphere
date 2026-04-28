import { useEquirectPreview } from '@/hooks/usePreview';
import { Spinner } from '@/components/Spinner';

export function EquirectStrip(): JSX.Element {
  const preview = useEquirectPreview(1024);

  return (
    <div className="aspect-[2/1] w-full overflow-hidden rounded border border-ink-700 bg-ink-950">
      {preview.isPending ? (
        <Spinner />
      ) : preview.isError ? (
        <div className="flex h-full w-full items-center justify-center text-xs text-coral-400">
          {preview.error.message}
        </div>
      ) : (
        <img src={preview.data} alt="Equirect preview" className="h-full w-full object-cover" />
      )}
    </div>
  );
}
