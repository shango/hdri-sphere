"""32-bit EXR read/write and chrome-ball plate validation."""

from __future__ import annotations

import os
from typing import Tuple

import numpy as np

try:
    import OpenEXR
    import Imath  # noqa: F401  # required by OpenEXR for PixelType
    _HAS_OPENEXR = True
except ImportError:  # pragma: no cover - exercised only on machines without OpenEXR
    _HAS_OPENEXR = False

try:
    import imageio.v3 as iio
    _HAS_IMAGEIO = True
except ImportError:  # pragma: no cover
    _HAS_IMAGEIO = False


_RGB_CHANNELS = ("R", "G", "B")


def load_exr(path: str) -> np.ndarray:
    """Load 32-bit EXR file as float32 RGB.

    Returns:
        np.ndarray of shape (H, W, 3), dtype float32, linear scene-referred.

    Raises:
        ValueError: file is not a valid EXR, not float, or not 3-channel.
        FileNotFoundError: path does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    if _HAS_OPENEXR:
        return _load_with_openexr(path)
    if _HAS_IMAGEIO:
        return _load_with_imageio(path)
    raise RuntimeError("Neither OpenEXR nor imageio is installed; cannot read EXR.")


def save_exr(path: str, image: np.ndarray) -> None:
    """Save float32 RGB array as 32-bit ZIP-compressed EXR.

    Args:
        image: float32 array of shape (H, W, 3), linear scene-referred.
    """
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"Expected (H, W, 3) array, got shape {image.shape}")

    image = np.ascontiguousarray(image.astype(np.float32, copy=False))

    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)

    if _HAS_OPENEXR:
        _save_with_openexr(path, image)
        return
    if _HAS_IMAGEIO:
        iio.imwrite(path, image)
        return
    raise RuntimeError("Neither OpenEXR nor imageio is installed; cannot write EXR.")


def validate_chrome_ball_plate(image: np.ndarray) -> Tuple[bool, str]:
    """Sanity check that the input looks like a chrome ball plate.

    Returns:
        (is_valid, message). message is empty when valid.
    """
    if image.ndim != 3 or image.shape[2] != 3:
        return False, f"Expected 3-channel RGB image, got shape {image.shape}"

    h, w, _ = image.shape
    if h < 1024 or w < 1024:
        return False, f"Image too small ({w}x{h}); need at least 1024x1024"

    if not np.isfinite(image).all():
        return False, "Image contains NaN or Inf values"

    max_v = float(image.max())
    min_v = float(image.min())
    mean_v = float(image.mean())

    if max_v <= 0.0:
        return False, "Image is entirely black"
    if mean_v <= 1e-6:
        return False, "Image is nearly entirely black"
    if min_v >= max_v - 1e-6:
        return False, "Image has no dynamic range (constant values)"

    if max_v <= 1.0:
        return (
            False,
            "Image max value <= 1.0; this does not look like a true HDR plate "
            "(expected values exceeding 1.0 from chrome ball highlights).",
        )

    return True, ""


# ---------------------------------------------------------------------------
# OpenEXR backend
# ---------------------------------------------------------------------------


def _load_with_openexr(path: str) -> np.ndarray:
    exr = OpenEXR.InputFile(path)
    try:
        header = exr.header()
        channels = header["channels"]
        for ch in _RGB_CHANNELS:
            if ch not in channels:
                raise ValueError(f"EXR missing channel '{ch}': {path}")

        dw = header["dataWindow"]
        width = dw.max.x - dw.min.x + 1
        height = dw.max.y - dw.min.y + 1

        pixel_type = channels["R"].type
        # PixelType: UINT=0, HALF=1, FLOAT=2
        if pixel_type.v == Imath.PixelType.HALF:
            np_dtype = np.float16
            pt = Imath.PixelType(Imath.PixelType.HALF)
        elif pixel_type.v == Imath.PixelType.FLOAT:
            np_dtype = np.float32
            pt = Imath.PixelType(Imath.PixelType.FLOAT)
        else:
            raise ValueError(f"Unsupported EXR pixel type: {pixel_type.v}")

        raw = exr.channels(_RGB_CHANNELS, pt)
        planes = [
            np.frombuffer(buf, dtype=np_dtype).reshape((height, width)) for buf in raw
        ]
        rgb = np.stack(planes, axis=-1).astype(np.float32, copy=False)
        return rgb
    finally:
        exr.close()


def _save_with_openexr(path: str, image: np.ndarray) -> None:
    height, width, _ = image.shape
    pt = Imath.PixelType(Imath.PixelType.FLOAT)
    header = OpenEXR.Header(width, height)
    header["channels"] = {ch: Imath.Channel(pt) for ch in _RGB_CHANNELS}
    header["compression"] = Imath.Compression(Imath.Compression.ZIP_COMPRESSION)

    out = OpenEXR.OutputFile(path, header)
    try:
        r = image[..., 0].tobytes()
        g = image[..., 1].tobytes()
        b = image[..., 2].tobytes()
        out.writePixels({"R": r, "G": g, "B": b})
    finally:
        out.close()


# ---------------------------------------------------------------------------
# imageio fallback
# ---------------------------------------------------------------------------


def _load_with_imageio(path: str) -> np.ndarray:
    arr = iio.imread(path)
    if arr.ndim == 2:
        arr = np.stack([arr, arr, arr], axis=-1)
    if arr.shape[-1] > 3:
        arr = arr[..., :3]
    if arr.shape[-1] != 3:
        raise ValueError(f"Expected 3+ channel EXR, got shape {arr.shape}")
    return arr.astype(np.float32, copy=False)
