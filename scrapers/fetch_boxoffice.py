"""
Scrape Box Office Mojo worldwide top lifetime gross for entertainment comparison chart.
Also includes manually curated non-film comparisons (Eras Tour, Spotify, etc.).
"""

import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from utils import has_changed, now_iso, write_json

OUT_PATH = "franchise/entertainment-comps.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"}

BOM_URL = "https://www.boxofficemojo.com/chart/ww_top_lifetime_gross/?area=XWW"

# Non-film manual seed for context (revenue in billions USD)
MANUAL_COMPS = [
    {"name": "Taylor Swift — Eras Tour",         "revenue_bn": 2.08, "year": 2024, "type": "concert",  "source": "Billboard"},
    {"name": "Avengers: Endgame",                 "revenue_bn": 2.80, "year": 2019, "type": "film",    "source": "Box Office Mojo"},
    {"name": "Avatar",                            "revenue_bn": 2.92, "year": 2009, "type": "film",    "source": "Box Office Mojo"},
    {"name": "Spotify — annual revenue",          "revenue_bn": 15.7, "year": 2024, "type": "platform","source": "Spotify IR"},
    {"name": "GTA V — total revenue",             "revenue_bn": 8.0,  "year": 2026, "type": "game",    "source": "Take-Two IR (est.)"},
    {"name": "GTA VI — projected Year 1",         "revenue_bn": 3.2,  "year": 2027, "type": "game",    "source": "DFC Intelligence", "is_prediction": True},
    {"name": "Red Dead Redemption 2",             "revenue_bn": 1.5,  "year": 2023, "type": "game",    "source": "Take-Two IR (est.)"},
    {"name": "Call of Duty: Modern Warfare III",  "revenue_bn": 1.4,  "year": 2024, "type": "game",    "source": "Activision"},
]


def parse_revenue(raw: str) -> float | None:
    """Parse '$2,923,710,708' → 2.92 (billions)."""
    clean = raw.replace("$", "").replace(",", "").strip()
    try:
        return round(float(clean) / 1_000_000_000, 2)
    except ValueError:
        return None


def fetch_bom_top_films(n: int = 10) -> list[dict]:
    try:
        resp = requests.get(BOM_URL, headers=HEADERS, timeout=20)
        if not resp.ok:
            print(f"  BOM: HTTP {resp.status_code}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        rows = soup.select("table tr")[1:n+1]  # skip header
        films = []

        for row in rows:
            cells = [c.get_text(strip=True) for c in row.find_all("td")]
            if len(cells) < 3:
                continue
            rank_raw, title, lifetime_raw = cells[0], cells[1], cells[2]
            revenue = parse_revenue(lifetime_raw)
            if revenue and title:
                films.append({
                    "name": title,
                    "revenue_bn": revenue,
                    "type": "film",
                    "source": "Box Office Mojo (WW lifetime)",
                    "rank_worldwide": int(rank_raw) if rank_raw.isdigit() else None,
                })

        print(f"  BOM: {len(films)} films scraped")
        return films

    except Exception as e:
        print(f"  BOM scrape error: {e}")
        return []


def main() -> None:
    print("Building entertainment comparisons dataset...")

    films = fetch_bom_top_films(10)

    # Merge: start with manual comps, add films not already present by name
    film_names = {f["name"].lower() for f in films}
    unique_manual = [m for m in MANUAL_COMPS if m["name"].lower() not in film_names]

    all_entries = unique_manual + films

    # Sort by revenue descending
    all_entries.sort(key=lambda x: x["revenue_bn"], reverse=True)

    print(f"  Total: {len(all_entries)} entries")
    for e in all_entries[:6]:
        flag = " *pred*" if e.get("is_prediction") else ""
        print(f"    {e['name'][:40]:40s}  ${e['revenue_bn']:.2f}B{flag}")

    payload = {
        "last_updated": now_iso(),
        "source": "Box Office Mojo + manual curation",
        "note": "Revenue in USD billions. Films = worldwide box office lifetime gross. Games = estimated total revenue.",
        "entries": all_entries,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("Entertainment comps updated.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
