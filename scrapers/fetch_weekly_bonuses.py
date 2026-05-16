#!/usr/bin/env python3
"""
fetch_weekly_bonuses.py — GTA Online weekly bonus events + weekly sales (Scraper B)

GTA Online weekly events post every Thursday. Rockstar announces:
  • 2×/3× GTA$ bonus multipliers on specific activities (bonuses[])
  • XX% off discounts on vehicles, properties, or categories (sales[])

Both are parsed from the same Newswire "This Week in GTA" article.

The sales[] array is new — it captures discount % and item description per week.
When item-catalogue.json is available, sale prices and vehicle IDs are resolved too.

Output: data/gta-5/economy/weekly-bonuses.json

Sources:
  https://www.rockstargames.com/newswire/tag/gtaonline (HTML fallback)
  Newswire RSS feed

Usage:
  python3 scrapers/fetch_weekly_bonuses.py
"""

import json
import re
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import write_json, has_changed, load_existing, now_iso

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[fetch_weekly_bonuses] requests/bs4 not available")
    requests = None
    BeautifulSoup = None

ROOT       = Path(__file__).parent.parent
DATA_DIR   = ROOT / "data"
OUTPUT_REL = "gta-5/economy/weekly-bonuses.json"

NEWSWIRE_RSS  = "https://www.rockstargames.com/newswire/feed.xml"
NEWSWIRE_URL  = "https://www.rockstargames.com/newswire/tag/gtaonline"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; gtavi-ai-bot/1.0; +https://gtavi.ai)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Activity → ID mapping for bonus multipliers ───────────────────────────────

ACTIVITY_KEYWORDS = {
    "cayo perico":        "cayo-perico",
    "acid lab":           "acid-lab",
    "nightclub":          "nightclub",
    "bunker":             "bunker",
    "casino heist":       "diamond-casino-heist",
    "auto shop":          "auto-shop",
    "agency":             "agency-vip-contract",
    "garment factory":    "garment-factory",
    "contact mission":    "contact-missions",
    "casino work":        "casino-missions",
    "vip work":           "vip-work",
    "headhunter":         "vip-work",
    "mc business":        "mc-cocaine",
    "cocaine lockup":     "mc-cocaine",
    "vehicle cargo":      "vehicle-warehouse",
    "special cargo":      "special-cargo",
    "hangar":             "hangar",
    "gunrunning":         "bunker",
    "salvage yard":       "salvage-yard",
    "security contract":  "security-contracts",
    "payphone":           "payphone-hits",
    "exotic export":      "exotic-exports",
}

# ── Sale extraction patterns ──────────────────────────────────────────────────

# Matches "40% off the Oppressor Mk II" / "30% off all Warstock vehicles" etc.
SALE_RE = re.compile(
    r'(\d+)%\s+off\s+(?:the\s+|all\s+|on\s+|on\s+all\s+)?(.{3,80}?)(?=,\s*\d+%|\.|\n|and\s+\d+%|$)',
    re.IGNORECASE,
)
# Also matches "[item] is XX% off"
SALE_RE2 = re.compile(
    r'([A-Z][A-Za-z0-9\s\-\']{3,60}?)\s+(?:is|are)\s+(\d+)%\s+off',
    re.IGNORECASE,
)

MULTIPLIER_RE = re.compile(r'(\d+)[xX×]\s*(gta\s*\$|bonus|cash|money|\$)', re.IGNORECASE)


def parse_multiplier(text: str) -> int:
    m = MULTIPLIER_RE.search(text)
    if m:
        val = int(m.group(1))
        return val if 1 < val <= 4 else 2
    if "triple" in text.lower():
        return 3
    if "double" in text.lower():
        return 2
    return 2


def clean_item_description(raw: str) -> str:
    """Strip trailing noise from a sale item description."""
    raw = raw.strip()
    # Remove trailing conjunctions/punctuation
    raw = re.sub(r'\s+(and|or|with|plus|for)$', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'[.,;:!]+$', '', raw)
    return raw.strip()


def load_item_catalogue() -> dict[str, dict]:
    """Load item-catalogue.json as a slug→item dict for sale price resolution."""
    path = DATA_DIR / "gta-5/economy/item-catalogue.json"
    if not path.exists():
        return {}
    with open(path) as f:
        data = json.load(f)
    return {item["id"]: item for item in data.get("items", [])}


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[''']", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def resolve_sale_item(description: str, catalogue: dict[str, dict]) -> dict | None:
    """Try to match a sale description to a catalogue item."""
    if not catalogue:
        return None
    # Try exact slug match
    slug = slugify(description)
    if slug in catalogue:
        return catalogue[slug]
    # Try partial name match
    desc_lower = description.lower()
    for item in catalogue.values():
        if item["name"].lower() in desc_lower or desc_lower in item["name"].lower():
            return item
    return None


def extract_sales(text: str, catalogue: dict[str, dict]) -> list[dict]:
    """Extract weekly sale/discount entries from article text."""
    sales: list[dict] = []
    seen_descriptions: set[str] = set()

    def add_sale(pct: int, description: str) -> None:
        desc = clean_item_description(description)
        if not desc or pct < 5 or pct > 80:
            return
        key = f"{pct}-{desc.lower()[:30]}"
        if key in seen_descriptions:
            return
        seen_descriptions.add(key)

        entry: dict = {
            "discount_pct":    pct,
            "item_description": desc[:80],
        }

        # Try to resolve to a catalogue item
        matched = resolve_sale_item(desc, catalogue)
        if matched:
            entry["item_id"]    = matched["id"]
            entry["item_name"]  = matched["name"]
            entry["base_price"] = matched["price"]
            if matched["price"]:
                entry["sale_price"] = round(matched["price"] * (1 - pct / 100))

        sales.append(entry)

    # Pattern 1: "XX% off [item]"
    for m in SALE_RE.finditer(text):
        add_sale(int(m.group(1)), m.group(2))

    # Pattern 2: "[item] is XX% off"
    for m in SALE_RE2.finditer(text):
        add_sale(int(m.group(2)), m.group(1))

    return sales


# ── Newswire fetch ────────────────────────────────────────────────────────────

def fetch_newswire_article(session: "requests.Session") -> tuple[str, str, str]:
    """
    Return (article_text, article_title, pub_date) for the latest weekly GTA Online post.
    Falls back through RSS → HTML listing → empty string.
    """
    # Try RSS
    for rss_url in [NEWSWIRE_RSS, NEWSWIRE_RSS.replace("feed.xml", "feed/")]:
        try:
            resp = session.get(rss_url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "xml")
                for item in soup.find_all("item")[:20]:
                    title_el = item.find("title")
                    if not title_el:
                        continue
                    title_text = title_el.get_text(strip=True)
                    if any(kw in title_text.lower() for kw in [
                        "this week", "weekly update", "bonuses", "week in gta"
                    ]):
                        link_el = item.find("link")
                        pub_el  = item.find("pubDate")
                        article_url = link_el.get_text(strip=True) if link_el else None
                        pub_date    = pub_el.get_text(strip=True) if pub_el else ""
                        if article_url:
                            try:
                                art = session.get(article_url, headers=HEADERS, timeout=15)
                                if art.status_code == 200:
                                    art_soup = BeautifulSoup(art.text, "html.parser")
                                    return art_soup.get_text(separator=" ", strip=True), title_text, pub_date
                            except Exception:
                                pass
                        return "", title_text, pub_date
        except Exception:
            pass

    # Fallback: scrape the Newswire tag page directly
    try:
        resp = session.get(NEWSWIRE_URL, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            # Find weekly event article links
            for a in soup.find_all("a", href=True):
                href = a["href"]
                link_text = a.get_text(strip=True).lower()
                if "week" in href.lower() or "week" in link_text:
                    full_url = href if href.startswith("http") else f"https://www.rockstargames.com{href}"
                    try:
                        art = session.get(full_url, headers=HEADERS, timeout=15)
                        if art.status_code == 200:
                            art_soup = BeautifulSoup(art.text, "html.parser")
                            return art_soup.get_text(separator=" ", strip=True), a.get_text(strip=True), ""
                    except Exception:
                        pass
    except Exception as e:
        print(f"[fetch_weekly_bonuses] Newswire HTML fallback failed: {e}")

    return "", "", ""


def fetch_weekly_data(session: "requests.Session", catalogue: dict[str, dict]) -> tuple[list[dict], list[dict], str, str]:
    """Return (bonuses, sales, title, pub_date)."""
    article_text, title, pub_date = fetch_newswire_article(session)

    if not article_text:
        print("[fetch_weekly_bonuses] Could not fetch Newswire article")
        return [], [], title, pub_date

    # ── Bonuses ──
    bonuses_map: dict[str, dict] = {}
    for keyword, activity_id in ACTIVITY_KEYWORDS.items():
        if keyword.lower() in article_text.lower():
            idx = article_text.lower().find(keyword.lower())
            context = article_text[max(0, idx - 120):idx + 200]
            multiplier = parse_multiplier(context)
            existing = bonuses_map.get(activity_id)
            if not existing or multiplier > existing["multiplier"]:
                bonuses_map[activity_id] = {
                    "activity_id":   activity_id,
                    "multiplier":    multiplier,
                    "keyword_found": keyword,
                    "source_title":  title,
                    "pub_date":      pub_date,
                }

    # ── Sales ──
    sales = extract_sales(article_text, catalogue)

    return list(bonuses_map.values()), sales, title, pub_date


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if requests is None or BeautifulSoup is None:
        print("[fetch_weekly_bonuses] deps missing — writing empty record")
        result = {
            "last_updated": now_iso(),
            "source":       "Rockstar Newswire (dependencies unavailable)",
            "week_start":   datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "bonuses":      [],
            "sales":        [],
            "note":         "pip install requests beautifulsoup4 lxml",
        }
        write_json(OUTPUT_REL, result)
        return

    catalogue = load_item_catalogue()
    if catalogue:
        print(f"[fetch_weekly_bonuses] Loaded {len(catalogue)} catalogue items for sale resolution")

    session = requests.Session()
    print("[fetch_weekly_bonuses] Fetching Newswire weekly post…")

    bonuses, sales, title, pub_date = fetch_weekly_data(session, catalogue)

    # If fetch failed, preserve existing data rather than overwriting with empty
    if not bonuses and not sales:
        existing = load_existing(OUTPUT_REL)
        if existing.get("bonuses") or existing.get("sales"):
            print("[fetch_weekly_bonuses] Fetch failed — preserving existing data")
            return

    print(f"[fetch_weekly_bonuses] Bonuses: {len(bonuses)}  |  Sales: {len(sales)}")
    for b in bonuses:
        print(f"  bonus: {b['activity_id']} × {b['multiplier']}")
    for s in sales:
        resolved = f" → {s.get('item_name','?')} ${s.get('sale_price',0):,}" if "sale_price" in s else ""
        print(f"  sale:  -{s['discount_pct']}% {s['item_description'][:40]}{resolved}")

    result = {
        "last_updated": now_iso(),
        "source":       "Rockstar Newswire",
        "week_start":   datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "note":         "Updated every Thursday. Multipliers apply to net_profit_per_hr in IncomeAdviser. Sales[] resolved against item-catalogue.json.",
        "bonuses":      bonuses,
        "sales":        sales,
        "article_title": title,
    }

    if has_changed(result, OUTPUT_REL):
        write_json(OUTPUT_REL, result)
        print(f"[fetch_weekly_bonuses] ✓ Updated")
    else:
        print(f"[fetch_weekly_bonuses] No change")


if __name__ == "__main__":
    main()
