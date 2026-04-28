import { useEffect, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useEditorStore } from '@/stores/editorStore';
import { startProcess } from '@/lib/api';
import { useJobPolling } from '@/hooks/useJobPolling';
import type { Technique } from '@/types/api';

const TIERS: { value: Technique; label: string; sub: string; eta: string }[] = [
  { value: 'fast', label: 'Fast', sub: 'Boundary extension', eta: '~0.3s' },
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
    }
  }, [job.data?.status, projectId, queryClient]);

  return (
    <div className="border-t border-ink-700 px-4 py-3">
      <div className="mb-2 text-xs uppercase tracking-wider text-ink-300">Technique</div>
      <div className="grid gap-2">
        {TIERS.map((t) => (
          <button
            key={t.value}
            type="button"
            onClick={() => {
              setTechnique(t.value);
              startInpaint.mutate(t.value);
            }}
            className={[
              'flex items-center justify-between rounded border px-3 py-2 text-left transition',
              technique === t.value
                ? 'border-accent-500 bg-accent-500/10'
                : 'border-ink-600 hover:bg-ink-800',
            ].join(' ')}
          >
            <span>
              <span className="block text-sm font-medium">{t.label}</span>
              <span className="text-xs text-ink-300">{t.sub}</span>
            </span>
            <span className="font-mono text-xs text-ink-300">{t.eta}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
