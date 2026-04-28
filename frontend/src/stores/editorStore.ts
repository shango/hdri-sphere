import { create } from 'zustand';
import type { Technique, ViewMode } from '@/types/api';

export type BrushMode = 'add' | 'remove';

export interface EditorState {
  projectId: string | null;
  sourceFilename: string | null;
  imageWidth: number;
  imageHeight: number;
  ballCenter: [number, number];
  ballRadius: number;

  viewMode: ViewMode;
  previousViewMode: ViewMode;
  brushMode: BrushMode;
  brushSize: number;
  exposure: number;
  technique: Technique;
  outputResolution: [number, number];

  setProject: (info: {
    projectId: string;
    sourceFilename: string;
    imageWidth: number;
    imageHeight: number;
    ballCenter: [number, number];
    ballRadius: number;
  }) => void;
  setViewMode: (mode: ViewMode) => void;
  temporaryViewOriginal: () => void;
  restoreViewMode: () => void;
  setBrushMode: (mode: BrushMode) => void;
  toggleBrushMode: () => void;
  setBrushSize: (size: number) => void;
  setExposure: (exp: number) => void;
  setTechnique: (t: Technique) => void;
  setOutputResolution: (res: [number, number]) => void;
  reset: () => void;
}

const INITIAL = {
  projectId: null,
  sourceFilename: null,
  imageWidth: 0,
  imageHeight: 0,
  ballCenter: [0, 0] as [number, number],
  ballRadius: 0,

  viewMode: 'inpainted' as ViewMode,
  previousViewMode: 'inpainted' as ViewMode,
  brushMode: 'add' as BrushMode,
  brushSize: 30,
  exposure: 0,
  technique: 'good' as Technique,
  outputResolution: [4096, 2048] as [number, number],
};

export const useEditorStore = create<EditorState>((set, get) => ({
  ...INITIAL,

  setProject: (info) =>
    set({
      projectId: info.projectId,
      sourceFilename: info.sourceFilename,
      imageWidth: info.imageWidth,
      imageHeight: info.imageHeight,
      ballCenter: info.ballCenter,
      ballRadius: info.ballRadius,
    }),
  setViewMode: (mode) =>
    set((s) => ({ viewMode: mode, previousViewMode: s.viewMode })),
  temporaryViewOriginal: () =>
    set((s) =>
      s.viewMode === 'original'
        ? s
        : { previousViewMode: s.viewMode, viewMode: 'original' },
    ),
  restoreViewMode: () => set({ viewMode: get().previousViewMode }),
  setBrushMode: (mode) => set({ brushMode: mode }),
  toggleBrushMode: () =>
    set((s) => ({ brushMode: s.brushMode === 'add' ? 'remove' : 'add' })),
  setBrushSize: (size) => set({ brushSize: Math.max(2, Math.min(200, size)) }),
  setExposure: (exp) => set({ exposure: Math.max(-3, Math.min(3, exp)) }),
  setTechnique: (t) => set({ technique: t }),
  setOutputResolution: (res) => set({ outputResolution: res }),
  reset: () => set({ ...INITIAL }),
}));
