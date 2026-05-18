"""
fetch_vehicle_mods.py — GTA Online vehicle total upgrade cost database.

Captures the full upgrade cost for meta-relevant vehicles: the amount
required to take a vehicle from purchase to full competitive spec.

'Full upgrade cost' = all performance mods (engine, transmission, brakes,
suspension, turbo, armour) + weapons where applicable + trade price
conditions if any.

Why this matters:
  A vehicle's buy price alone is misleading. The Oppressor Mk2 costs $3.89M
  to buy but another $1.3M to fully upgrade — total cost of ownership $5.2M.
  Without this layer, break-even and ROI calculations are materially wrong.

Sources:
  Community-curated from GTABase.com, GTAForums upgrade cost guides,
  and Broughy1322 vehicle data.

Output:
  data/gta-5/economy/vehicle-mods.json

Usage:
  python3 scrapers/fetch_vehicle_mods.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import write_json, has_changed, now_iso

OUT_PATH = "gta-5/economy/vehicle-mods.json"

# ── Vehicle upgrade cost catalogue ────────────────────────────────────────────
# All figures sourced from GTABase / Broughy1322 / GTAForums upgrade guides.
# upgrade_cost = full performance spec (engine, trans, brakes, suspension, turbo)
# weapons_cost = weaponisation/missile/mg upgrades where applicable
# armour_cost = full armour upgrade
# total_cost_of_ownership = buy_price + upgrade_cost + weapons_cost + armour_cost
#
# buy_price: current standard price (not trade price)
# trade_price: if applicable, requires mission unlock
# trade_unlock: how to get trade price

VEHICLES: list[dict] = [
    # ── S-tier meta vehicles ──────────────────────────────────────────────────
    {
        "id": "oppressor-mk2",
        "name": "Oppressor Mk II",
        "class": "motorcycle",
        "buy_price": 3890250,
        "trade_price": 2925000,
        "trade_unlock": "Complete 5 Mobile Operations",
        "upgrade_cost": 495000,
        "weapons_cost": 775500,   # missiles + machine guns + countermeasures
        "armour_cost": 0,
        "total_cost_standard": 5160750,
        "total_cost_trade": 4195250,
        "notes": "Most used vehicle in GTA Online. Missiles are mandatory — budget $775k for weapons.",
        "source": "GTABase + community",
    },
    {
        "id": "mk2-workshop",
        "name": "Terrorbyte (Mk2 Workshop required)",
        "class": "facility",
        "buy_price": 1375000,
        "trade_price": None,
        "upgrade_cost": 580000,   # Mk2 workshop upgrade specifically
        "weapons_cost": 0,
        "armour_cost": 0,
        "total_cost_standard": 1955000,
        "notes": "Required to upgrade Oppressor Mk2 weapons. Must buy Terrorbyte first.",
        "source": "Community",
    },
    {
        "id": "kosatka",
        "name": "Kosatka Submarine",
        "class": "submarine",
        "buy_price": 2200000,
        "trade_price": None,
        "upgrade_cost": 1545000,  # sonar, guided missiles, sparrow, periscope
        "weapons_cost": 0,
        "armour_cost": 0,
        "total_cost_standard": 3745000,
        "notes": "Guided missiles ($1.9M) optional but excellent. Sparrow helicopter strongly recommended.",
        "source": "GTABase",
    },
    # ── Top supercars (Broughy tested) ────────────────────────────────────────
    {
        "id": "deveste-eight",
        "name": "Deveste Eight",
        "class": "super",
        "buy_price": 1795000,
        "trade_price": 1350000,
        "trade_unlock": "Complete 10 Import/Export sells",
        "upgrade_cost": 295000,
        "weapons_cost": 0,
        "armour_cost": 10000,
        "total_cost_standard": 2100000,
        "total_cost_trade": 1655000,
        "notes": "Top-tier super. Trade price dramatically reduces cost.",
        "source": "Broughy1322 + GTABase",
    },
    {
        "id": "pariah",
        "name": "Ocelot Pariah",
        "class": "sports",
        "buy_price": 1420000,
        "trade_price": None,
        "upgrade_cost": 295000,
        "weapons_cost": 0,
        "armour_cost": 10000,
        "total_cost_standard": 1725000,
        "notes": "Fastest sports car by top speed. Excellent value.",
        "source": "Broughy1322",
    },
    {
        "id": "krieger",
        "name": "Übermacht Krieger",
        "class": "super",
        "buy_price": 2875000,
        "trade_price": 2162500,
        "trade_unlock": "Win a Street Race Series",
        "upgrade_cost": 295000,
        "weapons_cost": 0,
        "armour_cost": 10000,
        "total_cost_standard": 3180000,
        "total_cost_trade": 2467500,
        "source": "Broughy1322",
    },
    # ── Combat/utility vehicles ────────────────────────────────────────────────
    {
        "id": "nightshark",
        "name": "Nightshark",
        "class": "suv",
        "buy_price": 1245000,
        "trade_price": 935000,
        "trade_unlock": "Complete 5 Mobile Operations",
        "upgrade_cost": 295000,
        "weapons_cost": 442500,   # miniguns
        "armour_cost": 0,
        "total_cost_standard": 1982500,
        "total_cost_trade": 1672500,
        "notes": "Best bang-for-buck armoured vehicle. Miniguns highly recommended.",
        "source": "Community",
    },
    {
        "id": "insurgent-pickup-custom",
        "name": "Insurgent Pick-Up Custom",
        "class": "suv",
        "buy_price": 1350000,
        "trade_price": None,
        "upgrade_cost": 295000,
        "weapons_cost": 382500,
        "armour_cost": 0,
        "total_cost_standard": 2027500,
        "notes": "Best for protection in public sessions. Required: Weaponized Vehicle Workshop.",
        "source": "Community",
    },
    {
        "id": "stromberg",
        "name": "Ocelot Stromberg",
        "class": "sports-classic",
        "buy_price": 3185350,
        "trade_price": 2395000,
        "trade_unlock": "Complete 12 Vehicle Cargo exports",
        "upgrade_cost": 295000,
        "weapons_cost": 625000,   # missiles + torpedoes
        "armour_cost": 0,
        "total_cost_standard": 4105350,
        "total_cost_trade": 3315000,
        "notes": "Submersible + missiles. Useful for Cayo Perico approach variants.",
        "source": "GTABase",
    },
    {
        "id": "akula",
        "name": "Akula",
        "class": "helicopter",
        "buy_price": 4071840,
        "trade_price": 3050000,
        "trade_unlock": "Complete 10 Air Freight Cargo sells",
        "upgrade_cost": 0,
        "weapons_cost": 800000,   # missiles + guns
        "armour_cost": 0,
        "total_cost_standard": 4871840,
        "total_cost_trade": 3850000,
        "notes": "Off-radar helicopter. Best stealth approach vehicle. Trade price saves $1M+.",
        "source": "GTABase",
    },
    {
        "id": "sparrow",
        "name": "Buckingham Sparrow",
        "class": "helicopter",
        "buy_price": 1815000,
        "trade_price": None,
        "upgrade_cost": 0,
        "weapons_cost": 495000,
        "armour_cost": 0,
        "total_cost_standard": 2310000,
        "notes": "Kosatka-docked helicopter. Missiles mandatory. Fastest route to island in Cayo Perico.",
        "source": "Community",
    },
    # ── Grinding utility ───────────────────────────────────────────────────────
    {
        "id": "brickade-6x6",
        "name": "Brickade 6×6 (Acid Lab)",
        "class": "truck",
        "buy_price": 0,
        "trade_price": None,
        "upgrade_cost": 0,
        "weapons_cost": 0,
        "armour_cost": 0,
        "total_cost_standard": 0,
        "notes": "Free after completing The First Dose missions. Hosts the Acid Lab.",
        "source": "Rockstar",
    },
    {
        "id": "terrorbyte",
        "name": "Terrorbyte",
        "class": "truck",
        "buy_price": 1375000,
        "trade_price": None,
        "upgrade_cost": 340000,   # drone station + scanner
        "weapons_cost": 505000,   # missiles + minigun turret
        "armour_cost": 0,
        "total_cost_standard": 2220000,
        "notes": "Required for Client Jobs (Oppressor Mk2 upgrade). Drone station useful for sourcing.",
        "source": "GTABase",
    },
    # ── Heist approach vehicles ────────────────────────────────────────────────
    {
        "id": "toreador",
        "name": "Pegassi Toreador",
        "class": "sports-classic",
        "buy_price": 3660000,
        "trade_price": None,
        "upgrade_cost": 295000,
        "weapons_cost": 625000,
        "armour_cost": 0,
        "total_cost_standard": 4580000,
        "notes": "Submersible + missiles. Counter for griefers. Boost speed useful for getaways.",
        "source": "Community",
    },
    {
        "id": "avenger",
        "name": "Avenger",
        "class": "aircraft",
        "buy_price": 3950000,
        "trade_price": None,
        "upgrade_cost": 0,
        "weapons_cost": 870000,
        "armour_cost": 0,
        "total_cost_standard": 4820000,
        "notes": "Mobile command centre. Required for certain Doomsday Heist setups.",
        "source": "GTABase",
    },
    # ── Business delivery vehicles ─────────────────────────────────────────────
    {
        "id": "moc",
        "name": "Mobile Operations Center (MOC)",
        "class": "truck",
        "buy_price": 1225000,
        "trade_price": None,
        "upgrade_cost": 895000,   # command center + vehicle workshop + living quarters
        "weapons_cost": 0,
        "armour_cost": 0,
        "total_cost_standard": 2120000,
        "notes": "Required for Mobile Operations missions and weaponised vehicle customisation.",
        "source": "GTABase",
    },
    # ── Popular racing / open world vehicles ──────────────────────────────────
    {
        "id": "sx-25",
        "name": "Sultan Classic (Karin)",
        "class": "sports",
        "buy_price": 1795000,
        "trade_price": None,
        "upgrade_cost": 295000,
        "weapons_cost": 0,
        "armour_cost": 10000,
        "total_cost_standard": 2100000,
        "source": "Broughy1322",
    },
    {
        "id": "itali-rsx",
        "name": "Grotti Itali RSX",
        "class": "sports",
        "buy_price": 3465000,
        "trade_price": 2598750,
        "trade_unlock": "Win a Street Race Series",
        "upgrade_cost": 295000,
        "weapons_cost": 0,
        "armour_cost": 10000,
        "total_cost_standard": 3770000,
        "total_cost_trade": 2903750,
        "notes": "Best sports car for lap time. Trade price saves $866k.",
        "source": "Broughy1322",
    },
]

# ── Mod cost categories for the economy page ──────────────────────────────────
MOD_CATEGORIES = {
    "performance": {
        "label": "Full Performance",
        "description": "Engine, transmission, brakes, suspension, turbo",
        "typical_cost": 295000,
    },
    "weapons": {
        "label": "Weaponisation",
        "description": "Missiles, guns, countermeasures",
        "typical_cost": 500000,
    },
    "armour": {
        "label": "Armour",
        "description": "Full armour plating",
        "typical_cost": 10000,
    },
}


def main() -> None:
    print("[fetch_vehicle_mods] Building vehicle upgrade cost registry…")

    # Compute aggregates
    vehicles_with_tco = [v for v in VEHICLES if v.get("buy_price", 0) > 0]
    avg_upgrade = sum(v.get("upgrade_cost", 0) for v in vehicles_with_tco) / max(len(vehicles_with_tco), 1)
    avg_weapons = sum(v.get("weapons_cost", 0) for v in vehicles_with_tco) / max(len(vehicles_with_tco), 1)

    output = {
        "last_updated": now_iso(),
        "source": "GTABase.com + Broughy1322 + GTAForums upgrade cost guides",
        "note": (
            "Total Cost of Ownership = buy_price + upgrade_cost + weapons_cost + armour_cost. "
            "upgrade_cost = full performance (engine/trans/brakes/suspension/turbo). "
            "Trade prices require specific mission completions. "
            "Figures based on standard shop prices, not event week discounts."
        ),
        "vehicle_count": len(VEHICLES),
        "avg_upgrade_cost": round(avg_upgrade),
        "avg_weapons_cost": round(avg_weapons),
        "mod_categories": MOD_CATEGORIES,
        "vehicles": VEHICLES,
    }

    print(f"  Vehicles: {len(VEHICLES)}")
    print(f"  Avg upgrade cost: ${avg_upgrade:,.0f}")
    print(f"  Avg weapons cost: ${avg_weapons:,.0f}")
    print(f"\n  Top 5 by TCO:")
    sorted_v = sorted(VEHICLES, key=lambda v: v.get("total_cost_standard", 0), reverse=True)
    for v in sorted_v[:5]:
        print(f"    {v['name']:40} TCO=${v.get('total_cost_standard',0):,}")

    if has_changed(output, OUT_PATH):
        write_json(OUT_PATH, output)
        print(f"\n[fetch_vehicle_mods] ✓ Saved to vehicle-mods.json")
    else:
        print("\n[fetch_vehicle_mods] No changes")


if __name__ == "__main__":
    main()
