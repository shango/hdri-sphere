import math

from core.ball_detect import detect_ball
from scripts.generate_test_ball import synthesize_ball


def test_detects_synthetic_ball_center_and_radius():
    size = 1200
    img = synthesize_ball(size=size, add_photog=False)
    cx, cy, r = detect_ball(img)

    expected_cx = size // 2
    expected_cy = size // 2
    expected_r = int(size * 0.45)

    # Within 5% of image size for center, 10% for radius.
    assert abs(cx - expected_cx) < 0.05 * size
    assert abs(cy - expected_cy) < 0.05 * size
    assert math.isclose(r, expected_r, rel_tol=0.10)
