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
    <div className="flex h-full w-full items-center justify-center p-4">
      <div className="aspect-square h-full max-h-[80vh] w-full max-w-[80vh]">
        <ReactCompareSlider
          itemOne={
            <ReactCompareSliderImage
              src={original.data}
              alt="Original"
              style={{ objectFit: 'contain', background: '#0b0d10' }}
            />
          }
          itemTwo={
            <ReactCompareSliderImage
              src={inpainted.data}
              alt="Inpainted"
              style={{ objectFit: 'contain', background: '#0b0d10' }}
            />
          }
        />
      </div>
    </div>
  );
}

function Failure({ msg }: { msg: string }): JSX.Element {
  return (
    <div className="flex h-full w-full items-center justify-center text-sm text-red-400">
      {msg}
    </div>
  );
}
