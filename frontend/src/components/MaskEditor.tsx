import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Stage, Layer, Image as KonvaImage, Line, Circle } from 'react-konva';
import useImage from 'use-image';
import type Konva from 'konva';
import type { KonvaEventObject } from 'konva/lib/Node';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useEditorStore } from '@/stores/editorStore';
import { useBallPreview } from '@/hooks/usePreview';
import { setMask } from '@/lib/api';
import { rasterizeMaskPng } from '@/lib/maskRaster';
import { computeFit, stageToImage } from '@/lib/coords';
import { BrushControls } from '@/components/BrushControls';
import { Spinner } from '@/components/Spinner';
import type { BrushMode } from '@/stores/editorStore';

export interface Point {
  x: number;
  y: number;
}

export interface Stroke {
  mode: BrushMode;
  brushSize: number;
  points: Point[];
}

const STAGE_SIZE = 720;

export function MaskEditor(): JSX.Element {
  const projectId = useEditorStore((s) => s.projectId);
  const imageWidth = useEditorStore((s) => s.imageWidth);
  const imageHeight = useEditorStore((s) => s.imageHeight);
  const brushMode = useEditorStore((s) => s.brushMode);
  const brushSize = useEditorStore((s) => s.brushSize);

  const ballPreview = useBallPreview('original');
  const [ballImg] = useImage(ballPreview.data ?? '', 'anonymous');

  const fit = useMemo(
    () => computeFit(Math.max(imageWidth, imageHeight) || 1, STAGE_SIZE),
    [imageWidth, imageHeight],
  );

  const [strokes, setStrokes] = useState<Stroke[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [cursor, setCursor] = useState<Point | null>(null);
  const stageRef = useRef<Konva.Stage>(null);

  const queryClient = useQueryClient();
  const submitMask = useMutation({
    mutationFn: async (committed: Stroke[]) => {
      if (!projectId) return;
      const png = await rasterizeMaskPng(committed, imageWidth, imageHeight);
      await setMask(projectId, { auto: false, mask_data: png });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['preview', projectId] });
    },
  });

  const getStagePoint = (stage: Konva.Stage): Point | null => {
    const pos = stage.getPointerPosition();
    if (!pos) return null;
    return { x: pos.x, y: pos.y };
  };

  const beginStroke = useCallback(
    (e: KonvaEventObject<MouseEvent | TouchEvent>) => {
      const stage = e.target.getStage();
      if (!stage) return;
      const pt = getStagePoint(stage);
      if (!pt) return;
      const imgPt = { x: stageToImage(pt.x, fit), y: stageToImage(pt.y, fit) };
      setIsDrawing(true);
      setStrokes((prev) => [
        ...prev,
        { mode: brushMode, brushSize: brushSize / fit.scale, points: [imgPt] },
      ]);
    },
    [brushMode, brushSize, fit],
  );

  const continueStroke = useCallback(
    (e: KonvaEventObject<MouseEvent | TouchEvent>) => {
      const stage = e.target.getStage();
      if (!stage) return;
      const pt = getStagePoint(stage);
      if (!pt) return;
      setCursor(pt);
      if (!isDrawing) return;
      const imgPt = { x: stageToImage(pt.x, fit), y: stageToImage(pt.y, fit) };
      setStrokes((prev) => {
        const next = prev.slice();
        const last = next[next.length - 1];
        if (last) {
          next[next.length - 1] = { ...last, points: [...last.points, imgPt] };
        }
        return next;
      });
    },
    [fit, isDrawing],
  );

  const endStroke = useCallback(() => {
    if (!isDrawing) return;
    setIsDrawing(false);
    submitMask.mutate(strokes);
  }, [isDrawing, strokes, submitMask]);

  // Reset strokes when project changes.
  useEffect(() => {
    setStrokes([]);
  }, [projectId]);

  if (ballPreview.isPending || !ballImg) return <Spinner label="Loading ball preview" />;
  if (ballPreview.isError)
    return (
      <div className="flex h-full w-full items-center justify-center text-sm text-red-400">
        {ballPreview.error.message}
      </div>
    );

  return (
    <div className="flex h-full w-full flex-col items-center gap-3 p-4">
      <BrushControls onResetStrokes={() => setStrokes([])} />
      <div
        className="relative rounded border border-ink-700 bg-ink-900"
        style={{ width: STAGE_SIZE, height: STAGE_SIZE }}
        onMouseLeave={() => setCursor(null)}
      >
        <Stage
          ref={stageRef}
          width={STAGE_SIZE}
          height={STAGE_SIZE}
          onMouseDown={beginStroke}
          onMouseMove={continueStroke}
          onMouseUp={endStroke}
          onTouchStart={beginStroke}
          onTouchMove={continueStroke}
          onTouchEnd={endStroke}
        >
          <Layer listening={false}>
            <KonvaImage image={ballImg} width={STAGE_SIZE} height={STAGE_SIZE} />
          </Layer>
          <Layer listening={false} opacity={0.45}>
            {strokes.map((s, i) => (
              <Line
                key={i}
                points={flattenStagePoints(s.points, fit)}
                stroke={s.mode === 'add' ? '#ff4d4d' : '#5b9dff'}
                strokeWidth={s.brushSize * fit.scale}
                lineCap="round"
                lineJoin="round"
                tension={0.2}
                globalCompositeOperation={
                  s.mode === 'add' ? 'source-over' : 'destination-out'
                }
              />
            ))}
          </Layer>
          <Layer listening={false}>
            {cursor ? (
              <Circle
                x={cursor.x}
                y={cursor.y}
                radius={brushSize / 2}
                stroke={brushMode === 'add' ? '#ff4d4d' : '#5b9dff'}
                strokeWidth={1}
                dash={[4, 4]}
              />
            ) : null}
          </Layer>
        </Stage>
        {submitMask.isPending ? (
          <div className="absolute right-2 top-2 rounded bg-ink-800/80 px-2 py-1 text-xs text-ink-200">
            Saving mask…
          </div>
        ) : null}
      </div>
    </div>
  );
}

function flattenStagePoints(points: Point[], fit: ReturnType<typeof computeFit>): number[] {
  const flat: number[] = [];
  for (const p of points) {
    flat.push(p.x * fit.scale, p.y * fit.scale);
  }
  return flat;
}
