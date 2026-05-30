#!/usr/bin/env python3
"""
fetch_rdr2_economy.py — RDR2 economy data scraper.

Scrapes the Red Dead Wiki (reddead.fandom.com) for:
  - Shop prices by honour tier
  - Mission payouts (story + RDR Online roles)
  - Hunting / pelt values (Trapper, Butcher)
  - Fence prices (stolen goods, black market)

Output files:
  data/rdr2/economy/shop-prices.json
  data/rdr2/economy/hunting.json
  data/rdr2/economy/mission-payouts.json
  data/rdr2/economy/online-roles.json

Run manually — not in nightly CI (RDR2 is a static reference, not live data).

Usage:
    python3 scrapers/rdr2/fetch_rdr2_economy.py

Dependencies: requests, beautifulsoup4 (pip install requests beautifulsoup4)
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils import write_json, now_iso

# ── Wiki base URL ─────────────────────────────────────────────────────────────
RDR_WIKI_BASE = "https://reddead.fandom.com/wiki"

def fetch_shop_prices() -> dict:
    """Scrape General Store and Gunsmith price tables from RDR2 wiki."""
    # TODO: implement BeautifulSoup scraping of RDR2 wiki shop pages
    # Target pages:
    #   /wiki/General_Store_(Red_Dead_Redemption_2)
    #   /wiki/Gunsmith_(Red_Dead_Redemption_2)
    #   /wiki/Fence_(Red_Dead_Redemption_2)
    raise NotImplementedError("fetch_shop_prices: implement BeautifulSoup scraping")

def fetch_hunting_values() -> dict:
    """Scrape pelt and carcass values from RDR2 wiki."""
    # TODO: implement scraping of:
    #   /wiki/Compendium_(Red_Dead_Redemption_2) — animal entries with pelt values
    #   /wiki/Trapper_(Red_Dead_Redemption_2)
    raise NotImplementedError("fetch_hunting_values: implement scraping")

def fetch_mission_payouts() -> dict:
    """Scrape story mission and RDR Online role payouts."""
    # TODO: implement scraping of:
    #   /wiki/Missions_in_Red_Dead_Redemption_2 — payouts table
    #   /wiki/Trader — role income data
    #   /wiki/Collector — role income data
    #   /wiki/Naturalist — role income data
    raise NotImplementedError("fetch_mission_payouts: implement scraping")

if __name__ == "__main__":
    print("fetch_rdr2_economy.py — RDR2 economy scraper")
    print("Status: STUB — implement scraping functions above before running")
    print()
    print("Target output:")
    print("  data/rdr2/economy/shop-prices.json")
    print("  data/rdr2/economy/hunting.json")
    print("  data/rdr2/economy/mission-payouts.json")
    print("  data/rdr2/economy/online-roles.json")
    print()
    print("Wiki base:", RDR_WIKI_BASE)
    print("See function docstrings for target pages.")
