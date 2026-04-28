"""Command-line entrypoint for the chrome-ball -> equirect HDRI pipeline.

Usage:
    python -m scripts.cli process INPUT.exr OUTPUT.exr \
        [--technique fast] [--width 4096] [--height 2048] \
        [--no-mask] [--ball cx,cy,r]
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ball_detect import BallDetectionError, detect_ball  # noqa: E402
from core.exr_io import load_exr, save_exr, validate_chrome_ball_plate  # noqa: E402
from core.inpaint import get_inpainter  # noqa: E402
from core.mask_estimate import estimate_photographer_mask  # noqa: E402
from core.unwrap import ball_to_equirect  # noqa: E402


def _parse_ball(spec: str) -> tuple[int, int, int]:
    parts = spec.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("--ball expects 'cx,cy,r'")
    cx, cy, r = (int(p.strip()) for p in parts)
    return cx, cy, r


def cmd_process(args: argparse.Namespace) -> int:
    t0 = time.perf_counter()

    print(f"Loading {args.input}")
    image = load_exr(args.input)
    valid, message = validate_chrome_ball_plate(image)
    if not valid:
        print(f"WARNING: {message}", file=sys.stderr)

    if args.ball is not None:
        cx, cy, r = args.ball
        print(f"Using manual ball: center=({cx}, {cy}) r={r}")
    else:
        try:
            cx, cy, r = detect_ball(image)
        except BallDetectionError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(f"Detected ball: center=({cx}, {cy}) r={r}")

    inpainter = get_inpainter(args.technique)

    if args.no_mask:
        print("Skipping mask + inpaint (--no-mask)")
        ball_for_unwrap = image
    else:
        print("Estimating photographer mask")
        mask = estimate_photographer_mask(image, (cx, cy), r)
        coverage = float((mask > 0).sum()) / mask.size * 100.0
        print(f"Mask coverage: {coverage:.2f}% of frame")

        print(f"Inpainting with technique='{args.technique}'")
        ball_for_unwrap = inpainter.inpaint(image, mask, (cx, cy), r)

    print(f"Unwrapping to equirect {args.width}x{args.height}")
    equirect = ball_to_equirect(
        ball_for_unwrap, (cx, cy), r, output_width=args.width, output_height=args.height
    )

    if not np.isfinite(equirect).all():
        print("ERROR: equirect contains non-finite values", file=sys.stderr)
        return 3

    print(f"Saving {args.output}")
    save_exr(args.output, equirect)

    print(f"Done in {time.perf_counter() - t0:.2f}s")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cli", description="HDRI tool CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_proc = sub.add_parser("process", help="Convert chrome ball EXR to equirect EXR")
    p_proc.add_argument("input", help="Input chrome ball EXR")
    p_proc.add_argument("output", help="Output equirect EXR")
    p_proc.add_argument(
        "--technique",
        default="good",
        choices=["fast", "good", "best"],
        help="Inpaint technique: fast (boundary NS), good (freq-aware), best (PatchMatch)",
    )
    p_proc.add_argument("--width", type=int, default=4096)
    p_proc.add_argument("--height", type=int, default=2048)
    p_proc.add_argument(
        "--no-mask",
        action="store_true",
        help="Skip mask estimation + inpaint; unwrap raw plate.",
    )
    p_proc.add_argument(
        "--ball",
        type=_parse_ball,
        default=None,
        help="Override ball detection. Format: cx,cy,r",
    )
    p_proc.set_defaults(func=cmd_process)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
