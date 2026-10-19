#!/usr/bin/env python3
"""Preprocess a profile photo (dp.png) into the luminance grid used by make_ascii_svg.py.

Usage:
  python scripts/prep_photo.py [input_image] [dist]

- input_image defaults to the GitHub avatar (auto-downloaded to dist/avatar.png)
- output: dist/ascii_grid.json  (ROWS x COLS luminance matrix, 0.0 black -> 1.0 white)
"""
import io
import json
import os
import sys
import urllib.request

from PIL import Image, ImageOps

COLS = 140          # 140 chars * 6px = 840px wide
ROWS = 88           # 88 lines * 10px = 880px tall


def load_image(src):
    if src.startswith("http://") or src.startswith("https://"):
        req = urllib.request.Request(src, headers={"User-Agent": "profile-art-script"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return Image.open(io.BytesIO(r.read())).convert("RGB")
    return Image.open(src).convert("RGB")


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/Pushyanth02.png"
    outdir = sys.argv[2] if len(sys.argv) > 2 else "dist"
    os.makedirs(outdir, exist_ok=True)

    img = load_image(src)

    # letterbox the (usually square) source into the 840x880 card instead of
    # cropping, padding with the image's own corner colour so it blends in
    scale = ROWS * 4
    img = img.resize((scale, scale), Image.LANCZOS)
    corner = img.getpixel((2, 2))
    canvas = Image.new("RGB", (COLS * 4, ROWS * 4), corner)
    canvas.paste(img, ((COLS * 4 - scale) // 2, 0))

    g = ImageOps.autocontrast(canvas.convert("L"), cutoff=1)
    g = g.resize((COLS, ROWS), Image.LANCZOS)
    g = ImageOps.autocontrast(g, cutoff=1)

    px = g.load()
    grid = [[round(px[x, y] / 255.0, 4) for x in range(COLS)] for y in range(ROWS)]

    out = os.path.join(outdir, "ascii_grid.json")
    with open(out, "w") as f:
        json.dump({"cols": COLS, "rows": ROWS, "lum": grid}, f)
    print(f"wrote {out}  ({COLS}x{ROWS} grid from {src})")


if __name__ == "__main__":
    main()
