"""Pydantic request/response schemas. Mirrored to frontend/src/types/api.ts."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Technique = Literal["fast", "good", "best"]
ViewMode = Literal["original", "mask", "inpainted", "compare"]
JobStatusName = Literal["pending", "running", "complete", "failed"]


class ProjectCreated(BaseModel):
    project_id: str
    width: int
    height: int
    ball_center: tuple[int, int]
    ball_radius: int


class ProjectStateResponse(BaseModel):
    project_id: str
    width: int
    height: int
    ball_center: tuple[int, int]
    ball_radius: int
    has_mask: bool
    selected_technique: Technique
    output_resolution: tuple[int, int]
    cached_techniques: list[str]


class MaskAutoRequest(BaseModel):
    auto: Literal[True] = True


class MaskDataRequest(BaseModel):
    """Body for ``POST /api/mask/{project_id}`` with custom mask.

    ``mask_data`` is a base64-encoded PNG. Width and height must match
    the project's source plate. Pixels with R>0 are considered masked.
    """

    auto: Literal[False] = False
    mask_data: str = Field(..., description="base64-encoded PNG mask")


class BallOverrideRequest(BaseModel):
    center_x: int
    center_y: int
    radius: int


class ProcessRequest(BaseModel):
    technique: Technique = "good"


class ProcessStarted(BaseModel):
    job_id: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatusName
    progress: int
    message: str
    error: Optional[str] = None
    kind: str
    project_id: Optional[str] = None


class ExportRequest(BaseModel):
    technique: Technique = "good"
    width: int = 4096
    height: int = 2048


class ExportStarted(BaseModel):
    job_id: str


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    inpainters: list[str]
