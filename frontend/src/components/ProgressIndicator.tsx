import type { JobStatus } from '@/types/api';

interface Props {
  job: JobStatus | undefined;
}

export function ProgressIndicator({ job }: Props): JSX.Element | null {
  if (!job) return null;
  if (job.status === 'complete') return null;

  if (job.status === 'failed') {
    return (
      <div className="border-t border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-300">
        Job failed: {job.error ?? job.message}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 border-t border-ink-700 bg-ink-800/40 px-4 py-2 text-sm text-ink-200">
      <span className="h-3 w-3 animate-spin rounded-full border-2 border-ink-500 border-t-accent-500" />
      <span>{job.message || `${job.kind}…`}</span>
      {job.progress > 0 ? (
        <div className="ml-auto h-1 w-32 overflow-hidden rounded-full bg-ink-700">
          <div
            className="h-full bg-accent-500"
            style={{ width: `${job.progress}%` }}
          />
        </div>
      ) : null}
    </div>
  );
}
