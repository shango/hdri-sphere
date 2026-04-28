"""Final EXR export.

Export is synchronous because the unwrap step is fast (a few seconds at 4K)
and inpainting is cached. Streams the resulting EXR back as a file
attachment.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.deps import require_project
from app.schemas import Technique
from app.state import project_dir

router = APIRouter()


@router.get("/export/{project_id}")
def export_equirect(
    project=Depends(require_project),
    technique: Technique = Query("good"),
    width: int = Query(4096, ge=512, le=8192),
    height: int = Query(2048, ge=256, le=4096),
) -> FileResponse:
    """Render and return the final equirect EXR for download."""
    if project.ball_hdr is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Project not loaded"
        )

    out_dir = project_dir(project.project_id)
    out_name = f"equirect_{technique}_{width}x{height}.exr"
    out_path = os.path.join(out_dir, out_name)

    project.export_equirect(out_path, technique=technique, resolution=(width, height))

    return FileResponse(
        out_path,
        media_type="image/x-exr",
        filename=out_name,
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
    )
