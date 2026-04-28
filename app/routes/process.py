"""Mask, processing, and job-status endpoints."""

from __future__ import annotations

import base64
import io
from typing import Union

import numpy as np
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from PIL import Image

from core.project import HDRIProject

from app.deps import get_job_tracker, require_project
from app.schemas import (
    BallOverrideRequest,
    JobStatusResponse,
    MaskAutoRequest,
    MaskDataRequest,
    ProcessRequest,
    ProcessStarted,
)
from app.workers.job_runner import JobTracker

router = APIRouter()


# ---------------------------------------------------------------------------
# Mask
# ---------------------------------------------------------------------------


@router.post("/mask/{project_id}")
def update_mask(
    body: Union[MaskAutoRequest, MaskDataRequest],
    project=Depends(require_project),
) -> dict:
    if isinstance(body, MaskAutoRequest):
        project.auto_mask()
        return {"ok": True, "source": "auto"}

    raw = _decode_base64_png(body.mask_data)
    if raw.shape[:2] != project.ball_hdr.shape[:2]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Mask shape {raw.shape[:2]} does not match plate "
                f"{project.ball_hdr.shape[:2]}"
            ),
        )
    binary = (raw > 0).astype(np.uint8) * 255
    project.update_mask(binary)
    return {"ok": True, "source": "client"}


@router.post("/ball/{project_id}")
def override_ball(
    body: BallOverrideRequest, project=Depends(require_project)
) -> dict:
    """Manual override of detected ball geometry."""
    h, w = project.ball_hdr.shape[:2]
    if not (0 <= body.center_x < w and 0 <= body.center_y < h):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Center out of image"
        )
    if body.radius < 1 or body.radius > max(w, h):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Radius out of range"
        )
    project.update_ball((body.center_x, body.center_y), body.radius)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Process
# ---------------------------------------------------------------------------


@router.post("/process/{project_id}", response_model=ProcessStarted)
def start_process(
    body: ProcessRequest,
    background_tasks: BackgroundTasks,
    project=Depends(require_project),
    tracker: JobTracker = Depends(get_job_tracker),
) -> ProcessStarted:
    if project.mask is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No mask. Run auto-detect or upload a custom mask first.",
        )

    project.selected_technique = body.technique
    job_id = tracker.create_job(project_id=project.project_id, kind="inpaint")
    background_tasks.add_task(_run_inpaint, project, body.technique, job_id, tracker)
    return ProcessStarted(job_id=job_id)


@router.get("/job/{job_id}/status", response_model=JobStatusResponse)
def job_status(
    job_id: str, tracker: JobTracker = Depends(get_job_tracker)
) -> JobStatusResponse:
    state = tracker.get_status(job_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
        )
    return JobStatusResponse(
        job_id=state.job_id,
        status=state.status,
        progress=state.progress,
        message=state.message,
        error=state.error,
        kind=state.kind,
        project_id=state.project_id,
    )


# ---------------------------------------------------------------------------
# Background runners
# ---------------------------------------------------------------------------


def _run_inpaint(
    project: HDRIProject, technique: str, job_id: str, tracker: JobTracker
) -> None:
    try:
        tracker.mark_running(job_id, f"Inpainting with '{technique}'")
        project.get_inpainted(technique)
        tracker.complete_job(job_id, {"technique": technique})
    except Exception as exc:  # pragma: no cover - defensive
        tracker.fail_job(job_id, str(exc))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _decode_base64_png(b64: str) -> np.ndarray:
    if "," in b64:
        b64 = b64.split(",", 1)[1]  # strip data URL prefix
    try:
        raw = base64.b64decode(b64)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Bad base64: {exc}"
        ) from exc

    try:
        with Image.open(io.BytesIO(raw)) as im:
            im = im.convert("L")
            return np.array(im, dtype=np.uint8)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid PNG: {exc}"
        ) from exc
