import { useEditorStore } from '@/stores/editorStore';

export function ExposureSlider(): JSX.Element {
  const exposure = useEditorStore((s) => s.exposure);
  const setExposure = useEditorStore((s) => s.setExposure);

  return (
    <div className="flex items-center gap-3">
      <input
        id="exposure"
        type="range"
        min={-3}
        max={3}
        step={0.1}
        value={exposure}
        onChange={(e) => setExposure(parseFloat(e.target.value))}
        className="flex-1"
      />
      <span className="w-14 text-right font-mono text-xs tabular-nums text-ink-100">
        {(exposure >= 0 ? '+' : '') + exposure.toFixed(1)} EV
      </span>
    </div>
  );
}
