#!/usr/bin/env python3
"""Identify the pinned Kubuntu Try/Install frame in an isolated QEMU guest.

This is a conservative layout check, not a general application identifier. No
host interaction or installation is performed. Refuse a click if the frame
does not match the observed welcome screen at exactly 1280x800.
"""
import pathlib
import sys


def check(path: pathlib.Path):
    with path.open("rb") as f:
        if f.readline().strip() != b"P6":
            return False, "not a binary PPM image"
        dims = f.readline().strip().split()
        if len(dims) != 2:
            return False, "invalid PPM size line"
        width, height = map(int, dims)
        if (width, height) != (1280, 800):
            return False, "unknown framebuffer size"
        if f.readline().strip() != b"255":
            return False, "unsupported PPM color depth"
        data = f.read()
    if len(data) != width * height * 3:
        return False, "incomplete PPM framebuffer"

    def pixel(x, y):
        offset = 3 * (y * width + x)
        return data[offset:offset + 3]

    # Color samples are away from letters and edges; both blue buttons plus
    # dark backdrop must be present before selecting the LEFT (Try) button.
    expected = (
        (350, 638, (20, 45, 81)),
        (900, 639, (20, 45, 81)),
        (640, 740, (0, 24, 61)),
        (350, 585, (0, 24, 64)),
    )
    for x, y, rgb in expected:
        if any(abs(a - b) > 22 for a, b in zip(pixel(x, y), rgb)):
            return False, f"unexpected framebuffer at {x},{y}"
    return True, "pinned Try/Install layout visible"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: check-try-frame.py FRAME.ppm")
    try:
        ok, message = check(pathlib.Path(sys.argv[1]))
    except (ValueError, OSError) as error:
        ok, message = False, str(error)
    print(("PASS: " if ok else "WAIT: ") + message)
    raise SystemExit(0 if ok else 1)
