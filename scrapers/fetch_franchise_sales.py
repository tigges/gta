"""
Build GTA franchise sales dataset.

Data hierarchy (most reliable first):
1. Take-Two official earnings / press releases  — confirmed units sold-in
2. VGChartz HTML scrape                         — regional estimates
3. Curated community records                    — cited sources

Launch-week and year-1 data is sparse for early titles (III, VC, SA).
Fields use null rather than 0 when genuinely unknown.

GTA VI year-1 is a projection (DFC Intelligence / analyst consensus).
"""

import csv
import io
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import has_changed, now_iso, write_json

OUT_PATH = "franchise/sales.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

# ──────────────────────────────────────────────
# Curated seed — sourced from TT earnings, press
# units in millions
# ──────────────────────────────────────────────
SEED: list[dict] = [
    {
        "id":             "gta-3",
        "short":          "GTA III",
        "full_title":     "Grand Theft Auto III",
        "year":           2001,
        "launch_units_m": None,   # no reliable 1-week data
        "year1_units_m":  None,
        "total_units_m":  17.33,
        "total_source":   "Take-Two / Wikipedia",
        "is_prediction":  False,
    },
    {
        "id":             "gta-vc",
        "short":          "GTA VC",
        "full_title":     "Grand Theft Auto: Vice City",
        "year":           2002,
        "launch_units_m": None,
        "year1_units_m":  None,
        "total_units_m":  17.5,
        "total_source":   "Take-Two",
        "is_prediction":  False,
    },
    {
        "id":             "gta-sa",
        "short":          "GTA SA",
        "full_title":     "Grand Theft Auto: San Andreas",
        "year":           2004,
        "launch_units_m": 1.0,    # 1M first day US+UK (NPD/ELSPA)
        "year1_units_m":  None,
        "total_units_m":  27.5,
        "total_source":   "Take-Two",
        "launch_source":  "NPD/ELSPA",
        "is_prediction":  False,
    },
    {
        "id":             "gta-4",
        "short":          "GTA IV",
        "full_title":     "Grand Theft Auto IV",
        "year":           2008,
        "launch_units_m": 6.0,    # first week globally (TT earnings)
        "year1_units_m":  13.0,   # estimate incl. TLAD/TBOGT
        "total_units_m":  25.0,
        "total_source":   "Take-Two earnings",
        "launch_source":  "Take-Two earnings Q1 FY2009",
        "is_prediction":  False,
    },
    {
        "id":             "gta-5",
        "short":          "GTA V",
        "full_title":     "Grand Theft Auto V",
        "year":           2013,
        "launch_units_m": 11.21,  # 24h (TT press release Sept 18 2013)
        "year1_units_m":  29.47,  # TT earnings FY2014
        "total_units_m":  225.0,  # TT IR Feb 2026
        "total_source":   "Take-Two IR (Feb 2026)",
        "launch_source":  "Take-Two press release 2013-09-18",
        "is_prediction":  False,
    },
    {
        "id":             "gta-6",
        "short":          "GTA VI",
        "full_title":     "Grand Theft Auto VI",
        "year":           2026,
        "launch_units_m": None,   # TBC
        "year1_units_m":  40.0,   # DFC Intelligence projection
        "total_units_m":  None,
        "total_source":   None,
        "launch_source":  None,
        "year1_source":   "DFC Intelligence analyst projection",
        "is_prediction":  True,
        "prediction_range": {"low": 35.0, "high": 55.0},
    },
]

# ──────────────────────────────────────────────────────────────────
# Optional VGChartz enrichment — overrides year1/total if scraped
# VGChartz game DB page IDs for GTA titles
# ──────────────────────────────────────────────────────────────────
VGCHARTZ_IDS = {
    "gta-3":  "4200",
    "gta-vc": "4201",
    "gta-sa": "4202",
    "gta-4":  "4203",
    "gta-5":  "228521",
}


def try_vgchartz_enrich(titles: list[dict]) -> list[dict]:
    """Best-effort VGChartz scrape. Silently skips on failure."""
    title_map = {t["id"]: t for t in titles}

    for game_id, vc_id in VGCHARTZ_IDS.items():
        url = f"https://www.vgchartz.com/game/{vc_id}/"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if not resp.ok:
                continue

            import re
            # Look for "Total Shipped" or "Total Sales" figure
            match = re.search(
                r"Total\s+(?:Shipped|Sales)[^0-9]*([0-9.]+)m",
                resp.text, re.IGNORECASE
            )
            if match and game_id in title_map:
                vc_total = float(match.group(1))
                existing = title_map[game_id]["total_units_m"]
                # Only use VGChartz if we don't have TT data or it's fresher
                if existing is None:
                    title_map[game_id]["total_units_m"] = vc_total
                    title_map[game_id]["total_source"] = "VGChartz"
                    print(f"    VGChartz enriched {game_id}: {vc_total}M")
        except Exception:
            continue

    return list(title_map.values())


def main() -> None:
    print("Building franchise sales dataset...")
    titles = [dict(t) for t in SEED]  # work on copies

    print("  Attempting VGChartz enrichment...")
    titles = try_vgchartz_enrich(titles)

    # Summary
    for t in titles:
        flag = " *predicted*" if t["is_prediction"] else ""
        total = f"{t['total_units_m']}M" if t["total_units_m"] else "unknown"
        print(f"  {t['short']:8s} total={total}{flag}")

    payload = {
        "last_updated": now_iso(),
        "note": "Units sold-in (millions). Launch = first 7 days. Year 1 = 12 months from release. Total = lifetime to most recent data.",
        "titles": titles,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("Sales data updated.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
