import { useEffect, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useEditorStore } from '@/stores/editorStore';
import { startProcess } from '@/lib/api';
import { useJobPolling } from '@/hooks/useJobPolling';
import { useProjectState } from '@/hooks/useProjectState';
import { StatusDot } from '@/components/ui/StatusDot';
import { Pill } from '@/components/ui/Pill';
import type { Technique } from '@/types/api';

const TIERS: { value: Technique; label: string; sub: string; eta: string }[] = [
  { value: 'fast', label: 'Fast', sub: 'Boundary extension (NS)', eta: '~0.3s' },
  { value: 'good', label: 'Good', sub: 'Frequency-aware + radial', eta: '~2s' },
  { value: 'best', label: 'Best', sub: 'PatchMatch exemplar', eta: '~8s' },
];

export function TechniquePanel(): JSX.Element {
  const projectId = useEditorStore((s) => s.projectId);
  const technique = useEditorStore((s) => s.technique);
  const setTechnique = useEditorStore((s) => s.setTechnique);
  const queryClient = useQueryClient();
  const [jobId, setJobId] = useState<string | null>(null);
  const job = useJobPolling(jobId);
  const state = useProjectState();
  const cached = state.data?.cached_techniques ?? [];

  const startInpaint = useMutation({
    mutationFn: async (t: Technique) => {
      if (!projectId) throw new Error('No project');
      const res = await startProcess(projectId, { technique: t });
      return res.job_id;
    },
    onSuccess: (newJobId) => setJobId(newJobId),
  });

  useEffect(() => {
    if (job.data?.status === 'complete') {
      void queryClient.invalidateQueries({ queryKey: ['preview', projectId] });
      void queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    }
  }, [job.data?.status, projectId, queryClient]);

  const isRunning =
    job.data && (job.data.status === 'pending' || job.data.status === 'running');

  return (
    <div className="grid gap-2">
      {TIERS.map((t) => {
        const active = technique === t.value;
        const isCached = cached.includes(t.value);
        const runningHere = isRunning && job.data?.message?.includes(t.value);
        return (
          <button
            key={t.value}
            type="button"
            onClick={() => {
              setTechnique(t.value);
              startInpaint.mutate(t.value);
            }}
            className={[
              'group flex items-center justify-between gap-3 rounded-md border px-3 py-2 text-left transition',
              active
                ? 'border-lime-500/60 bg-lime-500/5'
                : 'border-ink-700 bg-ink-850 hover:border-ink-500 hover:bg-ink-800',
            ].join(' ')}
          >
            <div className="flex items-center gap-3">
              <StatusDot
                tone={runningHere ? 'amber' : active ? 'lime' : 'muted'}
                pulse={runningHere}
              />
              <span className="flex flex-col">
                <span className="text-sm font-medium text-ink-100">{t.label}</span>
                <span className="text-2xs text-ink-400">{t.sub}</span>
              </span>
            </div>
            <div className="flex items-center gap-2">
              {isCached ? <Pill tone="muted">Cached</Pill> : null}
              <span className="font-mono text-2xs text-ink-400">{t.eta}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
