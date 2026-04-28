"""Inpainter registry. All three tiers are available."""

from __future__ import annotations

from .base import Inpainter
from .boundary import BoundaryInpainter
from .frequency import FrequencyAwareInpainter
from .patchmatch import PatchMatchInpainter

INPAINTERS: dict[str, Inpainter] = {
    "fast": BoundaryInpainter(),
    "good": FrequencyAwareInpainter(),
    "best": PatchMatchInpainter(),
}


def get_inpainter(name: str) -> Inpainter:
    if name not in INPAINTERS:
        available = ", ".join(sorted(INPAINTERS))
        raise ValueError(f"Unknown inpainter '{name}'. Available: {available}")
    return INPAINTERS[name]


__all__ = [
    "Inpainter",
    "BoundaryInpainter",
    "FrequencyAwareInpainter",
    "PatchMatchInpainter",
    "INPAINTERS",
    "get_inpainter",
]
