// Translate between Konva stage coords (display pixels) and source-image coords.
// The stage is fit-to-square; the source image may be larger.

export interface FitInfo {
  scale: number; // image -> stage
  invScale: number; // stage -> image
  stageSize: number;
  imageSize: number;
}

export function computeFit(imageSize: number, stageSize: number): FitInfo {
  const scale = stageSize / imageSize;
  return { scale, invScale: 1 / scale, stageSize, imageSize };
}

export function stageToImage(p: number, fit: FitInfo): number {
  return p * fit.invScale;
}

export function imageToStage(p: number, fit: FitInfo): number {
  return p * fit.scale;
}
