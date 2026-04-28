"""Process-wide singletons: project store, job tracker, upload directory.

Routes pull these via small dependency-injection helpers in ``app.deps``.
"""

from __future__ import annotations

import os
import shutil
import threading
import time
from typing import Dict, Optional

from core.project import HDRIProject

from app.workers.job_runner import JobTracker


UPLOAD_ROOT = os.environ.get("HDRI_UPLOAD_ROOT", "/tmp/hdri_uploads")
PROJECT_TTL_SECONDS = int(os.environ.get("PROJECT_TTL_HOURS", "24")) * 3600
MAX_UPLOAD_SIZE_BYTES = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "200")) * 1024 * 1024


class ProjectStore:
    """In-memory registry of active projects keyed by UUID."""

    def __init__(self) -> None:
        self._projects: Dict[str, HDRIProject] = {}
        self._touch: Dict[str, float] = {}
        self._lock = threading.Lock()

    def add(self, project: HDRIProject) -> None:
        with self._lock:
            self._projects[project.project_id] = project
            self._touch[project.project_id] = time.time()

    def get(self, project_id: str) -> Optional[HDRIProject]:
        with self._lock:
            p = self._projects.get(project_id)
            if p is not None:
                self._touch[project_id] = time.time()
            return p

    def remove(self, project_id: str) -> bool:
        with self._lock:
            p = self._projects.pop(project_id, None)
            self._touch.pop(project_id, None)
        if p is None:
            return False
        _delete_project_dir(p.project_id)
        return True

    def cleanup_expired(self) -> int:
        cutoff = time.time() - PROJECT_TTL_SECONDS
        with self._lock:
            stale = [pid for pid, t in self._touch.items() if t < cutoff]
            for pid in stale:
                self._projects.pop(pid, None)
                self._touch.pop(pid, None)
        for pid in stale:
            _delete_project_dir(pid)
        return len(stale)


def _delete_project_dir(project_id: str) -> None:
    path = os.path.join(UPLOAD_ROOT, project_id)
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)


def project_dir(project_id: str) -> str:
    path = os.path.join(UPLOAD_ROOT, project_id)
    os.makedirs(path, exist_ok=True)
    return path


# Process-wide singletons.
project_store = ProjectStore()
job_tracker = JobTracker()
