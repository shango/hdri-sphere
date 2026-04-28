"""Project state container for an in-progress HDRI conversion.

A single ``HDRIProject`` holds the loaded plate, ball geometry, current
mask, and a cache of inpainted results keyed by ``(technique, mask_hash)``.
Caching means switching techniques in the UI returns instantly the second
time. Mutating the mask invalidates the cache.

This module is web-framework-agnostic — it imports nothing from FastAPI.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np

from core.ball_detect import detect_ball
from core.exr_io import load_exr, save_exr
from core.inpaint import get_inpainter
from core.mask_estimate import estimate_photographer_mask
from core.unwrap import ball_to_equirect


@dataclass
class HDRIProject:
    """State of a single in-progress HDRI conversion. Holds NumPy arrays."""

    project_id: str
    source_path: str

    ball_hdr: Optional[np.ndarray] = None
    ball_center: Optional[Tuple[int, int]] = None
    ball_radius: Optional[int] = None

    mask: Optional[np.ndarray] = None

    # Cache: (technique_name, mask_hash) -> inpainted_hdr
    inpaint_cache: dict = field(default_factory=dict)

    selected_technique: str = "good"
    output_resolution: Tuple[int, int] = (4096, 2048)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @classmethod
    def new(cls, source_path: str) -> "HDRIProject":
        return cls(project_id=str(uuid.uuid4()), source_path=source_path)

    def load(self) -> None:
        """Load the EXR and detect the ball. Idempotent."""
        if self.ball_hdr is not None and self.ball_center is not None:
            return
        self.ball_hdr = load_exr(self.source_path)
        cx, cy, r = detect_ball(self.ball_hdr)
        self.ball_center = (cx, cy)
        self.ball_radius = r

    def is_loaded(self) -> bool:
        return self.ball_hdr is not None and self.ball_center is not None

    # ------------------------------------------------------------------
    # Mask
    # ------------------------------------------------------------------

    def auto_mask(self) -> np.ndarray:
        """Generate auto mask from current ball geometry. Invalidates cache."""
        self._require_loaded()
        assert self.ball_hdr is not None and self.ball_center is not None
        assert self.ball_radius is not None
        self.mask = estimate_photographer_mask(
            self.ball_hdr, self.ball_center, self.ball_radius
        )
        self.inpaint_cache.clear()
        return self.mask

    def update_mask(self, new_mask: np.ndarray) -> None:
        """Replace the mask with a user-supplied one. Invalidates cache."""
        self._require_loaded()
        if new_mask.ndim != 2:
            raise ValueError(f"Expected 2D mask, got shape {new_mask.shape}")
        if new_mask.shape != self.ball_hdr.shape[:2]:  # type: ignore[union-attr]
            raise ValueError(
                f"Mask shape {new_mask.shape} != image {self.ball_hdr.shape[:2]}"  # type: ignore[union-attr]
            )
        self.mask = (new_mask > 0).astype(np.uint8) * 255
        self.inpaint_cache.clear()

    def update_ball(self, center: Tuple[int, int], radius: int) -> None:
        """User override of detected ball geometry. Invalidates cache."""
        self.ball_center = (int(center[0]), int(center[1]))
        self.ball_radius = int(radius)
        self.inpaint_cache.clear()
        # Mask is geometry-dependent; clear it so next preview regenerates.
        self.mask = None

    # ------------------------------------------------------------------
    # Inpaint (cached)
    # ------------------------------------------------------------------

    def get_inpainted(self, technique: str) -> np.ndarray:
        """Return the inpainted ball image for ``technique``, using cache."""
        self._require_loaded()
        if self.mask is None:
            raise RuntimeError("Cannot inpaint: no mask. Call auto_mask() first.")

        key = (technique, self._mask_hash())
        cached = self.inpaint_cache.get(key)
        if cached is not None:
            return cached

        assert self.ball_hdr is not None and self.ball_center is not None
        assert self.ball_radius is not None
        inpainter = get_inpainter(technique)
        result = inpainter.inpaint(
            self.ball_hdr, self.mask, self.ball_center, self.ball_radius
        )
        self.inpaint_cache[key] = result
        return result

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_equirect(
        self,
        output_path: str,
        technique: Optional[str] = None,
        resolution: Optional[Tuple[int, int]] = None,
    ) -> None:
        """Render and save the final equirect EXR."""
        self._require_loaded()
        technique = technique or self.selected_technique
        width, height = resolution or self.output_resolution

        if self.mask is None:
            ball_for_unwrap = self.ball_hdr
        else:
            ball_for_unwrap = self.get_inpainted(technique)

        assert ball_for_unwrap is not None and self.ball_center is not None
        assert self.ball_radius is not None
        equirect = ball_to_equirect(
            ball_for_unwrap,
            self.ball_center,
            self.ball_radius,
            output_width=width,
            output_height=height,
        )
        os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
        save_exr(output_path, equirect)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _require_loaded(self) -> None:
        if not self.is_loaded():
            raise RuntimeError("Project not loaded. Call .load() first.")

    def _mask_hash(self) -> str:
        assert self.mask is not None
        return hashlib.sha256(self.mask.tobytes()).hexdigest()
