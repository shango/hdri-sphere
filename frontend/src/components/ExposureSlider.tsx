import { useEditorStore } from '@/stores/editorStore';

export function ExposureSlider(): JSX.Element {
  const exposure = useEditorStore((s) => s.exposure);
  const setExposure = useEditorStore((s) => s.setExposure);

  return (
    <div className="flex items-center gap-3 px-4 py-2">
      <label htmlFor="exposure" className="w-20 text-xs uppercase tracking-wider text-ink-300">
        Exposure
      </label>
      <input
        id="exposure"
        type="range"
        min={-3}
        max={3}
        step={0.1}
        value={exposure}
        onChange={(e) => setExposure(parseFloat(e.target.value))}
        className="flex-1 accent-accent-500"
      />
      <span className="w-16 text-right font-mono text-sm tabular-nums">
        {(exposure >= 0 ? '+' : '') + exposure.toFixed(1)} EV
      </span>
    </div>
  );
}
