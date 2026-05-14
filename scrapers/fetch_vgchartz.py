"""
Fetch GTA franchise regional sales estimates from VGChartz.

VGChartz changed methodology in 2018 — now only tracks official shipment
data from publishers. For GTA titles, Take-Two earnings reports are
more reliable. This scraper tries VGChartz then falls back to seed data
sourced from TT earnings.

Adds regional breakdown (NA / EU / Japan / Other) where available.
"""

import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from utils import has_changed, now_iso, write_json

OUT_PATH = "franchise/vgchartz.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"}

# Regional estimates sourced from VGChartz + analyst notes
# All values in millions of units
SEED = [
    {
        "id": "gta-3",  "short": "GTA III",  "year": 2001,
        "na_m": 6.5,  "eu_m": 7.2,  "jp_m": 0.8,  "other_m": 2.8,  "total_m": 17.33,
        "source": "VGChartz",
    },
    {
        "id": "gta-vc", "short": "GTA VC",   "year": 2002,
        "na_m": 6.8,  "eu_m": 7.5,  "jp_m": 0.9,  "other_m": 2.3,  "total_m": 17.5,
        "source": "VGChartz",
    },
    {
        "id": "gta-sa", "short": "GTA SA",   "year": 2004,
        "na_m": 10.5, "eu_m": 11.2, "jp_m": 1.2,  "other_m": 4.6,  "total_m": 27.5,
        "source": "VGChartz",
    },
    {
        "id": "gta-4",  "short": "GTA IV",   "year": 2008,
        "na_m": 9.8,  "eu_m": 10.5, "jp_m": 0.8,  "other_m": 3.9,  "total_m": 25.0,
        "source": "Take-Two earnings",
    },
    {
        "id": "gta-5",  "short": "GTA V",    "year": 2013,
        "na_m": 90.0, "eu_m": 88.0, "jp_m": 4.0,  "other_m": 43.0, "total_m": 225.0,
        "source": "Take-Two IR (Feb 2026)",
    },
    {
        "id": "gta-6",  "short": "GTA VI",   "year": 2026,
        "na_m": None, "eu_m": None, "jp_m": None, "other_m": None,
        "year1_m": 40.0, "total_m": None,
        "source": "DFC Intelligence (projection)", "is_prediction": True,
    },
]


def try_enrich_from_vgchartz(titles: list[dict]) -> list[dict]:
    """Best-effort VGChartz HTML scrape for regional data."""
    vc_ids = {"gta-3": "4200", "gta-vc": "4201", "gta-sa": "4202",
              "gta-4": "4203", "gta-5": "228521"}
    for t in titles:
        vc_id = vc_ids.get(t["id"])
        if not vc_id:
            continue
        try:
            resp = requests.get(f"https://www.vgchartz.com/game/{vc_id}/", headers=HEADERS, timeout=15)
            if not resp.ok:
                continue
            soup = BeautifulSoup(resp.text, "lxml")
            text = resp.text
            # VGChartz uses a specific table for regional sales
            na = re.search(r"North America[^0-9]*([0-9.]+)m", text, re.I)
            eu = re.search(r"(?:Europe|PAL)[^0-9]*([0-9.]+)m", text, re.I)
            jp = re.search(r"Japan[^0-9]*([0-9.]+)m", text, re.I)
            if na:
                t["na_m"] = float(na.group(1))
                t["source"] = "VGChartz (live)"
            if eu:
                t["eu_m"] = float(eu.group(1))
            if jp:
                t["jp_m"] = float(jp.group(1))
        except Exception:
            pass
    return titles


def main() -> None:
    print("Building VGChartz regional sales data...")
    titles = [dict(t) for t in SEED]
    titles = try_enrich_from_vgchartz(titles)

    for t in titles:
        flag = " *pred*" if t.get("is_prediction") else ""
        print(f"  {t['short']:8s} NA={t.get('na_m','?')}M  EU={t.get('eu_m','?')}M  total={t.get('total_m','?')}M{flag}")

    payload = {
        "last_updated": now_iso(),
        "source": "VGChartz + Take-Two IR + DFC Intelligence",
        "note": "Regional estimates in millions of units. NA/EU splits are estimates where TT doesn't report separately.",
        "titles": titles,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("VGChartz data updated.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
