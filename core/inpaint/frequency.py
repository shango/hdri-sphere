"""Tier 2 inpainter: frequency-aware fill (low band: NS boundary; high band: radial)."""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np

from core.hdr_utils import from_log_space, hdr_safe_composite, to_log_space

from .radial import radial_fill


class FrequencyAwareInpainter:
    name = "good"
    description = "Frequency-aware fill with radial sampling"
    estimated_seconds = 2.0

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
        log_f = log_uint8.astype(np.float32)

        # Low frequency = blurred version (smooth gradient across the ball).
        low = cv2.GaussianBlur(log_f, (101, 101), 30)
        high = log_f - low  # zero-mean detail layer

        binary_mask = (mask > 0).astype(np.uint8) * 255

        # Low band: cv2.inpaint NS per channel on uint8 representation.
        low_uint8 = np.clip(low, 0.0, 255.0).astype(np.uint8)
        low_filled_uint8 = np.empty_like(low_uint8)
        for c in range(3):
            low_filled_uint8[..., c] = cv2.inpaint(
                low_uint8[..., c], binary_mask, 15, cv2.INPAINT_NS
            )
        low_filled = low_filled_uint8.astype(np.float32)

        # High band: radial fill (median of unmasked samples at same radius).
        # Operate on the float high-frequency residual directly.
        high_filled = radial_fill(high, mask, ball_center, ball_radius)

        # Recombine, clip back to uint8 log-space range, then invert log.
        recombined = np.clip(low_filled + high_filled, 0.0, 255.0).astype(np.uint8)
        inpainted_hdr = from_log_space(recombined, params)

        return hdr_safe_composite(image, inpainted_hdr, mask, feather_radius=15)
