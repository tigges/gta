#!/usr/bin/env python3
"""
fetch_weekly_bonuses.py — Scrapes Rockstar Newswire for GTA Online weekly bonus events.

GTA Online weekly events post every Thursday. They announce 2×/3× GTA$ bonuses
on specific activities, which dynamically reorder the income recommendation in the
IncomeAdviser tool (a 2× bonus on Contact Missions turns them from C-tier to S-tier).

Output: data/gta-5/economy/weekly-bonuses.json

Sources:
  https://www.rockstargames.com/newswire/tag/gtaonline
  RSS: https://www.rockstargames.com/newswire/feed.xml

Usage:
  python3 scrapers/fetch_weekly_bonuses.py
"""

import re
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from utils import write_json, has_changed, load_existing, now_iso

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[fetch_weekly_bonuses] requests/bs4 not available")
    requests = None
    BeautifulSoup = None

OUTPUT_PATH = "data/gta-5/economy/weekly-bonuses.json"

NEWSWIRE_RSS = "https://www.rockstargames.com/newswire/feed.xml"
NEWSWIRE_URL = "https://www.rockstargames.com/newswire/tag/gtaonline"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; gtavi-ai-bot/1.0; +https://gtavi.ai)",
}

# Keywords that map to business/activity IDs in business-profiles.json
ACTIVITY_KEYWORDS = {
    "cayo perico":        {"id": "cayo-perico",          "multiplier_likely": 2},
    "acid lab":           {"id": "acid-lab",             "multiplier_likely": 2},
    "nightclub":          {"id": "nightclub",            "multiplier_likely": 2},
    "bunker":             {"id": "bunker",               "multiplier_likely": 2},
    "casino heist":       {"id": "diamond-casino-heist", "multiplier_likely": 2},
    "auto shop":          {"id": "auto-shop",            "multiplier_likely": 2},
    "agency":             {"id": "agency-vip-contract",  "multiplier_likely": 2},
    "garment factory":    {"id": "garment-factory",      "multiplier_likely": 2},
    "contact mission":    {"id": "contact-missions",     "multiplier_likely": 2},
    "vip work":           {"id": "vip-work",             "multiplier_likely": 2},
    "headhunter":         {"id": "vip-work",             "multiplier_likely": 2},
    "mc business":        {"id": "mc-cocaine",           "multiplier_likely": 2},
    "cocaine":            {"id": "mc-cocaine",           "multiplier_likely": 2},
    "vehicle cargo":      {"id": "vehicle-warehouse",    "multiplier_likely": 2},
    "special cargo":      {"id": "special-cargo",        "multiplier_likely": 2},
    "hangar":             {"id": "hangar",               "multiplier_likely": 2},
    "gunrunning":         {"id": "bunker",               "multiplier_likely": 2},
}

MULTIPLIER_RE = re.compile(r'(\d+)[xX×]\s*(gta\s*\$|bonus|cash|money)', re.IGNORECASE)


def parse_multiplier(text: str) -> int:
    m = MULTIPLIER_RE.search(text)
    if m:
        return int(m.group(1))
    if "triple" in text.lower():
        return 3
    if "double" in text.lower():
        return 2
    return 2  # default assumption if mentioned as active bonus


def fetch_latest_bonuses(session) -> list[dict]:
    """Fetch the latest GTA Online weekly update post from Newswire."""
    bonuses = []
    try:
        # Try RSS first — structured and fast
        resp = session.get(NEWSWIRE_RSS, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "xml")
            items = soup.find_all("item")
            
            # Find the most recent GTA Online weekly update post
            for item in items[:20]:
                title = item.find("title")
                link = item.find("link")
                pub_date = item.find("pubDate")
                
                if not title:
                    continue
                
                title_text = title.get_text(strip=True).lower()
                if any(kw in title_text for kw in ["this week", "bonuses", "gta online weekly", "weekly update"]):
                    # Fetch the article page
                    article_url = link.get_text(strip=True) if link else None
                    if article_url:
                        try:
                            art_resp = session.get(article_url, headers=HEADERS, timeout=15)
                            if art_resp.status_code == 200:
                                art_soup = BeautifulSoup(art_resp.text, "html.parser")
                                article_text = art_soup.get_text(separator=" ", strip=True)
                                
                                # Scan for activity bonuses
                                for keyword, activity in ACTIVITY_KEYWORDS.items():
                                    if keyword.lower() in article_text.lower():
                                        # Find surrounding context for multiplier
                                        idx = article_text.lower().find(keyword.lower())
                                        context = article_text[max(0, idx-100):idx+200]
                                        multiplier = parse_multiplier(context)
                                        
                                        bonuses.append({
                                            "activity_id":  activity["id"],
                                            "keyword_found": keyword,
                                            "multiplier":   multiplier,
                                            "source_url":   article_url,
                                            "source_title": title.get_text(strip=True),
                                            "pub_date":     pub_date.get_text(strip=True) if pub_date else None,
                                        })
                        except Exception as e:
                            print(f"  [warn] Could not fetch article: {e}")
                    break  # Only process the most recent weekly post
                    
    except Exception as e:
        print(f"[fetch_weekly_bonuses] RSS fetch error: {e}")
    
    # Deduplicate by activity_id, keep highest multiplier
    seen = {}
    for b in bonuses:
        aid = b["activity_id"]
        if aid not in seen or b["multiplier"] > seen[aid]["multiplier"]:
            seen[aid] = b
    return list(seen.values())


def main():
    existing = load_existing(OUTPUT_PATH)

    if requests is None or BeautifulSoup is None:
        print("[fetch_weekly_bonuses] deps missing — writing empty bonuses")
        result = {
            "last_updated": now_iso(),
            "source": "Rockstar Newswire (scraping unavailable)",
            "week_start": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "bonuses": [],
            "note": "No bonuses detected — check manually at rockstargames.com/newswire"
        }
        write_json(OUTPUT_PATH, result)
        return

    session = requests.Session()
    print("[fetch_weekly_bonuses] Fetching latest Newswire post...")
    
    bonuses = fetch_latest_bonuses(session)
    print(f"[fetch_weekly_bonuses] Found {len(bonuses)} active bonuses")
    for b in bonuses:
        print(f"  {b['activity_id']}: {b['multiplier']}× ({b['keyword_found']})")

    # Compute effective $/hr with multiplier applied
    # Base values from business-profiles.json — loaded at runtime by the UI
    result = {
        "last_updated": now_iso(),
        "source": "Rockstar Newswire (rockstargames.com/newswire)",
        "week_start": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "note": "Updated every Thursday when Rockstar posts weekly events. Multipliers apply to net_profit_per_hr.",
        "bonuses": bonuses,
    }

    if has_changed(OUTPUT_PATH, result):
        write_json(OUTPUT_PATH, result)
        print(f"[fetch_weekly_bonuses] Updated {OUTPUT_PATH}")
    else:
        print("[fetch_weekly_bonuses] No changes")


if __name__ == "__main__":
    main()
