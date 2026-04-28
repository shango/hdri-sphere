import numpy as np

from core.mask_estimate import estimate_photographer_mask
from scripts.generate_test_ball import synthesize_ball


def test_mask_is_inside_ball_and_nonempty():
    size = 1200
    img = synthesize_ball(size=size, add_photog=True)
    cx, cy = size // 2, size // 2
    r = int(size * 0.45)

    mask = estimate_photographer_mask(img, (cx, cy), r)
    assert mask.shape == img.shape[:2]
    assert mask.dtype == np.uint8
    assert mask.max() == 255
    assert mask.min() == 0
    assert (mask > 0).any(), "mask should be non-empty for a synthetic photog blob"

    # No mask pixels outside the ball circle.
    yy, xx = np.ogrid[:size, :size]
    inside = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
    outside_mask_pixels = (mask > 0) & ~inside
    assert not outside_mask_pixels.any()
