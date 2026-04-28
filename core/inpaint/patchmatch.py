"""Tier 3 inpainter: PatchMatch exemplar fill with vectorized fallback.

If a PatchMatch library is installed at import time, we delegate to it. If
not, we fall back to a numpy-vectorized exemplar-based fill that walks the
mask boundary inward, copying the best-matching unmasked patch into each
boundary pixel. The fallback is significantly slower than the PRD's stated
~8 seconds for a 1500x1500 region but produces acceptable results.

All work happens in log-space; values outside the mask are preserved
exactly via :func:`hdr_safe_composite`.
"""

from __future__ import annotations

from typing import Optional, Tuple

import cv2
import numpy as np

from core.hdr_utils import from_log_space, hdr_safe_composite, to_log_space


_PATCH_LIB: Optional[str] = None
_pm_inpaint = None

try:  # pragma: no cover - environment-dependent
    from patch_match import inpaint as _pm_inpaint  # type: ignore

    _PATCH_LIB = "patch_match"
except Exception:
    try:  # pragma: no cover
        from PyPatchMatch import patch_match as _pm  # type: ignore

        _pm_inpaint = _pm.inpaint
        _PATCH_LIB = "PyPatchMatch"
    except Exception:
        _pm_inpaint = None
        _PATCH_LIB = None


class PatchMatchInpainter:
    name = "best"
    description = "Exemplar-based PatchMatch (or vectorized fallback)"
    estimated_seconds = 30.0 if _PATCH_LIB is None else 8.0

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

        if _pm_inpaint is not None:  # pragma: no cover - env-dependent
            try:
                filled_uint8 = _pm_inpaint(log_uint8, binary_mask, patch_size=9)
            except Exception:
                filled_uint8 = _exemplar_fill(log_uint8, binary_mask, ball_center, ball_radius)
        else:
            filled_uint8 = _exemplar_fill(log_uint8, binary_mask, ball_center, ball_radius)

        inpainted_hdr = from_log_space(filled_uint8, params)
        return hdr_safe_composite(image, inpainted_hdr, mask, feather_radius=15)


# ---------------------------------------------------------------------------
# Vectorized exemplar fallback
# ---------------------------------------------------------------------------


def _exemplar_fill(
    img_uint8: np.ndarray,
    mask_uint8: np.ndarray,
    ball_center: Tuple[int, int],
    ball_radius: int,
    patch_size: int = 9,
    candidates_per_iter: int = 256,
) -> np.ndarray:
    """Fill mask via greedy boundary-priority exemplar copy.

    Strategy: walk the mask boundary, and for each boundary pixel extract a
    patch_size x patch_size window. Compare the *known* portion of that
    window (where mask==0) against a random pool of candidate patches drawn
    from the unmasked ball interior. The best match (lowest SSD) donates
    its center pixel into the boundary pixel. Repeat until empty.

    Pure-numpy, no Cython. For a 1500x1500 ball with a typical photographer
    mask this runs in tens of seconds, which is acceptable for "Best" tier.
    """
    h, w, c = img_uint8.shape
    img = img_uint8.copy()
    mask = mask_uint8.copy()
    half = patch_size // 2

    # Donor pool = unmasked pixels strictly inside the ball, with a margin so
    # extracted patches don't reach outside the image or into the mask.
    cx, cy = ball_center
    yy, xx = np.ogrid[:h, :w]
    inside_ball = (xx - cx) ** 2 + (yy - cy) ** 2 <= max(1, ball_radius - half) ** 2
    donor_eligible = (mask == 0) & inside_ball
    donor_eligible[:half] = False
    donor_eligible[-half:] = False
    donor_eligible[:, :half] = False
    donor_eligible[:, -half:] = False
    donor_yx = np.argwhere(donor_eligible)
    if donor_yx.size == 0:
        # Nothing to copy from. Fall back to NS inpaint.
        out = np.empty_like(img)
        for ch in range(c):
            out[..., ch] = cv2.inpaint(img[..., ch], mask, 15, cv2.INPAINT_NS)
        return out

    rng = np.random.default_rng(42)
    max_iters = h * w  # safety bound; actual loop terminates when mask empties.

    for _ in range(max_iters):
        if not mask.any():
            break

        # Boundary = masked pixels touching at least one unmasked neighbor.
        kernel = np.ones((3, 3), np.uint8)
        unmasked = (mask == 0).astype(np.uint8)
        dilated_unmasked = cv2.dilate(unmasked, kernel)
        boundary = (mask > 0) & (dilated_unmasked > 0)

        # Restrict to pixels far enough from edges to extract full patches.
        boundary[:half] = False
        boundary[-half:] = False
        boundary[:, :half] = False
        boundary[:, -half:] = False

        boundary_yx = np.argwhere(boundary)
        if boundary_yx.size == 0:
            # Mask is non-empty but all remaining masked pixels are too close
            # to the image edge to fill via patch matching. Use NS to clean up.
            for ch in range(c):
                img[..., ch] = cv2.inpaint(img[..., ch], mask, 5, cv2.INPAINT_NS)
            mask[:] = 0
            break

        # Sample a random pool of donor centers for this iteration.
        n_donors = min(candidates_per_iter, donor_yx.shape[0])
        idx = rng.choice(donor_yx.shape[0], size=n_donors, replace=False)
        donors = donor_yx[idx]  # (n_donors, 2) in (y, x)

        donor_patches = _extract_patches(img, donors, half)  # (n_donors, P, P, C)

        # Process boundary pixels in chunks to bound memory.
        chunk = 1024
        for start in range(0, boundary_yx.shape[0], chunk):
            block = boundary_yx[start : start + chunk]
            target_patches = _extract_patches(img, block, half)  # (B, P, P, C)
            target_masks = _extract_patches_mask(mask, block, half)  # (B, P, P) uint8

            # SSD between each target and each donor over known pixels only.
            # target_patches: (B, P, P, C); donor_patches: (D, P, P, C)
            t = target_patches.astype(np.int32)[:, None]   # (B, 1, P, P, C)
            d = donor_patches.astype(np.int32)[None, :]    # (1, D, P, P, C)
            diff = t - d
            sq = (diff * diff).sum(axis=-1)                # (B, D, P, P)
            known = (target_masks == 0).astype(np.int32)[:, None]  # (B, 1, P, P)
            ssd = (sq * known).sum(axis=(2, 3))            # (B, D)
            denom = known.sum(axis=(2, 3))                 # (B, 1) — same per row
            denom = np.maximum(denom, 1)
            ssd = ssd / denom

            best = ssd.argmin(axis=1)                      # (B,)
            chosen_centers = donor_patches[best, half, half]  # (B, C)

            ys = block[:, 0]
            xs = block[:, 1]
            img[ys, xs] = chosen_centers.astype(np.uint8)
            mask[ys, xs] = 0

    return img


def _extract_patches(img: np.ndarray, centers: np.ndarray, half: int) -> np.ndarray:
    """Extract (N, P, P, C) patches centered at each (y, x) in `centers`."""
    p = 2 * half + 1
    n = centers.shape[0]
    out = np.empty((n, p, p, img.shape[2]), dtype=img.dtype)
    for i in range(n):
        y, x = int(centers[i, 0]), int(centers[i, 1])
        out[i] = img[y - half : y + half + 1, x - half : x + half + 1]
    return out


def _extract_patches_mask(mask: np.ndarray, centers: np.ndarray, half: int) -> np.ndarray:
    p = 2 * half + 1
    n = centers.shape[0]
    out = np.empty((n, p, p), dtype=mask.dtype)
    for i in range(n):
        y, x = int(centers[i, 0]), int(centers[i, 1])
        out[i] = mask[y - half : y + half + 1, x - half : x + half + 1]
    return out
