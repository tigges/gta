"""
Fetch deeper GTA V PC metrics from SteamDB.

SteamDB blocks server IPs (returns 403). This scraper attempts the fetch
but falls back to a curated seed. Run manually from a local machine
with Cloudflare bypass if needed.

Key data: peak concurrent players (all-time), review count, price history.
"""

import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import has_changed, now_iso, write_json

OUT_PATH = "gta-5/meta/steamdb.json"
APP_ID = "271590"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

# Curated seed from SteamDB public data (updated periodically)
SEED = {
    "app_id": APP_ID,
    "name": "Grand Theft Auto V",
    "peak_concurrent_all_time": 364548,
    "peak_concurrent_date": "2020-04-05",  # COVID peak
    "peak_concurrent_source": "SteamDB",
    "review_count": 1850000,
    "review_score_pct": 87,
    "current_price_usd": 29.99,
    "lowest_price_usd": 7.49,
    "price_history_note": "Regular sales to $7.49. Base $29.99.",
}


def try_scrape() -> dict | None:
    try:
        url = f"https://steamdb.info/app/{APP_ID}/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 403:
            print("  SteamDB: 403 (Cloudflare block) — using seed data")
            return None
        if not resp.ok:
            print(f"  SteamDB: HTTP {resp.status_code}")
            return None

        text = resp.text
        peak = re.search(r"All-Time Peak[^0-9]*([0-9,]+)", text)
        reviews = re.search(r"([0-9,]+)\s+reviews", text, re.I)

        return {
            "peak_concurrent_all_time": int(peak.group(1).replace(",", "")) if peak else None,
            "review_count": int(reviews.group(1).replace(",", "")) if reviews else None,
        }
    except Exception as e:
        print(f"  SteamDB scrape error: {e}")
        return None


def main() -> None:
    print("Fetching SteamDB data for GTA V...")
    live = try_scrape()

    data = {**SEED}
    if live:
        data.update({k: v for k, v in live.items() if v is not None})

    payload = {
        "last_updated": now_iso(),
        "source": "SteamDB (steamdb.info) — seed + live where accessible",
        **data,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("SteamDB data updated.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
