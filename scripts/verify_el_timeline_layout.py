#!/usr/bin/env python3
"""Verify Extended Look label packer: zero same-row overlaps at common widths."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS = json.loads((ROOT / "data/gta-6/trailer-analysis.json").read_text())
EL = next(t for t in EVENTS["trailers"] if t.get("youtube_id") == "tJbzMqJGH4k")

SECTIONS = [
    ("Mission 1 — Venture Apartments", 0, 190),
    ("Open World — Vice City & Leonida", 190, 540),
    ("Mission 2 — Highway Chase", 540, 760),
    ("Open World — Keys & Activities", 760, 1060),
    ("Mission 3 — Corporate Gala", 1060, 1400),
    ("Developer Reveals", 1400, 1609),
]

CHAR_W = 6.1
PAD = 12
MAX_SHIFT = 96
SHIFT_STEP = 12


def label_text(entity: str, t: int) -> str:
    name = entity[:26] + "…" if len(entity) > 28 else entity
    return f"{name} ({t // 60}:{t % 60:02d})"


def width(text: str) -> int:
    return int(len(text) * CHAR_W + 8)


def layout(events, t0, t1, plot_w):
    evs = sorted((e for e in events if t0 <= e["t"] < t1), key=lambda e: e["t"])
    dur = max(1, t1 - t0)
    rows: list[list[tuple[float, float]]] = [[]]
    out = []

    def fits(row, left, right):
        return all(right + PAD <= b[0] or left - PAD >= b[1] for b in row)

    for ev in evs:
        pin = ((ev["t"] - t0) / dur) * plot_w
        text = label_text(ev["entity"], ev["t"])
        w = width(text)
        prefer_r = pin + 4
        prefer_l = pin - 4 - w
        xs = [prefer_r, prefer_l]
        d = SHIFT_STEP
        while d <= MAX_SHIFT:
            xs += [prefer_r + d, prefer_r - d, prefer_l + d, prefer_l - d]
            d += SHIFT_STEP

        placed = None
        for r, row in enumerate(rows):
            for raw in xs:
                left = max(0, min(raw, max(0, plot_w - w)))
                if fits(row, left, left + w):
                    placed = (r, left)
                    break
            if placed:
                break
        if not placed:
            rows.append([])
            left = max(0, min(pin + 4, max(0, plot_w - w)))
            placed = (len(rows) - 1, left)
        r, left = placed
        rows[r].append((left, left + w))
        out.append({"text": text, "row": r, "left": left, "right": left + w, "pin": pin, "t": ev["t"]})
    return out


def overlaps(placements):
    n = 0
    pairs = []
    for i, a in enumerate(placements):
        for b in placements[i + 1 :]:
            if a["row"] != b["row"]:
                continue
            if not (a["right"] + PAD <= b["left"] or b["right"] + PAD <= a["left"]):
                n += 1
                pairs.append((a["text"], b["text"]))
    return n, pairs


def main() -> int:
    events = EL["events"]
    widths = (640, 960, 1100, 1280)
    failed = 0
    print("Extended Look label packer — same-row overlap check")
    print(f"{len(events)} events · {len(SECTIONS)} sections · widths {list(widths)}\n")
    for w in widths:
        print(f"== plotW={w} ==")
        for name, t0, t1 in SECTIONS:
            p = layout(events, t0, t1, w)
            n, pairs = overlaps(p)
            rows = max((x["row"] for x in p), default=0) + 1
            status = "OK" if n == 0 else "OVERLAP"
            print(f"  {status:8} {name:42} events={len(p):2} rows={rows} overlaps={n}")
            for a, b in pairs:
                print(f"           collide: {a}  ×  {b}")
                failed += 1
        print()
    if failed:
        print(f"FAIL — {failed} overlapping pair(s)")
        return 1
    print("PASS — no same-row overlaps at any tested width")
    return 0


if __name__ == "__main__":
    sys.exit(main())
