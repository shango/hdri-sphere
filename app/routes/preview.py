"""Preview rendering endpoints. All previews are tone-mapped JPEGs.

Raw EXR data is never sent to the browser — it would be 100MB+ per request.
Tone-mapping happens server-side using ``core.hdr_utils.tonemap_for_preview``.
"""

from __future__ import annotations

import io
from typing import Literal

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from core.hdr_utils import tonemap_for_preview
from core.unwrap import ball_to_equirect

from app.deps import require_project
from app.schemas import Technique, ViewMode

router = APIRouter()


_MAX_BALL_PREVIEW = 1024
_DEFAULT_EQUIRECT_PREVIEW = 1024


@router.get("/preview/{project_id}/ball")
def preview_ball(
    project=Depends(require_project),
    view_mode: ViewMode = Query("original"),
    exposure: float = Query(0.0, ge=-6.0, le=6.0),
    technique: Technique = Query("good"),
) -> Response:
    """Render a ball-space preview as a tone-mapped JPEG."""
    if project.ball_hdr is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Project not loaded"
        )

    if view_mode == "original":
        rgb = tonemap_for_preview(project.ball_hdr, exposure=exposure)
    elif view_mode == "mask":
        rgb = _render_mask_overlay(project.ball_hdr, project.mask, exposure)
    elif view_mode == "inpainted":
        if project.mask is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No mask. Generate or upload a mask first.",
            )
        inpainted = project.get_inpainted(technique)
        rgb = tonemap_for_preview(inpainted, exposure=exposure)
    elif view_mode == "compare":
        # Side-by-side: left = original, right = inpainted.
        if project.mask is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No mask. Generate or upload a mask first.",
            )
        left = tonemap_for_preview(project.ball_hdr, exposure=exposure)
        right = tonemap_for_preview(project.get_inpainted(technique), exposure=exposure)
        rgb = np.concatenate([left, right], axis=1)
    else:  # pragma: no cover - exhausted by type
        raise HTTPException(status_code=400, detail=f"Unknown view_mode: {view_mode}")

    rgb = _downsample(rgb, _MAX_BALL_PREVIEW)
    return _jpeg_response(rgb)


@router.get("/preview/{project_id}/equirect")
def preview_equirect(
    project=Depends(require_project),
    technique: Technique = Query("good"),
    exposure: float = Query(0.0, ge=-6.0, le=6.0),
    size: int = Query(_DEFAULT_EQUIRECT_PREVIEW, ge=256, le=2048),
) -> Response:
    """Render an equirect preview at low resolution as JPEG."""
    if project.ball_hdr is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Project not loaded"
        )

    if project.mask is None:
        ball_for_unwrap = project.ball_hdr
    else:
        ball_for_unwrap = project.get_inpainted(technique)

    width = int(size)
    height = max(2, width // 2)
    equirect = ball_to_equirect(
        ball_for_unwrap,
        project.ball_center,
        project.ball_radius,
        output_width=width,
        output_height=height,
    )
    rgb = tonemap_for_preview(equirect, exposure=exposure)
    return _jpeg_response(rgb)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render_mask_overlay(
    ball_hdr: np.ndarray, mask: np.ndarray | None, exposure: float
) -> np.ndarray:
    base = tonemap_for_preview(ball_hdr, exposure=exposure)
    if mask is None:
        return base
    overlay = base.copy()
    red = np.zeros_like(base)
    red[..., 0] = 255  # red channel — RGB order
    alpha = (mask > 0).astype(np.float32)[..., None] * 0.5
    overlay = (overlay.astype(np.float32) * (1.0 - alpha) + red.astype(np.float32) * alpha)
    return np.clip(overlay, 0, 255).astype(np.uint8)


def _downsample(rgb: np.ndarray, max_dim: int) -> np.ndarray:
    h, w = rgb.shape[:2]
    longest = max(h, w)
    if longest <= max_dim:
        return rgb
    scale = max_dim / longest
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))
    return cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)


def _jpeg_response(rgb: np.ndarray, quality: int = 85) -> Response:
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    ok, buf = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, int(quality)])
    if not ok:
        raise HTTPException(status_code=500, detail="JPEG encode failed")
    return Response(content=buf.tobytes(), media_type="image/jpeg")
