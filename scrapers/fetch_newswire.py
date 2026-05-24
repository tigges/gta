"""
Aggregate GTA VI intelligence from multiple RSS/press sources.

Sources (in priority order):
- Rockstar Newswire HTML scrape — official announcements
- SEC EDGAR Take-Two 8-K filings — material event disclosures (delay announcements)
- Rockstar Intel RSS — #1 credible specialist press
- GTAForums GTA VI subforum RSS — community megathreads, first-look leaks
- Kotaku GTA 6 tag RSS — broke Florida/Vice City story
- Eurogamer RSS — filtered for GTA content
- Insider Gaming RSS — leaked Take-Two data accurately

Each item tagged with: source, tier (official/press/community), timestamp.
"""

import re
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from utils import has_changed, now_iso, write_json

OUT_PATH = "feeds/newswire.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

GTA_KEYWORDS = [
    "gta", "grand theft auto", "rockstar", "leonida",
    "jason duval", "lucia caminos", "gta 6", "gta vi",
    "gta online", "gta v", "take-two", "ttwo",
]

SOURCES = [
    {
        "id": "rockstar-intel",
        "name": "Rockstar Intel",
        "url": "https://www.rockstarintel.com/feed",
        "tier": "press",
        "filter_gta": False,  # all content is GTA-related
    },
    {
        "id": "gtaforums-vi",
        "name": "GTAForums",
        "url": "https://gtaforums.com/forum/367-grand-theft-auto-vi/?rss",
        "tier": "community",
        "filter_gta": False,  # GTA VI subforum — all relevant
    },
    {
        "id": "kotaku-gta",
        "name": "Kotaku",
        "url": "https://kotaku.com/tag/grand-theft-auto-6/rss",
        "tier": "press",
        "filter_gta": False,
    },
    {
        "id": "eurogamer",
        "name": "Eurogamer",
        "url": "https://www.eurogamer.net/feed",
        "tier": "press",
        "filter_gta": True,
    },
    {
        "id": "insider-gaming",
        "name": "Insider Gaming",
        "url": "https://insider-gaming.com/feed/",
        "tier": "press",
        "filter_gta": True,
    },
]

# SEC EDGAR Atom feed for Take-Two Interactive 8-K filings
# CIK 0000945114 = Take-Two Interactive Software Inc.
EDGAR_8K_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar"
    "?action=getcompany&CIK=0000945114&type=8-K"
    "&dateb=&owner=include&count=20&search_text=&output=atom"
)
EDGAR_HEADERS = {
    "User-Agent": "GTAVI.AI research bot contact@gtavi.ai",
    "Accept": "application/atom+xml",
}


def parse_date(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return raw[:10] if raw else None


def is_gta_related(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in GTA_KEYWORDS)


def fetch_rss(source: dict) -> list[dict]:
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=20)
        if not resp.ok:
            print(f"  ✗ {source['name']}: HTTP {resp.status_code}")
            return []

        soup = BeautifulSoup(resp.text, "lxml-xml")
        items = soup.find_all("item")
        results = []

        for item in items:
            title = item.find("title")
            link  = item.find("link") or item.find("guid")
            pub   = item.find("pubDate") or item.find("dc:date") or item.find("published")
            desc  = item.find("description") or item.find("summary")

            title_text = title.get_text(strip=True) if title else ""
            link_text  = link.get_text(strip=True) if link else ""
            desc_text  = (desc.get_text(strip=True) if desc else "")[:300]

            if not title_text or not link_text:
                continue

            if source["filter_gta"] and not is_gta_related(title_text + " " + desc_text):
                continue

            results.append({
                "source_id":   source["id"],
                "source_name": source["name"],
                "tier":        source["tier"],
                "title":       title_text,
                "url":         link_text,
                "published_at": parse_date(pub.get_text(strip=True) if pub else None),
                "summary":     re.sub(r"<[^>]+>", "", desc_text).strip()[:200],
            })

        print(f"  ✓ {source['name']}: {len(results)} items")
        return results

    except Exception as e:
        print(f"  ✗ {source['name']}: {e}")
        return []


def fetch_rockstar_newswire() -> list[dict]:
    """Scrape the Rockstar Newswire HTML page directly — JS-rendered, limited data."""
    try:
        resp = requests.get(
            "https://www.rockstargames.com/newswire",
            headers=HEADERS, timeout=20
        )
        if not resp.ok:
            return []

        # The newswire page is largely client-rendered, but article links are in the HTML
        soup = BeautifulSoup(resp.text, "lxml")
        items = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/newswire/article/" not in href:
                continue
            text = a.get_text(strip=True)
            if len(text) < 10:
                continue
            full_url = f"https://www.rockstargames.com{href}" if href.startswith("/") else href
            items.append({
                "source_id":    "rockstar-newswire",
                "source_name":  "Rockstar Newswire",
                "tier":         "official",
                "title":        text,
                "url":          full_url,
                "published_at": None,
                "summary":      "",
                "img_url":      None,
            })

        # Deduplicate by URL
        seen: set[str] = set()
        unique = []
        for item in items:
            if item["url"] not in seen:
                seen.add(item["url"])
                unique.append(item)

        print(f"  ✓ Rockstar Newswire HTML: {len(unique)} articles found")
        return unique[:20]  # latest 20

    except Exception as e:
        print(f"  ✗ Rockstar Newswire HTML: {e}")
        return []


def fetch_edgar_8k() -> list[dict]:
    """Fetch recent Take-Two 8-K filings from SEC EDGAR Atom feed.
    8-Ks capture material events: delay announcements, date confirmations,
    earnings guidance changes — high-signal official news."""
    try:
        import time
        time.sleep(0.15)  # EDGAR rate limit — 10 req/s max
        resp = requests.get(EDGAR_8K_URL, headers=EDGAR_HEADERS, timeout=20)
        if not resp.ok:
            print(f"  ✗ SEC EDGAR 8-K: HTTP {resp.status_code}")
            return []

        soup = BeautifulSoup(resp.text, "lxml-xml")
        entries = soup.find_all("entry")
        results = []

        for entry in entries:
            title = entry.find("title")
            link  = entry.find("link")
            updated = entry.find("updated") or entry.find("published")
            summary = entry.find("summary") or entry.find("content")

            title_text = title.get_text(strip=True) if title else ""
            link_href  = link.get("href", "") if link else ""
            date_text  = updated.get_text(strip=True)[:10] if updated else None
            summ_text  = (summary.get_text(strip=True) if summary else "")[:200]

            if not title_text:
                continue

            results.append({
                "source_id":    "sec-edgar",
                "source_name":  "SEC EDGAR (Take-Two 8-K)",
                "tier":         "official",
                "title":        f"Take-Two 8-K: {title_text}",
                "url":          link_href,
                "published_at": f"{date_text}T00:00:00Z" if date_text else None,
                "summary":      summ_text,
            })

        print(f"  ✓ SEC EDGAR 8-K: {len(results)} filings")
        return results[:10]  # latest 10

    except Exception as e:
        print(f"  ✗ SEC EDGAR 8-K: {e}")
        return []


def main() -> None:
    print("Fetching intelligence feeds...")
    all_items: list[dict] = []

    # Official sources first
    all_items.extend(fetch_rockstar_newswire())
    all_items.extend(fetch_edgar_8k())

    # Press + community sources
    for source in SOURCES:
        all_items.extend(fetch_rss(source))

    # Deduplicate by URL
    seen: set[str] = set()
    unique = []
    for item in all_items:
        key = item["url"].rstrip("/").lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    # Sort: official first, then by date descending
    def sort_key(item: dict):
        tier_order = {"official": 0, "press": 1, "community": 2}
        date = item.get("published_at") or "1970-01-01"
        return (tier_order.get(item["tier"], 9), [-ord(c) for c in date])

    unique.sort(key=lambda x: (
        {"official": 0, "press": 1, "community": 2}.get(x["tier"], 9),
        -(ord(x["published_at"][0]) if x.get("published_at") else 0),
    ))

    # Sort by date properly
    def date_sort(item: dict) -> str:
        return item.get("published_at") or "1970-01-01"

    official = [i for i in unique if i["tier"] == "official"]
    press = sorted([i for i in unique if i["tier"] == "press"], key=date_sort, reverse=True)
    community = sorted([i for i in unique if i["tier"] == "community"], key=date_sort, reverse=True)
    unique = official + press + community

    print(f"  Total: {len(unique)} items ({len(official)} official, {len(press)} press, {len(community)} community)")

    payload = {
        "last_updated": now_iso(),
        "sources": [s["id"] for s in SOURCES] + ["rockstar-newswire"],
        "items": unique,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("Feed updated.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
