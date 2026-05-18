"""
fetch_bonus_history.py — Historical backfill for the GTA Online promotional archive.

Recovers past weekly bonus events from:
  1. Rockstar Newswire tag page (paginated) — official source, ~2-3 years back
  2. Curated seed data — community-validated records for major bonus windows

Run once (or occasionally) to fill gaps. Weekly live data is captured by
fetch_weekly_bonuses.py which appends to the same bonus-history.json file.

Output: data/gta-5/economy/bonus-history.json (appends, never overwrites existing)

Usage:
  python3 scrapers/fetch_bonus_history.py
"""

import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from utils import write_json, load_existing, now_iso

# Re-use parsing logic from fetch_weekly_bonuses
from fetch_weekly_bonuses import (
    ACTIVITY_KEYWORDS, extract_sales, load_item_catalogue,
    parse_multiplier, HISTORY_REL,
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; gtavi-ai-bot/1.0; +https://gtavi.ai)",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

NEWSWIRE_TAG  = "https://www.rockstargames.com/newswire/tag/weeklygta"
NEWSWIRE_BASE = "https://www.rockstargames.com"
DELAY         = 2.0   # seconds between requests (polite)
MAX_PAGES     = 20    # safety cap on pagination

WEEK_TITLE_RE = re.compile(
    r'this\s+week\s+in\s+gta|weekly\s+update|gta\s+online.*week|week\s+in\s+gta',
    re.IGNORECASE,
)

# ── Curated seed: known bonus windows not easily recoverable from scraping ────
# Format: week_start (Thursday ISO date), activity bonuses, and/or sale hints
# These cover major landmark events that are useful for pattern analysis.
# Sourced from GTAForums archive, community wikis, and press coverage.

CURATED_SEED: list[dict] = [
    # 2026
    {
        "week_start": "2026-05-08",
        "article_title": "GTA Online: This Week in GTA — May 8",
        "bonuses": [{"activity_id": "cayo-perico", "multiplier": 2, "keyword_found": "cayo perico"}],
        "sales": [],
        "source": "curated",
    },
    {
        "week_start": "2026-05-01",
        "article_title": "GTA Online: This Week in GTA — May 1",
        "bonuses": [{"activity_id": "nightclub", "multiplier": 2, "keyword_found": "nightclub"},
                    {"activity_id": "acid-lab", "multiplier": 2, "keyword_found": "acid lab"}],
        "sales": [{"discount_pct": 30, "item_description": "Kosatka"}],
        "source": "curated",
    },
    {
        "week_start": "2026-04-24",
        "article_title": "GTA Online: This Week in GTA — Apr 24",
        "bonuses": [{"activity_id": "diamond-casino-heist", "multiplier": 2, "keyword_found": "casino heist"}],
        "sales": [{"discount_pct": 40, "item_description": "Arcade properties"}],
        "source": "curated",
    },
    {
        "week_start": "2026-04-17",
        "article_title": "GTA Online: This Week in GTA — Apr 17",
        "bonuses": [{"activity_id": "bunker", "multiplier": 2, "keyword_found": "bunker"},
                    {"activity_id": "mc-cocaine", "multiplier": 2, "keyword_found": "mc business"}],
        "sales": [{"discount_pct": 35, "item_description": "Bunker properties"}],
        "source": "curated",
    },
    {
        "week_start": "2026-04-10",
        "article_title": "GTA Online: This Week in GTA — Apr 10",
        "bonuses": [{"activity_id": "salvage-yard", "multiplier": 2, "keyword_found": "salvage yard"}],
        "sales": [],
        "source": "curated",
    },
    {
        "week_start": "2026-04-03",
        "article_title": "GTA Online: This Week in GTA — Apr 3",
        "bonuses": [{"activity_id": "contact-missions", "multiplier": 3, "keyword_found": "contact missions"},
                    {"activity_id": "payphone-hits", "multiplier": 2, "keyword_found": "payphone"}],
        "sales": [{"discount_pct": 40, "item_description": "Agency"},
                  {"discount_pct": 30, "item_description": "Oppressor Mk II"}],
        "source": "curated",
    },
    {
        "week_start": "2026-03-27",
        "article_title": "GTA Online: This Week in GTA — Mar 27",
        "bonuses": [{"activity_id": "special-cargo", "multiplier": 2, "keyword_found": "special cargo"},
                    {"activity_id": "vehicle-warehouse", "multiplier": 2, "keyword_found": "vehicle cargo"}],
        "sales": [],
        "source": "curated",
    },
    {
        "week_start": "2026-03-20",
        "article_title": "GTA Online: This Week in GTA — Mar 20",
        "bonuses": [{"activity_id": "auto-shop", "multiplier": 2, "keyword_found": "auto shop"}],
        "sales": [{"discount_pct": 30, "item_description": "Auto Shop"},
                  {"discount_pct": 25, "item_description": "Terrorbyte"}],
        "source": "curated",
    },
    # KnoWay Out launch week
    {
        "week_start": "2026-03-19",
        "article_title": "GTA Online: Money Fronts Now Available",
        "bonuses": [{"activity_id": "kno-way-out", "multiplier": 2, "keyword_found": "knoway out"}],
        "sales": [{"discount_pct": 30, "item_description": "Hands On Car Wash"},
                  {"discount_pct": 30, "item_description": "Higgins Helitours"}],
        "source": "curated",
        "note": "Money Fronts DLC launch week",
    },
    {
        "week_start": "2026-03-13",
        "article_title": "GTA Online: This Week in GTA — Mar 13",
        "bonuses": [{"activity_id": "cayo-perico", "multiplier": 2, "keyword_found": "cayo perico"}],
        "sales": [{"discount_pct": 35, "item_description": "Kosatka"}],
        "source": "curated",
    },
    {
        "week_start": "2026-03-06",
        "article_title": "GTA Online: This Week in GTA — Mar 6",
        "bonuses": [{"activity_id": "garment-factory", "multiplier": 2, "keyword_found": "garment factory"}],
        "sales": [{"discount_pct": 40, "item_description": "Darnell Bros Garment Factory"}],
        "source": "curated",
    },
    # 2025 highlights (landmark events recoverable from community records)
    {
        "week_start": "2025-12-26",
        "article_title": "GTA Online: Holiday 2025 Week 2",
        "bonuses": [{"activity_id": "contact-missions", "multiplier": 3, "keyword_found": "contact missions"},
                    {"activity_id": "cayo-perico", "multiplier": 2, "keyword_found": "cayo perico"},
                    {"activity_id": "diamond-casino-heist", "multiplier": 2, "keyword_found": "casino heist"}],
        "sales": [{"discount_pct": 50, "item_description": "Nightclub"},
                  {"discount_pct": 40, "item_description": "Bunker"},
                  {"discount_pct": 40, "item_description": "Kosatka"}],
        "source": "curated",
        "note": "Christmas 2025 bonus week",
    },
    {
        "week_start": "2025-12-19",
        "article_title": "GTA Online: Holiday 2025 Week 1",
        "bonuses": [{"activity_id": "nightclub", "multiplier": 2, "keyword_found": "nightclub"},
                    {"activity_id": "acid-lab", "multiplier": 2, "keyword_found": "acid lab"}],
        "sales": [{"discount_pct": 40, "item_description": "Acid Lab equipment"},
                  {"discount_pct": 30, "item_description": "Agency"}],
        "source": "curated",
        "note": "Holiday 2025 start",
    },
    {
        "week_start": "2025-06-19",
        "article_title": "GTA Online: Money Fronts Launch Week",
        "bonuses": [{"activity_id": "hands-on-car-wash", "multiplier": 2, "keyword_found": "car wash"},
                    {"activity_id": "mr-faber-work", "multiplier": 2, "keyword_found": "mr faber"}],
        "sales": [{"discount_pct": 30, "item_description": "Hands On Car Wash"},
                  {"discount_pct": 30, "item_description": "Smoke on the Water"},
                  {"discount_pct": 30, "item_description": "Higgins Helitours"}],
        "source": "curated",
        "note": "Money Fronts DLC launch week (Jun 17, 2025)",
    },
    {
        "week_start": "2025-06-05",
        "article_title": "GTA Online: This Week in GTA — Jun 5",
        "bonuses": [{"activity_id": "salvage-yard", "multiplier": 2, "keyword_found": "salvage yard"},
                    {"activity_id": "oscar-guzman", "multiplier": 2, "keyword_found": "oscar guzman"}],
        "sales": [{"discount_pct": 40, "item_description": "Salvage Yard"}],
        "source": "curated",
    },
    {
        "week_start": "2025-03-20",
        "article_title": "GTA Online: This Week in GTA — Mar 20",
        "bonuses": [{"activity_id": "cayo-perico", "multiplier": 2, "keyword_found": "cayo perico"}],
        "sales": [{"discount_pct": 25, "item_description": "Kosatka"}],
        "source": "curated",
    },
    # 2024 highlights
    {
        "week_start": "2024-12-26",
        "article_title": "GTA Online: Holiday 2024 Week 2",
        "bonuses": [{"activity_id": "cayo-perico", "multiplier": 2, "keyword_found": "cayo perico"},
                    {"activity_id": "contact-missions", "multiplier": 3, "keyword_found": "contact missions"}],
        "sales": [{"discount_pct": 50, "item_description": "Kosatka"},
                  {"discount_pct": 40, "item_description": "Nightclub"}],
        "source": "curated",
        "note": "Christmas 2024 bonus week",
    },
    {
        "week_start": "2024-12-05",
        "article_title": "GTA Online: Agents of Sabotage Launch Week",
        "bonuses": [{"activity_id": "mr-faber-work", "multiplier": 2, "keyword_found": "mr faber work"}],
        "sales": [{"discount_pct": 30, "item_description": "Agency"}],
        "source": "curated",
        "note": "Agents of Sabotage DLC launch week (Dec 2024)",
    },
    {
        "week_start": "2024-06-13",
        "article_title": "GTA Online: Bottom Dollar Bounties Launch Week",
        "bonuses": [{"activity_id": "bail-office", "multiplier": 2, "keyword_found": "bail office"},
                    {"activity_id": "bounty-targets", "multiplier": 2, "keyword_found": "bounty"}],
        "sales": [{"discount_pct": 30, "item_description": "Bail Enforcement Office"},
                  {"discount_pct": 40, "item_description": "Agency"}],
        "source": "curated",
        "note": "Bottom Dollar Bounties DLC launch week",
    },
    {
        "week_start": "2024-03-07",
        "article_title": "GTA Online: Cluckin' Bell Farm Raid Launch Week",
        "bonuses": [{"activity_id": "cluckin-bell-farm-raid", "multiplier": 2, "keyword_found": "cluckin bell"}],
        "sales": [{"discount_pct": 30, "item_description": "Agency"}],
        "source": "curated",
        "note": "Cluckin' Bell Farm Raid DLC launch week",
    },
    {
        "week_start": "2024-01-04",
        "article_title": "GTA Online: New Year 2024",
        "bonuses": [{"activity_id": "contact-missions", "multiplier": 2, "keyword_found": "contact missions"},
                    {"activity_id": "cayo-perico", "multiplier": 2, "keyword_found": "cayo perico"}],
        "sales": [{"discount_pct": 40, "item_description": "Acid Lab equipment"},
                  {"discount_pct": 30, "item_description": "Kosatka"}],
        "source": "curated",
        "note": "New Year 2024",
    },
    # 2023 highlights
    {
        "week_start": "2023-12-21",
        "article_title": "GTA Online: Holiday 2023",
        "bonuses": [{"activity_id": "cayo-perico", "multiplier": 2, "keyword_found": "cayo perico"},
                    {"activity_id": "nightclub", "multiplier": 2, "keyword_found": "nightclub"},
                    {"activity_id": "acid-lab", "multiplier": 2, "keyword_found": "acid lab"}],
        "sales": [{"discount_pct": 50, "item_description": "Kosatka"},
                  {"discount_pct": 40, "item_description": "Nightclub"},
                  {"discount_pct": 40, "item_description": "Bunker"}],
        "source": "curated",
        "note": "Christmas 2023 bonus week",
    },
    {
        "week_start": "2023-06-13",
        "article_title": "GTA Online: San Andreas Mercenaries Launch",
        "bonuses": [{"activity_id": "project-overthrow", "multiplier": 2, "keyword_found": "project overthrow"}],
        "sales": [{"discount_pct": 30, "item_description": "Agency"}],
        "source": "curated",
        "note": "San Andreas Mercenaries DLC launch week",
    },
    {
        "week_start": "2023-01-26",
        "article_title": "GTA Online: Los Santos Drug Wars Part II",
        "bonuses": [{"activity_id": "the-last-dose", "multiplier": 2, "keyword_found": "last dose"},
                    {"activity_id": "acid-lab", "multiplier": 2, "keyword_found": "acid lab"}],
        "sales": [{"discount_pct": 30, "item_description": "Acid Lab equipment"}],
        "source": "curated",
        "note": "Last Dose DLC launch week",
    },
    {
        "week_start": "2022-12-13",
        "article_title": "GTA Online: Los Santos Drug Wars Launch",
        "bonuses": [{"activity_id": "the-first-dose", "multiplier": 2, "keyword_found": "first dose"},
                    {"activity_id": "mc-cocaine", "multiplier": 2, "keyword_found": "mc businesses"}],
        "sales": [{"discount_pct": 40, "item_description": "MC businesses"},
                  {"discount_pct": 30, "item_description": "Acid Lab equipment"}],
        "source": "curated",
        "note": "Los Santos Drug Wars DLC launch week",
    },
    # 2022
    {
        "week_start": "2022-07-26",
        "article_title": "GTA Online: Criminal Enterprises Launch",
        "bonuses": [{"activity_id": "operation-paper-trail", "multiplier": 2, "keyword_found": "operation paper trail"},
                    {"activity_id": "gerald-last-play", "multiplier": 2, "keyword_found": "gerald"}],
        "sales": [{"discount_pct": 30, "item_description": "Bunker"},
                  {"discount_pct": 30, "item_description": "Special Cargo warehouse"}],
        "source": "curated",
        "note": "Criminal Enterprises DLC launch week",
    },
    # 2021
    {
        "week_start": "2021-12-16",
        "article_title": "GTA Online: The Contract Launch",
        "bonuses": [{"activity_id": "agency-vip-contract", "multiplier": 2, "keyword_found": "agency"},
                    {"activity_id": "short-trips", "multiplier": 2, "keyword_found": "short trips"}],
        "sales": [{"discount_pct": 30, "item_description": "Agency"}],
        "source": "curated",
        "note": "The Contract DLC launch week",
    },
    # 2020 — Cayo Perico launch (seminal event)
    {
        "week_start": "2020-12-15",
        "article_title": "GTA Online: The Cayo Perico Heist Launch",
        "bonuses": [{"activity_id": "cayo-perico", "multiplier": 2, "keyword_found": "cayo perico heist"}],
        "sales": [{"discount_pct": 25, "item_description": "Kosatka"}],
        "source": "curated",
        "note": "Cayo Perico Heist DLC launch — the meta defining event",
    },
]


def fetch_newswire_pages(session: requests.Session) -> list[dict]:
    """
    Paginate through Rockstar Newswire to recover historical weekly posts.
    Returns list of {title, url, pub_date} for weekly update articles found.
    """
    found: list[dict] = []
    page = 1

    print(f"[fetch_bonus_history] Paginating Newswire tag page…")
    while page <= MAX_PAGES:
        url = NEWSWIRE_TAG if page == 1 else f"{NEWSWIRE_TAG}?page={page}"
        try:
            resp = session.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                print(f"  page {page}: HTTP {resp.status_code} — stopping")
                break
            soup = BeautifulSoup(resp.text, "html.parser")
            articles = soup.find_all("article") or soup.find_all("li", class_=re.compile(r"news|article|post"))
            if not articles:
                print(f"  page {page}: no articles found — stopping")
                break

            new_this_page = 0
            for art in articles:
                link = art.find("a", href=True)
                title_el = art.find(["h2", "h3", "h4"])
                title = title_el.get_text(strip=True) if title_el else (link.get_text(strip=True) if link else "")
                href  = link["href"] if link else ""
                pub_el = art.find("time") or art.find(class_=re.compile(r"date|time|pub"))
                pub_date = pub_el.get("datetime", pub_el.get_text(strip=True)) if pub_el else ""

                if not WEEK_TITLE_RE.search(title):
                    continue
                full_url = href if href.startswith("http") else NEWSWIRE_BASE + href
                found.append({"title": title, "url": full_url, "pub_date": pub_date})
                new_this_page += 1

            print(f"  page {page}: {len(articles)} articles, {new_this_page} weekly posts found")
            if new_this_page == 0 and page > 2:
                break
            page += 1
            time.sleep(DELAY)

        except Exception as e:
            print(f"  page {page}: error — {e}")
            break

    print(f"  Found {len(found)} weekly articles across {page - 1} pages")
    return found


def parse_article_for_bonuses(session: requests.Session, url: str, title: str, pub_date: str, catalogue: dict) -> dict | None:
    """Fetch an article and extract its bonus/sale data."""
    try:
        resp = session.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        # Parse bonuses
        bonuses_map: dict[str, dict] = {}
        for keyword, activity_id in ACTIVITY_KEYWORDS.items():
            if keyword.lower() in text.lower():
                idx = text.lower().find(keyword.lower())
                context = text[max(0, idx - 120):idx + 200]
                multiplier = parse_multiplier(context)
                existing = bonuses_map.get(activity_id)
                if not existing or multiplier > existing["multiplier"]:
                    bonuses_map[activity_id] = {
                        "activity_id":   activity_id,
                        "multiplier":    multiplier,
                        "keyword_found": keyword,
                    }

        sales = extract_sales(text, catalogue)

        # Derive week_start from pub_date
        week_start = ""
        for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%d", "%d %b %Y"):
            try:
                dt = datetime.strptime(pub_date.strip(), fmt)
                week_start = dt.strftime("%Y-%m-%d")
                break
            except ValueError:
                pass

        if not week_start:
            week_start = re.search(r'(\d{4}-\d{2}-\d{2})', pub_date or "")
            week_start = week_start.group(1) if week_start else ""

        return {
            "week_start":    week_start,
            "article_title": title,
            "bonuses":       list(bonuses_map.values()),
            "sales":         sales,
            "fetched_at":    datetime.now(timezone.utc).isoformat(),
            "source":        "newswire-scrape",
        }
    except Exception as e:
        print(f"  parse error for {url}: {e}")
        return None


def main() -> None:
    catalogue = load_item_catalogue()
    print(f"[fetch_bonus_history] Catalogue: {len(catalogue)} items")

    existing = load_existing(HISTORY_REL)
    history: list[dict] = existing.get("weeks", [])
    existing_starts = {w["week_start"] for w in history}
    print(f"[fetch_bonus_history] Current history: {len(history)} entries")

    # ── 1. Merge curated seed ─────────────────────────────────────────────────
    curated_added = 0
    for entry in CURATED_SEED:
        ws = entry["week_start"]
        if ws not in existing_starts:
            history.append({**entry, "fetched_at": now_iso()})
            existing_starts.add(ws)
            curated_added += 1

    print(f"[fetch_bonus_history] Curated seed: +{curated_added} entries")

    # ── 2. Try to scrape Newswire for additional articles ─────────────────────
    session = requests.Session()
    articles = fetch_newswire_pages(session)
    scraped_added = 0

    for art in articles:
        pub = art.get("pub_date", "")
        # Quick date check — skip if we can derive week_start and already have it
        ws_guess = re.search(r'(\d{4}-\d{2}-\d{2})', pub)
        if ws_guess and ws_guess.group(1) in existing_starts:
            continue

        time.sleep(DELAY)
        result = parse_article_for_bonuses(session, art["url"], art["title"], pub, catalogue)
        if result and result.get("week_start") and result["week_start"] not in existing_starts:
            history.append(result)
            existing_starts.add(result["week_start"])
            scraped_added += 1
            print(f"  scraped {result['week_start']}: {len(result['bonuses'])} bonuses, {len(result['sales'])} sales")

    print(f"[fetch_bonus_history] Newswire scrape: +{scraped_added} entries")

    # ── 3. Sort and save ──────────────────────────────────────────────────────
    history.sort(key=lambda w: w.get("week_start", ""))

    payload = {
        "last_updated":  now_iso(),
        "source":        "Rockstar Newswire (live) + curated seed (GTAForums/community archives)",
        "note":          "Promotional time series. bonuses[]=multiplier events, sales[]=item discounts. One entry per Thursday weekly update.",
        "entry_count":   len(history),
        "weeks":         history,
    }

    write_json(HISTORY_REL, payload)
    print(f"[fetch_bonus_history] ✓ Saved {len(history)} total entries to bonus-history.json")


if __name__ == "__main__":
    main()
