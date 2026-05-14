"""
Fetch Take-Two Interactive (TTWO) stock price history from Yahoo Finance.

Monthly closing prices from 2013 (GTA V launch) onwards.
Annotates key GTA VI milestones so the chart can show market reaction
to each announcement, trailer, and delay.

No API key required — Yahoo Finance public endpoint.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import has_changed, now_iso, write_json

OUT_PATH = "franchise/ttwo-stock.json"

YAHOO_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/TTWO"
    "?interval=1mo&range=15y"
)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0"}

# Key GTA VI milestones for chart annotation
ANNOTATIONS = [
    { "date": "2013-09-17", "label": "GTA V launch",          "type": "launch",   "color": "#f59e0b" },
    { "date": "2022-02-14", "label": "Zynga acquired",         "type": "corporate","color": "#52525b" },
    { "date": "2022-09-18", "label": "Data breach / leak",     "type": "leak",     "color": "#ef4444" },
    { "date": "2023-11-08", "label": "\"Coming 2025\" (ER)",   "type": "date_set", "color": "#0d9488" },
    { "date": "2023-12-04", "label": "Trailer 1",              "type": "trailer",  "color": "#f59e0b" },
    { "date": "2024-10-31", "label": "\"Fall 2025\" (ER)",     "type": "date_set", "color": "#0d9488" },
    { "date": "2025-02-12", "label": "Delay to 2026",          "type": "delay",    "color": "#ef4444" },
    { "date": "2025-05-06", "label": "Trailer 2",              "type": "trailer",  "color": "#f59e0b" },
    { "date": "2026-02-12", "label": "Nov 19 confirmed (ER)",  "type": "confirmed","color": "#0d9488" },
    { "date": "2026-03-27", "label": "Official launch date",   "type": "confirmed","color": "#f59e0b" },
]


def fetch() -> list[dict]:
    resp = requests.get(YAHOO_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    result = data["chart"]["result"][0]
    timestamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]

    prices = []
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        prices.append({
            "date":  dt.strftime("%Y-%m-%d"),
            "close": round(close, 2),
        })

    return prices


def main() -> None:
    print("Fetching TTWO stock price history (Yahoo Finance)...")
    prices = fetch()
    print(f"  {len(prices)} monthly data points")
    print(f"  Range: {prices[0]['date']} → {prices[-1]['date']}")
    print(f"  Latest close: ${prices[-1]['close']}")

    payload = {
        "last_updated": now_iso(),
        "source": "Yahoo Finance — TTWO monthly closing price",
        "symbol": "TTWO",
        "currency": "USD",
        "note": "Monthly closing prices. Annotations mark key GTA VI milestones.",
        "annotations": ANNOTATIONS,
        "prices": prices,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("Stock data updated.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
