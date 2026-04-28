"""FastAPI dependency providers — small, typed accessors for the singletons."""

from __future__ import annotations

from fastapi import HTTPException, status

from core.project import HDRIProject

from app.state import job_tracker as _job_tracker
from app.state import project_store as _project_store
from app.workers.job_runner import JobTracker


def get_project_store():
    return _project_store


def get_job_tracker() -> JobTracker:
    return _job_tracker


def require_project(project_id: str) -> HDRIProject:
    project = _project_store.get(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return project
