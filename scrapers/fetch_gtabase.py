#!/usr/bin/env python3
"""
fetch_gtabase.py — Scrapes GTABase.com for GTA Online business and heist $/hr data.

GTABase has the most accurate community-maintained tables for:
- Business profit per hour (with setup costs)
- Heist payout breakdowns
- Contact mission $/hr rankings

Output: data/gta-5/economy/gtabase-live.json
        (merged into business-profiles.json on next build)

Source: https://gtabase.com/gta-online/businesses/
        https://gtabase.com/gta-online/heists/

Usage:
  python3 scrapers/fetch_gtabase.py
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
    print("[fetch_gtabase] requests/bs4 not available — using seed data")
    requests = None
    BeautifulSoup = None

OUTPUT_PATH = "data/gta-5/economy/gtabase-live.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; gtavi-ai-bot/1.0; +https://gtavi.ai)",
    "Accept-Language": "en-US,en;q=0.9",
}

GTABASE_BUSINESSES = "https://gtabase.com/gta-online/businesses/"
GTABASE_HEISTS     = "https://gtabase.com/gta-online/heists/"

MONEY_RE = re.compile(r'[\$GTA\$\s]*([\d,]+(?:\.\d+)?)\s*[Kk]?', re.IGNORECASE)


def parse_money(text: str) -> int | None:
    """Parse a GTA$ value like '$1,200,000' or '1.2M' or '$1.2M/hr'."""
    text = text.strip().replace(",", "").replace("GTA$", "").replace("$", "").replace("/hr", "").replace("hour", "")
    text = text.strip()
    try:
        if "M" in text.upper():
            return int(float(re.sub(r'[Mm].*', '', text)) * 1_000_000)
        if "K" in text.upper():
            return int(float(re.sub(r'[Kk].*', '', text)) * 1_000)
        val = float(re.sub(r'[^0-9.]', '', text))
        if val > 0:
            return int(val)
    except (ValueError, TypeError):
        pass
    return None


def scrape_businesses(session) -> list[dict]:
    """Scrape GTABase business profit tables."""
    businesses = []
    try:
        resp = session.get(GTABASE_BUSINESSES, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"  [warn] GTABase businesses returned {resp.status_code}")
            return []
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # GTABase uses a structured table — parse it
        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            if not any(h in headers for h in ["business", "profit", "$/hr", "income"]):
                continue
                
            for row in table.find_all("tr")[1:]:  # skip header
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(cells) < 2:
                    continue
                    
                name = cells[0] if cells else ""
                # Try to find profit/hr column
                profit_hr = None
                for cell in cells[1:]:
                    p = parse_money(cell)
                    if p and 10_000 <= p <= 5_000_000:
                        profit_hr = p
                        break
                
                if name and profit_hr:
                    businesses.append({
                        "name": name,
                        "net_profit_per_hr": profit_hr,
                        "source": "GTABase",
                    })
        
        print(f"  Found {len(businesses)} businesses from GTABase")
    except Exception as e:
        print(f"  [warn] GTABase scrape error: {e}")
    
    return businesses


def scrape_heists(session) -> list[dict]:
    """Scrape GTABase heist payout table."""
    heists = []
    try:
        resp = session.get(GTABASE_HEISTS, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            if not any(h in headers for h in ["heist", "payout", "take", "cut"]):
                continue
                
            for row in table.find_all("tr")[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(cells) < 2:
                    continue
                    
                name = cells[0]
                payout = None
                for cell in cells[1:]:
                    p = parse_money(cell)
                    if p and 100_000 <= p <= 10_000_000:
                        payout = p
                        break
                
                if name and payout:
                    heists.append({
                        "name": name,
                        "payout_per_run_max": payout,
                        "source": "GTABase",
                    })
        
        print(f"  Found {len(heists)} heists from GTABase")
    except Exception as e:
        print(f"  [warn] GTABase heist scrape error: {e}")
    
    return heists


def main():
    if requests is None:
        print("[fetch_gtabase] deps missing — skipping")
        return

    session = requests.Session()
    print("[fetch_gtabase] Scraping GTABase.com...")
    
    businesses = scrape_businesses(session)
    time.sleep(2)  # polite delay
    heists = scrape_heists(session)

    result = {
        "last_updated": now_iso(),
        "source": "GTABase.com (gtabase.com/gta-online/)",
        "note": "Live-scraped $/hr and payout data. Used to validate and update business-profiles.json.",
        "businesses": businesses,
        "heists": heists,
    }

    if has_changed(result, OUTPUT_PATH):
        write_json(OUTPUT_PATH, result)
        print(f"[fetch_gtabase] Saved {len(businesses)} businesses + {len(heists)} heists to {OUTPUT_PATH}")
    else:
        print("[fetch_gtabase] No changes")


if __name__ == "__main__":
    main()
