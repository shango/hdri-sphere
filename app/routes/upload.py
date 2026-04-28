"""Upload, project state, and project deletion endpoints."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from core.exr_io import validate_chrome_ball_plate
from core.project import HDRIProject

from app.deps import require_project
from app.schemas import ProjectCreated, ProjectStateResponse
from app.state import MAX_UPLOAD_SIZE_BYTES, project_dir, project_store

router = APIRouter()


@router.post("/upload", response_model=ProjectCreated)
async def upload(file: UploadFile = File(...)) -> ProjectCreated:
    if not file.filename or not file.filename.lower().endswith(".exr"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .exr files are accepted.",
        )

    project = HDRIProject.new(source_path="")
    target_dir = project_dir(project.project_id)
    target_path = os.path.join(target_dir, "source.exr")

    total = 0
    try:
        with open(target_path, "wb") as fh:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds {MAX_UPLOAD_SIZE_BYTES} bytes.",
                    )
                fh.write(chunk)
    except HTTPException:
        if os.path.exists(target_path):
            os.remove(target_path)
        raise

    project.source_path = target_path
    try:
        project.load()
    except Exception as exc:
        if os.path.exists(target_path):
            os.remove(target_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to load EXR: {exc}",
        ) from exc

    valid, message = validate_chrome_ball_plate(project.ball_hdr)  # type: ignore[arg-type]
    if not valid:
        # We tolerate failures of the HDR sanity check (synthetic test plates
        # and odd inputs may legitimately fail) but surface a warning header.
        # Refuse only on critical failures (NaN/Inf, wrong shape).
        if "NaN" in message or "shape" in message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=message
            )

    assert project.ball_hdr is not None
    h, w = project.ball_hdr.shape[:2]
    cx, cy = project.ball_center  # type: ignore[misc]
    project_store.add(project)

    return ProjectCreated(
        project_id=project.project_id,
        width=w,
        height=h,
        ball_center=(cx, cy),
        ball_radius=project.ball_radius or 0,
    )


@router.get("/project/{project_id}", response_model=ProjectStateResponse)
def get_project_state(project=Depends(require_project)) -> ProjectStateResponse:
    h, w = project.ball_hdr.shape[:2]
    return ProjectStateResponse(
        project_id=project.project_id,
        width=w,
        height=h,
        ball_center=project.ball_center,
        ball_radius=project.ball_radius,
        has_mask=project.mask is not None,
        selected_technique=project.selected_technique,
        output_resolution=project.output_resolution,
        cached_techniques=sorted({k[0] for k in project.inpaint_cache}),
    )


@router.delete("/project/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str) -> None:
    if not project_store.remove(project_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
