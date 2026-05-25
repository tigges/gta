"""
Fetch Google Trends search interest for GTA keywords using pytrends.

Keywords cover GTA V era signals plus early GTA VI interest,
enabling cross-era comparison on the predictions page.
"""

import time
import random
from datetime import datetime

from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError

from utils import has_changed, now_iso, write_json

# Removed "GTA money glitch" (all-time max: 1) and "GTA weekly update" (all-time max: 0)
# — both produced near-zero data and wasted pytrends' 5-keyword-per-request cap.
KEYWORDS = ["GTA Online", "GTA V", "GTA 6"]
TIMEFRAME = "2013-01-01 2026-12-31"
GEO = ""  # worldwide
OUT_PATH = "gta-5/trends/search-interest.json"

# Colour palette — matches the chart component
COLORS = {
    "GTA V":      "#f59e0b",
    "GTA Online": "#22c55e",
    "GTA 6":      "#ef4444",
}

# pytrends caps at 5 keywords per request
BATCH_SIZE = 5
MAX_RETRIES = 5
BASE_BACKOFF = 15  # seconds


def fetch_batch_with_retry(pytrends: TrendReq, batch: list[str]) -> object:
    """Fetch a single batch, retrying on 429 with exponential backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            pytrends.build_payload(batch, timeframe=TIMEFRAME, geo=GEO)
            return pytrends.interest_over_time()
        except TooManyRequestsError:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = BASE_BACKOFF * (2 ** attempt) + random.uniform(0, 5)
            print(f"  429 rate limit — waiting {wait:.0f}s before retry {attempt + 2}/{MAX_RETRIES}...")
            time.sleep(wait)
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = BASE_BACKOFF * (2 ** attempt)
            print(f"  Error ({e}) — waiting {wait:.0f}s before retry...")
            time.sleep(wait)


def fetch() -> list[dict]:
    pytrends = TrendReq(hl="en-US", tz=0, timeout=(10, 60))
    results: dict[str, list[dict]] = {kw: [] for kw in KEYWORDS}

    for i in range(0, len(KEYWORDS), BATCH_SIZE):
        batch = KEYWORDS[i : i + BATCH_SIZE]
        print(f"  Fetching batch: {batch}")
        df = fetch_batch_with_retry(pytrends, batch)

        if df is None or df.empty:
            print(f"  Warning: empty response for batch {batch}")
        else:
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
            time.sleep(3 + random.uniform(0, 2))

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
