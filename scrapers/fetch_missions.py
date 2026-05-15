#!/usr/bin/env python3
"""
fetch_missions.py — Scrapes GTA Wiki for GTA V story mission payouts.

Sources:
  https://gta.fandom.com/wiki/Missions_in_GTA_V
  Individual mission pages for payout data

Output:
  data/gta-5/missions/story-missions.json

Usage:
  python3 scrapers/fetch_missions.py

Notes:
  - Merges scraped data with the curated seed in story-missions.json
  - Only updates records that have changed (has_changed guard)
  - GTA Wiki can be slow — uses 1.5s polite delay between requests
  - Falls back to cached seed if wiki is unreachable
"""

import time
import re
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from utils import write_json, has_changed, load_existing, now_iso

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[fetch_missions] requests/bs4 not installed — using seed data only")
    requests = None
    BeautifulSoup = None

SEED_PATH = "data/gta-5/missions/story-missions.json"
WIKI_MISSIONS_URL = "https://gta.fandom.com/wiki/Missions_in_GTA_V"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; gtavi-ai-bot/1.0; +https://gtavi.ai)",
    "Accept-Language": "en-US,en;q=0.9",
}

PAYOUT_RE = re.compile(r"\$([0-9,]+)", re.IGNORECASE)


def parse_payout(text: str) -> int | None:
    """Extract dollar amount from wiki text like '$9,000' or 'GTA$9000'."""
    if not text:
        return None
    text = text.replace("GTA$", "$").replace(",", "")
    m = PAYOUT_RE.search(text)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def fetch_mission_payout(session, mission_url: str) -> int | None:
    """Scrape a single mission page for its payout value."""
    try:
        resp = session.get(mission_url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")

        # Look for infobox reward row
        for row in soup.select("table.infobox tr, .pi-item"):
            label = row.select_one("th, .pi-data-label")
            value = row.select_one("td, .pi-data-value")
            if label and value:
                label_text = label.get_text(strip=True).lower()
                if any(kw in label_text for kw in ["reward", "payout", "pay", "money", "cash"]):
                    payout = parse_payout(value.get_text(strip=True))
                    if payout is not None:
                        return payout

        # Fallback: search article text for payout mentions
        article = soup.select_one("#mw-content-text")
        if article:
            text = article.get_text()
            lines = [l for l in text.split("\n") if "reward" in l.lower() or "payout" in l.lower()]
            for line in lines[:5]:
                payout = parse_payout(line)
                if payout and 100 <= payout <= 50_000_000:
                    return payout

        return None
    except Exception as e:
        print(f"  [warn] Failed to fetch {mission_url}: {e}")
        return None


def fetch_mission_list(session) -> list[dict]:
    """Scrape the GTA V missions index page for mission names and links."""
    try:
        resp = session.get(WIKI_MISSIONS_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[fetch_missions] Could not reach GTA Wiki: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    missions = []

    for link in soup.select("table.wikitable a[href*='/wiki/']"):
        title = link.get_text(strip=True)
        href = link.get("href", "")
        if not href or ":" in href or "#" in href:
            continue
        if len(title) < 3 or title.lower() in ("yes", "no", "hard", "easy"):
            continue
        full_url = f"https://gta.fandom.com{href}"
        missions.append({"title": title, "url": full_url})

    # Deduplicate by title
    seen = set()
    unique = []
    for m in missions:
        if m["title"] not in seen:
            seen.add(m["title"])
            unique.append(m)
    return unique


def title_to_id(title: str) -> str:
    """Convert mission title to a URL-safe ID."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def main():
    existing = load_existing(SEED_PATH)
    seed_missions = {m["id"]: m for m in existing.get("missions", [])}

    if requests is None or BeautifulSoup is None:
        print("[fetch_missions] Scraper deps missing — writing seed data as-is")
        write_json(SEED_PATH, existing)
        return

    session = requests.Session()
    print(f"[fetch_missions] Fetching mission list from GTA Wiki...")
    wiki_missions = fetch_mission_list(session)
    print(f"[fetch_missions] Found {len(wiki_missions)} missions on wiki")

    enriched = dict(seed_missions)  # start from seed

    for i, wm in enumerate(wiki_missions[:80]):  # cap at 80 to be polite
        mission_id = title_to_id(wm["title"])

        # Skip if we already have accurate data for this mission
        if mission_id in seed_missions and seed_missions[mission_id].get("payout") is not None:
            # Seed data takes precedence for known payouts
            continue

        print(f"  [{i+1}/{min(len(wiki_missions),80)}] Fetching: {wm['title']}")
        payout = fetch_mission_payout(session, wm["url"])

        if mission_id in enriched:
            if payout is not None:
                enriched[mission_id]["payout"] = payout
        else:
            enriched[mission_id] = {
                "id": mission_id,
                "title": wm["title"],
                "chapter": None,
                "protagonist": [],
                "payout": payout,
            }

        time.sleep(1.5)  # polite delay

    result = {
        "last_updated": now_iso(),
        "source": "GTA Wiki (Fandom) · community records · Rockstar Games",
        "note": "Story mission payouts at normal difficulty. Hard difficulty adds ~25%. Heists in heists.json.",
        "schema_version": "1.0",
        "missions": list(enriched.values()),
    }

    if has_changed(SEED_PATH, result):
        write_json(SEED_PATH, result)
        print(f"[fetch_missions] Updated {SEED_PATH} ({len(enriched)} missions)")
    else:
        print(f"[fetch_missions] No changes detected")


if __name__ == "__main__":
    main()
