"""Automatic photographer / tripod mask estimation for chrome ball plates."""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np

from core.hdr_utils import luminance, tonemap_for_preview


def estimate_photographer_mask(
    image: np.ndarray,
    ball_center: Tuple[int, int],
    ball_radius: int,
) -> np.ndarray:
    """Generate an automatic mask for the photographer/tripod region.

    Combines a geometric prior (Gaussian blob biased downward), a darkness
    score (log-luminance below ball-interior median), and an edge-density
    score (Canny + blur), then thresholds the weighted product.

    Returns:
        np.ndarray of shape (H, W), dtype uint8, values 0 or 255.
    """
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"Expected (H, W, 3) image, got {image.shape}")

    h, w = image.shape[:2]
    cx, cy = ball_center
    r = max(1, int(ball_radius))

    ball_mask = _disk_mask(h, w, cx, cy, r)

    geometric = _geometric_prior(h, w, cx, cy, r)
    darkness = _darkness_score(image, ball_mask)
    edges = _edge_density(image)

    score = geometric * (0.5 + 0.3 * darkness + 0.2 * edges)

    binary = (score > 0.5).astype(np.uint8) * 255
    binary = cv2.morphologyEx(
        binary, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    )

    binary[ball_mask == 0] = 0

    soft = cv2.GaussianBlur(binary, (11, 11), 0)
    return ((soft > 127).astype(np.uint8) * 255)


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------


def _disk_mask(h: int, w: int, cx: int, cy: int, r: int) -> np.ndarray:
    """Binary mask (uint8 0/255) of pixels inside the ball circle."""
    yy, xx = np.ogrid[:h, :w]
    inside = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
    return (inside.astype(np.uint8) * 255)


def _geometric_prior(h: int, w: int, cx: int, cy: int, r: int) -> np.ndarray:
    """Gaussian blob centered slightly below ball center; values in [0, 1]."""
    yy, xx = np.mgrid[:h, :w].astype(np.float32)
    offset_y = 0.15 * r
    sigma_x = max(1.0, 0.30 * r)
    sigma_y = max(1.0, 0.45 * r)

    dx = (xx - cx) / sigma_x
    dy = (yy - (cy + offset_y)) / sigma_y
    blob = np.exp(-0.5 * (dx * dx + dy * dy))
    return blob.astype(np.float32)


def _darkness_score(image: np.ndarray, ball_mask: np.ndarray) -> np.ndarray:
    """Score in [0, 1]; high where pixel is darker than ball-interior median."""
    lum = luminance(image)
    log_lum = np.log(0.001 + np.maximum(lum, 0.0))

    inside = ball_mask > 0
    if not np.any(inside):
        return np.zeros_like(log_lum, dtype=np.float32)

    median = float(np.median(log_lum[inside]))
    spread = float(np.std(log_lum[inside])) + 1e-3

    score = (median - log_lum) / (2.0 * spread)
    return np.clip(score, 0.0, 1.0).astype(np.float32)


def _edge_density(image: np.ndarray) -> np.ndarray:
    """Score in [0, 1] — Canny edges blurred to get local density."""
    preview = tonemap_for_preview(image, exposure=0.0, gamma=2.2)
    gray = cv2.cvtColor(preview, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 60, 150)
    density = cv2.GaussianBlur(edges.astype(np.float32) / 255.0, (21, 21), 7)
    peak = float(density.max())
    if peak <= 1e-6:
        return np.zeros_like(density, dtype=np.float32)
    return (density / peak).astype(np.float32)
