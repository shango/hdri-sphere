"""Radial fill: sample unmasked pixels at the same radius from ball center.

For each masked pixel, we hop around the ball to other angles at the same
radial distance and take the median of the unmasked samples. This works
well for chrome ball plates because reflections of distant environments
are roughly rotation-symmetric about the up axis at the same elevation.
"""

from __future__ import annotations

from typing import Sequence, Tuple

import numpy as np


_DEFAULT_OFFSETS_DEG: Tuple[float, ...] = (60.0, 120.0, 180.0, 240.0, 300.0)


def radial_fill(
    image: np.ndarray,
    mask: np.ndarray,
    ball_center: Tuple[int, int],
    ball_radius: int,
    angle_offsets_deg: Sequence[float] = _DEFAULT_OFFSETS_DEG,
) -> np.ndarray:
    """Fill masked pixels by sampling at the same radius around the ball.

    Args:
        image: float32 (H, W, 3). Treated as a flat field — caller decides
            whether this is linear HDR, log-space, or a high-frequency band.
        mask: uint8 (H, W); >0 = masked.
        ball_center, ball_radius: ball geometry in pixel coords.
        angle_offsets_deg: angles (in degrees) to add to each masked pixel's
            angle when looking up donor samples.

    Returns:
        float32 (H, W, 3). Pixels outside the mask are returned unchanged;
        masked pixels are replaced with the median of valid donor samples.
        If no offset hits a valid donor for a given pixel, that pixel is
        left as the original (caller must fill via other means).
    """
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"Expected (H, W, 3) image, got {image.shape}")
    if mask.shape[:2] != image.shape[:2]:
        raise ValueError(f"mask shape {mask.shape} does not match image")

    h, w = image.shape[:2]
    cx, cy = ball_center

    masked_yx = np.argwhere(mask > 0)
    if masked_yx.size == 0:
        return image.astype(np.float32, copy=True)

    my = masked_yx[:, 0].astype(np.float32)
    mx = masked_yx[:, 1].astype(np.float32)

    # Angle of each masked pixel from ball center (image-space, y-down).
    dx = mx - cx
    dy = my - cy
    radii = np.sqrt(dx * dx + dy * dy)
    base_angle = np.arctan2(dy, dx)

    # For each offset, sample at (radius, base_angle + offset).
    n_pix = masked_yx.shape[0]
    n_off = len(angle_offsets_deg)
    samples = np.empty((n_off, n_pix, 3), dtype=np.float32)
    valid = np.zeros((n_off, n_pix), dtype=bool)

    for i, deg in enumerate(angle_offsets_deg):
        rad = np.deg2rad(deg)
        sx = cx + radii * np.cos(base_angle + rad)
        sy = cy + radii * np.sin(base_angle + rad)
        sxi = np.rint(sx).astype(np.int32)
        syi = np.rint(sy).astype(np.int32)

        in_bounds = (sxi >= 0) & (sxi < w) & (syi >= 0) & (syi < h)
        sxi_c = np.clip(sxi, 0, w - 1)
        syi_c = np.clip(syi, 0, h - 1)

        unmasked = mask[syi_c, sxi_c] == 0
        ok = in_bounds & unmasked
        valid[i] = ok

        samples[i] = image[syi_c, sxi_c]

    # Median over valid samples per pixel. Use NaN to mark invalid then nanmedian.
    samples_nan = samples.copy()
    samples_nan[~valid] = np.nan
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        filled = np.nanmedian(samples_nan, axis=0)

    out = image.astype(np.float32, copy=True)
    has_donor = np.any(valid, axis=0)
    target_y = masked_yx[has_donor, 0]
    target_x = masked_yx[has_donor, 1]
    out[target_y, target_x] = filled[has_donor].astype(np.float32, copy=False)
    return out
