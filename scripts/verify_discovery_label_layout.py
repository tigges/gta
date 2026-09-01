#!/usr/bin/env python3
"""Verify discovery-chart bilateral packer: zero same-row overlaps on EL."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data/gta-6/trailer-analysis.json").read_text())
EL = next(t for t in DATA["trailers"] if t.get("youtube_id") == "tJbzMqJGH4k")

CHAR_W = 6.1
PAD = 12
MAX_SHIFT = 96
SHIFT_STEP = 12


def short_name(entity: str) -> str:
    return " ".join(entity.split()[:2])


def width(text: str) -> int:
    return int(len(text) * CHAR_W + 8)


def labeled(events):
    out = []
    for i, e in enumerate(events):
        if e["type"] in ("reveal", "character") or i < 3 or e.get("confidence") == "confirmed":
            out.append(e)
    return out


def layout(events, plot_w, duration):
    evs = sorted(events, key=lambda e: e["t"])
    above: list[list[tuple[float, float]]] = [[]]
    below: list[list[tuple[float, float]]] = [[]]
    out = []

    def fits(row, left, right):
        return all(right + PAD <= b[0] or left - PAD >= b[1] for b in row)

    for i, ev in enumerate(evs):
        pin = (ev["t"] / max(1, duration)) * plot_w
        text = short_name(ev["entity"])
        w = width(text)
        prefer_r = pin - w / 2
        prefer_l = pin - w
        prefer_f = pin
        xs = [prefer_r, prefer_f, prefer_l]
        d = SHIFT_STEP
        while d <= MAX_SHIFT:
            xs += [prefer_r + d, prefer_r - d, prefer_f + d, prefer_l - d]
            d += SHIFT_STEP

        placed = None
        sides = ("above", "below") if i % 2 == 0 else ("below", "above")

        def try_side(side):
            nonlocal placed
            rows = above if side == "above" else below
            for r, row in enumerate(rows):
                for raw in xs:
                    left = max(0, min(raw, max(0, plot_w - w)))
                    if fits(row, left, left + w):
                        placed = (side, r, left)
                        return True
            return False

        for side in sides:
            if try_side(side):
                break
        if not placed:
            side = "above" if len(above) <= len(below) else "below"
            rows = above if side == "above" else below
            rows.append([])
            if not try_side(side):
                left = max(0, min(pin - w / 2, max(0, plot_w - w)))
                placed = (side, len(rows) - 1, left)

        side, r, left = placed
        rows = above if side == "above" else below
        rows[r].append((left, left + w))
        out.append({"text": text, "side": side, "row": r, "left": left, "right": left + w})
    return out, len(above), len(below)


def overlaps(placements):
    n = 0
    pairs = []
    for i, a in enumerate(placements):
        for b in placements[i + 1 :]:
            if a["side"] != b["side"] or a["row"] != b["row"]:
                continue
            if not (a["right"] + PAD <= b["left"] or b["right"] + PAD <= a["left"]):
                n += 1
                pairs.append((a["text"], b["text"], a["side"], a["row"]))
    return n, pairs


def main() -> int:
    events = labeled(EL["events"])
    ok = True
    print(f"EL labeled events: {len(events)}")
    for w in (640, 960, 1100, 1280):
        plot = w - 20
        places, above_n, below_n = layout(events, plot, EL["duration_sec"])
        n, pairs = overlaps(places)
        status = "PASS" if n == 0 else "FAIL"
        if n:
            ok = False
        print(f"  {status}  width={w}  above={above_n} below={below_n}  overlaps={n}")
        for p in pairs[:6]:
            print(f"         collide: {p}")
    print("OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
