// Rasterize a list of strokes (in image-space coords) onto an offscreen canvas
// of the source-image dimensions, then encode to a base64 PNG suitable for
// POST /api/mask/{id}.

import type { Stroke } from '@/components/MaskEditor';

export function rasterizeMaskPng(
  strokes: Stroke[],
  width: number,
  height: number,
  baseMask?: ImageBitmap | HTMLImageElement | null,
): Promise<string> {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('canvas 2D context unavailable');

  ctx.fillStyle = 'black';
  ctx.fillRect(0, 0, width, height);

  if (baseMask) {
    // Server returns the auto-mask; treat any non-zero as masked.
    ctx.globalCompositeOperation = 'lighter';
    ctx.drawImage(baseMask, 0, 0, width, height);
  }

  for (const stroke of strokes) {
    if (stroke.points.length < 2) continue;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = stroke.brushSize;
    ctx.beginPath();
    ctx.moveTo(stroke.points[0]!.x, stroke.points[0]!.y);
    for (let i = 1; i < stroke.points.length; i += 1) {
      const pt = stroke.points[i]!;
      ctx.lineTo(pt.x, pt.y);
    }
    if (stroke.mode === 'add') {
      ctx.globalCompositeOperation = 'source-over';
      ctx.strokeStyle = 'white';
    } else {
      ctx.globalCompositeOperation = 'destination-out';
      ctx.strokeStyle = 'black';
    }
    ctx.stroke();
  }

  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) {
        reject(new Error('canvas.toBlob returned null'));
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result;
        if (typeof result !== 'string') {
          reject(new Error('FileReader returned non-string'));
          return;
        }
        // Strip "data:image/png;base64," prefix; backend handles either form.
        const idx = result.indexOf(',');
        resolve(idx >= 0 ? result.slice(idx + 1) : result);
      };
      reader.onerror = () => reject(new Error('FileReader error'));
      reader.readAsDataURL(blob);
    }, 'image/png');
  });
}
