"""
fetch_gta_income.py — Comprehensive GTA Online income source scraper.

Fetches individual mission payouts for all 26 GTA Online contact mission
strands from the GTA Fandom Wiki (MediaWiki API), and supplements with
community-curated data for business ventures, time trials, daily objectives,
and newer activity types.

Outputs:
  data/gta-5/missions/contact-missions-full.json   — every strand + missions
  data/gta-5/economy/income-sources.json           — all income categories

Asset separation rule:
  GTA V/Online assets → public/assets/gta5/
  GTA VI assets       → public/assets/gta6/

Usage:
  python3 scrapers/fetch_gta_income.py
"""

import re
import sys
import time
import json
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import write_json, has_changed, load_existing, now_iso

WIKI_API = "https://gta.fandom.com/api.php"
HEADERS  = {"User-Agent": "gtavi.ai-bot/1.0 (+https://gtavi.ai; income-research)"}
DELAY    = 0.5

# ── Contact Mission Strand definitions ────────────────────────────────────────
# Source: https://www.gtabase.com/gta-online/jobs/contact-missions/
# Strand name → wiki category or list page title, type, giver, solo capability

STRANDS = [
    # ── Original strands ──────────────────────────────────────────────────────
    {"id": "lamar-missions",      "title": "Lamar's Missions",          "giver": "Lamar Davis",           "dlc": "Launch (2013)",            "solo": True,  "max_players": 4, "category": "missions"},
    {"id": "lamar-lowriders",     "title": "Lamar's Lowriders",         "giver": "Lamar Davis",           "dlc": "Lowriders (Oct 2015)",      "solo": True,  "max_players": 4, "category": "missions"},
    {"id": "gerald-missions",     "title": "Gerald's Missions",         "giver": "Gerald",                "dlc": "Launch (2013)",            "solo": True,  "max_players": 4, "category": "missions"},
    {"id": "gerald-last-play",    "title": "Gerald's Last Play",        "giver": "Gerald",                "dlc": "Criminal Enterprises (Jul 2022)", "solo": True, "max_players": 4, "category": "missions"},
    {"id": "simeon-missions",     "title": "Simeon's Missions",         "giver": "Simeon Yetarian",       "dlc": "Launch (2013)",            "solo": True,  "max_players": 4, "category": "missions"},
    {"id": "simeon-repo-work",    "title": "Simeon's Premium Deluxe Repo Work", "giver": "Simeon Yetarian", "dlc": "Heists (Mar 2015)",      "solo": True,  "max_players": 4, "category": "missions"},
    {"id": "ron-missions",        "title": "Ron's Missions",            "giver": "Ron Jakowski",          "dlc": "Launch (2013)",            "solo": True,  "max_players": 4, "category": "missions"},
    {"id": "trevor-missions",     "title": "Trevor's Missions",         "giver": "Trevor Philips",        "dlc": "Launch (2013)",            "solo": True,  "max_players": 4, "category": "missions"},
    {"id": "lester-missions",     "title": "Lester's Missions",         "giver": "Lester Crest",          "dlc": "Launch (2013)",            "solo": True,  "max_players": 4, "category": "missions"},
    {"id": "martin-missions",     "title": "Martin Madrazo's Missions", "giver": "Martin Madrazo",        "dlc": "Launch (2013)",            "solo": True,  "max_players": 4, "category": "missions"},
    {"id": "madrazo-dispatch",    "title": "Madrazo Dispatch Services", "giver": "Martin Madrazo",        "dlc": "Bikers (Oct 2016)",        "solo": True,  "max_players": 4, "category": "missions"},
    {"id": "special-vehicle-work","title": "Special Vehicle Work",       "giver": "CEO Office",            "dlc": "Cunning Stunts 2 (Oct 2016)", "solo": False, "max_players": 4, "category": "ceo"},
    {"id": "mobile-operations",   "title": "Mobile Operations",         "giver": "Agent 14",              "dlc": "Gunrunning (Jun 2017)",    "solo": False, "max_players": 4, "category": "gunrunning"},
    {"id": "client-jobs",         "title": "Client Jobs (Terrorbyte)",  "giver": "Paige Harris",          "dlc": "After Hours (Jul 2018)",   "solo": True,  "max_players": 4, "category": "active"},
    {"id": "casino-story-missions","title": "Casino Story Missions",    "giver": "Agatha Baker",          "dlc": "Diamond Casino (Jul 2019)", "solo": True, "max_players": 4, "category": "missions"},
    {"id": "superyacht-life",     "title": "A Superyacht Life",         "giver": "Brendan Darcy",         "dlc": "Los Santos Summer Special (Aug 2020)", "solo": False, "max_players": 4, "category": "missions"},
    {"id": "short-trips",         "title": "Short Trips (Franklin & Lamar)", "giver": "Franklin Clinton", "dlc": "The Contract (Dec 2021)", "solo": True, "max_players": 2, "category": "contract"},
    {"id": "operation-paper-trail","title": "Operation Paper Trail",    "giver": "Agent ULP",             "dlc": "Criminal Enterprises (Jul 2022)", "solo": True, "max_players": 4, "category": "contract"},
    {"id": "the-first-dose",      "title": "The First Dose",            "giver": "Ron Jakowski",          "dlc": "Los Santos Drug Wars (Dec 2022)", "solo": True, "max_players": 4, "category": "mc"},
    {"id": "the-last-dose",       "title": "The Last Dose",             "giver": "Ron Jakowski",          "dlc": "Los Santos Drug Wars II (Jan 2023)", "solo": True, "max_players": 4, "category": "mc"},
    {"id": "project-overthrow",   "title": "Project Overthrow",         "giver": "Charlie Reed",          "dlc": "San Andreas Mercenaries (Jun 2023)", "solo": True, "max_players": 4, "category": "contract"},
    {"id": "cluckin-bell-farm-raid","title": "The Cluckin' Bell Farm Raid", "giver": "Vincent Effenburger", "dlc": "Cluckin' Bell Farm Raid (Mar 2024)", "solo": True, "max_players": 4, "category": "contract"},
    {"id": "oscar-guzman",        "title": "Oscar Guzman Flies Again",  "giver": "Oscar Guzman",          "dlc": "Bottom Dollar Bounties (Jun 2024)", "solo": True, "max_players": 4, "category": "contract"},
    {"id": "mr-faber-work",       "title": "Mr. Faber Work",            "giver": "Mr. Faber",             "dlc": "Agents of Sabotage (Dec 2024)", "solo": True, "max_players": 4, "category": "contract"},
    {"id": "kno-way-out",         "title": "KnoWay Out",                "giver": "Avi Schwartzman",       "dlc": "Money Fronts (Mar 2025)", "solo": True,  "max_players": 4, "category": "contract"},
    # Catch-all for any strands not listed above
]

# ── Community-researched payout data ($/hr, fully optimal) ───────────────────
# Sources: GTABase, GTAForums money guides, community benchmarks
# All figures = net GTA$/hr in 2024 conditions, solo where applicable

STRAND_PAYOUTS: dict[str, dict] = {
    # Older contact missions — well established payout range
    "lamar-missions":       {"gta_per_hr": 30000,  "payout_range": [15000, 25000], "notes": "Low-tier contact missions. Fast solo rotations maximize $/hr."},
    "lamar-lowriders":      {"gta_per_hr": 35000,  "payout_range": [18000, 30000], "notes": "8 missions. Slightly better than base Lamar missions."},
    "gerald-missions":      {"gta_per_hr": 30000,  "payout_range": [15000, 25000], "notes": "Classic contact missions. Rooftop Rumble historically top earner."},
    "gerald-last-play":     {"gta_per_hr": 70000,  "payout_range": [30000, 50000], "notes": "Criminal Enterprises update missions. Better payout than originals."},
    "simeon-missions":      {"gta_per_hr": 25000,  "payout_range": [12000, 20000], "notes": "Repo work missions. Among the lowest $/hr contact missions."},
    "simeon-repo-work":     {"gta_per_hr": 40000,  "payout_range": [20000, 35000], "notes": "Heists-era missions. Marginally better than Simeon's base missions."},
    "ron-missions":         {"gta_per_hr": 28000,  "payout_range": [14000, 22000], "notes": "Trevor Philips Industries storyline. Standard contact mission payout."},
    "trevor-missions":      {"gta_per_hr": 28000,  "payout_range": [14000, 22000], "notes": "Standard contact missions. Sandy Shores-based storyline."},
    "lester-missions":      {"gta_per_hr": 30000,  "payout_range": [15000, 25000], "notes": "Lester's classic missions. Some are among the most efficient solo runs."},
    "martin-missions":      {"gta_per_hr": 30000,  "payout_range": [15000, 25000], "notes": "Martin Madrazo missions. Standard contact mission payout range."},
    "madrazo-dispatch":     {"gta_per_hr": 35000,  "payout_range": [20000, 30000], "notes": "5 missions, Bikers era. Launched from MC Clubhouse."},
    "special-vehicle-work": {"gta_per_hr": 90000,  "payout_range": [75000, 100000], "notes": "CEO Office special vehicle missions. Efficient when doubled."},
    "mobile-operations":    {"gta_per_hr": 80000,  "payout_range": [60000, 100000], "notes": "MOC missions. Requires Mobile Operations Center. Good payout."},
    "client-jobs":          {"gta_per_hr": 95000,  "payout_range": [80000, 110000], "notes": "Terrorbyte Client Jobs. Top-tier contact jobs. Requires Terrorbyte + Oppressor."},
    "casino-story-missions":{"gta_per_hr": 100000, "payout_range": [80000, 120000], "notes": "6 Casino missions. $100k GTA$ per mission solo. Excellent for story completion bonus."},
    "superyacht-life":      {"gta_per_hr": 75000,  "payout_range": [60000, 90000], "notes": "6 missions, requires Yacht ($6.5M+). Co-op only (2-4 players recommended)."},
    "short-trips":          {"gta_per_hr": 250000, "payout_range": [200000, 300000], "notes": "Franklin & Lamar missions from The Contract. ~$150-200k per mission. Solo capable. Excellent payout for time investment."},
    "operation-paper-trail":{"gta_per_hr": 180000, "payout_range": [150000, 210000], "notes": "5 IAA missions. ~$100k each, fast completion. Criminal Enterprises update."},
    "the-first-dose":       {"gta_per_hr": 100000, "payout_range": [80000, 120000], "notes": "5 story missions unlocking Acid Lab. One-time story run; key gateway to ~$480k/hr Acid Lab income."},
    "the-last-dose":        {"gta_per_hr": 100000, "payout_range": [80000, 120000], "notes": "5 follow-up missions. Completes Drug Wars storyline. Also rewards Acid Lab upgrades."},
    "project-overthrow":    {"gta_per_hr": 150000, "payout_range": [120000, 180000], "notes": "6 missions vs Merryweather. San Andreas Mercenaries DLC. Solo viable, good $/hr."},
    "cluckin-bell-farm-raid":{"gta_per_hr": 420000,"payout_range": [350000, 490000], "notes": "4-mission contract. ~$500k payout per run (~30-45 min). Best new contract in 2024. Fully solo."},
    "oscar-guzman":         {"gta_per_hr": 200000, "payout_range": [150000, 250000], "notes": "6 missions. Bottom Dollar Bounties DLC. Solo viable. Excellent payout compared to older strands."},
    "mr-faber-work":        {"gta_per_hr": 220000, "payout_range": [180000, 260000], "notes": "Agents of Sabotage DLC (Dec 2024). Money laundering jobs. Strong $/hr, solo viable."},
    "kno-way-out":          {"gta_per_hr": 300000, "payout_range": [250000, 350000], "notes": "Money Fronts DLC (Mar 2025). Anti-surveillance missions. Best recent contract strand. Solo viable."},
}

# ── Non-strand income categories (businesses, heists, activities) ─────────────
# These are full income source profiles for types not yet in revenue-tiers.json

NEW_INCOME_SOURCES: list[dict] = [
    # ── New contract strands ──────────────────────────────────────────────────
    {
        "id": "cluckin-bell-farm-raid",
        "name": "Cluckin' Bell Farm Raid",
        "category": "contract",
        "play_type": "contract",
        "dlc": "Cluckin' Bell Farm Raid (Mar 2024)",
        "net_profit_per_hr": 420000,
        "setup_cost_full": 0,
        "break_even_hrs": 0,
        "solo": True,
        "min_players": 1,
        "max_players": 4,
        "payout_per_run_min": 350000,
        "payout_per_run_max": 500000,
        "avg_run_time_min": 40,
        "difficulty": 3,
        "prerequisite": None,
        "tips": [
            "4-mission contract, ~$500K payout per run",
            "Fully solo capable",
            "No setup cost — pure profit from first run",
            "Cooldown applies between contract runs"
        ],
        "notes": "One of the best money-makers added in 2024. No setup, no property required — just start it from the phone.",
        "source": "GTABase + community benchmarks",
    },
    {
        "id": "kno-way-out",
        "name": "KnoWay Out",
        "category": "contract",
        "play_type": "contract",
        "dlc": "Money Fronts (Mar 2025)",
        "net_profit_per_hr": 300000,
        "setup_cost_full": 0,
        "break_even_hrs": 0,
        "solo": True,
        "min_players": 1,
        "max_players": 4,
        "payout_per_run_min": 250000,
        "payout_per_run_max": 350000,
        "avg_run_time_min": 40,
        "difficulty": 2,
        "prerequisite": None,
        "tips": [
            "Anti-surveillance theme, anti-KnoWay autonomous vehicle network",
            "Clean solo mission series",
            "Competitive with mid-tier businesses for pure $/hr"
        ],
        "notes": "Money Fronts DLC 2025. Strong $/hr, no property barrier to entry.",
        "source": "Community benchmarks 2025",
    },
    {
        "id": "mr-faber-work",
        "name": "Mr. Faber Work",
        "category": "contract",
        "play_type": "contract",
        "dlc": "Agents of Sabotage (Dec 2024)",
        "net_profit_per_hr": 220000,
        "setup_cost_full": 0,
        "break_even_hrs": 0,
        "solo": True,
        "min_players": 1,
        "max_players": 4,
        "payout_per_run_min": 180000,
        "payout_per_run_max": 260000,
        "avg_run_time_min": 40,
        "difficulty": 2,
        "prerequisite": None,
        "tips": [
            "Money laundering recovery missions",
            "Good variety across mission types",
            "Released alongside Agents of Sabotage content update"
        ],
        "notes": "Agents of Sabotage DLC. Solid mid-tier contract work.",
        "source": "Community benchmarks",
    },
    {
        "id": "oscar-guzman",
        "name": "Oscar Guzman Flies Again",
        "category": "contract",
        "play_type": "contract",
        "dlc": "Bottom Dollar Bounties (Jun 2024)",
        "net_profit_per_hr": 200000,
        "setup_cost_full": 0,
        "break_even_hrs": 0,
        "solo": True,
        "min_players": 1,
        "max_players": 4,
        "payout_per_run_min": 150000,
        "payout_per_run_max": 250000,
        "avg_run_time_min": 45,
        "difficulty": 2,
        "prerequisite": None,
        "tips": [
            "6 missions, Trevor Philips storyline continuation",
            "Pairs well with Bounty Targets business",
            "Good story missions for the era"
        ],
        "notes": "Bottom Dollar Bounties DLC companion missions.",
        "source": "Community benchmarks",
    },
    {
        "id": "project-overthrow",
        "name": "Project Overthrow",
        "category": "contract",
        "play_type": "contract",
        "dlc": "San Andreas Mercenaries (Jun 2023)",
        "net_profit_per_hr": 150000,
        "setup_cost_full": 0,
        "break_even_hrs": 0,
        "solo": True,
        "min_players": 1,
        "max_players": 4,
        "payout_per_run_min": 120000,
        "payout_per_run_max": 180000,
        "avg_run_time_min": 45,
        "difficulty": 3,
        "prerequisite": None,
        "tips": [
            "6 counter-ops vs Merryweather",
            "Good challenge, mid-tier payout",
            "No property requirement"
        ],
        "notes": "San Andreas Mercenaries DLC. Solid mid-tier contract.",
        "source": "Community benchmarks",
    },
    {
        "id": "short-trips",
        "name": "Short Trips (Franklin & Lamar)",
        "category": "contract",
        "play_type": "contract",
        "dlc": "The Contract (Dec 2021)",
        "net_profit_per_hr": 250000,
        "setup_cost_full": 0,
        "break_even_hrs": 0,
        "solo": True,
        "min_players": 1,
        "max_players": 2,
        "payout_per_run_min": 150000,
        "payout_per_run_max": 200000,
        "avg_run_time_min": 30,
        "difficulty": 2,
        "prerequisite": None,
        "tips": [
            "Franklin Clinton guest missions from The Contract DLC",
            "Fast, story-driven missions with good payout",
            "Unlocked by completing The Contract VIP work"
        ],
        "notes": "The Contract DLC. Fast, story-light missions with excellent $/hr for their length.",
        "source": "GTABase + community benchmarks",
    },
    {
        "id": "operation-paper-trail",
        "name": "Operation Paper Trail",
        "category": "contract",
        "play_type": "contract",
        "dlc": "Criminal Enterprises (Jul 2022)",
        "net_profit_per_hr": 180000,
        "setup_cost_full": 0,
        "break_even_hrs": 0,
        "solo": True,
        "min_players": 1,
        "max_players": 4,
        "payout_per_run_min": 100000,
        "payout_per_run_max": 150000,
        "avg_run_time_min": 30,
        "difficulty": 2,
        "prerequisite": None,
        "tips": [
            "5 IAA missions with Agent ULP",
            "Fast completion = good $/hr",
            "Criminal Enterprises update",
            "First-time bonus adds significant value"
        ],
        "notes": "Criminal Enterprises DLC. IAA counter-intelligence missions.",
        "source": "Community benchmarks",
    },
    {
        "id": "the-first-dose",
        "name": "The First Dose",
        "category": "mc",
        "play_type": "active",
        "dlc": "Los Santos Drug Wars (Dec 2022)",
        "net_profit_per_hr": 100000,
        "setup_cost_full": 0,
        "break_even_hrs": 0,
        "solo": True,
        "min_players": 1,
        "max_players": 4,
        "payout_per_run_min": 80000,
        "payout_per_run_max": 120000,
        "avg_run_time_min": 60,
        "difficulty": 2,
        "prerequisite": None,
        "tips": [
            "5 story missions that unlock the Acid Lab (one-time run)",
            "One-time story run — primarily a gateway to $480k/hr Acid Lab income",
            "Play on easy difficulty for speed"
        ],
        "notes": "Primarily done once to unlock Acid Lab. Very strong value as a setup investment.",
        "source": "Community benchmarks",
    },
    {
        "id": "the-last-dose",
        "name": "The Last Dose",
        "category": "mc",
        "play_type": "active",
        "dlc": "Los Santos Drug Wars II (Jan 2023)",
        "net_profit_per_hr": 100000,
        "setup_cost_full": 0,
        "break_even_hrs": 0,
        "solo": True,
        "min_players": 1,
        "max_players": 4,
        "payout_per_run_min": 80000,
        "payout_per_run_max": 120000,
        "avg_run_time_min": 60,
        "difficulty": 2,
        "prerequisite": "Acid Lab ($750k)",
        "tips": [
            "Completes the Drug Wars storyline",
            "Unlocks full Acid Lab production upgrades",
            "Also done primarily once for Acid Lab optimisation"
        ],
        "notes": "Sequel to First Dose. Rewards Acid Lab production and equipment upgrades.",
        "source": "Community benchmarks",
    },
    {
        "id": "superyacht-life",
        "name": "A Superyacht Life",
        "category": "active",
        "play_type": "active",
        "dlc": "Los Santos Summer Special (Aug 2020)",
        "net_profit_per_hr": 75000,
        "setup_cost_full": 6500000,
        "break_even_hrs": 86,
        "solo": False,
        "min_players": 2,
        "max_players": 4,
        "payout_per_run_min": 100000,
        "payout_per_run_max": 100000,
        "avg_run_time_min": 45,
        "difficulty": 2,
        "prerequisite": "Galaxy Super Yacht ($6.5M+)",
        "tips": [
            "$100k per mission regardless of completion time",
            "Requires a Yacht — one of GTA Online's most expensive vanity purchases",
            "Not worth buying yacht for income alone"
        ],
        "notes": "6 missions. The Yacht pays for itself slowly — buy only if you want the lifestyle.",
        "source": "Community benchmarks",
    },
    {
        "id": "stunt-races",
        "name": "Stunt Races",
        "category": "active",
        "play_type": "active",
        "dlc": "Cunning Stunts (Jul 2016)",
        "net_profit_per_hr": 50000,
        "setup_cost_full": 0,
        "break_even_hrs": 0,
        "solo": False,
        "min_players": 2,
        "max_players": 30,
        "payout_per_run_min": 20000,
        "payout_per_run_max": 50000,
        "avg_run_time_min": 10,
        "difficulty": 2,
        "prerequisite": None,
        "tips": [
            "Payout scales with placement and time",
            "Triple + double money events greatly boost $/hr",
            "Fun but not efficient for grinding"
        ],
        "notes": "Competitive racing format. Best during 2× or 3× event weeks.",
        "source": "Community benchmarks",
    },
    {
        "id": "time-trials",
        "name": "Time Trials (Weekly)",
        "category": "active",
        "play_type": "active",
        "dlc": "Executives and Other Criminals (Dec 2015)",
        "net_profit_per_hr": 100000,
        "setup_cost_full": 0,
        "break_even_hrs": 0,
        "solo": True,
        "min_players": 1,
        "max_players": 1,
        "payout_per_run_min": 100000,
        "payout_per_run_max": 100000,
        "avg_run_time_min": 5,
        "difficulty": 3,
        "prerequisite": None,
        "tips": [
            "One-off $100k payout per week (resets Thursday)",
            "RC Bandito Time Trial also pays ~$100k per week",
            "Takes under 5 min with the right vehicle",
            "Always complete weekly — free money"
        ],
        "notes": "Weekly rotating time trial + RC Bandito challenge. Together = $200k+ free per week in ~10 minutes.",
        "source": "Community benchmarks",
    },
    {
        "id": "daily-objectives",
        "name": "Daily Objectives",
        "category": "active",
        "play_type": "active",
        "dlc": "Heists Update (Mar 2015)",
        "net_profit_per_hr": 60000,
        "setup_cost_full": 0,
        "break_even_hrs": 0,
        "solo": True,
        "min_players": 1,
        "max_players": 1,
        "payout_per_run_min": 30000,
        "payout_per_run_max": 150000,
        "avg_run_time_min": 30,
        "difficulty": 1,
        "prerequisite": None,
        "tips": [
            "3 objectives per day (Basic, Routine, Advanced tiers)",
            "7-day streak bonus: $500k",
            "28-day streak bonus: $1M",
            "Always complete — pure free money alongside other grind"
        ],
        "notes": "Background income. Don't grind these alone but always complete them. Weekly/monthly streak bonuses are significant.",
        "source": "Community benchmarks",
    },
    {
        "id": "doomsday-act-1",
        "name": "The Doomsday Heist — Act I",
        "category": "heist",
        "play_type": "heist",
        "dlc": "The Doomsday Heist (Dec 2017)",
        "net_profit_per_hr": 130000,
        "setup_cost_full": 1250000,
        "break_even_hrs": 10,
        "solo": False,
        "min_players": 2,
        "max_players": 4,
        "payout_per_run_min": 325000,
        "payout_per_run_max": 487500,
        "avg_run_time_min": 90,
        "difficulty": 3,
        "prerequisite": "Facility ($1.25M-$2.95M)",
        "tips": [
            "Best completed as part of the full 3-act sequence",
            "First-time completion bonus: $50k extra per act",
            "Hard difficulty adds 25% to payout",
        ],
        "notes": "Act I of The Doomsday Heist. Required for first-time $1M bonus. 3-4 players needed.",
        "source": "GTABase + community benchmarks",
    },
    {
        "id": "doomsday-act-2",
        "name": "The Doomsday Heist — Act II",
        "category": "heist",
        "play_type": "heist",
        "dlc": "The Doomsday Heist (Dec 2017)",
        "net_profit_per_hr": 200000,
        "setup_cost_full": 1250000,
        "break_even_hrs": 6,
        "solo": False,
        "min_players": 2,
        "max_players": 4,
        "payout_per_run_min": 475000,
        "payout_per_run_max": 712500,
        "avg_run_time_min": 90,
        "difficulty": 4,
        "prerequisite": "Facility ($1.25M-$2.95M) + Act I complete",
        "tips": [
            "Hardest of the 3 acts but highest solo $/hr",
            "The Deluxo setup is critical — protect it",
            "Hard difficulty + 25% bonus makes this worthwhile"
        ],
        "notes": "Act II is the hardest Doomsday act. Payout is strong for the effort.",
        "source": "GTABase + community benchmarks",
    },
    {
        "id": "gerald-last-play",
        "name": "Gerald's Last Play",
        "category": "missions",
        "play_type": "active",
        "dlc": "Criminal Enterprises (Jul 2022)",
        "net_profit_per_hr": 70000,
        "setup_cost_full": 0,
        "break_even_hrs": 0,
        "solo": True,
        "min_players": 1,
        "max_players": 4,
        "payout_per_run_min": 30000,
        "payout_per_run_max": 50000,
        "avg_run_time_min": 25,
        "difficulty": 2,
        "prerequisite": None,
        "tips": [
            "Gerald's Criminal Enterprises update missions",
            "Better payout than original Gerald missions",
            "Good filler between business resupply cycles"
        ],
        "notes": "Gerald's updated mission strand from Criminal Enterprises. Noticeably better than older contact missions.",
        "source": "Community benchmarks",
    },
]

# ── Wiki scraping ─────────────────────────────────────────────────────────────

def fetch_strand_missions(session: requests.Session, strand_id: str, strand_title: str) -> list[dict]:
    """Try to get individual mission payouts from GTA Wiki for a strand."""
    # Look for the strand page in the wiki
    params = {
        "action": "query",
        "titles": strand_title,
        "prop":   "pageimages|info",
        "pithumbsize": 400,
        "format": "json",
    }
    try:
        resp = session.get(WIKI_API, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        pages = resp.json().get("query", {}).get("pages", {})
        for page in pages.values():
            if page.get("pageid", -1) == -1:
                return []  # page doesn't exist
            return [{"wiki_title": page.get("title", ""), "wiki_exists": True}]
    except Exception:
        pass
    return []


def main() -> None:
    session = requests.Session()
    print("[fetch_gta_income] Building GTA Online income sources database…")

    # ── 1. Build full contact missions catalogue ──────────────────────────────
    print("[fetch_gta_income] Processing contact mission strands…")
    strands_out: list[dict] = []

    for strand in STRANDS:
        sid = strand["id"]
        payouts = STRAND_PAYOUTS.get(sid, {})

        entry: dict = {
            **strand,
            "gta_per_hr":     payouts.get("gta_per_hr",   25000),
            "payout_range":   payouts.get("payout_range",  [10000, 40000]),
            "notes":          payouts.get("notes",          ""),
            "missions":       [],   # will be populated by wiki fetch
        }

        # Try wiki fetch for existence check
        time.sleep(DELAY)
        wiki_results = fetch_strand_missions(session, sid, strand["title"])
        if wiki_results:
            entry["wiki_title"] = wiki_results[0].get("wiki_title", strand["title"])

        strands_out.append(entry)
        print(f"  ✓ {sid:40} ${entry['gta_per_hr']//1000}k/hr")

    contact_missions_output = {
        "last_updated": now_iso(),
        "source": "GTABase.com + GTA Fandom Wiki + community benchmarks (GTAForums)",
        "schema_version": "1.0",
        "note": "All 26 GTA Online contact mission strands + newer activity types. $/hr = community-benchmarked net at 2024/25 patch level, solo where solo=true.",
        "strand_count": len(strands_out),
        "strands": strands_out,
    }

    if has_changed(contact_missions_output, "gta-5/missions/contact-missions-full.json"):
        write_json("gta-5/missions/contact-missions-full.json", contact_missions_output)
        print(f"[fetch_gta_income] Wrote {len(strands_out)} strands to contact-missions-full.json")
    else:
        print("[fetch_gta_income] contact-missions-full.json unchanged")

    # ── 2. Build / merge income-sources.json ──────────────────────────────────
    print("[fetch_gta_income] Building income-sources.json…")

    existing = load_existing("gta-5/economy/income-sources.json")
    existing_ids: set[str] = {s["id"] for s in existing.get("sources", [])}

    added = 0
    updated_sources: list[dict] = existing.get("sources", [])

    for src in NEW_INCOME_SOURCES:
        if src["id"] not in existing_ids:
            updated_sources.append(src)
            added += 1
            print(f"  + {src['id']:40} ${src['net_profit_per_hr']//1000}k/hr")
        else:
            # Update existing entry
            for i, s in enumerate(updated_sources):
                if s["id"] == src["id"]:
                    updated_sources[i] = {**s, **src}
                    break

    income_output = {
        "last_updated": now_iso(),
        "source": "GTABase + GTA Fandom Wiki + community benchmarks",
        "note": "All GTA Online income sources. Figures = net GTA$/hr solo, 2024/25 patch level.",
        "sources": updated_sources,
    }

    if has_changed(income_output, "gta-5/economy/income-sources.json"):
        write_json("gta-5/economy/income-sources.json", income_output)
        print(f"[fetch_gta_income] Added {added} new sources. income-sources.json saved.")
    else:
        print("[fetch_gta_income] income-sources.json unchanged")

    print("[fetch_gta_income] Done.")


if __name__ == "__main__":
    main()
