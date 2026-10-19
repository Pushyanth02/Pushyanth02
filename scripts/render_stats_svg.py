#!/usr/bin/env python3
"""Render the animated streak/numbers card SVG (840x880) from fetched user data.

Usage: python scripts/render_stats_svg.py [dist/user-data.json] [dist/stats.svg]

Animation: sections slide/fade in top -> bottom, activity bars grow from the
baseline, and a terminal cursor keeps blinking.
"""
import json
import os
import sys
from datetime import datetime

W, H = 840, 880

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def pretty_date(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{MONTHS[d.month - 1]} {d.day}"


def compute(days):
    counts = [d["contributionCount"] for d in days]
    total = sum(counts)
    active = sum(1 for c in counts if c > 0)

    best_i = max(range(len(counts)), key=lambda i: counts[i]) if counts else 0
    best = (counts[best_i], days[best_i]["date"]) if counts and counts[best_i] > 0 else (0, None)

    longest = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)

    current = 0
    idx = len(counts) - 1
    if counts and counts[idx] == 0:
        idx -= 1  # today may not have happened yet; streak survives until midnight
    while idx >= 0 and counts[idx] > 0:
        current += 1
        idx -= 1

    return {"total": total, "active": active, "best": best,
            "longest": longest, "current": current}


def row(x, y, label, value, sub="", idx=0, big=False):
    delay = round(150 + idx * 170, 1)
    size, fill = ("58px", "#A7F3D0") if big else ("40px", "#C7D2FE")
    out = [
        f'<g class="sec" style="animation-delay:{delay}ms">',
        f'  <text class="lab" x="{x}" y="{y}">{esc(label)}</text>',
        f'  <text class="val" x="{x}" y="{y + 56}" font-size="{size}" fill="{fill}">{esc(value)}</text>',
    ]
    if sub:
        out.append(f'  <text class="sub" x="{x}" y="{y + 84}">{esc(sub)}</text>')
    out.append("</g>")
    return "\n".join(out)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "dist/user-data.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "dist/stats.svg"
    data = json.load(open(src))

    days = [d for w in data["weeks"] for d in w["contributionDays"]]
    days = days[-365:]
    st = compute(days)

    last60 = days[-60:]
    maxc = max((d["contributionCount"] for d in last60), default=1) or 1

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}" role="img" '
             f'aria-label="GitHub streak and contribution stats for {esc(data["name"])}">')
    s.append("<style>")
    s.append("  text{font:15px ui-monospace,'SF Mono','Cascadia Code',Consolas,monospace}")
    s.append("  .title{fill:#8B949E;font-size:14px}")
    s.append("  .lab{fill:#8B949E;font-size:12px;letter-spacing:2.5px;font-weight:700}")
    s.append("  .val{font-weight:700}")
    s.append("  .sub{fill:#8B949E;font-size:13px}")
    s.append("  .sec{opacity:0;animation:sec .6s cubic-bezier(.2,.7,.3,1) forwards}")
    s.append("  @keyframes sec{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}")
    s.append("  .bar{transform:scaleY(0);transform-box:fill-box;transform-origin:bottom;"
             "animation:grow .7s cubic-bezier(.2,.7,.3,1) forwards}")
    s.append("  @keyframes grow{to{transform:scaleY(1)}}")
    s.append("  .cursor{animation:blink 1.1s steps(1) infinite}")
    s.append("  @keyframes blink{50%{opacity:0}}")
    s.append("</style>")

    s.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="16" fill="#0D1117" '
             f'stroke="#A7F3D01F"/>')

    # terminal chrome
    s.append('<circle cx="34" cy="30" r="7" fill="#FF5F57"/>'
             '<circle cx="58" cy="30" r="7" fill="#FEBC2E"/>'
             '<circle cx="82" cy="30" r="7" fill="#28C840"/>')
    s.append(f'<text class="title" x="108" y="36">{esc(data["login"].lower())}@github: ~/stats</text>')
    s.append('<line x1="0" y1="56" x2="840" y2="56" stroke="#FFFFFF12"/>')

    idx = 0
    s.append(row(44, 108, "TOTAL CONTRIBUTIONS · LAST 365 DAYS",
                 f"{st['total']:,}", f"{st['active']} active days · avg {st['total'] / max(st['active'], 1):.1f}/day",
                 idx, big=True)); idx += 1

    s.append('<line x1="44" y1="238" x2="796" y2="238" stroke="#FFFFFF12"/>')

    col2 = 448
    s.append(row(44, 282, "CURRENT STREAK", f"{st['current']}", "days and counting" if st["current"] > 0 else "commit today to start it", idx)); idx += 1
    s.append(row(col2, 282, "LONGEST STREAK", f"{st['longest']}", "personal record", idx)); idx += 1

    if st["best"][1]:
        best_txt = f"{st['best'][0]}"
        best_sub = f"on {pretty_date(st['best'][1])} · most in a single day"
    else:
        best_txt, best_sub = "0", "no contributions yet"
    s.append(row(44, 412, "BEST DAY", best_txt, best_sub, idx)); idx += 1

    s.append(row(col2, 412, "PUBLIC REPOS", f"{data.get('repos', 0)}",
                 f"⭐ {data.get('stars', 0)} stars earned", idx)); idx += 1

    s.append('<line x1="44" y1="542" x2="796" y2="542" stroke="#FFFFFF12"/>')

    # community row
    s.append(f'<g class="sec" style="animation-delay:{150 + idx * 170}ms">'
             f'<text class="lab" x="44" y="586">COMMUNITY</text>'
             f'<text class="val" font-size="26" fill="#FBCFE8" x="44" y="624">'
             f'{data.get("followers", 0)} followers · {data.get("following", 0)} following</text></g>')
    idx += 1

    # activity bars — last 60 days
    s.append(f'<g class="sec" style="animation-delay:{150 + idx * 170}ms">'
             f'<text class="lab" x="44" y="668">ACTIVITY · LAST 60 DAYS</text></g>')
    idx += 1
    bx, base, bw, bmax = 44, 812, 11, 100
    bars = []
    for i, d in enumerate(last60):
        c = d["contributionCount"]
        h = max((c / maxc) * bmax, 4 if c > 0 else 2)
        x = bx + i * (bw + 2.6)
        bars.append(f'<rect class="bar" x="{x:.1f}" y="{base - h:.1f}" width="{bw}" '
                    f'height="{h:.1f}" rx="2.5" fill="{"#39D353" if c > 0 else "#1b2a20"}" '
                    f'style="animation-delay:{900 + i * 22:.0f}ms">'
                    f'<title>{d["date"]}: {c} contribution(s)</title></rect>')
    s.append(f'<g>{"".join(bars)}</g>')

    # footer prompt with blinking cursor
    s.append(f'<g class="sec" style="animation-delay:{150 + idx * 170}ms">'
             f'<text class="sub" x="44" y="850" fill="#A7F3D0">'
             f'$ git commit -m "keep showing up"</text>'
             f'<rect class="cursor" x="336" y="838" width="10" height="18" fill="#A7F3D0"/></g>')

    s.append("</svg>")

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as f:
        f.write("\n".join(s))
    print(f"wrote {out}  (total={st['total']} current={st['current']} "
          f"longest={st['longest']} best={st['best'][0]} active={st['active']})")


if __name__ == "__main__":
    main()
