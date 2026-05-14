"""
Fetch Google Trends search interest for GTA keywords using pytrends.

Keywords cover GTA V era signals plus early GTA VI interest,
enabling cross-era comparison on the predictions page.
"""

import time
from datetime import datetime

from pytrends.request import TrendReq

from utils import has_changed, now_iso, write_json

KEYWORDS = ["GTA Online", "GTA money glitch", "GTA weekly update", "GTA V", "GTA 6"]
TIMEFRAME = "2013-01-01 2025-12-31"
GEO = ""  # worldwide
OUT_PATH = "trends/search-interest.json"

# Colour palette — matches the chart component
COLORS = {
    "GTA V": "#f59e0b",
    "GTA Online": "#22c55e",
    "GTA 6": "#ef4444",
    "GTA money glitch": "#a78bfa",
    "GTA weekly update": "#38bdf8",
}

# pytrends caps at 5 keywords per request; if you add more, batch them.
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
            time.sleep(2)  # be polite to the unofficial API

    keywords_out = []
    for kw in KEYWORDS:
        keywords_out.append(
            {
                "keyword": kw,
                "color": COLORS.get(kw, "#ffffff"),
                "data": results[kw],
            }
        )

    return keywords_out


def main() -> None:
    print("Fetching Google Trends data...")
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
