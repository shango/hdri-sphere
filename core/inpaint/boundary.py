"""Tier 1 inpainter: cv2.inpaint Navier-Stokes in log-space."""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np

from core.hdr_utils import from_log_space, hdr_safe_composite, to_log_space


class BoundaryInpainter:
    name = "fast"
    description = "Boundary extension (Navier-Stokes)"
    estimated_seconds = 0.3

    def inpaint(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        ball_center: Tuple[int, int],
        ball_radius: int,
    ) -> np.ndarray:
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError(f"Expected (H, W, 3) image, got {image.shape}")
        if mask.shape[:2] != image.shape[:2]:
            raise ValueError(f"mask shape {mask.shape} != image {image.shape[:2]}")

        log_uint8, params = to_log_space(image)

        binary_mask = (mask > 0).astype(np.uint8) * 255

        filled_uint8 = np.empty_like(log_uint8)
        for c in range(3):
            filled_uint8[..., c] = cv2.inpaint(
                log_uint8[..., c], binary_mask, 15, cv2.INPAINT_NS
            )

        inpainted_hdr = from_log_space(filled_uint8, params)

        return hdr_safe_composite(image, inpainted_hdr, mask, feather_radius=15)
