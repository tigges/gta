"""
fetch_link_health.py — Outbound link health checker for gtavi.ai.

Checks all key outbound URLs used on the site (buy page store links,
affiliate product links, scraper source endpoints) and writes a
structured health report to data/feeds/link-health.json.

Runs nightly via fetch-data.yml. Results are displayed on
/admin/data-health (staging only).

Usage:
    python3 scrapers/fetch_link_health.py
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

sys.path.insert(0, str(__file__.replace("scrapers/fetch_link_health.py", "")))
from scrapers.utils import now_iso, write_json

TIMEOUT = 10
HEADERS = {"User-Agent": "gtavi.ai link-health-bot/1.0 (+https://gtavi.ai)"}

# ── URL registry ──────────────────────────────────────────────────────────────
# Each entry: (label, url)
# Keep to genuinely important outbound links — store roots + affiliate targets.
URLS = [
    # ── Store roots (buy page) ────────────────────────────────────────────────
    ("PlayStation Store (US)",      "https://store.playstation.com/en-us/"),
    ("PlayStation Store (UK)",      "https://store.playstation.com/en-gb/"),
    ("Xbox / Microsoft Store",      "https://www.xbox.com/en-US/games"),
    ("Steam",                       "https://store.steampowered.com/"),
    ("Rockstar Games Store",        "https://store.rockstargames.com/"),
    ("Epic Games Store",            "https://store.epicgames.com/en-US/"),

    # ── Amazon store roots (affiliate-tagged on buy page) ─────────────────────
    ("Amazon US",                   "https://www.amazon.com/"),
    ("Amazon UK",                   "https://www.amazon.co.uk/"),
    ("Amazon CA",                   "https://www.amazon.ca/"),
    ("Amazon DE",                   "https://www.amazon.de/"),
    ("Amazon FR",                   "https://www.amazon.fr/"),
    ("Amazon IT",                   "https://www.amazon.it/"),
    ("Amazon ES",                   "https://www.amazon.es/"),
    ("Amazon NL",                   "https://www.amazon.nl/"),
    ("Amazon JP",                   "https://www.amazon.co.jp/"),
    ("Amazon AU",                   "https://www.amazon.com.au/"),
    ("Amazon IN",                   "https://www.amazon.in/"),
    ("Amazon BR",                   "https://www.amazon.com.br/"),
    ("Amazon MX",                   "https://www.amazon.com.mx/"),

    # ── Affiliate programme dashboards ────────────────────────────────────────
    ("Amazon Associates Central",   "https://affiliate-program.amazon.com/"),
    ("Impact.com",                  "https://app.impact.com/"),
    ("Partnerize",                  "https://console.partnerize.com/"),

    # ── Key data source roots (scraper health signal) ─────────────────────────
    ("Rockstar Newswire",           "https://www.rockstargames.com/newswire"),
    ("Steam API",                   "https://store.steampowered.com/api/appdetails?appids=271590"),
    ("Yahoo Finance (TTWO)",        "https://finance.yahoo.com/quote/TTWO/"),
]


def check_url(label: str, url: str) -> dict:
    try:
        resp = requests.head(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
        # Some servers reject HEAD — fall back to GET with stream
        if resp.status_code == 405:
            resp = requests.get(url, timeout=TIMEOUT, headers=HEADERS, stream=True)
            resp.close()
        # 404/410 = genuinely gone; None = network failure = real problem.
        # 403/503 = bot-blocking but server is up — not a real outage.
        ok = resp.status_code not in (404, 410, 451)
        return {"label": label, "url": url, "status": resp.status_code, "ok": ok}
    except Exception as exc:
        return {"label": label, "url": url, "status": None, "ok": False, "error": str(exc)[:120]}


def main() -> None:
    print(f"Checking {len(URLS)} URLs…")
    results = []

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(check_url, label, url): (label, url) for label, url in URLS}
        for future in as_completed(futures):
            result = future.result()
            status_str = str(result["status"]) if result["status"] else "ERR"
            icon = "✓" if result["ok"] else "✗"
            print(f"  {icon} [{status_str:>3}] {result['label']}")
            results.append(result)

    results.sort(key=lambda r: (r["ok"], r["label"]))  # failures first

    ok_count   = sum(1 for r in results if r["ok"])
    fail_count = sum(1 for r in results if not r["ok"])
    print(f"\n{ok_count} OK · {fail_count} failing")

    payload = {
        "last_updated": now_iso(),
        "checked": len(results),
        "ok": ok_count,
        "failing": fail_count,
        "results": results,
    }
    write_json("feeds/link-health.json", payload)


if __name__ == "__main__":
    main()
