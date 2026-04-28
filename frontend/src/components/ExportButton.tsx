import { useState } from 'react';
import { useEditorStore } from '@/stores/editorStore';
import { exportUrl } from '@/lib/api';
import { Button } from '@/components/ui/Button';

const RESOLUTIONS: [number, number][] = [
  [2048, 1024],
  [4096, 2048],
  [8192, 4096],
];

export function ExportButton(): JSX.Element {
  const projectId = useEditorStore((s) => s.projectId);
  const technique = useEditorStore((s) => s.technique);
  const outputResolution = useEditorStore((s) => s.outputResolution);
  const setOutputResolution = useEditorStore((s) => s.setOutputResolution);
  const sourceFilename = useEditorStore((s) => s.sourceFilename);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async (): Promise<void> => {
    if (!projectId) return;
    setBusy(true);
    setError(null);
    try {
      const [w, h] = outputResolution;
      const url = exportUrl(projectId, { technique, width: w, height: h });
      const res = await fetch(url);
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const blob = await res.blob();
      const stem = (sourceFilename ?? 'export').replace(/\.exr$/i, '');
      const filename = `${stem}_equirect_${technique}_${w}x${h}.exr`;
      triggerDownload(blob, filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-2xs uppercase tracking-widest text-ink-400">Resolution</span>
        <select
          aria-label="Output resolution"
          className="rounded border border-ink-600 bg-ink-850 px-2 py-1 text-sm text-ink-100 focus:border-lime-500 focus:outline-none"
          value={`${outputResolution[0]}x${outputResolution[1]}`}
          onChange={(e) => {
            const [w, h] = e.target.value.split('x').map((n) => parseInt(n, 10));
            if (Number.isFinite(w) && Number.isFinite(h)) {
              setOutputResolution([w!, h!]);
            }
          }}
        >
          {RESOLUTIONS.map(([w, h]) => (
            <option key={`${w}x${h}`} value={`${w}x${h}`}>
              {w}×{h}
            </option>
          ))}
        </select>
      </div>
      <Button
        variant="primary"
        size="md"
        onClick={() => void handleExport()}
        disabled={busy}
        className="w-full"
      >
        {busy ? 'Exporting…' : `Export EXR (${technique})`}
      </Button>
      {error ? <p className="text-xs text-coral-400">{error}</p> : null}
      <p className="text-2xs leading-relaxed text-ink-500">
        Renders the equirect at full resolution and downloads a 32-bit linear
        EXR. Loads as-is in Maya / Houdini / Blender / Nuke / Unreal.
      </p>
    </div>
  );
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
