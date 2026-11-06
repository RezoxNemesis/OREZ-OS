#!/usr/bin/env python3
"""Reject blank virtual desktop frames after a Plasma process starts.

Read-only PPM classification is not full GUI or hardware certification.
"""
import pathlib
import sys


def inspect(path):
    with pathlib.Path(path).open("rb") as f:
        if f.readline().strip() != b"P6":
            return False, "unexpected PPM header"
        dims = f.readline().split()
        if len(dims) != 2:
            return False, "invalid PPM dimensions"
        width, height = map(int, dims)
        if not (640 <= width <= 4096 and 480 <= height <= 2160):
            return False, "unqualified frame resolution"
        if f.readline().strip() != b"255":
            return False, "unsupported PPM color depth"
        pixels = f.read()
    if len(pixels) != width * height * 3:
        return False, "incomplete framebuffer"

    total = 0
    lit = 0
    palette = set()
    for offset in range(0, len(pixels) - 2, 36):
        r, g, b = pixels[offset:offset+3]
        total += 1
        lit += max(r, g, b) > 18
        palette.add((r // 32, g // 32, b // 32))
    fraction = lit / max(total, 1)
    passed = fraction >= 0.03 and len(palette) >= 8
    return passed, f"lit_pixels={fraction:.2%} color_bins={len(palette)} ({width}x{height})"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: check-graphical-frame.py FRAME.ppm")
    try:
        passed, details = inspect(pathlib.Path(sys.argv[1]))
    except (OSError, ValueError) as exc:
        passed, details = False, str(exc)
    print(("PASS: visible desktop frame: " if passed else "BLOCKED: blank/unverified desktop: ") + details)
    raise SystemExit(0 if passed else 1)
