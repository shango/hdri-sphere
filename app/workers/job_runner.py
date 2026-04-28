"""In-memory job tracker for inpaint and export operations.

Project-scoped jobs persist only for the lifetime of the FastAPI process.
On restart, in-flight jobs are lost — clients should treat that as an
error and re-submit. This is acceptable because Railway restarts are rare
and processing is short (typical pipeline < 30 s).
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Literal, Optional

JobStatus = Literal["pending", "running", "complete", "failed"]


@dataclass
class JobState:
    job_id: str
    status: JobStatus = "pending"
    progress: int = 0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    project_id: Optional[str] = None
    kind: str = "inpaint"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


class JobTracker:
    """Thread-safe in-memory job registry."""

    def __init__(self) -> None:
        self._jobs: Dict[str, JobState] = {}
        self._lock = threading.Lock()

    def create_job(
        self, project_id: Optional[str] = None, kind: str = "inpaint"
    ) -> str:
        job_id = str(uuid.uuid4())
        with self._lock:
            self._jobs[job_id] = JobState(
                job_id=job_id, project_id=project_id, kind=kind
            )
        return job_id

    def mark_running(self, job_id: str, message: str = "") -> None:
        with self._lock:
            j = self._jobs.get(job_id)
            if j is None:
                return
            j.status = "running"
            j.message = message
            j.updated_at = time.time()

    def update_progress(self, job_id: str, progress: int, message: str = "") -> None:
        with self._lock:
            j = self._jobs.get(job_id)
            if j is None:
                return
            j.progress = max(0, min(100, int(progress)))
            if message:
                j.message = message
            j.updated_at = time.time()

    def complete_job(self, job_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        with self._lock:
            j = self._jobs.get(job_id)
            if j is None:
                return
            j.status = "complete"
            j.progress = 100
            j.result = result or {}
            j.message = ""
            j.updated_at = time.time()

    def fail_job(self, job_id: str, error: str) -> None:
        with self._lock:
            j = self._jobs.get(job_id)
            if j is None:
                return
            j.status = "failed"
            j.error = error
            j.message = error
            j.updated_at = time.time()

    def get_status(self, job_id: str) -> Optional[JobState]:
        with self._lock:
            return self._jobs.get(job_id)

    def cleanup_older_than(self, seconds: float) -> int:
        cutoff = time.time() - seconds
        with self._lock:
            stale = [k for k, v in self._jobs.items() if v.updated_at < cutoff]
            for k in stale:
                del self._jobs[k]
            return len(stale)
