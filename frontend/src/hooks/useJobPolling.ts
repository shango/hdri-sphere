import { useQuery } from '@tanstack/react-query';
import { getJobStatus } from '@/lib/api';
import type { JobStatus } from '@/types/api';

export function useJobPolling(jobId: string | null) {
  return useQuery<JobStatus>({
    queryKey: ['job', jobId],
    queryFn: () => {
      if (!jobId) throw new Error('No jobId');
      return getJobStatus(jobId);
    },
    enabled: !!jobId,
    staleTime: 0,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'pending' || status === 'running' ? 500 : false;
    },
  });
}
