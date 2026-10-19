#!/usr/bin/env python3
"""Render the animated contribution heatmap (light + dark) from fetched user data.

Usage: python scripts/render_heatmap.py [dist/user-data.json] [dist]

Produces:
  dist/contrib-heatmap.svg        (light theme)
  dist/contrib-heatmap-dark.svg   (dark theme)

Animation: contribution boxes reveal cell by cell (left -> right, top -> bottom),
then the most recent active cell keeps pulsing.
"""
import json
import os
import sys
from datetime import date, datetime

W, H = 840, 170
X0, Y0 = 38, 46          # grid origin (left labels + top month labels above)
CELL, GAP = 12, 3        # 15px pitch -> 53 weeks = 795px wide grid
PITCH = CELL + GAP

THEMES = {
    "contrib-heatmap-dark.svg": {
        "bg": "#0D1117", "border": "#A7F3D01F", "text": "#E6EDF3", "dim": "#8B949E",
        "empty": "#161B22", "levels": ["#161B22", "#0E4429", "#006D32", "#26A641", "#39D353"],
        "accent": "#39D353",
    },
    "contrib-heatmap.svg": {
        "bg": "#FFFFFF", "border": "#1F232814", "text": "#1F2328", "dim": "#656D76",
        "empty": "#EBEDF0", "levels": ["#EBEDF0", "#9BE9A8", "#40C463", "#30A14E", "#216E39"],
        "accent": "#1A7F37",
    },
}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DOW = {1: "Mon", 3: "Wed", 5: "Fri"}


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build_days(weeks):
    days = []
    for w in weeks:
        for d in w["contributionDays"]:
            days.append({
                "date": d["date"][:10],
                "count": d["contributionCount"],
            })
    return days


def level_for(count, thresholds):
    if count <= 0:
        return 0
    for i, t in enumerate(thresholds):
        if count <= t:
            return i + 1
    return 4


def render(theme, days, total, path):
    nonzero = sorted(d["count"] for d in days if d["count"] > 0)
    if nonzero:
        thresholds = [
            nonzero[len(nonzero) // 4],
            nonzero[len(nonzero) // 2],
            nonzero[(len(nonzero) * 3) // 4],
        ]
    else:
        thresholds = [1, 2, 3]

    # pad the front so the grid always starts on a Sunday (GitHub layout)
    first = datetime.strptime(days[0]["date"], "%Y-%m-%d").date()
    lead = (first.weekday() + 1) % 7  # Sunday == 6 on Python's Mon=0 .. Sun=6
    cells = [None] * lead + days
    while len(cells) % 7 != 0:
        cells.append(None)

    n_weeks = len(cells) // 7
    grid_w = n_weeks * PITCH

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}" role="img" aria-label="{esc(str(total))} contributions in the last year">')
    s.append("<style>")
    s.append("  text{font:11px ui-monospace,'SF Mono','Cascadia Code',Consolas,monospace}")
    s.append(f"  .t{{fill:{theme['text']};font-weight:700;font-size:13px}}")
    s.append(f"  .d{{fill:{theme['dim']}}}")
    s.append("  .c{opacity:0;animation:rv .45s ease forwards}")
    s.append("  @keyframes rv{to{opacity:1}}")
    s.append(f"  .pulse{{animation:rv .45s ease forwards, pl 2.2s ease-in-out 6s infinite}}"
             f"  @keyframes pl{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}")
    s.append("</style>")
    s.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="12" fill="{theme["bg"]}" '
             f'stroke="{theme["border"]}"/>')
    s.append(f'<text class="t" x="26" y="24">{total:,} contributions in the last year</text>')

    # legend (top right)
    lx = W - 26 - (5 * PITCH + 46)
    s.append(f'<text class="d" x="{lx}" y="24">Less</text>')
    for i in range(5):
        s.append(f'<rect x="{lx + 30 + i * PITCH}" y="14" width="{CELL}" height="{CELL}" '
                 f'rx="2.5" fill="{theme["levels"][i]}"/>')
    s.append(f'<text class="d" x="{lx + 30 + 5 * PITCH + 2}" y="24">More</text>')

    # month labels
    prev = None
    for wi in range(n_weeks):
        d0 = cells[wi * 7]
        if d0 is None:
            continue
        m = int(d0["date"][5:7]) - 1
        if m != prev:
            if prev is None or wi >= 3:
                x = X0 + wi * PITCH
                s.append(f'<text class="d" x="{x}" y="36">{MONTHS[m]}</text>')
            prev = m

    # weekday labels
    for r in range(7):
        if r in DOW:
            s.append(f'<text class="d" x="{X0 - 8}" y="{Y0 + r * PITCH + CELL - 2}" '
                     f'text-anchor="end">{DOW[r]}</text>')

    # cells, revealed one by one
    last_active = -1
    idx = 0
    for wi in range(n_weeks):
        for r in range(7):
            c = cells[wi * 7 + r]
            x = X0 + wi * PITCH
            y = Y0 + r * PITCH
            if c is None:
                continue
            lv = level_for(c["count"], thresholds)
            delay = round(idx * 13, 1)
            cls = "c"
            if c["count"] > 0:
                last_active = idx
            s.append(f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                     f'rx="2.5" fill="{theme["levels"][lv]}" style="animation-delay:{delay}ms">'
                     f'<title>{c["date"]}: {c["count"]} contribution(s)</title></rect>')
            idx += 1

    # re-render the most recent active cell with the pulse class
    if last_active >= 0:
        wi, r = divmod(last_active, 7)
        c = cells[last_active]
        x, y = X0 + wi * PITCH, Y0 + r * PITCH
        lv = level_for(c["count"], thresholds)
        s.append(f'<rect class="pulse" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                 f'rx="2.5" fill="{theme["levels"][lv]}" style="animation-delay:{last_active * 13}ms, 6s">'
                 f'<title>{c["date"]}: {c["count"]} contribution(s)</title></rect>')

    s.append("</svg>")
    with open(path, "w") as f:
        f.write("\n".join(s))
    print(f"wrote {path}  ({n_weeks} weeks, {total} contributions, grid {grid_w}px)")


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "dist/user-data.json"
    outdir = sys.argv[2] if len(sys.argv) > 2 else "dist"
    data = json.load(open(src))
    days = build_days(data["weeks"])
    total = data.get("totalContributions") or sum(d["count"] for d in days)
    os.makedirs(outdir, exist_ok=True)
    for name, theme in THEMES.items():
        render(theme, days, total, os.path.join(outdir, name))


if __name__ == "__main__":
    main()
