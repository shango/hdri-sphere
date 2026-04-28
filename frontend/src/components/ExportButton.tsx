import { useState } from 'react';
import { useEditorStore } from '@/stores/editorStore';
import { exportUrl } from '@/lib/api';

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
    <div className="flex flex-col gap-2 border-t border-ink-700 px-4 py-3">
      <div className="flex items-center gap-3">
        <label htmlFor="outputRes" className="text-xs uppercase tracking-wider text-ink-300">
          Output
        </label>
        <select
          id="outputRes"
          className="rounded border border-ink-600 bg-ink-800 px-2 py-1 text-sm"
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
      <button
        type="button"
        onClick={() => void handleExport()}
        disabled={busy}
        className="rounded bg-accent-500 px-4 py-2 font-medium text-ink-900 transition hover:bg-accent-600 disabled:opacity-60"
      >
        {busy ? 'Exporting…' : 'Export EXR'}
      </button>
      {error ? <p className="text-sm text-red-400">{error}</p> : null}
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
