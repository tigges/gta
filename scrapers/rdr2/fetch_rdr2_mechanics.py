#!/usr/bin/env python3
"""
fetch_rdr2_mechanics.py — RDR2 mechanics scraper for GTA VI prediction inputs.

Enriches data/rdr2/mechanics/index.json with wiki-sourced documentation
for each tracked mechanic. Scrapes:
  - Honour system page (honour tiers, effects)
  - Weapon carry page (carry limits)
  - Wanted/law system page (star thresholds)

Run manually — not in nightly CI (RDR2 is a static reference).

Usage:
    python3 scrapers/rdr2/fetch_rdr2_mechanics.py

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
    log.warning("requests/beautifulsoup4 not installed — enrichment skipped")

RDR_WIKI_BASE = "https://reddead.fandom.com/wiki"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

OUT_PATH = "rdr2/mechanics/index.json"

# ── Mechanic enrichment metadata ──────────────────────────────────────────────
# Maps mechanic id → wiki page path + key detail fields to extract.
# The scraper pulls the intro paragraph from each wiki page as wiki_summary.

MECHANIC_WIKI_PAGES = {
    "greet-antagonize":      "Honor_(Red_Dead_Redemption_2)",
    "limited-weapon-inventory": "Weapons_in_Red_Dead_Redemption_2",
    "advanced-looting":      "Looting_(Red_Dead_Redemption_2)",
    "dynamic-wanted-system": "Wanted_Level_(Red_Dead_Redemption_2)",
    "honour-pricing":        "Honor_(Red_Dead_Redemption_2)",
    "wildlife-hunting":      "Hunting_(Red_Dead_Redemption_2)",
    "detective-mode":        "Eagle_Eye",
}

# ── Curated fallback enrichment ───────────────────────────────────────────────
# Full text paragraphs used if wiki is unavailable.

MECHANIC_ENRICHMENTS = {
    "greet-antagonize": {
        "wiki_page": f"{RDR_WIKI_BASE}/Honor_(Red_Dead_Redemption_2)",
        "wiki_summary": (
            "The Honor system in Red Dead Redemption 2 measures Arthur Morgan's "
            "moral standing, ranging from Dishonorable (−8) to Honorable (+8). "
            "Honour affects NPC dialogue, shop prices (±25%), mission availability, "
            "and the game's ending. Greet/antagonize interactions are the primary "
            "real-time honour adjustment mechanic."
        ),
        "honour_tiers": [
            {"tier": "Dishonorable",  "score": -8,  "price_effect": "Fence −25%; stores +10%"},
            {"tier": "Low",           "score": -4,  "price_effect": "Fence −10%; stores neutral"},
            {"tier": "Neutral",       "score":  0,  "price_effect": "No modifier"},
            {"tier": "Honorable",     "score":  4,  "price_effect": "Stores −10%"},
            {"tier": "Most Honorable","score":  8,  "price_effect": "Stores −25%"},
        ],
    },
    "limited-weapon-inventory": {
        "wiki_page": f"{RDR_WIKI_BASE}/Weapons_in_Red_Dead_Redemption_2",
        "wiki_summary": (
            "RDR2 limits Arthur to carrying 2 long guns (rifles/shotguns) and "
            "4 handguns simultaneously. Additional weapons are stored on the horse "
            "and accessed from the horse's side. This creates a supply/demand tension "
            "for tactical loadout decisions that GTA VI is reportedly inheriting."
        ),
        "carry_limits": {
            "handguns":           4,
            "long_guns":          2,
            "horse_storage":      "unlimited (all owned weapons)",
            "thrown_items":       "1 type equipped, stack in satchel",
        },
    },
    "advanced-looting": {
        "wiki_page": f"{RDR_WIKI_BASE}/Looting_(Red_Dead_Redemption_2)",
        "wiki_summary": (
            "Manual looting in RDR2 requires the player to hold a button and watch "
            "an animation to search bodies, open drawers, and check containers. "
            "Each loot action takes 2–5 real seconds. There is no instant-loot mechanic. "
            "This time-cost is a key design signal for GTA VI's expected loot system."
        ),
        "loot_sources": ["bodies", "drawers", "safes", "gloveboxes", "wardrobes", "lockboxes"],
        "avg_loot_time_seconds": 3,
        "typical_loot_rdr$": {"low": 0.10, "high": 25.00},
    },
    "dynamic-wanted-system": {
        "wiki_page": f"{RDR_WIKI_BASE}/Wanted_Level_(Red_Dead_Redemption_2)",
        "wiki_summary": (
            "RDR2's wanted system is witness-driven rather than detection-based. "
            "NPCs who witness a crime flee and alert law enforcement. Law arrives "
            "only after a witness reports. Wearing a mask prevents identification "
            "(bounty accrual) if no witness survives. Six wanted stars reintroduce "
            "military-grade army response."
        ),
        "star_thresholds": [
            {"stars": 1, "response": "Deputy",       "note": "Single witness report"},
            {"stars": 2, "response": "Sheriff posse", "note": "Active pursuit"},
            {"stars": 3, "response": "Bounty hunters","note": "Cross-county chase"},
            {"stars": 4, "response": "Pinkerton agents","note": "Interstate pursuit"},
            {"stars": 5, "response": "Army",          "note": "Military response"},
            {"stars": 6, "response": "Full military",  "note": "Rumoured GTA VI return; T2 trailer hint"},
        ],
        "mask_mechanic": "Wearing mask prevents bounty accumulation if no witness survives",
        "bounty_persistence": "Cross-session; cleared at sheriff's office (fee) or post office",
    },
    "wildlife-hunting": {
        "wiki_page": f"{RDR_WIKI_BASE}/Hunting_(Red_Dead_Redemption_2)",
        "wiki_summary": (
            "Hunting in RDR2 requires tracking animals using Eagle Eye, studying "
            "them, and using the correct weapon/ammo to achieve a perfect pelt. "
            "Disturbing an animal (wrong ammo, wrong approach) degrades pelt quality. "
            "Perfect pelts unlock exclusive Trapper clothing. "
            "The system is the most sophisticated hunting mechanic in any GTA-adjacent title."
        ),
        "quality_factors": ["weapon calibre", "ammo type", "hit location", "animal study"],
        "trapper_unlock": "Unique clothing sets (not available at standard shops)",
    },
    "detective-mode": {
        "wiki_page": f"{RDR_WIKI_BASE}/Eagle_Eye",
        "wiki_summary": (
            "Eagle Eye is RDR2's enhanced perception mode (hold R3/LS). "
            "It highlights animal tracks, herbs, collectibles, and threats in yellow/orange. "
            "Analogous to GTA V's heightened sense mechanic. "
            "GTA VI's reported 'threat detection' mechanic is likely an evolution of this."
        ),
        "activates_with": "R3/LS hold (controller)",
        "highlights":     ["tracks", "plants", "threats", "collectibles", "clues"],
    },
}


# ── Scraping helper ───────────────────────────────────────────────────────────

def _get_intro(wiki_path: str) -> str | None:
    """Fetch the first content paragraph from a wiki page."""
    if not SCRAPING_AVAILABLE:
        return None
    url = f"{RDR_WIKI_BASE}/{wiki_path}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            log.warning("HTTP %s for %s", resp.status_code, url)
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        content = soup.find("div", class_=lambda c: c and "mw-parser-output" in c)
        if not content:
            return None
        for p in content.find_all("p", recursive=False):
            text = p.get_text(" ", strip=True)
            if len(text) > 80:
                return text
    except Exception as exc:
        log.warning("Failed to fetch intro for %s: %s", wiki_path, exc)
    return None


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    log.info("fetch_rdr2_mechanics.py — starting")

    existing = load_existing(OUT_PATH)
    if not existing:
        log.error("No existing mechanics seed at data/%s — aborting", OUT_PATH)
        return

    mechanics = existing.get("mechanics", [])
    enriched_count = 0

    for mech in mechanics:
        mid = mech.get("id", "")
        if mid not in MECHANIC_ENRICHMENTS:
            continue

        enrichment = dict(MECHANIC_ENRICHMENTS[mid])

        # Try to pull a live intro paragraph from the wiki
        wiki_path = MECHANIC_WIKI_PAGES.get(mid)
        if wiki_path and SCRAPING_AVAILABLE:
            log.info("Fetching wiki intro for mechanic: %s", mid)
            live_summary = _get_intro(wiki_path)
            if live_summary:
                enrichment["wiki_summary"] = live_summary
                enrichment["wiki_summary_source"] = "scraped"
                log.info("  Got live summary (%d chars)", len(live_summary))
            else:
                enrichment["wiki_summary_source"] = "seed"
                log.info("  Using seed summary for %s", mid)
            time.sleep(1)
        else:
            enrichment["wiki_summary_source"] = "seed"

        mech.update(enrichment)
        enriched_count += 1

    payload = {
        **existing,
        "last_updated": now_iso(),
        "mechanics": mechanics,
        "enriched_count": enriched_count,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        log.info("Updated: data/%s (%d mechanics enriched)", OUT_PATH, enriched_count)
    else:
        log.info("No change: data/%s", OUT_PATH)

    log.info("fetch_rdr2_mechanics.py — done")


if __name__ == "__main__":
    main()
