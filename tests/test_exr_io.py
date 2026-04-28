import numpy as np
import pytest

from core.exr_io import load_exr, save_exr, validate_chrome_ball_plate


def _make_hdr(h=1200, w=1200):
    rng = np.random.default_rng(0)
    base = rng.random((h, w, 3), dtype=np.float32) * 0.5
    base[300:400, 300:400] += 50.0  # HDR highlight
    return base.astype(np.float32)


def test_save_load_roundtrip(tmp_path):
    img = _make_hdr()
    path = tmp_path / "rt.exr"
    save_exr(str(path), img)
    loaded = load_exr(str(path))
    assert loaded.shape == img.shape
    assert loaded.dtype == np.float32
    np.testing.assert_allclose(loaded, img, rtol=1e-5, atol=1e-6)


def test_validate_accepts_hdr_plate():
    img = _make_hdr()
    valid, msg = validate_chrome_ball_plate(img)
    assert valid, msg


def test_validate_rejects_small():
    img = np.ones((512, 512, 3), dtype=np.float32) * 2.0
    valid, msg = validate_chrome_ball_plate(img)
    assert not valid
    assert "too small" in msg.lower()


def test_validate_rejects_ldr():
    img = np.ones((1200, 1200, 3), dtype=np.float32) * 0.5
    valid, msg = validate_chrome_ball_plate(img)
    assert not valid


def test_validate_rejects_black():
    img = np.zeros((1200, 1200, 3), dtype=np.float32)
    valid, msg = validate_chrome_ball_plate(img)
    assert not valid


def test_load_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_exr(str(tmp_path / "nope.exr"))
