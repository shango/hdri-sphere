import { useQuery } from '@tanstack/react-query';
import { getProjectState } from '@/lib/api';
import { useEditorStore } from '@/stores/editorStore';

export function useProjectState() {
  const projectId = useEditorStore((s) => s.projectId);
  return useQuery({
    queryKey: ['project', projectId],
    queryFn: () => {
      if (!projectId) throw new Error('No project');
      return getProjectState(projectId);
    },
    enabled: !!projectId,
    staleTime: 5_000,
  });
}
