#!/usr/bin/env python3
"""Render the ASCII portrait SVG (840x880) from the preprocessed luminance grid.

Usage: python scripts/make_ascii_svg.py [dist/ascii_grid.json] [dist/avi-ascii.svg]

Animation: rows materialize top -> bottom (staggered fade-in), then the whole
portrait breathes with a very subtle glow pulse.
"""
import json
import os
import sys

# dark pixels -> dense glyphs, bright pixels -> sparse glyphs
RAMP = "@%#*+=-:. "

W, H = 840, 880
CELL_W, CELL_H = 6, 10


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "dist/ascii_grid.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "dist/avi-ascii.svg"
    grid = json.load(open(src))
    cols, rows, lum = grid["cols"], grid["rows"], grid["lum"]

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}" role="img" aria-label="ASCII portrait">')
    s.append("<defs>")
    s.append('  <linearGradient id="pg" x1="0" y1="0" x2="1" y2="1">')
    s.append('    <stop offset="0" stop-color="#A7F3D0"/>')
    s.append('    <stop offset=".55" stop-color="#C7D2FE"/>')
    s.append('    <stop offset="1" stop-color="#FBCFE8"/>')
    s.append("  </linearGradient>")
    s.append("</defs>")
    s.append("<style>")
    s.append("  text{font:10px ui-monospace,'SF Mono','Cascadia Code',Consolas,monospace;white-space:pre}")
    s.append("  .r{opacity:0;animation:rv .4s ease forwards}")
    s.append("  @keyframes rv{to{opacity:1}}")
    s.append("  .all{animation:breathe 5s ease-in-out 4.2s infinite alternate}")
    s.append("  @keyframes breathe{from{opacity:1}to{opacity:.86}}")
    s.append("</style>")
    s.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="16" fill="#0D1117" '
             f'stroke="#A7F3D01F"/>')
    s.append('<g class="all" fill="url(#pg)">')
    for y in range(rows):
        line = "".join(RAMP[min(int(lum[y][x] * len(RAMP)), len(RAMP) - 1)]
                       for x in range(cols))
        line = line.rstrip()
        delay = round(y * 38, 1)
        s.append(f'<text class="r" x="2" y="{y * CELL_H + 10}" '
                 f'style="animation-delay:{delay}ms">{esc(line)}</text>')
    s.append("</g>")
    s.append("</svg>")

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as f:
        f.write("\n".join(s))
    print(f"wrote {out}  ({rows} rows x {cols} cols)")


if __name__ == "__main__":
    main()
