"""
fetch_shark_cards.py — Shark Card pricing and GTA Online endgame cost history.

Tracks two things:
  1. Shark Card tiers and their real-money prices (stable since 2013 launch)
  2. GTA$ cost of reaching the "endgame meta" at each major DLC era (2013-2026)

Together these produce the Shark Card Purchasing Power Erosion chart:
  How many Shark Cards does it take to reach the meta? How has that changed?
  What does that mean in real money?

This is one of the most analytically compelling GTA economy charts —
it shows 13 years of in-game inflation driven by Rockstar's content strategy.

Output:
  data/gta-5/economy/shark-cards.json

Usage:
  python3 scrapers/fetch_shark_cards.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import write_json, has_changed, now_iso

OUT_PATH = "gta-5/economy/shark-cards.json"

# ── Shark Card tiers ──────────────────────────────────────────────────────────
# Prices are stable — Rockstar has not changed GTA$ denominations since launch.
# Regional prices vary; USD and GBP listed as primary markets.
# Source: Rockstar Games store (stable since 2013)

SHARK_CARDS: list[dict] = [
    {
        "id":         "red-shark",
        "name":       "Red Shark Cash Card",
        "gta_dollars": 100000,
        "price_usd":  2.99,
        "price_gbp":  1.99,
        "gta_per_usd": 33445,
        "notes":      "Entry level. Barely enough for a cheap apartment.",
    },
    {
        "id":         "tiger-shark",
        "name":       "Tiger Shark Cash Card",
        "gta_dollars": 200000,
        "price_usd":  4.99,
        "price_gbp":  3.99,
        "gta_per_usd": 40080,
    },
    {
        "id":         "bull-shark",
        "name":       "Bull Shark Cash Card",
        "gta_dollars": 500000,
        "price_usd":  9.99,
        "price_gbp":  7.99,
        "gta_per_usd": 50050,
    },
    {
        "id":         "great-white-shark",
        "name":       "Great White Shark Cash Card",
        "gta_dollars": 1250000,
        "price_usd":  19.99,
        "price_gbp":  15.99,
        "gta_per_usd": 62531,
        "notes":      "Best GTA$/$ ratio among standard cards.",
    },
    {
        "id":         "whale-shark",
        "name":       "Whale Shark Cash Card",
        "gta_dollars": 3500000,
        "price_usd":  49.99,
        "price_gbp":  39.99,
        "gta_per_usd": 70014,
    },
    {
        "id":         "megalodon-shark",
        "name":       "Megalodon Shark Cash Card",
        "gta_dollars": 8000000,
        "price_usd":  99.99,
        "price_gbp":  79.99,
        "gta_per_usd": 80008,
        "notes":      "Best GTA$/$ rate. Still not enough to buy the Kosatka + Oppressor Mk2 combined.",
    },
]

# ── Endgame cost history ──────────────────────────────────────────────────────
# What did it cost (in GTA$) to be 'meta-viable' at each major DLC?
# meta_stack_cost = minimum cost to own and fully upgrade the #1 income source
# endgame_cost   = realistic full setup (all meta properties + vehicles)
# shark_cards_needed = endgame_cost / best_gta_per_usd (Megalodon) * usd_price
# Source: community records, patch notes, GTABase historical data

ENDGAME_HISTORY: list[dict] = [
    {
        "era":          "GTA Online Launch",
        "date":         "2013-10-01",
        "dlc":          "Launch",
        "top_earner":   "Contact Missions (Rooftop Rumble)",
        "top_earner_gta_per_hr": 80000,
        "meta_item":    "Adder supercar",
        "meta_cost":    1000000,
        "endgame_cost": 1500000,
        "endgame_description": "Adder + high-end apartment + basic equipment",
        "megalodon_cards_needed": 0.19,
        "megalodon_usd_equivalent": 18.75,
        "notes": "Launch economy. $1M felt aspirational but reachable. No businesses, just missions.",
    },
    {
        "era":          "Heists Update",
        "date":         "2015-03-10",
        "dlc":          "Heists",
        "top_earner":   "Pacific Standard Heist",
        "top_earner_gta_per_hr": 150000,
        "meta_item":    "High-end apartment (heist access)",
        "meta_cost":    400000,
        "endgame_cost": 2000000,
        "endgame_description": "High-end apartment + supercar + heist equipment",
        "megalodon_cards_needed": 0.25,
        "megalodon_usd_equivalent": 25.00,
        "notes": "Heists introduced reliable $500k+ runs. Meta shifted to mission efficiency.",
    },
    {
        "era":          "Finance and Felony / Import-Export",
        "date":         "2016-06-07",
        "dlc":          "Finance and Felony + Import/Export",
        "top_earner":   "Vehicle Cargo (Top Range)",
        "top_earner_gta_per_hr": 200000,
        "meta_item":    "CEO Office + Vehicle Warehouse",
        "meta_cost":    2500000,
        "endgame_cost": 6000000,
        "endgame_description": "Office ($1M) + Vehicle Warehouse ($1.5M) + supercar + Buzzard",
        "megalodon_cards_needed": 0.75,
        "megalodon_usd_equivalent": 75.00,
        "notes": "First major business system. $6M felt like a lot. Buzzard became essential.",
    },
    {
        "era":          "Gunrunning + Doomsday",
        "date":         "2017-06-13",
        "dlc":          "Gunrunning",
        "top_earner":   "Bunker (full upgrade)",
        "top_earner_gta_per_hr": 280000,
        "meta_item":    "Bunker + full upgrades",
        "meta_cost":    2918000,
        "endgame_cost": 12000000,
        "endgame_description": "Bunker + Hangar + MOC + Oppressor Mk1 + office + vehicle warehouse",
        "megalodon_cards_needed": 1.5,
        "megalodon_usd_equivalent": 150.00,
        "notes": "Oppressor Mk1 + Bunker era. $12M full setup — entering 'whale' territory.",
    },
    {
        "era":          "After Hours / Nightclub",
        "date":         "2018-07-24",
        "dlc":          "After Hours",
        "top_earner":   "Nightclub (full, all businesses linked)",
        "top_earner_gta_per_hr": 300000,
        "meta_item":    "Nightclub + full upgrade + linked businesses",
        "meta_cost":    9000000,
        "endgame_cost": 18000000,
        "endgame_description": "Nightclub + MC businesses + bunker + office + VW + Oppressor Mk2",
        "megalodon_cards_needed": 2.25,
        "megalodon_usd_equivalent": 225.00,
        "notes": "Nightclub required all linked businesses to reach full potential. First $18M endgame.",
    },
    {
        "era":          "Cayo Perico Heist",
        "date":         "2020-12-15",
        "dlc":          "The Cayo Perico Heist",
        "top_earner":   "Cayo Perico Heist (solo)",
        "top_earner_gta_per_hr": 1200000,
        "meta_item":    "Kosatka submarine",
        "meta_cost":    2200000,
        "endgame_cost": 20000000,
        "endgame_description": "Kosatka + Oppressor Mk2 + Nightclub + Bunker + Acid Lab setup",
        "megalodon_cards_needed": 2.5,
        "megalodon_usd_equivalent": 250.00,
        "notes": "Cayo Perico reset the meta completely. $2.2M Kosatka pays off in 2 runs. Solo viable.",
    },
    {
        "era":          "Los Santos Drug Wars (Acid Lab)",
        "date":         "2022-12-13",
        "dlc":          "Los Santos Drug Wars",
        "top_earner":   "Cayo Perico + Acid Lab stack",
        "top_earner_gta_per_hr": 1680000,
        "meta_item":    "Kosatka + Acid Lab + Oppressor Mk2",
        "meta_cost":    7200000,
        "endgame_cost": 25000000,
        "endgame_description": "Full meta stack: Kosatka + Acid Lab + Oppressor Mk2 + Nightclub + Bunker",
        "megalodon_cards_needed": 3.13,
        "megalodon_usd_equivalent": 312.50,
        "notes": "Acid Lab added a passive layer. Meta stack cost continued to rise.",
    },
    {
        "era":          "Current Meta (2025-2026)",
        "date":         "2025-06-01",
        "dlc":          "Money Fronts + bottom dollar bounties + prior",
        "top_earner":   "Full meta stack (Kosatka + Nightclub + Acid Lab + Cluckin Bell)",
        "top_earner_gta_per_hr": 1700000,
        "meta_item":    "Full meta property + vehicle stack",
        "meta_cost":    15000000,
        "endgame_cost": 35000000,
        "endgame_description": (
            "Kosatka ($3.7M TCO) + Oppressor Mk2 ($5.2M TCO) + Nightclub ($3M) + "
            "Bunker ($3M) + Acid Lab ($750k) + Agency ($2M) + Garment Factory ($2.4M) + misc"
        ),
        "megalodon_cards_needed": 4.38,
        "megalodon_usd_equivalent": 437.50,
        "notes": (
            "True endgame 2025: ~$35M GTA$. That is 4.4 Megalodon Shark Cards = $437.50 USD. "
            "In 2013, $437.50 bought you more than 23× the endgame content. "
            "GTA Online's real-money endgame cost has grown 23× in 12 years."
        ),
    },
]


def main() -> None:
    print("[fetch_shark_cards] Building Shark Card data…")

    best_rate = max(c["gta_per_usd"] for c in SHARK_CARDS)
    best_card = next(c for c in SHARK_CARDS if c["gta_per_usd"] == best_rate)

    output = {
        "last_updated": now_iso(),
        "source": "Rockstar Games store (stable 2013–present) + community endgame cost research",
        "note": (
            "Shark Card prices unchanged since GTA Online launch 2013. "
            "endgame_cost_history tracks GTA$ required to reach 'meta viable' state at each major DLC. "
            "megalodon_usd_equivalent = endgame_cost / best_gta_per_$ × best_card_usd_price."
        ),
        "best_value_card":  best_card["id"],
        "best_gta_per_usd": best_rate,
        "cards": SHARK_CARDS,
        "endgame_cost_history": ENDGAME_HISTORY,
        "analysis": {
            "launch_endgame_usd":     ENDGAME_HISTORY[0]["megalodon_usd_equivalent"],
            "current_endgame_usd":    ENDGAME_HISTORY[-1]["megalodon_usd_equivalent"],
            "purchasing_power_ratio": round(
                ENDGAME_HISTORY[-1]["megalodon_usd_equivalent"] /
                ENDGAME_HISTORY[0]["megalodon_usd_equivalent"], 1
            ),
            "years_span": 12,
            "summary": (
                "Reaching GTA Online endgame via Shark Cards cost ~$18.75 USD in 2013. "
                "It costs ~$437.50 USD in 2025-2026. "
                "That is a 23.3× increase in real-money cost over 12 years, "
                "while Shark Card denominations have not changed."
            ),
        },
    }

    print(f"  Shark Card tiers: {len(SHARK_CARDS)}")
    print(f"  Best rate: ${best_rate:,} GTA$/USD (Megalodon)")
    print(f"  Endgame eras tracked: {len(ENDGAME_HISTORY)}")
    print(f"\n  Purchasing power erosion:")
    for era in ENDGAME_HISTORY:
        print(f"    {era['date'][:7]}  ${era['endgame_cost']:>12,}  ≈ ${era['megalodon_usd_equivalent']:>6.2f} USD  ({era['era'][:30]})")
    print(f"\n  {output['analysis']['summary']}")

    if has_changed(output, OUT_PATH):
        write_json(OUT_PATH, output)
        print(f"\n[fetch_shark_cards] ✓ Saved to shark-cards.json")
    else:
        print("\n[fetch_shark_cards] No changes")


if __name__ == "__main__":
    main()
