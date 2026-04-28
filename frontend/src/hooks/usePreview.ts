import { useQuery } from '@tanstack/react-query';
import { useEditorStore } from '@/stores/editorStore';
import { ballPreviewUrl, equirectPreviewUrl } from '@/lib/api';
import type { ViewMode } from '@/types/api';

async function fetchAsObjectUrl(url: string): Promise<string> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Preview ${url} failed: ${res.status}`);
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

export function useBallPreview(viewMode: ViewMode) {
  const projectId = useEditorStore((s) => s.projectId);
  const exposure = useEditorStore((s) => s.exposure);
  const technique = useEditorStore((s) => s.technique);

  return useQuery({
    queryKey: ['preview', projectId, 'ball', viewMode, technique, exposure],
    queryFn: async () => {
      if (!projectId) throw new Error('No project');
      return fetchAsObjectUrl(
        ballPreviewUrl(projectId, { view_mode: viewMode, exposure, technique }),
      );
    },
    enabled: !!projectId,
  });
}

export function useEquirectPreview(size = 1024) {
  const projectId = useEditorStore((s) => s.projectId);
  const exposure = useEditorStore((s) => s.exposure);
  const technique = useEditorStore((s) => s.technique);

  return useQuery({
    queryKey: ['preview', projectId, 'equirect', technique, exposure, size],
    queryFn: async () => {
      if (!projectId) throw new Error('No project');
      return fetchAsObjectUrl(
        equirectPreviewUrl(projectId, { exposure, technique, size }),
      );
    },
    enabled: !!projectId,
  });
}
