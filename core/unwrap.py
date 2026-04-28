"""Mirror-ball -> equirectangular projection.

Camera looks down -Z at the chrome ball; the ball reflects view rays
according to Snell's law. For each output equirect pixel we compute the
world direction it represents, derive the ball-surface normal that would
reflect a -Z view ray to that direction, then sample the ball image at
the orthographic projection of that normal.
"""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np


def ball_to_equirect(
    ball_image: np.ndarray,
    ball_center: Tuple[int, int],
    ball_radius: int,
    output_width: int = 4096,
    output_height: int = 2048,
) -> np.ndarray:
    """Convert a mirror-ball image to equirectangular (lat-long) projection.

    Output is float32 RGB with shape (output_height, output_width, 3).
    Pixels whose corresponding ray exits the ball (the back-of-ball blind
    spot) are filled with 0.
    """
    if ball_image.ndim != 3 or ball_image.shape[2] != 3:
        raise ValueError(f"Expected (H, W, 3) image, got {ball_image.shape}")
    if output_width < 2 or output_height < 2:
        raise ValueError("Output resolution too small")

    cx, cy = ball_center
    r = float(ball_radius)
    if r <= 0:
        raise ValueError("ball_radius must be positive")

    u = (np.arange(output_width, dtype=np.float32) + 0.5) / output_width
    v = (np.arange(output_height, dtype=np.float32) + 0.5) / output_height

    phi = (u - 0.5) * (2.0 * np.pi)        # longitude
    theta = (0.5 - v) * np.pi              # latitude (positive = up)

    cos_t = np.cos(theta)[:, None]
    sin_t = np.sin(theta)[:, None]
    sin_p = np.sin(phi)[None, :]
    cos_p = np.cos(phi)[None, :]

    # World direction (the ray we want to sample from the environment).
    dx = cos_t * sin_p
    dy = sin_t * np.ones_like(sin_p)
    dz = cos_t * cos_p

    # View direction toward the ball is -Z. The reflected ray equals the
    # outgoing direction (dx, dy, dz). The surface normal is the half-vector
    # between view (+Z, since we negate the incoming -Z) and reflection.
    nx = dx
    ny = dy
    nz = dz + 1.0
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    safe = norm > 1e-6
    nx = np.where(safe, nx / np.where(safe, norm, 1.0), 0.0)
    ny = np.where(safe, ny / np.where(safe, norm, 1.0), 0.0)

    # Orthographic projection of the normal onto the image plane.
    # Image y grows downward but our math has y up, so flip ny.
    map_x = (cx + nx * r).astype(np.float32)
    map_y = (cy - ny * r).astype(np.float32)

    out_of_ball = ~safe
    map_x[out_of_ball] = -1.0
    map_y[out_of_ball] = -1.0

    equirect = cv2.remap(
        ball_image,
        map_x,
        map_y,
        interpolation=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0.0, 0.0, 0.0),
    )
    # Cubic resampling can overshoot at high-contrast boundaries; negative
    # radiance is unphysical and confuses some DCCs.
    np.clip(equirect, 0.0, None, out=equirect)
    return equirect.astype(np.float32, copy=False)
