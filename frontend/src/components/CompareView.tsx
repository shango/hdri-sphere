import { ReactCompareSlider, ReactCompareSliderImage } from 'react-compare-slider';
import { useBallPreview } from '@/hooks/usePreview';
import { Spinner } from '@/components/Spinner';

export function CompareView(): JSX.Element {
  const original = useBallPreview('original');
  const inpainted = useBallPreview('inpainted');

  if (original.isPending || inpainted.isPending) return <Spinner label="Rendering" />;
  if (original.isError) return <Failure msg={original.error.message} />;
  if (inpainted.isError) return <Failure msg={inpainted.error.message} />;

  return (
    <div className="flex h-full w-full items-center justify-center p-6">
      <div className="relative aspect-square h-full max-h-[80vh] w-full max-w-[80vh] overflow-hidden rounded-md border border-ink-700 bg-ink-950">
        <ReactCompareSlider
          itemOne={
            <ReactCompareSliderImage
              src={original.data}
              alt="Original"
              style={{ objectFit: 'contain', background: '#0a0b0c' }}
            />
          }
          itemTwo={
            <ReactCompareSliderImage
              src={inpainted.data}
              alt="Inpainted"
              style={{ objectFit: 'contain', background: '#0a0b0c' }}
            />
          }
        />
        <span className="pointer-events-none absolute left-3 top-3 rounded bg-ink-950/70 px-2 py-0.5 text-2xs uppercase tracking-widest text-ink-200">
          Original
        </span>
        <span className="pointer-events-none absolute right-3 top-3 rounded bg-ink-950/70 px-2 py-0.5 text-2xs uppercase tracking-widest text-lime-400">
          Inpainted
        </span>
      </div>
    </div>
  );
}

function Failure({ msg }: { msg: string }): JSX.Element {
  return (
    <div className="flex h-full w-full items-center justify-center text-sm text-coral-400">
      {msg}
    </div>
  );
}
