import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadExr, setMask } from '@/lib/api';
import { useEditorStore } from '@/stores/editorStore';

export function Uploader(): JSX.Element {
  const setProject = useEditorStore((s) => s.setProject);
  const queryClient = useQueryClient();
  const [progress, setProgress] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  const upload = useMutation({
    mutationFn: async (file: File) => {
      setError(null);
      setProgress(0);
      const created = await uploadExr(file, (frac) => setProgress(frac));
      await setMask(created.project_id, { auto: true });
      return { created, file };
    },
    onSuccess: ({ created, file }) => {
      setProject({
        projectId: created.project_id,
        sourceFilename: file.name,
        imageWidth: created.width,
        imageHeight: created.height,
        ballCenter: created.ball_center,
        ballRadius: created.ball_radius,
      });
      void queryClient.invalidateQueries({
        queryKey: ['preview', created.project_id],
      });
    },
    onError: (err: unknown) => {
      setError(err instanceof Error ? err.message : String(err));
    },
  });

  const onDrop = useCallback(
    (accepted: File[]) => {
      const file = accepted[0];
      if (!file) return;
      if (!file.name.toLowerCase().endsWith('.exr')) {
        setError('Only .exr files are accepted.');
        return;
      }
      upload.mutate(file);
    },
    [upload],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/x-exr': ['.exr'] },
    maxFiles: 1,
    multiple: false,
    disabled: upload.isPending,
  });

  return (
    <div className="flex w-full items-center justify-center p-10">
      <div className="grid w-full max-w-4xl grid-cols-1 gap-8 md:grid-cols-[1fr,18rem]">
        <div
          {...getRootProps()}
          className={[
            'flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-8 py-20 text-center transition',
            isDragActive
              ? 'border-lime-500 bg-lime-500/5'
              : 'border-ink-700 hover:border-ink-500 hover:bg-ink-900/50',
            upload.isPending ? 'pointer-events-none opacity-60' : '',
          ].join(' ')}
        >
          <input {...getInputProps()} />
          <svg viewBox="0 0 64 64" className="mb-4 h-10 w-10 text-ink-500" aria-hidden>
            <circle cx="32" cy="32" r="22" fill="none" stroke="currentColor" strokeWidth="2" />
            <circle cx="24" cy="24" r="6" fill="currentColor" opacity="0.3" />
            <path d="M22 44 L42 44" stroke="currentColor" strokeWidth="2" />
          </svg>
          <p className="text-lg font-medium text-ink-100">
            {upload.isPending
              ? 'Uploading…'
              : isDragActive
                ? 'Drop the EXR here'
                : 'Drag a chrome ball EXR'}
          </p>
          <p className="mt-2 text-sm text-ink-400">
            or click to browse — 32-bit linear EXR only
          </p>

          {upload.isPending ? (
            <div className="mt-6 h-1 w-2/3 overflow-hidden rounded-full bg-ink-800">
              <div
                className="h-full bg-lime-500 transition-[width] duration-150"
                style={{ width: `${Math.round(progress * 100)}%` }}
              />
            </div>
          ) : null}

          {error ? (
            <p className="mt-6 max-w-lg text-sm text-coral-400">{error}</p>
          ) : null}
        </div>

        <aside className="flex flex-col gap-4 rounded-xl border border-ink-700 bg-ink-900/50 p-5 text-sm text-ink-300">
          <div>
            <h2 className="text-2xs font-semibold uppercase tracking-widest text-ink-400">
              How it works
            </h2>
            <ol className="mt-2 space-y-2 text-xs leading-relaxed text-ink-300">
              <li>
                <span className="font-mono text-ink-500">01</span> Upload a 32-bit
                EXR plate of a chrome ball.
              </li>
              <li>
                <span className="font-mono text-ink-500">02</span> Auto-detect
                the ball and mask the photographer/tripod.
              </li>
              <li>
                <span className="font-mono text-ink-500">03</span> Inpaint the
                masked region — pick fast, good, or best.
              </li>
              <li>
                <span className="font-mono text-ink-500">04</span> Unwrap to
                equirectangular and download.
              </li>
            </ol>
          </div>
          <div className="border-t border-ink-700 pt-4">
            <h2 className="text-2xs font-semibold uppercase tracking-widest text-ink-400">
              Requirements
            </h2>
            <ul className="mt-2 space-y-1 text-xs text-ink-300">
              <li>· 32-bit linear EXR (float)</li>
              <li>· at least 1024 × 1024</li>
              <li>· max-channel ≥ 1.0 (true HDR)</li>
              <li>· single bracket (no multi-exposure merge)</li>
            </ul>
          </div>
        </aside>
      </div>
    </div>
  );
}
