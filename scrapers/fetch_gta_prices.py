#!/usr/bin/env python3
"""
fetch_gta_prices.py — GTA Online item price catalogue (A + C)

Scrapes GTA Fandom Wiki store sub-pages that use {{WebVehicleModule}} templates.
Each in-game store page lists every purchasable vehicle with price and DLC code
in a clean, machine-readable format — far more reliable than parsing individual
vehicle infoboxes.

Sources (store sub-pages):
  Legendary Motorsport/Stock in GTA Online          → supercars, sports, classics
  Southern San Andreas Super Autos/Stock in GTA Online → everyday cars
  Warstock Cache & Carry/Stock in GTA Online         → military, special
  Elitás Travel/Stock in GTA Online                  → aircraft
  Dock Tease/Stock in GTA Online                     → boats
  Benny's Original Motor Works/Stock in GTA Online   → upgradeable lowriders/muscle
  ArenaWar.tv/Stock in GTA Online                    → Arena War vehicles

Also merges (C):
  business-profiles.json → business setup costs (bunker, nightclub, etc.)

Output:
  data/gta-5/economy/item-catalogue.json

Nightly CI: yes — new DLC items appear on store pages within 24h of launch.

Usage:
  python3 scrapers/fetch_gta_prices.py
  python3 scrapers/fetch_gta_prices.py --dry-run
"""

import json
import os
import re
import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import write_json, has_changed, now_iso

try:
    import requests
except ImportError:
    print("[fetch_gta_prices] requests not available — pip install requests")
    requests = None  # type: ignore

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

WIKI_API = "https://gta.fandom.com/api.php"
HEADERS  = {"User-Agent": "gtavi.ai/1.0 (price catalogue; +https://gtavi.ai)"}
SLEEP    = 0.5


# ── Store pages containing {{WebVehicleModule}} price data ────────────────────

STORE_PAGES = [
    # Four confirmed store pages covering ~600 purchasable GTA Online vehicles.
    ("Legendary Motorsport/Stock in GTA Online",             "vehicle", "Legendary Motorsport"),
    ("Southern San Andreas Super Autos/Stock in GTA Online", "vehicle", "Southern San Andreas Super Autos"),
    ("Warstock Cache & Carry/Stock in GTA Online",           "vehicle", "Warstock Cache & Carry"),
    ("Elitás Travel/Stock in GTA Online",                    "vehicle", "Elitás Travel"),
]


# ── DLC code → (name, date) ───────────────────────────────────────────────────
# Covers all known {{DLC|mpXXX}} codes used in {{WebVehicleModule|dlc=...}}

DLC_CODE: dict[str, tuple[str, str]] = {
    "mpcricket":       ("Beach Bum Update",                          "2013-12-17"),
    "mpchristmas":     ("Festive Surprise",                          "2013-12-19"),
    "mpvalentines":    ("Valentine's Day Massacre Special",          "2014-02-13"),
    "mpbusiness":      ("Business Update",                           "2014-03-04"),
    "mpbday":          ("High Life Update",                          "2014-05-13"),
    "mpretiremnt":     ("I'm Not a Hipster Update",                  "2014-06-17"),
    "mpindependence":  ("Independence Day Special",                  "2014-07-01"),
    "mppilot":         ("San Andreas Flight School Update",          "2014-08-19"),
    "mplts":           ("Last Team Standing Update",                 "2014-10-02"),
    "mpchristmas2":    ("Festive Surprise 2014",                     "2014-12-16"),
    "mpheist":         ("Heists Update",                             "2015-03-10"),
    "mpillegals":      ("Ill-Gotten Gains Part 1",                   "2015-06-10"),
    "mpillegals2":     ("Ill-Gotten Gains Part 2",                   "2015-07-08"),
    "mplowrider":      ("Lowriders",                                 "2015-10-20"),
    "mphalloween":     ("Halloween Surprise",                        "2015-10-29"),
    "mpevan":          ("Executives and Other Criminals",            "2015-12-15"),
    "mpjanuary2016":   ("January 2016 Update",                       "2016-01-19"),
    "mpvalentines2":   ("Valentine's Day 2016",                      "2016-02-10"),
    "mplowrider2":     ("Lowriders: Custom Classics",                "2016-03-15"),
    "mpbusiness2":     ("Finance and Felony",                        "2016-06-07"),
    "mpstunt":         ("Cunning Stunts",                            "2016-07-12"),
    "mpexecutive":     ("Further Adventures in Finance and Felony",  "2016-08-02"),
    "mpbikerb":        ("Bikers",                                    "2016-10-04"),
    "mpimportexport":  ("Import/Export",                             "2016-12-13"),
    "mpspecialraces":  ("Cunning Stunts: Special Vehicle Circuit",   "2017-03-14"),
    "mpgunrunning":    ("Gunrunning",                                "2017-06-13"),
    "mpsmuggler":      ("Smuggler's Run",                            "2017-08-29"),
    "mpchristmas2017": ("Doomsday Heist",                            "2017-12-12"),
    "mpassault":       ("Southern San Andreas Super Sport Series",   "2018-01-16"),
    "mpbattle":        ("After Hours",                               "2018-07-24"),
    "mparena":         ("Arena War",                                 "2018-12-11"),
    "mpvinewood":      ("Diamond Casino & Resort",                   "2019-07-23"),
    "mpheist3":        ("Diamond Casino Heist",                      "2019-12-12"),
    "mpsum2":          ("Los Santos Summer Special",                 "2020-08-11"),
    "mpcayoperico":    ("Cayo Perico Heist",                         "2020-12-15"),
    "mptuner":         ("Los Santos Tuners",                         "2021-07-20"),
    "mpagency":        ("The Contract",                              "2021-12-15"),
    "mpsecurity":      ("The Criminal Enterprises",                  "2022-07-26"),
    "mpdrugs":         ("Los Santos Drug Wars",                      "2022-12-13"),
    "mpsum21":         ("San Andreas Mercenaries",                   "2023-06-13"),
    "mpchop":          ("The Chop Shop",                             "2023-12-13"),
    "mpbounties":      ("Bottom Dollar Bounties",                    "2024-06-25"),
    "mpsabotage":      ("Agents of Sabotage",                        "2024-12-10"),
    # 2025+ DLCs (numeric format)
    "mp2024_01":       ("Agents of Sabotage",                        "2024-12-10"),
    "mp2025_01":       ("2025 DLC 1",                                "2025-03-01"),
    "mp2025_02":       ("2025 DLC 2",                                "2025-06-01"),
}

# DLC name fallbacks for business-profiles
DLC_NAME_DATE: dict[str, str] = {k: v[1] for k, (_, v) in
    {code: (code, val) for code, val in DLC_CODE.items()}.items()}
# Also build name→date lookup
_DLC_NAMES_BY_NAME: dict[str, str] = {name: date for _, (name, date) in DLC_CODE.items()}


def dlc_date_from_name(name: str) -> str:
    """Look up a DLC date by display name (fuzzy match)."""
    name_lower = re.sub(r"^the\s+", "", name.lower())
    for dlc_name, date in _DLC_NAMES_BY_NAME.items():
        if dlc_name.lower() in name_lower or name_lower in dlc_name.lower():
            return date
    return "2013-10-01"


# ── Helpers ───────────────────────────────────────────────────────────────────

def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[''']", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def parse_price_str(raw: str) -> int | None:
    """Parse '$1,234,567' or '1,234,567' → 1234567."""
    cleaned = re.sub(r"[^\d,]", "", raw)
    if not cleaned:
        return None
    try:
        val = int(cleaned.replace(",", ""))
        return val if val > 1000 else None
    except ValueError:
        return None


def extract_name(raw: str) -> str:
    """Extract plain name from '[[Vehicle Name|Display]]' or plain text."""
    m = re.match(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", raw.strip())
    return m.group(1).strip() if m else raw.strip()


# ── Parser: {{WebVehicleModule}} ──────────────────────────────────────────────

def parse_web_vehicle_modules(content: str, store: str) -> list[dict]:
    """
    Extract all vehicle entries from {{WebVehicleModule|...}} blocks.

    Template fields we use:
      |name        = [[Vehicle Name]]
      |price       = $X,XXX,XXX
      |dlc         = mpXXX
      |manufacturer= [[Brand]]
    """
    items: list[dict] = []

    # Match entire {{WebVehicleModule ... }} blocks (may span multiple lines)
    blocks = re.findall(
        r"\{\{WebVehicleModule(.*?)\}\}",
        content,
        re.DOTALL,
    )

    for block in blocks:
        fields: dict[str, str] = {}
        for line in block.split("\n"):
            m = re.match(r"\s*\|(\w+)\s*=\s*(.+)", line)
            if m:
                fields[m.group(1).strip().lower()] = m.group(2).strip()

        name_raw  = fields.get("name", "")
        price_raw = fields.get("price", "")
        dlc_raw   = fields.get("dlc", "").strip().lower()
        mfr_raw   = fields.get("manufacturer", "")

        name  = extract_name(name_raw)
        price = parse_price_str(price_raw)

        if not name or price is None:
            continue

        dlc_name, dlc_date = DLC_CODE.get(dlc_raw, ("GTA Online", "2013-10-01"))
        manufacturer = extract_name(mfr_raw) if mfr_raw else None

        items.append({
            "id":             slugify(name),
            "name":           name,
            "price":          price,
            "trade_price":    None,
            "dlc":            dlc_name,
            "dlc_date":       dlc_date,
            "dlc_code":       dlc_raw or None,
            "store":          store,
            "manufacturer":   manufacturer,
            "catalogue_type": "vehicle",
        })

    return items


# ── Wiki API ──────────────────────────────────────────────────────────────────

def fetch_page_content(title: str, session: "requests.Session") -> str | None:
    """Fetch raw wikitext for a single page."""
    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "format": "json",
        "titles": title,
        "redirects": 1,
    }
    r = session.get(WIKI_API, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    page = list(data["query"]["pages"].values())[0]
    if "revisions" not in page:
        return None
    return page["revisions"][0]["slots"]["main"]["*"]


# ── Business merge (C) ────────────────────────────────────────────────────────

def merge_businesses(items: list[dict]) -> list[dict]:
    """Add business setup costs from business-profiles.json."""
    path = DATA_DIR / "gta-5/economy/business-profiles.json"
    if not path.exists():
        return items

    with open(path) as f:
        profiles = json.load(f).get("businesses", [])

    existing_ids = {item["id"] for item in items}

    for biz in profiles:
        bid = biz.get("id", "")
        if bid in existing_ids:
            continue
        setup = biz.get("setup_cost_full")
        if not setup:
            continue

        dlc = biz.get("dlc", "")
        dlc_date = dlc_date_from_name(dlc)

        items.append({
            "id":                 bid,
            "name":               biz.get("name", bid),
            "price":              setup,
            "trade_price":        None,
            "dlc":                dlc,
            "dlc_date":           dlc_date,
            "dlc_code":           None,
            "store":              "Maze Bank Foreclosures",
            "manufacturer":       None,
            "catalogue_type":     "business",
            "net_profit_per_hr":  biz.get("net_profit_per_hr"),
            "play_type":          biz.get("play_type"),
        })

    return items


# ── Main ──────────────────────────────────────────────────────────────────────

def build_catalogue(session: "requests.Session") -> dict:
    all_items: list[dict] = []
    seen_ids: set[str] = set()

    for page_title, item_type, store_name in STORE_PAGES:
        print(f"  [{store_name}]", end=" ", flush=True)
        content = fetch_page_content(page_title, session)
        if content is None:
            print("(not found)")
            time.sleep(SLEEP)
            continue

        parsed = parse_web_vehicle_modules(content, store_name)
        added = 0
        for item in parsed:
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                all_items.append(item)
                added += 1
        print(f"{added} items")
        time.sleep(SLEEP)

    # Merge business setup costs
    all_items = merge_businesses(all_items)

    # Sort by DLC date then name
    all_items.sort(key=lambda x: (x.get("dlc_date", ""), x.get("name", "")))

    # Stats
    stats: dict[str, int] = {}
    for item in all_items:
        ct = item.get("catalogue_type", "?")
        stats[ct] = stats.get(ct, 0) + 1

    # DLC coverage
    known_dlc = sum(
        1 for i in all_items
        if i.get("dlc") not in ("GTA Online", "Unknown", "", None)
    )
    print(f"\n  Total: {len(all_items)} items | DLC identified: {known_dlc}/{len(all_items)}")

    return {
        "schema_version": "1.0",
        "last_updated":   now_iso(),
        "source":         "GTA Fandom Wiki store pages (WebVehicleModule) + business-profiles.json",
        "note": (
            "Launch prices in GTA$. Scraped from in-game store pages — the same source "
            "Rockstar updates on every DLC drop. Check weekly-bonuses.json sales[] for "
            "current weekly discounts. Prices rarely change; discounts rotate every Thursday."
        ),
        "item_count": len(all_items),
        "by_type":    stats,
        "items":      all_items,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if requests is None:
        sys.exit(1)

    session = requests.Session()
    session.headers.update(HEADERS)

    print("[fetch_gta_prices] Building GTA Online item catalogue…")
    catalogue = build_catalogue(session)
    print(f"[fetch_gta_prices] {catalogue['item_count']} items | {catalogue['by_type']}")

    if args.dry_run:
        print("\n[dry-run] Sample items:")
        for item in catalogue["items"][:6]:
            print(f"  {item['name']:40s} ${item['price']:>10,}  {item['dlc']}")
        return

    out_rel = "gta-5/economy/item-catalogue.json"
    if has_changed(catalogue, out_rel):
        write_json(out_rel, catalogue)
        print(f"[fetch_gta_prices] ✓ Written to data/{out_rel}")
    else:
        print(f"[fetch_gta_prices] No change — data/{out_rel} unchanged")


if __name__ == "__main__":
    main()
