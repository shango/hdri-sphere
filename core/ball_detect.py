"""Chrome ball detection in an HDR plate via Hough circle transform."""

from __future__ import annotations

from typing import List, Tuple

import cv2
import numpy as np

from core.hdr_utils import tonemap_for_preview


class BallDetectionError(Exception):
    """Raised when chrome ball cannot be auto-detected."""


def detect_ball(image: np.ndarray) -> Tuple[int, int, int]:
    """Detect the chrome ball in an HDR plate.

    Returns:
        (center_x, center_y, radius) in pixels.
    """
    if image.ndim != 3 or image.shape[2] != 3:
        raise BallDetectionError(f"Expected (H, W, 3) image, got {image.shape}")

    height, width = image.shape[:2]
    min_dim = min(width, height)

    preview = tonemap_for_preview(image, exposure=0.0, gamma=2.2)
    gray = cv2.cvtColor(preview, cv2.COLOR_RGB2GRAY)
    gray = cv2.medianBlur(gray, 5)

    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1.0,
        minDist=max(1, width // 2),
        param1=100,
        param2=30,
        minRadius=max(1, min_dim // 8),
        maxRadius=max(2, min_dim // 2),
    )

    if circles is None or len(circles) == 0 or circles.shape[1] == 0:
        raise BallDetectionError(
            "Could not auto-detect a chrome ball. Try cropping the plate "
            "tighter to the ball or specify center/radius manually."
        )

    candidates: List[Tuple[float, float, float]] = [
        (float(c[0]), float(c[1]), float(c[2])) for c in circles[0]
    ]

    best = max(candidates, key=lambda c: _boundary_gradient_score(gray, c))
    cx, cy, r = best
    return int(round(cx)), int(round(cy)), int(round(r))


def _boundary_gradient_score(
    gray: np.ndarray, circle: Tuple[float, float, float], n_samples: int = 180
) -> float:
    """Mean Sobel-magnitude along the boundary of a candidate circle.

    Chrome balls have a very sharp edge transition; whichever Hough candidate
    has the strongest boundary gradient is the most likely true ball.
    """
    cx, cy, r = circle
    h, w = gray.shape

    sobel_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(sobel_x, sobel_y)

    angles = np.linspace(0.0, 2.0 * np.pi, n_samples, endpoint=False)
    xs = np.clip((cx + r * np.cos(angles)).astype(np.int32), 0, w - 1)
    ys = np.clip((cy + r * np.sin(angles)).astype(np.int32), 0, h - 1)
    return float(mag[ys, xs].mean())
