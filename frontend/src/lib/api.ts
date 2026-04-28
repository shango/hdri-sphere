import type {
  JobStatus,
  ProcessRequest,
  ProcessStarted,
  ProjectCreated,
  ProjectStateResponse,
  Technique,
  ViewMode,
  MaskBody,
  BallOverrideRequest,
} from '@/types/api';

async function jsonOrThrow<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // ignore parse errors
    }
    throw new Error(`${res.status} ${detail}`);
  }
  return res.json() as Promise<T>;
}

export function uploadExr(
  file: File,
  onProgress?: (fraction: number) => void,
): Promise<ProjectCreated> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const fd = new FormData();
    fd.append('file', file);
    xhr.open('POST', '/api/upload');
    xhr.upload.onprogress = (ev) => {
      if (ev.lengthComputable && onProgress) onProgress(ev.loaded / ev.total);
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as ProjectCreated);
        } catch (err) {
          reject(err);
        }
      } else {
        let msg = `${xhr.status} ${xhr.statusText}`;
        try {
          const body = JSON.parse(xhr.responseText) as { detail?: string };
          if (body.detail) msg = body.detail;
        } catch {
          /* noop */
        }
        reject(new Error(msg));
      }
    };
    xhr.onerror = () => reject(new Error('Network error during upload'));
    xhr.send(fd);
  });
}

export async function getProjectState(
  projectId: string,
): Promise<ProjectStateResponse> {
  const res = await fetch(`/api/project/${projectId}`);
  return jsonOrThrow<ProjectStateResponse>(res);
}

export async function deleteProject(projectId: string): Promise<void> {
  const res = await fetch(`/api/project/${projectId}`, { method: 'DELETE' });
  if (!res.ok && res.status !== 404) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
}

export async function setMask(projectId: string, body: MaskBody): Promise<void> {
  const res = await fetch(`/api/mask/${projectId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await jsonOrThrow<{ ok: boolean }>(res);
}

export async function setBall(
  projectId: string,
  body: BallOverrideRequest,
): Promise<void> {
  const res = await fetch(`/api/ball/${projectId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  await jsonOrThrow<{ ok: boolean }>(res);
}

export async function startProcess(
  projectId: string,
  body: ProcessRequest,
): Promise<ProcessStarted> {
  const res = await fetch(`/api/process/${projectId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return jsonOrThrow<ProcessStarted>(res);
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`/api/job/${jobId}/status`);
  return jsonOrThrow<JobStatus>(res);
}

export interface BallPreviewParams {
  view_mode: ViewMode;
  exposure: number;
  technique: Technique;
}

export function ballPreviewUrl(projectId: string, p: BallPreviewParams): string {
  const params = new URLSearchParams({
    view_mode: p.view_mode,
    exposure: String(p.exposure),
    technique: p.technique,
  });
  return `/api/preview/${projectId}/ball?${params.toString()}`;
}

export interface EquirectPreviewParams {
  technique: Technique;
  exposure: number;
  size: number;
}

export function equirectPreviewUrl(
  projectId: string,
  p: EquirectPreviewParams,
): string {
  const params = new URLSearchParams({
    technique: p.technique,
    exposure: String(p.exposure),
    size: String(p.size),
  });
  return `/api/preview/${projectId}/equirect?${params.toString()}`;
}

export interface ExportParams {
  technique: Technique;
  width: number;
  height: number;
}

export function exportUrl(projectId: string, p: ExportParams): string {
  const params = new URLSearchParams({
    technique: p.technique,
    width: String(p.width),
    height: String(p.height),
  });
  return `/api/export/${projectId}?${params.toString()}`;
}
