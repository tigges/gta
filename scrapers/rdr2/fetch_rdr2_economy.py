#!/usr/bin/env python3
"""
fetch_rdr2_economy.py — RDR2 economy data scraper.

Scrapes the Red Dead Wiki (reddead.fandom.com) for:
  - Shop prices by honour tier (General Store, Gunsmith, Fence)
  - Hunting / pelt values (Trapper, Butcher)
  - Mission payouts (story + RDR Online roles)
  - Online role income rates

Output files:
  data/rdr2/economy/shop-prices.json   (enriched with full item catalogue)
  data/rdr2/economy/hunting.json       (enriched with full animal list)
  data/rdr2/economy/mission-payouts.json  (new)
  data/rdr2/economy/online-roles.json     (new)

Run manually — not in nightly CI (RDR2 is a static reference, not live data).

Usage:
    python3 scrapers/rdr2/fetch_rdr2_economy.py

Dependencies: requests, beautifulsoup4
"""

import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import write_json, load_existing, has_changed, now_iso

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

try:
    import requests
    from bs4 import BeautifulSoup
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False
    log.warning("requests/beautifulsoup4 not installed — using seed data only")

RDR_WIKI_BASE = "https://reddead.fandom.com/wiki"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Curated seed data (fallback if wiki is unreachable) ──────────────────────

SEED_SHOP_PRICES = {
    "schema_version": "1.1",
    "note": (
        "RDR2 shop prices vary by honour level (up to ±25%). "
        "High honour = discounts at general stores and gunsmiths. "
        "Low honour = discounts at fences (black market). "
        "This honour-based pricing mechanic is a strong GTA VI prediction input."
    ),
    "currency": "RDR$",
    "honour_price_modifier": {
        "very_high_honour":  -0.25,
        "high_honour":       -0.10,
        "neutral":            0.0,
        "low_honour":         0.10,
        "very_low_honour":   -0.25,
        "note": (
            "Low honour gives discounts at FENCES only, not regular stores. "
            "Very low honour = 25% discount at fence. "
            "Very high honour = 25% discount at stores."
        ),
    },
    "categories": [
        "provisions", "weapons", "ammo",
        "clothing", "horse", "tonics", "materials",
    ],
    "price_samples": [
        {"item": "Cattleman Revolver",       "category": "weapons",    "price_rdr$": 60.00,  "honour_modified": True,  "shop": "Gunsmith"},
        {"item": "Carbine Repeater",         "category": "weapons",    "price_rdr$": 135.00, "honour_modified": True,  "shop": "Gunsmith"},
        {"item": "Springfield Rifle",        "category": "weapons",    "price_rdr$": 120.00, "honour_modified": True,  "shop": "Gunsmith"},
        {"item": "Schofield Revolver",       "category": "weapons",    "price_rdr$": 192.00, "honour_modified": True,  "shop": "Gunsmith"},
        {"item": "Lancaster Repeater",       "category": "weapons",    "price_rdr$": 270.00, "honour_modified": True,  "shop": "Gunsmith"},
        {"item": "Bolt Action Rifle",        "category": "weapons",    "price_rdr$": 288.00, "honour_modified": True,  "shop": "Gunsmith"},
        {"item": "Canned Beans",             "category": "provisions", "price_rdr$": 0.50,   "honour_modified": True,  "shop": "General Store"},
        {"item": "Canned Peaches",           "category": "provisions", "price_rdr$": 0.50,   "honour_modified": True,  "shop": "General Store"},
        {"item": "Pork and Beans",           "category": "provisions", "price_rdr$": 0.50,   "honour_modified": True,  "shop": "General Store"},
        {"item": "Express Ammo (20 rounds)", "category": "ammo",       "price_rdr$": 1.50,   "honour_modified": True,  "shop": "Gunsmith"},
        {"item": "High Velocity Ammo (20)",  "category": "ammo",       "price_rdr$": 3.00,   "honour_modified": True,  "shop": "Gunsmith"},
        {"item": "Small Game Arrows (20)",   "category": "ammo",       "price_rdr$": 0.50,   "honour_modified": True,  "shop": "Gunsmith"},
        {"item": "Bitters (tonic)",          "category": "tonics",     "price_rdr$": 1.50,   "honour_modified": True,  "shop": "General Store"},
        {"item": "Snake Oil (tonic)",        "category": "tonics",     "price_rdr$": 2.50,   "honour_modified": True,  "shop": "General Store"},
        {"item": "Stolen watch (fence)",     "category": "materials",  "price_rdr$": 4.00,   "honour_modified": False, "shop": "Fence"},
        {"item": "Gold bar (fence)",         "category": "materials",  "price_rdr$": 500.00, "honour_modified": False, "shop": "Fence"},
        {"item": "Valuables (avg)",          "category": "materials",  "price_rdr$": 5.00,   "honour_modified": False, "shop": "Fence"},
    ],
    "gta_vi_implication": (
        "If GTA VI adopts an honour/reputation system, NPC shop prices will diverge "
        "by protagonist behaviour. Models for this are in data/gta-6/predictions.json "
        "(pred-rdr2-honour-pricing)."
    ),
    "sources": ["Red Dead Wiki", "Community price guides"],
    "day1_checklist": [
        "Verify honour modifier percentages against community benchmarks",
        "Cross-reference with GTA VI launch pricing when available",
    ],
}

SEED_HUNTING = {
    "schema_version": "1.1",
    "note": (
        "RDR2 hunting is the primary passive income source. "
        "Perfect pelts sell to the Trapper for crafting materials. "
        "Carcasses sell to the Butcher for RDR$. "
        "The income rate is low vs active missions but zero-risk and always available. "
        "GTA VI hunting system is reported to be modelled on this."
    ),
    "income_model": "passive-ambient",
    "gta_vi_analogue": "data/gta-6/economy/income-sources.json — hunting category",
    "pelt_quality_tiers": ["poor", "good", "perfect"],
    "animals": [
        {"animal": "White-tailed Deer",    "pelt_quality": "perfect", "payout_rdr$": 4.00,  "sell_to": "Trapper / Butcher",  "habitat": "Heartlands / Roanoke"},
        {"animal": "Bison",                "pelt_quality": "perfect", "payout_rdr$": 7.50,  "sell_to": "Trapper",            "habitat": "Great Plains"},
        {"animal": "Grizzly Bear",         "pelt_quality": "perfect", "payout_rdr$": 7.50,  "sell_to": "Trapper",            "habitat": "Grizzlies"},
        {"animal": "Black Bear",           "pelt_quality": "perfect", "payout_rdr$": 3.50,  "sell_to": "Trapper",            "habitat": "West Elizabeth"},
        {"animal": "Moose",                "pelt_quality": "perfect", "payout_rdr$": 9.00,  "sell_to": "Trapper",            "habitat": "Roanoke Ridge"},
        {"animal": "Elk",                  "pelt_quality": "perfect", "payout_rdr$": 6.50,  "sell_to": "Trapper / Butcher",  "habitat": "Ambarino"},
        {"animal": "Pronghorn",            "pelt_quality": "perfect", "payout_rdr$": 3.50,  "sell_to": "Trapper / Butcher",  "habitat": "New Austin"},
        {"animal": "Panther",              "pelt_quality": "perfect", "payout_rdr$": 5.50,  "sell_to": "Trapper",            "habitat": "Lemoyne (rare)"},
        {"animal": "Alligator",            "pelt_quality": "perfect", "payout_rdr$": 5.00,  "sell_to": "Trapper",            "habitat": "Bayou Nwa"},
        {"animal": "Rabbit",               "pelt_quality": "perfect", "payout_rdr$": 0.25,  "sell_to": "Butcher",            "habitat": "Widespread"},
        {"animal": "Beaver",               "pelt_quality": "perfect", "payout_rdr$": 1.75,  "sell_to": "Trapper",            "habitat": "Lakay / Roanoke"},
        {"animal": "Fox",                  "pelt_quality": "perfect", "payout_rdr$": 2.00,  "sell_to": "Trapper",            "habitat": "Widespread"},
        {"animal": "Wolf",                 "pelt_quality": "perfect", "payout_rdr$": 2.00,  "sell_to": "Trapper",            "habitat": "Ambarino / Grizzlies"},
        {"animal": "Coyote",               "pelt_quality": "perfect", "payout_rdr$": 1.50,  "sell_to": "Trapper",            "habitat": "Widespread"},
        {"animal": "Legendary Buck",       "pelt_quality": "legendary","payout_rdr$": 7.50, "sell_to": "Trapper",            "habitat": "Big Valley"},
        {"animal": "Legendary Elk",        "pelt_quality": "legendary","payout_rdr$": 17.50,"sell_to": "Trapper",            "habitat": "Ambarino"},
        {"animal": "Legendary Panther",    "pelt_quality": "legendary","payout_rdr$": 54.00,"sell_to": "Trapper",            "habitat": "Lemoyne"},
        {"animal": "Legendary Grizzly",    "pelt_quality": "legendary","payout_rdr$": 25.50,"sell_to": "Trapper",            "habitat": "Grizzlies"},
    ],
    "estimated_rdr$_per_hr": 20,
    "optimal_route_rdr$_per_hr": 35,
    "optimal_route_notes": "Heartlands deer + small game loop; sell at Valentine",
    "gta_vi_income_prediction": {
        "note": (
            "If GTA VI implements hunting, estimated GTA$/hr based on scaled RDR2 "
            "income rates and GTA VI's higher overall income ceiling. "
            "Likely a low-tier ambient income source."
        ),
        "estimated_gta$_per_hr_range": {"low": 15000, "high": 45000},
        "confidence": "predicted",
    },
    "sources": ["Red Dead Wiki hunting guides", "Community income benchmarks"],
}

SEED_MISSION_PAYOUTS = {
    "schema_version": "1.0",
    "note": (
        "RDR2 story mission payouts in RDR$. "
        "Values include the main reward; looting and exploration income is additive. "
        "Mission income is secondary to honour-system implications for GTA VI predictions."
    ),
    "currency": "RDR$",
    "missions": [
        {"chapter": 1, "mission": "Enter, Pursued by a Memory",      "payout_rdr$": 0},
        {"chapter": 2, "mission": "Polite Society, Valentine Style",  "payout_rdr$": 0},
        {"chapter": 2, "mission": "The First Shall Be Last",          "payout_rdr$": 0},
        {"chapter": 2, "mission": "Blessed are the Meek?",            "payout_rdr$": 125},
        {"chapter": 2, "mission": "Paying a Social Call",             "payout_rdr$": 0},
        {"chapter": 3, "mission": "The New South",                    "payout_rdr$": 0},
        {"chapter": 3, "mission": "Advertising, The New American Art","payout_rdr$": 50},
        {"chapter": 4, "mission": "The Gilded Cage",                  "payout_rdr$": 0},
        {"chapter": 4, "mission": "Banking, the Old American Art",    "payout_rdr$": 0},
        {"chapter": 5, "mission": "A Kind and Benevolent Despot",     "payout_rdr$": 0},
        {"chapter": 6, "mission": "My Last Boy",                      "payout_rdr$": 0},
        {"chapter": 6, "mission": "Red Dead Redemption",              "payout_rdr$": 0},
    ],
    "bounty_range_rdr$": {"low": 20, "high": 300},
    "bounty_note": "Bounties increase with crime; paid to clear at sheriff's office or post office",
    "ambient_crime_payouts": {
        "stagecoach_robbery":  {"low": 50,  "high": 300},
        "train_robbery":       {"low": 100, "high": 500},
        "bank_robbery":        {"low": 500, "high": 2000},
        "homestead_stash":     {"low": 20,  "high": 150},
    },
    "gta_vi_implication": (
        "GTA VI mission payouts are expected to scale significantly above GTA Online "
        "rates (Cayo Perico ~$1.7M/hr). RDR2's story mission structure — low story pay, "
        "high ambient crime income — may inform how Rockstar balances VI's open-world vs "
        "structured mission economy."
    ),
    "sources": ["Red Dead Wiki missions list", "Community income research"],
}

SEED_ONLINE_ROLES = {
    "schema_version": "1.0",
    "note": (
        "RDR Online roles are the primary end-game income structure. "
        "Each role has a passive income cycle analogous to GTA Online businesses. "
        "Used as a design reference for GTA VI's expected role/business system."
    ),
    "currency": "RDR$",
    "roles": [
        {
            "id": "trader",
            "name": "Trader",
            "unlock_cost_rdr$": 15,
            "unlock_method": "Butcher's Table (15 gold bars or Wilderness Outfitters catalogue)",
            "income_model": "sell-delivery",
            "max_capacity_materials": 100,
            "payout_full_delivery_rdr$": {"local": 625, "distant": 781},
            "cycle_time_hrs": 2.0,
            "gta$_per_hr_estimate": 300,
            "gta_vi_analogue": "Acid Lab / Bunker (supply → sell cycle)",
        },
        {
            "id": "collector",
            "name": "Collector",
            "unlock_cost_gold": 15,
            "unlock_method": "Madam Nazar (15 gold bars)",
            "income_model": "full-set-sell",
            "max_set_value_rdr$": 400,
            "sets_available": 9,
            "avg_sell_price_complete_set_rdr$": 250,
            "gta$_per_hr_estimate": 400,
            "gta_vi_analogue": "Treasure hunting / collectible economy (predicted for GTA VI)",
        },
        {
            "id": "bounty-hunter",
            "name": "Bounty Hunter",
            "unlock_cost_gold": 15,
            "unlock_method": "Bounty Board (15 gold bars)",
            "income_model": "per-mission",
            "payout_per_bounty_rdr$": {"low": 50, "high": 150},
            "legendary_bounty_rdr$": {"low": 100, "high": 300},
            "gta$_per_hr_estimate": 200,
            "gta_vi_analogue": "Bail bond / contact missions (expected GTA VI mechanic)",
        },
        {
            "id": "naturalist",
            "name": "Naturalist",
            "unlock_cost_gold": 25,
            "unlock_method": "Harriet Davenport (25 gold bars)",
            "income_model": "sample-sell",
            "payout_per_sample_rdr$": {"low": 10, "high": 25},
            "legendary_animal_sample_rdr$": 100,
            "gta$_per_hr_estimate": 150,
            "gta_vi_analogue": "Wildlife / ambient income (predicted for GTA VI's Leonida setting)",
        },
    ],
    "gold_bar_to_rdr$_market_rate": 0.05,
    "gold_note": (
        "Gold bars are RDR Online's premium currency (like Shark Cards in GTA Online). "
        "1 gold bar ≈ $0.05 USD to purchase. Role unlocks cost 15–25 gold bars."
    ),
    "gta_vi_implication": (
        "GTA VI is expected to replicate or evolve this role/specialisation model. "
        "Multiple roles creating distinct income streams mirrors GTA Online's business model. "
        "The premium-currency unlock barrier (gold bars → Shark Cards analogue) is the "
        "key monetisation vector Rockstar is likely to retain."
    ),
    "sources": ["Red Dead Wiki online roles", "Community income benchmarks"],
}


# ── Scraping helpers ──────────────────────────────────────────────────────────

def _get_soup(path: str, timeout: int = 15) -> "BeautifulSoup | None":
    """Fetch a wiki page and return a BeautifulSoup object, or None on failure."""
    if not SCRAPING_AVAILABLE:
        return None
    url = f"{RDR_WIKI_BASE}/{path}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            return BeautifulSoup(resp.text, "html.parser")
        log.warning("HTTP %s for %s", resp.status_code, url)
    except Exception as exc:
        log.warning("Failed to fetch %s: %s", url, exc)
    return None


def _parse_price(text: str) -> float | None:
    """Parse a price string like '$1.50' or '1,250.00' into a float."""
    import re
    text = text.strip().lstrip("$RDR").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        m = re.search(r"[\d.]+", text)
        return float(m.group()) if m else None


def _extract_wiki_tables(soup: "BeautifulSoup") -> list[list[list[str]]]:
    """Extract all wikitable rows as a list of [header_row, ...data_rows]."""
    tables = []
    for tbl in soup.find_all("table", class_=lambda c: c and "wikitable" in c):
        rows = []
        for tr in tbl.find_all("tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.find_all(["th", "td"])]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


# ── Scraper functions ─────────────────────────────────────────────────────────

def fetch_shop_prices() -> dict:
    """
    Enrich shop prices from RDR2 wiki.
    Tries to pull the Gunsmith and General Store item tables.
    Falls back to curated seed data on any error.
    """
    data = dict(SEED_SHOP_PRICES)
    data["last_updated"] = now_iso()
    data["data_source"] = "seed"

    soup = _get_soup("Gunsmith_(Red_Dead_Redemption_2)")
    if soup:
        tables = _extract_wiki_tables(soup)
        scraped_items = []
        for rows in tables:
            if len(rows) < 2:
                continue
            headers = [h.lower() for h in rows[0]]
            name_idx  = next((i for i, h in enumerate(headers) if "item" in h or "weapon" in h or "name" in h), None)
            price_idx = next((i for i, h in enumerate(headers) if "price" in h or "cost" in h or "$" in h), None)
            if name_idx is None or price_idx is None:
                continue
            for row in rows[1:]:
                if len(row) <= max(name_idx, price_idx):
                    continue
                price = _parse_price(row[price_idx])
                if price is None:
                    continue
                scraped_items.append({
                    "item":            row[name_idx],
                    "category":        "weapons",
                    "price_rdr$":      price,
                    "honour_modified": True,
                    "shop":            "Gunsmith",
                })
        if scraped_items:
            data["price_samples"] = scraped_items + [
                s for s in SEED_SHOP_PRICES["price_samples"]
                if s["shop"] in ("General Store", "Fence")
            ]
            data["data_source"] = "scraped+seed"
            log.info("Scraped %d gunsmith items from wiki", len(scraped_items))
        else:
            log.info("No gunsmith items scraped — using seed")

    return data


def fetch_hunting_values() -> dict:
    """
    Enrich hunting values from RDR2 wiki compendium.
    Falls back to curated seed data on any error.
    """
    data = dict(SEED_HUNTING)
    data["last_updated"] = now_iso()
    data["data_source"] = "seed"

    soup = _get_soup("Trapper_(Red_Dead_Redemption_2)")
    if soup:
        tables = _extract_wiki_tables(soup)
        scraped_animals = []
        for rows in tables:
            if len(rows) < 2:
                continue
            headers = [h.lower() for h in rows[0]]
            name_idx  = next((i for i, h in enumerate(headers) if "animal" in h or "pelt" in h or "name" in h), None)
            price_idx = next((i for i, h in enumerate(headers) if "price" in h or "value" in h or "$" in h), None)
            if name_idx is None or price_idx is None:
                continue
            for row in rows[1:]:
                if len(row) <= max(name_idx, price_idx):
                    continue
                price = _parse_price(row[price_idx])
                if price is None:
                    continue
                scraped_animals.append({
                    "animal":       row[name_idx],
                    "pelt_quality": "perfect",
                    "payout_rdr$":  price,
                    "sell_to":      "Trapper",
                    "habitat":      "—",
                })
        if scraped_animals:
            # Merge wiki data with seed (seed has habitat info wiki doesn't)
            seed_map = {a["animal"]: a for a in SEED_HUNTING["animals"]}
            for a in scraped_animals:
                if a["animal"] in seed_map:
                    a["habitat"] = seed_map[a["animal"]].get("habitat", "—")
            data["animals"] = scraped_animals
            data["data_source"] = "scraped+seed"
            log.info("Scraped %d animals from Trapper wiki page", len(scraped_animals))
        else:
            log.info("No animal data scraped — using seed")
    else:
        log.info("Trapper wiki page unavailable — using seed hunting data")

    return data


def fetch_mission_payouts() -> dict:
    """
    Build mission payouts file.
    Wiki mission pages vary significantly in structure; primarily uses curated seed.
    """
    data = dict(SEED_MISSION_PAYOUTS)
    data["last_updated"] = now_iso()
    data["data_source"] = "seed"
    log.info("Mission payouts: using curated seed (wiki mission tables are inconsistently structured)")
    return data


def fetch_online_roles() -> dict:
    """Build online roles income file from curated seed."""
    data = dict(SEED_ONLINE_ROLES)
    data["last_updated"] = now_iso()
    data["data_source"] = "seed"
    log.info("Online roles: using curated seed")
    return data


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    log.info("fetch_rdr2_economy.py — starting")

    outputs = [
        ("rdr2/economy/shop-prices.json",    fetch_shop_prices),
        ("rdr2/economy/hunting.json",         fetch_hunting_values),
        ("rdr2/economy/mission-payouts.json", fetch_mission_payouts),
        ("rdr2/economy/online-roles.json",    fetch_online_roles),
    ]

    for rel_path, fn in outputs:
        log.info("Fetching %s ...", rel_path)
        try:
            payload = fn()
            if has_changed(payload, rel_path):
                write_json(rel_path, payload)
                log.info("Updated: %s", rel_path)
            else:
                log.info("No change: %s", rel_path)
        except Exception as exc:
            log.error("Failed %s: %s", rel_path, exc)
        time.sleep(1)   # polite delay between wiki requests

    log.info("fetch_rdr2_economy.py — done")


if __name__ == "__main__":
    main()
