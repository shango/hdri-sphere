import { useHotkeys } from 'react-hotkeys-hook';
import { useEditorStore } from '@/stores/editorStore';

export function useShortcuts(): void {
  const setViewMode = useEditorStore((s) => s.setViewMode);
  const temporaryViewOriginal = useEditorStore((s) => s.temporaryViewOriginal);
  const restoreViewMode = useEditorStore((s) => s.restoreViewMode);
  const toggleBrushMode = useEditorStore((s) => s.toggleBrushMode);
  const brushSize = useEditorStore((s) => s.brushSize);
  const setBrushSize = useEditorStore((s) => s.setBrushSize);

  useHotkeys('1', () => setViewMode('original'));
  useHotkeys('2', () => setViewMode('mask'));
  useHotkeys('3', () => setViewMode('inpainted'));
  useHotkeys('4', () => setViewMode('compare'));
  useHotkeys('x', () => toggleBrushMode());
  useHotkeys('[', () => setBrushSize(brushSize - 5));
  useHotkeys(']', () => setBrushSize(brushSize + 5));

  useHotkeys('\\', (e) => {
    e.preventDefault();
    temporaryViewOriginal();
  }, { keydown: true, keyup: false });
  useHotkeys(
    '\\',
    () => restoreViewMode(),
    { keydown: false, keyup: true },
  );
}
