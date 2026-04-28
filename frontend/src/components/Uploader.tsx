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
      // Generate the auto-mask immediately so the editor opens in a useful state.
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
    <div className="flex w-full items-center justify-center p-8">
      <div
        {...getRootProps()}
        className={[
          'flex w-full max-w-3xl cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-8 py-24 text-center transition',
          isDragActive
            ? 'border-accent-500 bg-ink-800'
            : 'border-ink-600 hover:border-ink-400 hover:bg-ink-800/50',
          upload.isPending ? 'pointer-events-none opacity-60' : '',
        ].join(' ')}
      >
        <input {...getInputProps()} />
        <p className="text-xl font-medium">
          {upload.isPending
            ? 'Uploading…'
            : isDragActive
              ? 'Drop the EXR here'
              : 'Drag & drop a chrome ball EXR'}
        </p>
        <p className="mt-2 text-sm text-ink-300">or click to browse — 32-bit linear EXR only</p>

        {upload.isPending ? (
          <div className="mt-6 h-2 w-2/3 overflow-hidden rounded-full bg-ink-700">
            <div
              className="h-full bg-accent-500 transition-[width] duration-150"
              style={{ width: `${Math.round(progress * 100)}%` }}
            />
          </div>
        ) : null}

        {error ? (
          <p className="mt-6 max-w-lg text-sm text-red-400">{error}</p>
        ) : null}
      </div>
    </div>
  );
}
