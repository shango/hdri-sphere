"""HDR space conversions, tone mapping, and feathered compositing utilities."""

from __future__ import annotations

from typing import Dict, Tuple

import cv2
import numpy as np


def luminance(hdr: np.ndarray) -> np.ndarray:
    """Compute Rec. 709 luminance (single-channel float32)."""
    if hdr.ndim != 3 or hdr.shape[2] != 3:
        raise ValueError(f"Expected (H, W, 3) image, got {hdr.shape}")
    r, g, b = hdr[..., 0], hdr[..., 1], hdr[..., 2]
    return (0.2126 * r + 0.7152 * g + 0.0722 * b).astype(np.float32, copy=False)


def to_log_space(
    hdr: np.ndarray, epsilon: float = 0.001
) -> Tuple[np.ndarray, Dict[str, float]]:
    """Convert linear HDR to a uint8 log-space image plus inversion params.

    Inpainting algorithms that take 8-bit input (cv2.inpaint, PatchMatch
    libraries, etc.) cannot tolerate the dynamic range of HDR plates. A log
    transform compresses the range so a single bright pixel doesn't dominate.
    """
    if hdr.dtype != np.float32:
        hdr = hdr.astype(np.float32)
    safe = np.maximum(hdr, 0.0)
    log_img = np.log(epsilon + safe)
    lo = float(log_img.min())
    hi = float(log_img.max())
    span = max(hi - lo, 1e-6)
    norm = (log_img - lo) / span
    uint8 = np.clip(norm * 255.0, 0.0, 255.0).astype(np.uint8)
    params = {"epsilon": epsilon, "lo": lo, "hi": hi}
    return uint8, params


def from_log_space(log_uint8: np.ndarray, params: Dict[str, float]) -> np.ndarray:
    """Inverse of to_log_space. Returns float32 linear HDR."""
    epsilon = params["epsilon"]
    lo = params["lo"]
    hi = params["hi"]
    span = max(hi - lo, 1e-6)
    norm = log_uint8.astype(np.float32) / 255.0
    log_img = norm * span + lo
    linear = np.exp(log_img) - epsilon
    return np.maximum(linear, 0.0).astype(np.float32, copy=False)


def hdr_safe_composite(
    original_hdr: np.ndarray,
    inpainted_hdr: np.ndarray,
    mask: np.ndarray,
    feather_radius: int = 15,
) -> np.ndarray:
    """Composite inpainted into original with a feathered mask boundary.

    Values outside the (feathered) mask are preserved exactly. The feather
    only affects a thin transition band around the mask edge.
    """
    if original_hdr.shape != inpainted_hdr.shape:
        raise ValueError(
            f"shape mismatch: {original_hdr.shape} vs {inpainted_hdr.shape}"
        )
    if mask.shape[:2] != original_hdr.shape[:2]:
        raise ValueError(f"mask shape {mask.shape} does not match image")

    mask_f = (mask.astype(np.float32) / 255.0)
    if feather_radius > 0:
        k = max(3, int(feather_radius) * 2 + 1)
        mask_f = cv2.GaussianBlur(mask_f, (k, k), feather_radius / 1.5)
    mask_f = np.clip(mask_f, 0.0, 1.0)[..., None]

    composite = original_hdr * (1.0 - mask_f) + inpainted_hdr * mask_f
    return composite.astype(np.float32, copy=False)


def tonemap_for_preview(
    hdr: np.ndarray, exposure: float = 0.0, gamma: float = 2.2
) -> np.ndarray:
    """Reinhard tone-map an HDR image to uint8 RGB for preview display."""
    scale = float(2.0**exposure)
    scaled = np.maximum(hdr.astype(np.float32) * scale, 0.0)
    mapped = scaled / (1.0 + scaled)
    if gamma and gamma != 1.0:
        mapped = np.power(mapped, 1.0 / gamma)
    return np.clip(mapped * 255.0, 0.0, 255.0).astype(np.uint8)
