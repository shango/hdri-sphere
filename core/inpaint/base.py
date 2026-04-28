"""Inpainter Protocol that all tiers must satisfy."""

from __future__ import annotations

from typing import Protocol, Tuple

import numpy as np


class Inpainter(Protocol):
    """Common interface for every inpaint tier.

    Implementations must preserve the input's HDR values exactly outside the
    mask. Operate in log-space internally so single bright pixels do not
    dominate averaging operations.
    """

    name: str
    description: str
    estimated_seconds: float

    def inpaint(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        ball_center: Tuple[int, int],
        ball_radius: int,
    ) -> np.ndarray:
        ...
