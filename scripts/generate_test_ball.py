"""Synthesize a fake chrome ball EXR reflecting a known environment.

The synthetic environment is a colored gradient: longitude maps to hue
(R-G-B around the equator) and latitude maps to brightness (a hot-spot at
the zenith and a dark band at the nadir). This gives every region of the
ball a unique color so unwrap orientation can be verified visually.

Usage:
    python -m scripts.generate_test_ball OUTPUT.exr [--size 2048] [--photog]

The optional --photog flag adds a dark photographer-shaped blob in front
of the ball so mask estimation has something to detect.
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

# Ensure project root on path when running from scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.exr_io import save_exr  # noqa: E402


def synthesize_ball(size: int = 2048, add_photog: bool = False) -> np.ndarray:
    """Render a synthetic chrome ball reflecting a colored gradient."""
    h = w = size
    cy = cx = size // 2
    r = int(size * 0.45)

    yy, xx = np.mgrid[:h, :w].astype(np.float32)
    nx = (xx - cx) / r
    ny = -(yy - cy) / r  # image y is flipped relative to math y
    nz_sq = 1.0 - nx * nx - ny * ny
    inside = nz_sq > 0.0
    nz = np.where(inside, np.sqrt(np.maximum(nz_sq, 0.0)), 0.0)

    # Reflect view direction (-Z) about the surface normal:
    # R = V - 2*(V . N)*N, V = (0,0,-1), so R = (0,0,-1) + 2*Nz*N.
    # That gives the outgoing direction for each surface point.
    dot = nz  # V . N = -(-Nz) for V=(0,0,-1) -> V.N = -Nz; |V.N| = Nz
    rx = 2.0 * dot * nx
    ry = 2.0 * dot * ny
    rz = -1.0 + 2.0 * dot * nz

    # Convert reflection direction to (longitude, latitude) and color.
    phi = np.arctan2(rx, rz)            # [-pi, pi]
    theta = np.arcsin(np.clip(ry, -1.0, 1.0))  # [-pi/2, pi/2]

    hue = (phi / (2.0 * np.pi)) + 0.5    # [0, 1]
    brightness = 0.5 + 0.5 * np.sin(theta)  # 0 (nadir) -> 1 (zenith)
    # HDR boost for the upper hemisphere.
    boost = np.where(theta > 0.0, 1.0 + 8.0 * np.sin(theta) ** 2, 1.0)

    rgb = _hue_to_rgb(hue) * brightness[..., None] * boost[..., None]
    rgb[~inside] = 0.0  # background

    if add_photog:
        # Dark blob slightly below center, simulating photographer/tripod.
        bx = cx
        by = cy + int(0.2 * r)
        sx = 0.30 * r
        sy = 0.45 * r
        dx = (xx - bx) / sx
        dy = (yy - by) / sy
        blob = np.exp(-0.5 * (dx * dx + dy * dy))
        # Multiplicative darkening, only inside the ball.
        darkening = 1.0 - 0.85 * blob
        darkening = np.where(inside, darkening, 1.0)
        rgb = rgb * darkening[..., None]

    return rgb.astype(np.float32, copy=False)


def _hue_to_rgb(hue: np.ndarray) -> np.ndarray:
    """Cheap hue -> RGB (saturation 1, value 1). hue in [0, 1]."""
    h6 = (hue % 1.0) * 6.0
    f = h6 - np.floor(h6)
    p = np.zeros_like(h6)
    q = 1.0 - f
    t = f
    one = np.ones_like(h6)

    sector = np.floor(h6).astype(np.int32) % 6
    r = np.choose(sector, [one, q, p, p, t, one])
    g = np.choose(sector, [t, one, one, q, p, p])
    b = np.choose(sector, [p, p, t, one, one, q])
    return np.stack([r, g, b], axis=-1).astype(np.float32)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synthesize a chrome ball test EXR.")
    parser.add_argument("output", help="Output EXR path")
    parser.add_argument("--size", type=int, default=2048, help="Square image size")
    parser.add_argument(
        "--photog", action="store_true", help="Add synthetic photographer/tripod blob"
    )
    args = parser.parse_args(argv)

    img = synthesize_ball(size=args.size, add_photog=args.photog)
    save_exr(args.output, img)
    print(f"Wrote {args.output} ({img.shape[1]}x{img.shape[0]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
