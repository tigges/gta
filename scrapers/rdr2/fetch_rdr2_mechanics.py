#!/usr/bin/env python3
"""
fetch_rdr2_mechanics.py — RDR2 mechanics scraper for GTA VI prediction inputs.

Scrapes community sources and wiki for confirmed/documented RDR2 mechanics
that are reported to transfer to GTA VI. Populates:
  data/rdr2/mechanics/index.json

Tracked mechanics (from confirmed community reports):
  - Greet/antagonize NPC system
  - Limited weapon carry + vehicle storage
  - Advanced manual looting
  - Witness-based wanted system (6-star)
  - Honour/relationship system
  - Wildlife hunting and tracking
  - Detective/threat detection

Run manually — not in nightly CI.

Usage:
    python3 scrapers/rdr2/fetch_rdr2_mechanics.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils import write_json, now_iso

# ── Sources ───────────────────────────────────────────────────────────────────
RDR_WIKI_BASE   = "https://reddead.fandom.com/wiki"
GTAFORUMS_BASE  = "https://gtaforums.com"
REDDIT_GTA6     = "https://www.reddit.com/r/GTA6"

def fetch_honour_system_data() -> dict:
    """Scrape RDR2 wiki honour system documentation."""
    # TODO: /wiki/Honor_(Red_Dead_Redemption_2)
    raise NotImplementedError

def fetch_weapon_system_data() -> dict:
    """Scrape RDR2 weapon carry/storage system documentation."""
    # TODO: /wiki/Weapons_(Red_Dead_Redemption_2)#Carry_Capacity
    raise NotImplementedError

def fetch_wanted_system_data() -> dict:
    """Scrape RDR2 wanted/law system documentation."""
    # TODO: /wiki/Wanted_(Red_Dead_Redemption_2)
    raise NotImplementedError

if __name__ == "__main__":
    print("fetch_rdr2_mechanics.py — RDR2 mechanics scraper")
    print("Status: STUB — implement scraping functions above before running")
    print()
    print("Target output: data/rdr2/mechanics/index.json")
    print("Current data: manually curated — see data/rdr2/mechanics/index.json")
