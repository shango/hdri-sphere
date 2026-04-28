// Mirrors app/schemas.py. Keep in sync.

export type Technique = 'fast' | 'good' | 'best';
export type ViewMode = 'original' | 'mask' | 'inpainted' | 'compare';
export type JobStatusName = 'pending' | 'running' | 'complete' | 'failed';

export interface ProjectCreated {
  project_id: string;
  width: number;
  height: number;
  ball_center: [number, number];
  ball_radius: number;
}

export interface ProjectStateResponse {
  project_id: string;
  width: number;
  height: number;
  ball_center: [number, number];
  ball_radius: number;
  has_mask: boolean;
  selected_technique: Technique;
  output_resolution: [number, number];
  cached_techniques: string[];
}

export interface ProcessRequest {
  technique: Technique;
}

export interface ProcessStarted {
  job_id: string;
}

export interface JobStatus {
  job_id: string;
  status: JobStatusName;
  progress: number;
  message: string;
  error: string | null;
  kind: string;
  project_id: string | null;
}

export interface BallOverrideRequest {
  center_x: number;
  center_y: number;
  radius: number;
}

export interface MaskAutoBody {
  auto: true;
}

export interface MaskDataBody {
  auto: false;
  mask_data: string;
}

export type MaskBody = MaskAutoBody | MaskDataBody;

export interface HealthResponse {
  status: 'ok';
  inpainters: string[];
}
