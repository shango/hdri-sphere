import numpy as np

from core.hdr_utils import (
    from_log_space,
    hdr_safe_composite,
    luminance,
    to_log_space,
    tonemap_for_preview,
)


def _hdr(h=64, w=64):
    rng = np.random.default_rng(1)
    base = rng.random((h, w, 3), dtype=np.float32) * 5.0
    base[10:20, 10:20] += 100.0
    return base.astype(np.float32)


def test_log_roundtrip_preserves_relative_values():
    img = _hdr()
    u8, params = to_log_space(img)
    assert u8.dtype == np.uint8
    back = from_log_space(u8, params)
    # Lossy due to uint8 quantization, but ranks should be preserved.
    a = img.flatten()
    b = back.flatten()
    # Pearson correlation high, max relative error bounded.
    corr = float(np.corrcoef(a, b)[0, 1])
    assert corr > 0.99


def test_tonemap_clamps_to_uint8():
    img = _hdr()
    u8 = tonemap_for_preview(img)
    assert u8.dtype == np.uint8
    assert u8.min() >= 0 and u8.max() <= 255


def test_composite_preserves_outside_mask_exactly():
    h, w = 64, 64
    rng = np.random.default_rng(2)
    orig = rng.random((h, w, 3), dtype=np.float32) * 10.0
    inpainted = rng.random((h, w, 3), dtype=np.float32) * 10.0
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[20:30, 20:30] = 255

    out = hdr_safe_composite(orig, inpainted, mask, feather_radius=0)
    # Outside the mask, output equals original exactly.
    np.testing.assert_array_equal(out[0:5, 0:5], orig[0:5, 0:5])


def test_luminance_shape():
    img = _hdr()
    lum = luminance(img)
    assert lum.shape == img.shape[:2]
    assert lum.dtype == np.float32
