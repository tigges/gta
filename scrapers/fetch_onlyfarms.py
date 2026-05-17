#!/usr/bin/env python3
"""
fetch_onlyfarms.py — Scrapes GTAFarms.com (OnlyFarms) for community-verified GTA Online $/hr data.

GTAFarms aggregates community tier lists and $/hr benchmarks with confidence ratings.
"Where multiple sources agree, confidence is high. Where they diverge, flag for verification."

Output: data/gta-5/economy/community-validation.json

Usage:
  python3 scrapers/fetch_onlyfarms.py
"""

import re
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))
from utils import write_json, has_changed, load_existing, now_iso

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[fetch_onlyfarms] deps missing")
    requests = None

OUTPUT_PATH = "gta-5/economy/community-validation.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; gtavi-ai-bot/1.0; +https://gtavi.ai)"}

SOURCES = [
    "https://gtabase.com/gta-online/businesses/",
    "https://onlyfarms.gg/guides/gta-online-money-guide-2026-how-to-make-2m-fast-with-vehicle-cargo-races-and-bonuses/",
]

MONEY_RE = re.compile(r'\$?([\d,]+(?:\.\d+)?)\s*[MmKk]?', re.IGNORECASE)

def parse_money(text: str) -> int | None:
    text = text.strip().replace(",", "")
    try:
        if "M" in text.upper():
            return int(float(re.sub(r'[Mm].*', '', text)) * 1_000_000)
        if "K" in text.upper() or "k" in text:
            return int(float(re.sub(r'[Kk].*', '', text)) * 1_000)
        val = float(re.sub(r'[^0-9.]', '', text))
        if 10_000 < val < 5_000_000:
            return int(val)
    except (ValueError, TypeError):
        pass
    return None

def scrape_gtabase(session) -> list[dict]:
    results = []
    try:
        resp = session.get(SOURCES[0], headers=HEADERS, timeout=15)
        if not resp.ok:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            if not any(h in headers for h in ["business", "income", "profit"]):
                continue
            for row in table.find_all("tr")[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(cells) < 2:
                    continue
                name = cells[0]
                profit_hr = None
                for cell in cells[1:]:
                    p = parse_money(cell)
                    if p and 5_000 <= p <= 2_000_000:
                        profit_hr = p
                        break
                if name and profit_hr:
                    results.append({"name": name, "gta_per_hr": profit_hr, "source": "GTABase"})
        print(f"  GTABase: {len(results)} entries")
    except Exception as e:
        print(f"  [warn] GTABase scrape error: {e}")
    return results


def cross_validate(community: list[dict], our_data_path: str = "gta-5/economy/business-profiles.json") -> list[dict]:
    """Cross-validate community figures against our data. Flag discrepancies."""
    try:
        our = load_existing(our_data_path)
        our_map = {b["name"].lower(): b["net_profit_per_hr"] for b in our.get("businesses", [])}
    except Exception:
        return community

    validated = []
    for entry in community:
        name_lower = entry["name"].lower()
        our_val = next((v for k, v in our_map.items() if k in name_lower or name_lower in k), None)
        if our_val:
            diff_pct = abs(entry["gta_per_hr"] - our_val) / our_val * 100
            entry["our_value"] = our_val
            entry["diff_pct"] = round(diff_pct, 1)
            entry["confidence"] = "high" if diff_pct < 15 else "medium" if diff_pct < 40 else "low"
        validated.append(entry)
    return validated


def main():
    if not requests:
        print("[fetch_onlyfarms] requests missing")
        return

    session = requests.Session()
    print("[fetch_onlyfarms] Scraping community sources...")

    results = scrape_gtabase(session)
    validated = cross_validate(results)

    high_conf = sum(1 for r in validated if r.get("confidence") == "high")
    flagged   = sum(1 for r in validated if r.get("confidence") == "low")

    result = {
        "last_updated": now_iso(),
        "source": "GTABase.com · community cross-validation",
        "summary": {
            "total": len(validated),
            "high_confidence": high_conf,
            "flagged_for_review": flagged,
        },
        "entries": validated,
    }

    if has_changed(result, OUTPUT_PATH):
        write_json(OUTPUT_PATH, result)
        print(f"[fetch_onlyfarms] {len(validated)} entries — {high_conf} high conf, {flagged} flagged")
    else:
        print("[fetch_onlyfarms] No changes")


if __name__ == "__main__":
    main()
