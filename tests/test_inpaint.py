import numpy as np
import pytest

from core.inpaint import INPAINTERS, get_inpainter
from scripts.generate_test_ball import synthesize_ball


def _setup(size=512):
    img = synthesize_ball(size=size, add_photog=True)
    cx, cy = size // 2, size // 2
    r = int(size * 0.45)
    mask = np.zeros((size, size), dtype=np.uint8)
    mask[cy : cy + 40, cx - 20 : cx + 20] = 255
    return img, mask, (cx, cy), r


@pytest.mark.parametrize("technique", ["fast", "good", "best"])
def test_inpainter_preserves_outside_mask(technique):
    img, mask, center, r = _setup(size=512)
    out = get_inpainter(technique).inpaint(img, mask, center, r)

    assert out.dtype == np.float32
    assert out.shape == img.shape
    assert np.isfinite(out).all()

    # Far from the mask + feather, output should match the input.
    cx, cy = center
    far = np.zeros(img.shape[:2], dtype=bool)
    far[: cy - 60, :] = True
    np.testing.assert_allclose(out[far], img[far], rtol=1e-3, atol=1e-3)


def test_registry_lists_all_three():
    assert set(INPAINTERS) == {"fast", "good", "best"}


def test_get_inpainter_unknown_raises():
    with pytest.raises(ValueError):
        get_inpainter("nope")


def test_inpainter_changes_pixels_inside_mask():
    """Inpaint should at least try to fill — masked pixels should differ from
    the original photographer-darkened values for the 'good' tier."""
    img, mask, center, r = _setup(size=512)
    out = get_inpainter("good").inpaint(img, mask, center, r)

    masked_orig = img[mask > 0]
    masked_out = out[mask > 0]
    diff = np.abs(masked_orig - masked_out).mean()
    assert diff > 1e-3, "Inpaint produced no change inside the mask region"
