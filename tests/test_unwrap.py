import numpy as np

from core.unwrap import ball_to_equirect
from scripts.generate_test_ball import synthesize_ball


def test_equirect_shape_and_finite():
    size = 1024
    img = synthesize_ball(size=size, add_photog=False)
    cx, cy = size // 2, size // 2
    r = int(size * 0.45)

    eq = ball_to_equirect(img, (cx, cy), r, output_width=512, output_height=256)
    assert eq.shape == (256, 512, 3)
    assert eq.dtype == np.float32
    assert np.isfinite(eq).all()


def test_zenith_is_brighter_than_nadir():
    """The synthetic environment puts a bright HDR boost in the upper hemisphere.

    After unwrap, the top row of the equirect should be brighter than the bottom row.
    """
    size = 1024
    img = synthesize_ball(size=size, add_photog=False)
    cx, cy = size // 2, size // 2
    r = int(size * 0.45)

    eq = ball_to_equirect(img, (cx, cy), r, output_width=512, output_height=256)

    top_strip = eq[:20].mean()
    bottom_strip = eq[-20:].mean()
    assert top_strip > bottom_strip
