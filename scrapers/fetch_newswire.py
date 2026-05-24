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
    # Strauss Zelnick / executive interview tracker
    # CEO interviews in financial/entertainment press contain material GTA VI hints
    # (pricing stance, release confidence, marketing timing) before EDGAR filings.
    {
        "id": "variety-gaming",
        "name": "Variety",
        "url": "https://variety.com/v/gaming/feed/",
        "tier": "press",
        "filter_gta": True,
    },
    {
        "id": "the-game-business",
        "name": "The Game Business",
        "url": "https://www.thegamebusiness.com/feed",
        "tier": "press",
        "filter_gta": True,
    },
    # Bloomberg — Zelnick gives Bloomberg interviews with material Take-Two / GTA VI
    # pricing and release hints. Filter strictly for GTA keywords.
    {
        "id": "bloomberg-tech",
        "name": "Bloomberg Technology",
        "url": "https://feeds.bloomberg.com/technology/news.rss",
        "tier": "press",
        "filter_gta": True,
    },
]

# SEC EDGAR Atom feed for Take-Two Interactive 8-K filings
# CIK 0000946581 = Take-Two Interactive Software Inc. (NASDAQ: TTWO)
# NOTE: CIK 0000945114 was Global Industrial Co (GIC) — wrong company.
EDGAR_8K_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar"
    "?action=getcompany&CIK=0000946581&type=8-K"
    "&dateb=&owner=include&count=10&search_text=&output=atom"
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
            desc_text  = (desc.get_text(strip=True) if desc else "")[:500]

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
                "summary":     _strip_html(desc_text)[:200],
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


GTAFORUMS_SEED = [
    {
        "source_id":    "gtaforums-vi",
        "source_name":  "GTAForums",
        "tier":         "community",
        "title":        "GTA VI — Official Speculation & Discussion Megathread",
        "url":          "https://gtaforums.com/topic/885289-official-gta-vi-speculation-discussion/",
        "published_at": "2024-01-01T00:00:00Z",
        "summary":      "The primary GTA VI speculation megathread on GTAForums — the longest-running and most comprehensive community discussion thread for Grand Theft Auto VI.",
    },
    {
        "source_id":    "gtaforums-vi",
        "source_name":  "GTAForums",
        "tier":         "community",
        "title":        "GTA VI — Leaked Footage & Development Analysis",
        "url":          "https://gtaforums.com/topic/887948-gta-vi-source-code-leak/",
        "published_at": "2024-01-01T00:00:00Z",
        "summary":      "GTAForums analysis thread covering the September 2022 development leak — 90 alpha clips confirmed authentic by Rockstar. Detailed breakdown of economy, map, and mechanics visible in footage.",
    },
]


def _strip_html(text: str) -> str:
    """Strip HTML tags and decode HTML entities from a string."""
    if not text:
        return ""
    clean = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s{2,}", " ", clean).strip()


def _edgar_title(summary_html: str, date_str: str) -> str:
    """Build a human-readable 8-K title from the filing date + disclosed Items."""
    # Map Item codes → short labels (Item 2.02 etc.)
    ITEM_LABELS: dict[str, str] = {
        "2.02": "Results of Operations",
        "7.01": "Reg FD Disclosure",
        "8.01": "Other Events",
        "9.01": "Financial Statements",
        "5.02": "Director/Officer Change",
        "5.07": "Security Holders Vote",
        "1.01": "Material Agreement",
        "2.01": "Asset Acquisition",
    }
    found = re.findall(r"Item\s+(\d+\.\d+)", summary_html)
    labels = [ITEM_LABELS.get(code, f"Item {code}") for code in dict.fromkeys(found)]
    label_str = " · ".join(labels[:2]) if labels else "Current Report"
    # Format date: "2026-05-05" → "May 2026"
    try:
        from datetime import date as _date
        d = _date.fromisoformat(date_str[:10])
        month_str = d.strftime("%b %Y")
    except Exception:
        month_str = date_str[:7]
    return f"Take-Two 8-K · {month_str} — {label_str}"


def _get_ex99_url(index_url: str) -> str | None:
    """From an EDGAR filing index page, return the URL of the EX-99.1 press release."""
    try:
        import time
        time.sleep(0.25)
        resp = requests.get(index_url, headers={**EDGAR_HEADERS, "Accept": "text/html"}, timeout=15)
        if not resp.ok:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        for row in soup.find_all("tr"):
            row_text = row.get_text(" ", strip=True)
            # EX-99.1 = press release exhibit
            if "EX-99" in row_text or "99.1" in row_text:
                a = row.find("a", href=re.compile(r"\.htm$", re.I))
                if a:
                    href = a["href"]
                    href = re.sub(r"^/ix\?doc=", "", href)  # strip XBRL viewer prefix
                    return f"https://www.sec.gov{href}" if href.startswith("/") else href
        return None
    except Exception:
        return None


def _extract_pr_headline(doc_url: str) -> str:
    """Fetch an EDGAR press-release exhibit and extract the headline + first key figure."""
    try:
        import time, warnings
        from bs4 import XMLParsedAsHTMLWarning
        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
        time.sleep(0.25)
        resp = requests.get(doc_url, headers={**EDGAR_HEADERS, "Accept": "text/html"}, timeout=20)
        if not resp.ok:
            return ""
        soup = BeautifulSoup(resp.content[:80_000], "lxml")
        texts: list[str] = []
        for el in soup.find_all(string=True):
            t = re.sub(r"\s+", " ", el.strip())
            # Skip pure number/symbol lines and very short strings
            if len(t) > 30 and not re.match(r"^[\d\s,\.\$\%\(\)\-\/\*]+$", t):
                texts.append(t)
            if len(texts) >= 20:
                break
        headline = ""
        key_line = ""
        for t in texts:
            tl = t.lower()
            if not headline and (
                "reports" in tl or "announces" in tl or "take-two" in tl
                or "interactive" in tl or "fiscal" in tl
            ):
                headline = t
            if not key_line and (
                "billion" in tl or "million" in tl
                or "bookings" in tl or "revenue" in tl
                or "guidance" in tl
            ):
                key_line = t
            if headline and key_line:
                break
        if headline and key_line and headline != key_line:
            return f"{headline} — {key_line}"[:300]
        return (headline or key_line)[:300]
    except Exception:
        return ""


def fetch_edgar_8k() -> list[dict]:
    """Fetch recent Take-Two 8-K filings from SEC EDGAR Atom feed.
    For each filing, attempts to fetch the EX-99.1 press release to extract
    an actual headline + key figure. Falls back to Item-code descriptor."""
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

        for entry in entries[:5]:  # cap at 5 most recent filings
            link    = entry.find("link")
            updated = entry.find("updated") or entry.find("published")
            summary = entry.find("summary") or entry.find("content")

            link_href  = link.get("href", "") if link else ""
            date_text  = (updated.get_text(strip=True) if updated else "")[:10]
            summ_html  = summary.get_text(strip=True) if summary else ""

            if not date_text:
                continue

            # Attempt to extract a real headline from the EX-99.1 press release
            pr_summary = ""
            if link_href:
                ex_url = _get_ex99_url(link_href)
                if ex_url:
                    pr_summary = _extract_pr_headline(ex_url)

            results.append({
                "source_id":    "sec-edgar",
                "source_name":  "SEC EDGAR (Take-Two 8-K)",
                "tier":         "official",
                "title":        _edgar_title(summ_html, date_text),
                "url":          link_href,
                "published_at": f"{date_text}T00:00:00Z",
                "summary":      pr_summary or _strip_html(summ_html)[:200],
            })

        print(f"  ✓ SEC EDGAR 8-K: {len(results)} filings (press-release enriched)")
        return results

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
        items = fetch_rss(source)
        # GTAForums blocks server IPs (403) — fall back to curated seed
        if source["id"] == "gtaforums-vi" and not items:
            print(f"  ↩ GTAForums 403 — using curated seed ({len(GTAFORUMS_SEED)} items)")
            items = GTAFORUMS_SEED
        all_items.extend(items)

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
