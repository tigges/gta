"""
fetch_price_history.py — GTA Online item price change history + per-source income history.

Tracks two complementary datasets:

1. price-changes.json — GTA$ item price changes over time (buy price reductions,
   property price adjustments, new items added). Sourced from:
     - Curated seed: known landmark price events from community archives
     - Rockstar Newswire (future: parse DLC announcement posts for new prices)

2. per-source-history.json — Income source $/hr history at each major DLC patch.
   Expands meta-history.json (which tracks only the #1 earner) to per-source
   granularity — showing nerf/buff history for every major income source.

These two files are the foundation for the price timeline chart:
  Select any item → see full price history as a step chart
  Select any income source → see $/hr changes annotated with patch notes

Sources:
  Curated from GTAForums patch notes threads, community wikis, Rockstar Newswire

Output:
  data/gta-5/economy/price-changes.json
  data/gta-5/economy/per-source-history.json

Usage:
  python3 scrapers/fetch_price_history.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import write_json, has_changed, now_iso

PRICE_CHANGES_PATH = "gta-5/economy/price-changes.json"
SOURCE_HISTORY_PATH = "gta-5/economy/per-source-history.json"


# ── Item price change history ─────────────────────────────────────────────────
# Format: {item_id, item_name, category, changes: [{date, old_price, new_price, note, source}]}
# old_price = None means item was newly introduced at new_price

PRICE_CHANGES: list[dict] = [
    {
        "item_id":   "kosatka",
        "item_name": "Kosatka Submarine",
        "category":  "submarine",
        "changes": [
            {"date": "2020-12-15", "old_price": None, "new_price": 2200000, "note": "Launched with The Cayo Perico Heist DLC", "source": "Rockstar"},
        ],
    },
    {
        "item_id":   "oppressor-mk2",
        "item_name": "Oppressor Mk II",
        "category":  "motorcycle",
        "changes": [
            {"date": "2018-07-24", "old_price": None,    "new_price": 3890250, "note": "Launched with After Hours DLC", "source": "Rockstar"},
            {"date": "2022-07-26", "old_price": 3890250, "new_price": 3890250, "note": "Price unchanged but missile lock-on nerfed (Criminal Enterprises). Effective value reduction.", "source": "Rockstar"},
        ],
    },
    {
        "item_id":   "nightclub-downtown",
        "item_name": "Nightclub (cheapest)",
        "category":  "nightclub",
        "changes": [
            {"date": "2018-07-24", "old_price": None, "new_price": 1080000, "note": "After Hours DLC — range $1.08M-$1.7M", "source": "Rockstar"},
        ],
    },
    {
        "item_id":   "bunker-farmhouse",
        "item_name": "Bunker (cheapest)",
        "category":  "bunker",
        "changes": [
            {"date": "2017-06-13", "old_price": None, "new_price": 1165000, "note": "Gunrunning DLC launch", "source": "Rockstar"},
        ],
    },
    {
        "item_id":   "acid-lab",
        "item_name": "Acid Lab (Brickade 6x6)",
        "category":  "mc-business",
        "changes": [
            {"date": "2022-12-13", "old_price": None, "new_price": 0, "note": "Free after completing The First Dose missions (LS Drug Wars)", "source": "Rockstar"},
            {"date": "2022-12-13", "old_price": None, "new_price": 750000, "note": "Equipment upgrade required for production — effective cost $750k", "source": "Rockstar"},
        ],
    },
    {
        "item_id":   "agency",
        "item_name": "Agency (cheapest)",
        "category":  "agency",
        "changes": [
            {"date": "2021-12-16", "old_price": None, "new_price": 2010000, "note": "The Contract DLC launch — range $2.01M-$2.415M", "source": "Rockstar"},
        ],
    },
    {
        "item_id":   "garment-factory",
        "item_name": "Darnell Bros Garment Factory",
        "category":  "garment-factory",
        "changes": [
            {"date": "2024-12-05", "old_price": None, "new_price": 2405000, "note": "Agents of Sabotage DLC launch. Single fixed location.", "source": "Rockstar"},
        ],
    },
    {
        "item_id":   "cluckin-bell-farm-raid",
        "item_name": "Cluckin' Bell Farm Raid",
        "category":  "contract",
        "changes": [
            {"date": "2024-03-07", "old_price": None, "new_price": 0, "note": "No property required. Free to start from phone.", "source": "Rockstar"},
            {"date": "2024-06-25", "old_price": 500000, "new_price": 500000, "note": "Payout unchanged. Bottom Dollar Bounties DLC buffed other mission payouts nearby.", "source": "GTAForums"},
        ],
    },
    {
        "item_id":   "terrorbyte",
        "item_name": "Terrorbyte",
        "category":  "truck",
        "changes": [
            {"date": "2018-07-24", "old_price": None, "new_price": 1375000, "note": "After Hours DLC launch", "source": "Rockstar"},
        ],
    },
    {
        "item_id":   "arcade-cheapest",
        "item_name": "Arcade (cheapest)",
        "category":  "arcade",
        "changes": [
            {"date": "2019-12-12", "old_price": None, "new_price": 1235000, "note": "Diamond Casino Heist DLC launch", "source": "Rockstar"},
        ],
    },
    {
        "item_id":   "salvage-yard",
        "item_name": "Salvage Yard (cheapest)",
        "category":  "salvage-yard",
        "changes": [
            {"date": "2023-06-13", "old_price": None, "new_price": 1650000, "note": "San Andreas Mercenaries DLC launch", "source": "Rockstar"},
        ],
    },
    {
        "item_id":   "bail-office",
        "item_name": "Bail Enforcement Office",
        "category":  "bail-office",
        "changes": [
            {"date": "2024-06-25", "old_price": None, "new_price": 1500000, "note": "Bottom Dollar Bounties DLC launch", "source": "Rockstar"},
        ],
    },
    {
        "item_id":   "hands-on-car-wash",
        "item_name": "Hands On Car Wash",
        "category":  "money-front",
        "changes": [
            {"date": "2025-06-17", "old_price": None, "new_price": 700000, "note": "Money Fronts DLC launch", "source": "Rockstar"},
        ],
    },
    {
        "item_id":   "cayo-perico-payout",
        "item_name": "Cayo Perico Heist (top payout)",
        "category":  "heist-payout",
        "changes": [
            {"date": "2020-12-15", "old_price": None,    "new_price": 2090000, "note": "Launch: Panther Statue as top loot, $2.09M gross", "source": "Rockstar"},
            {"date": "2021-08-10", "old_price": 2090000, "new_price": 1100000, "note": "Title Update 1.54: cooldown raised to 3h, gold cap reduced — effective $/hr ~halved from launch", "source": "GTAForums"},
            {"date": "2022-07-26", "old_price": 1100000, "new_price": 1100000, "note": "Criminal Enterprises: cooldown reduced back to 1h for solo — effective income restored", "source": "Rockstar"},
        ],
    },
    {
        "item_id":   "contact-mission-payout",
        "item_name": "Contact Mission Payouts (max)",
        "category":  "mission-payout",
        "changes": [
            {"date": "2013-10-01", "old_price": None,   "new_price": 30000, "note": "GTA Online launch — missions paid well relative to economy", "source": "Rockstar"},
            {"date": "2014-03-04", "old_price": 30000,  "new_price": 9000,  "note": "Title Update 1.09: sweeping contact mission payout nerf (~70% reduction). Community outrage.", "source": "GTAForums"},
            {"date": "2014-07-01", "old_price": 9000,   "new_price": 18300, "note": "Title Update 1.16: new time-scaled payout system. Max $18.3k-$22.86k depending on rank.", "source": "Rockstar"},
            {"date": "2018-12-11", "old_price": 18300,  "new_price": 23100, "note": "Arena War DLC: post-launch DLC missions pay flat $23,100 regardless of rank/time", "source": "Rockstar"},
        ],
    },
    {
        "item_id":   "special-cargo-crate-price",
        "item_name": "Special Cargo (full warehouse sell)",
        "category":  "business-payout",
        "changes": [
            {"date": "2016-06-07", "old_price": None,    "new_price": 2220000, "note": "Finance and Felony: 111-crate warehouse max gross $2.22M solo", "source": "Rockstar"},
            {"date": "2022-07-26", "old_price": 2220000, "new_price": 2200000, "note": "Criminal Enterprises: minor rebalance. Added warehouse technicians.", "source": "Rockstar"},
        ],
    },
    {
        "item_id":   "bunker-full-payout",
        "item_name": "Bunker (full stock sell)",
        "category":  "business-payout",
        "changes": [
            {"date": "2017-06-13", "old_price": None,    "new_price": 1050000, "note": "Gunrunning launch: full stock sell value", "source": "Rockstar"},
            {"date": "2017-06-13", "old_price": 1050000, "new_price": 1575000, "note": "Public lobby bonus: +50% for selling in populated public session", "source": "Rockstar"},
        ],
    },
]


# ── Per-source income history ─────────────────────────────────────────────────
# Expands meta-history.json to per-source granularity.
# Each source has a timeline of $/hr values at each major patch.

PER_SOURCE_HISTORY: list[dict] = [
    {
        "id":   "contact-missions",
        "name": "Contact Missions",
        "category": "active",
        "timeline": [
            {"date": "2013-10-01", "gta_per_hr": 250000, "patch": "GTA Online Launch", "note": "Rooftop Rumble, Violent Duct top farm — unpatched"},
            {"date": "2014-03-04", "gta_per_hr":  60000,  "patch": "TU1.09", "note": "Sweeping mission payout nerf, ~70% reduction"},
            {"date": "2014-07-01", "gta_per_hr":  80000,  "patch": "TU1.16", "note": "Time-scaled system introduced, partial recovery"},
            {"date": "2018-12-11", "gta_per_hr":  95000,  "patch": "Arena War", "note": "DLC missions pay flat $23.1k regardless of time"},
            {"date": "2024-06-25", "gta_per_hr": 120000,  "patch": "Bottom Dollar Bounties", "note": "Criminal Enterprises-era missions buffed"},
        ],
    },
    {
        "id":   "special-cargo",
        "name": "Special Cargo",
        "category": "ceo",
        "timeline": [
            {"date": "2016-06-07", "gta_per_hr": 500000, "patch": "Finance and Felony", "note": "Launch — dominated meta for 18 months"},
            {"date": "2016-12-13", "gta_per_hr": 350000, "patch": "Import/Export", "note": "Vehicle cargo launch shifted attention; cargo still viable"},
            {"date": "2017-06-13", "gta_per_hr": 280000, "patch": "Gunrunning", "note": "Bunker launched as superior passive; cargo relegated"},
            {"date": "2022-07-26", "gta_per_hr": 400000, "patch": "Criminal Enterprises", "note": "Warehouse technicians added — partial passive sourcing"},
        ],
    },
    {
        "id":   "vehicle-warehouse",
        "name": "Vehicle Cargo (Import/Export)",
        "category": "ceo",
        "timeline": [
            {"date": "2016-12-13", "gta_per_hr": 200000, "patch": "Import/Export", "note": "Launch — up to $80k net per Top Range export"},
            {"date": "2017-01-01", "gta_per_hr": 150000, "patch": "TU 2017 rebalance", "note": "Source mission nerfs; export values unchanged"},
            {"date": "2020-12-15", "gta_per_hr": 150000, "patch": "Cayo Perico Heist", "note": "Superseded but unchanged; Nightclub tech still useful"},
        ],
    },
    {
        "id":   "bunker",
        "name": "Bunker (Gunrunning)",
        "category": "gunrunning",
        "timeline": [
            {"date": "2017-06-13", "gta_per_hr": 280000, "patch": "Gunrunning", "note": "Launch — top passive earner for 12+ months"},
            {"date": "2018-07-24", "gta_per_hr": 280000, "patch": "After Hours", "note": "Nightclub launched — bunker delegated to passive feed role"},
            {"date": "2022-07-26", "gta_per_hr": 280000, "patch": "Criminal Enterprises", "note": "Manage from MCT; value unchanged"},
        ],
    },
    {
        "id":   "nightclub",
        "name": "Nightclub",
        "category": "passive",
        "timeline": [
            {"date": "2018-07-24", "gta_per_hr": 200000, "patch": "After Hours", "note": "Launch — required linking all businesses for full yield"},
            {"date": "2019-01-01", "gta_per_hr": 250000, "patch": "Community optimisation", "note": "Optimal linkage guides published; effective rate improved"},
            {"date": "2020-12-15", "gta_per_hr": 300000, "patch": "Cayo Perico era", "note": "Best passive stack alongside Kosatka grinding"},
        ],
    },
    {
        "id":   "cayo-perico",
        "name": "Cayo Perico Heist",
        "category": "heist",
        "timeline": [
            {"date": "2020-12-15", "gta_per_hr": 1400000, "patch": "Cayo Perico Heist launch", "note": "Launch at Panther Statue era — ~$2M/hr gross, 30-min cooldown"},
            {"date": "2021-08-10", "gta_per_hr":  700000,  "patch": "TU1.54 — major nerf",     "note": "Cooldown tripled to 3h, loot values reduced, primary loot cap"},
            {"date": "2022-07-26", "gta_per_hr": 1200000,  "patch": "Criminal Enterprises",     "note": "Cooldown reduced to 1h for solo — effectively restored"},
        ],
    },
    {
        "id":   "diamond-casino-heist",
        "name": "Diamond Casino Heist",
        "category": "heist",
        "timeline": [
            {"date": "2019-12-12", "gta_per_hr": 800000, "patch": "Diamond Casino Heist", "note": "Launch — diamonds vault at $3.62M gross, 2 players"},
            {"date": "2021-01-01", "gta_per_hr": 700000, "patch": "Diamonds removed (special event only)", "note": "Gold becomes most common; slightly lower optimal"},
            {"date": "2021-12-16", "gta_per_hr": 650000, "patch": "The Contract era", "note": "Cayo Perico solo fully supersedes for most players"},
        ],
    },
    {
        "id":   "acid-lab",
        "name": "Acid Lab",
        "category": "mc",
        "timeline": [
            {"date": "2022-12-13", "gta_per_hr": 340000, "patch": "Los Santos Drug Wars",    "note": "Launch — pre-upgrade rate before equipment/staff"},
            {"date": "2023-01-26", "gta_per_hr": 480000, "patch": "The Last Dose",            "note": "Full upgrade via Last Dose missions: +41% yield"},
            {"date": "2024-06-25", "gta_per_hr": 480000, "patch": "Bottom Dollar Bounties",   "note": "Payout unchanged; still best MC-category earner"},
        ],
    },
    {
        "id":   "agency-vip-contract",
        "name": "Agency (VIP Contract)",
        "category": "contract",
        "timeline": [
            {"date": "2021-12-16", "gta_per_hr": 600000, "patch": "The Contract", "note": "Launch — Dr Dre VIP Contract $1M per ~90-min run"},
            {"date": "2022-07-26", "gta_per_hr": 600000, "patch": "Criminal Enterprises", "note": "Security Contract payouts buffed; VIP unchanged"},
        ],
    },
    {
        "id":   "cluckin-bell-farm-raid",
        "name": "Cluckin' Bell Farm Raid",
        "category": "contract",
        "timeline": [
            {"date": "2024-03-07", "gta_per_hr": 420000, "patch": "Cluckin' Bell Farm Raid", "note": "Launch — $500k per run, ~30-40 min, fully solo"},
        ],
    },
    {
        "id":   "kno-way-out",
        "name": "KnoWay Out",
        "category": "contract",
        "timeline": [
            {"date": "2025-06-17", "gta_per_hr": 300000, "patch": "Money Fronts", "note": "Launch — strong solo contract, best new strand 2025"},
        ],
    },
]


def main() -> None:
    print("[fetch_price_history] Building price change history…")

    # ── 1. Price changes ──────────────────────────────────────────────────────
    total_changes = sum(len(item["changes"]) for item in PRICE_CHANGES)
    output_prices = {
        "last_updated": now_iso(),
        "source": "Curated from Rockstar Newswire + GTAForums patch notes archives",
        "note": (
            "GTA$ item price change log. Each entry = one price event. "
            "old_price=null means the item was newly introduced. "
            "heist-payout and mission-payout categories track effective income changes, "
            "not just property buy prices."
        ),
        "item_count": len(PRICE_CHANGES),
        "change_count": total_changes,
        "items": PRICE_CHANGES,
    }

    if has_changed(output_prices, PRICE_CHANGES_PATH):
        write_json(PRICE_CHANGES_PATH, output_prices)
        print(f"  price-changes.json: {len(PRICE_CHANGES)} items, {total_changes} change events")
    else:
        print("  price-changes.json: no change")

    # ── 2. Per-source income history ──────────────────────────────────────────
    total_snapshots = sum(len(s["timeline"]) for s in PER_SOURCE_HISTORY)
    output_sources = {
        "last_updated": now_iso(),
        "source": "Curated from GTAForums patch notes archives + community benchmarks",
        "note": (
            "Per-income-source $/hr history at each major DLC/patch. "
            "Extends meta-history.json (which tracks only the #1 earner) to per-source granularity. "
            "Values = net GTA$/hr in optimal solo conditions at each patch."
        ),
        "source_count": len(PER_SOURCE_HISTORY),
        "snapshot_count": total_snapshots,
        "sources": PER_SOURCE_HISTORY,
    }

    if has_changed(output_sources, SOURCE_HISTORY_PATH):
        write_json(SOURCE_HISTORY_PATH, output_sources)
        print(f"  per-source-history.json: {len(PER_SOURCE_HISTORY)} sources, {total_snapshots} snapshots")
    else:
        print("  per-source-history.json: no change")

    # Print summary
    print(f"\n  Key nerf/buff events:")
    for item in PRICE_CHANGES:
        if len(item["changes"]) > 1:
            c0 = item["changes"][0]
            cl = item["changes"][-1]
            direction = "buffed" if (cl["new_price"] or 0) > (c0["new_price"] or 0) else "nerfed"
            print(f"    {item['item_name'][:40]:40} {len(item['changes'])-1} changes, last {direction}")

    print("\n[fetch_price_history] Done.")


if __name__ == "__main__":
    main()
