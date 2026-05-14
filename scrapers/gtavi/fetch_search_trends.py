"""
Fetch Google Trends search interest for GTA VI-specific keywords.

Tracks speculation and announcement signals from 2020 onward,
separate from the GTA V ecosystem trends in gta-5/trends/.
"""

import sys
import time
from pathlib import Path

from pytrends.request import TrendReq

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scrapers"))
from utils import has_changed, now_iso, write_json

KEYWORDS = [
    "GTA 6",
    "GTA VI",
    "GTA 6 release date",
    "GTA 6 trailer",
    "GTA 6 gameplay",
]
TIMEFRAME = "2020-01-01 2026-12-31"
GEO = ""  # worldwide
OUT_PATH = "gta-6/trends/search-interest.json"

COLORS = {
    "GTA 6": "#f59e0b",
    "GTA VI": "#fbbf24",
    "GTA 6 release date": "#ef4444",
    "GTA 6 trailer": "#22c55e",
    "GTA 6 gameplay": "#38bdf8",
}

BATCH_SIZE = 5


def fetch() -> list[dict]:
    pytrends = TrendReq(hl="en-US", tz=0, timeout=(10, 30))
    results: dict[str, list[dict]] = {kw: [] for kw in KEYWORDS}

    for i in range(0, len(KEYWORDS), BATCH_SIZE):
        batch = KEYWORDS[i : i + BATCH_SIZE]
        pytrends.build_payload(batch, timeframe=TIMEFRAME, geo=GEO)
        df = pytrends.interest_over_time()

        if df.empty:
            print(f"  Warning: empty response for batch {batch}")
            continue

        for kw in batch:
            if kw not in df.columns:
                continue
            for date, value in df[kw].items():
                results[kw].append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "value": int(value),
                    }
                )

        if i + BATCH_SIZE < len(KEYWORDS):
            time.sleep(2)

    return [
        {
            "keyword": kw,
            "color": COLORS.get(kw, "#ffffff"),
            "data": results[kw],
        }
        for kw in KEYWORDS
    ]


def main() -> None:
    print("Fetching GTA VI search trends...")
    keywords = fetch()
    total_points = sum(len(k["data"]) for k in keywords)
    print(f"  Parsed {total_points} data points across {len(keywords)} keywords")

    payload = {
        "last_updated": now_iso(),
        "source": "Google Trends via pytrends",
        "keywords": keywords,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("Data updated.")
    else:
        print("No changes detected, skipping write.")


if __name__ == "__main__":
    main()
