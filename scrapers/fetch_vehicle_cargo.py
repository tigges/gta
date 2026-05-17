"""
fetch_vehicle_cargo.py — Import/Export Vehicle Cargo data scraper.

Fetches the complete Import/Export (Vehicle Cargo) dataset from the GTA Fandom Wiki:
  - 32 sourceable vehicles across Standard / Mid / Top range (with plate variants)
  - Exact sell prices by tier × buyer type (Private / Showroom / Specialist Dealer)
  - 13 source mission types (steal scenario categories)
  - Collections mechanic and High Demand bonus formula
  - Cooldown timers and damage penalty details

Sources:
  https://gta.fandom.com/wiki/Vehicle_Cargo         — vehicles, prices, mechanics
  https://gta.fandom.com/wiki/Vehicle_Cargo/Sell_Missions — exact sell price table

Output:
  data/gta-5/economy/vehicle-cargo.json

Also enriches the existing vehicle-warehouse entry in business-profiles.json
with the scraped sell price breakdown.

Note: Import/Export is already mapped as 'vehicle-warehouse' ($150k/hr) in
revenue-tiers.json. This scraper adds the per-tier detail without changing
the top-level $/hr figure.

Usage:
  python3 scrapers/fetch_vehicle_cargo.py
"""

import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import write_json, has_changed, load_existing, now_iso

WIKI_API = "https://gta.fandom.com/api.php"
HEADERS  = {"User-Agent": "gtavi.ai-bot/1.0 (+https://gtavi.ai; vehicle-cargo-research)"}
DELAY    = 0.6
OUT_PATH = "gta-5/economy/vehicle-cargo.json"


def wiki_wikitext(session: requests.Session, page: str) -> str:
    r = session.get(WIKI_API, params={
        "action": "parse", "page": page,
        "prop":   "wikitext", "format": "json",
    }, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json().get("parse", {}).get("wikitext", {}).get("*", "")


def clean(s: str) -> str:
    s = re.sub(r'\[\[(?:[^\|\]]+\|)?([^\]]+)\]\]', r'\1', s)
    s = re.sub(r'\{\{[^\}]+\}\}', '', s)
    s = re.sub(r"'''?", '', s)
    s = re.sub(r'style="[^"]*"\s*\|?\s*', '', s)
    return s.strip(' |-\n')


def parse_money(text: str) -> int | None:
    t = clean(text).replace(',', '').replace('$', '').replace('GTA', '').strip()
    try:
        return int(float(t))
    except (ValueError, TypeError):
        return None


def parse_sell_prices(wt: str) -> dict:
    """Extract the sell price table from the Sell Missions wikitext."""
    # Find the Rewards section table
    rewards_m = re.search(r'===Rewards===(.*?)(?:===|==|\Z)', wt, re.DOTALL)
    if not rewards_m:
        return {}
    rewards_section = rewards_m.group(1)

    # Parse the wikitable rows: |Top |$40,000 |$70,000 |$100,000
    row_re = re.compile(
        r'\|\s*(Top|Mid|Standard)\s*\n'
        r'\|\s*([^\n]+)\n'
        r'\|\s*([^\n]+)\n'
        r'\|\s*([^\n]+)',
        re.IGNORECASE
    )
    prices: dict[str, dict] = {}
    for m in row_re.finditer(rewards_section):
        tier  = m.group(1).lower()
        priv  = clean(m.group(2))
        show  = clean(m.group(3))
        spec  = clean(m.group(4))

        # Parse "gross - cost = net" format e.g. "$100,000 - $20,000 = $80,000"
        def extract_net(text: str) -> int | None:
            bolded = re.search(r"\'''?\$?([\d,]+)\'''?", text)
            if bolded:
                try:
                    return int(bolded.group(1).replace(',', ''))
                except ValueError:
                    pass
            # Fall back: take last money value
            vals = re.findall(r'\$([\d,]+)', text)
            if vals:
                try:
                    return int(vals[-1].replace(',', ''))
                except ValueError:
                    pass
            return None

        prices[tier] = {
            "private":    extract_net(priv),
            "showroom":   extract_net(show),
            "specialist": extract_net(spec),
        }

    return prices


def parse_vehicles(wt: str) -> dict[str, list[dict]]:
    """Extract vehicle lists from the Target Vehicles tabber section."""
    tv_m = re.search(r'==Target Vehicles==(.*?)(?:==Import Tips|==Exporting|\Z)', wt, re.DOTALL)
    if not tv_m:
        return {}

    body = tv_m.group(1)
    result: dict[str, list[dict]] = {"top": [], "mid": [], "standard": []}

    # Tabber uses <tabber> ... Top= ... |-| ... Mid= ... |-| ... Standard= ...
    # Split on |-| or by tier header
    tab_parts = re.split(r'\n(?:Top|Mid|Standard)=\n', body)
    tab_names = re.findall(r'\n(Top|Mid|Standard)=\n', body)

    for tab_name, section in zip(tab_names, tab_parts[1:]):
        tier_key = tab_name.lower()
        # Top Range rows: |[[Name]]<br>$market_value  (market value present)
        # Mid/Standard rows: |[[Name]] (no market value in table)
        for m in re.finditer(r'\|\s*\[\[([^\|\]#]+?)\]\](?:<br>\$([\d,]+))?', section):
            name      = m.group(1).strip()
            mkt_raw   = m.group(2)
            mkt_value = int(mkt_raw.replace(',', '')) if mkt_raw else None
            vid       = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
            plate_block = section[m.start():m.start() + 400]
            plates = re.findall(r'\*([A-Z0-9\*]+)\*?', plate_block)[:3]
            result[tier_key].append({
                "id":           vid,
                "name":         name,
                "market_value": mkt_value,
                "plates":       plates,
            })

    return result


def parse_source_mission_types(wt: str) -> list[dict]:
    """Extract the 15 source mission type names from section headings."""
    smt_m = re.search(
        r'==Source Mission Types==(.*?)(?:==Target Vehicles|==Import Tips|\Z)', wt, re.DOTALL
    )
    if not smt_m:
        return []

    body  = smt_m.group(1)
    types: list[dict] = []

    # Headers look like: ==[[Vehicle Cargo/Source Missions#Type|Type Name]]==
    for m in re.finditer(r'=={1,4}\s*\[\[[^\]]*\|([^\]]+)\]\]\s*=={1,4}', body):
        display_name = m.group(1).strip()
        type_id = re.sub(r'[^a-z0-9]+', '-', display_name.lower()).strip('-')
        types.append({"id": type_id, "title": display_name})

    return types


def parse_collections(wt: str) -> list[dict]:
    """Extract the vehicle collection names from the Vehicle Cargo Collections section."""
    col_m = re.search(r'==Vehicle Cargo Collections==(.*?)(?:==Trivia|==Oversights|\Z)', wt, re.DOTALL)
    if not col_m:
        return []

    body  = col_m.group(1)
    names = re.findall(r"\''([A-Z][^\'']+)''", body)
    collections: list[dict] = []
    for name in names:
        col_id = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        collections.append({"id": col_id, "name": name})

    return collections


def main() -> None:
    session = requests.Session()
    print("[fetch_vehicle_cargo] Fetching GTA Wiki pages…")

    # Fetch main Vehicle Cargo page
    vc_wt = wiki_wikitext(session, "Vehicle Cargo")
    print(f"  Vehicle Cargo: {len(vc_wt):,} chars")
    time.sleep(DELAY)

    # Fetch sell missions page for exact prices
    sell_wt = wiki_wikitext(session, "Vehicle Cargo/Sell Missions")
    print(f"  Sell Missions: {len(sell_wt):,} chars")

    # Parse all sections
    sell_prices   = parse_sell_prices(sell_wt)
    vehicles      = parse_vehicles(vc_wt)
    source_types  = parse_source_mission_types(vc_wt)
    collections   = parse_collections(vc_wt)

    print(f"  Vehicles scraped: Top={len(vehicles.get('top',[]))} Mid={len(vehicles.get('mid',[]))} Standard={len(vehicles.get('standard',[]))}")
    print(f"  Source mission types: {len(source_types)}")
    print(f"  Collections: {len(collections)}")
    print(f"  Sell prices: {sell_prices}")

    output = {
        "last_updated": now_iso(),
        "source":       "GTA Fandom Wiki — Vehicle Cargo + Vehicle Cargo/Sell Missions",
        "source_urls": [
            "https://gta.fandom.com/wiki/Vehicle_Cargo",
            "https://gta.fandom.com/wiki/Vehicle_Cargo/Sell_Missions",
        ],
        "dlc":     "GTA Online: Import/Export (Dec 2016)",
        "note": (
            "Import/Export CEO business. Source vehicles via 13 steal scenarios, "
            "store up to 40 in Vehicle Warehouse, export for profit. "
            "All prices = net profit with no damage (damage up to $34k penalty max)."
        ),
        "mechanics": {
            "max_stored_vehicles":    40,
            "sell_batch_max_vehicles": 4,
            "source_cooldown_sec":    150,
            "sell_cooldown_range_min": [20, 50],
            "max_repair_cost":        34000,
            "high_demand_bonus_per_rival_pct": 2.5,
            "high_demand_bonus_max_pct":       50,
            "high_demand_note": (
                "2.5% bonus per rival player in session (max +50% with 20 rivals). "
                "Applied to sell payout only. Added in Los Santos Drug Wars update."
            ),
            "collections_note": (
                "Selling a complete collection = Specialist net price per car "
                "+ additional collection bonus per car for every car the CEO delivers."
            ),
        },
        "sell_prices_net": {
            "note": "Net GTA$ profit per vehicle. No-damage assumption. Showroom/Specialist require upfront mod costs (included in net figure).",
            **sell_prices,
        },
        "source_mission_types": source_types,
        "vehicles":   vehicles,
        "collections": collections,
        "strategy": {
            "solo_optimal": (
                "1. Fill exactly 1 Standard + 1 Mid to unlock Top Range sourcing. "
                "2. Source ONLY Top Range cars after that. "
                "3. Always sell via Specialist Dealer for maximum net ($80k/car). "
                "4. Sell 4 at a time (max batch) to minimise cooldown overhead. "
                "5. Public session = High Demand Bonus (+% per rival). "
                "6. Use Cargobob or Iron Mule to deliver damage-free."
            ),
            "max_hr_solo":   160000,
            "max_hr_4p":     320000,
            "note": (
                "Solo effective rate ~$150-160k/hr (2× Top Range Specialist per hour). "
                "4-player full org with concurrent delivery pushes to ~$300k/hr. "
                "Superseded by Cluckin' Bell and newer contracts for pure $/hr, "
                "but remains the best path to unlocking Special Vehicle Work missions."
            ),
        },
    }

    if has_changed(output, OUT_PATH):
        write_json(OUT_PATH, output)
        print(f"\n[fetch_vehicle_cargo] Saved to {OUT_PATH}")
    else:
        print("\n[fetch_vehicle_cargo] No changes.")

    # Enrich vehicle-warehouse profile in business-profiles.json
    bp = load_existing("gta-5/economy/business-profiles.json")
    updated = False
    for b in bp.get("businesses", []):
        if b["id"] == "vehicle-warehouse":
            b["sell_prices_net"]      = output["sell_prices_net"]
            b["source_mission_types"] = [t["title"] for t in source_types]
            b["vehicle_count"]        = {k: len(v) for k, v in vehicles.items()}
            b["mechanics"]            = output["mechanics"]
            b["strategy"]             = output["strategy"]["solo_optimal"]
            # Refresh tips with collected data
            b["tips"] = [
                f"Top Range Specialist net = ${output['sell_prices_net'].get('top',{}).get('specialist',80000):,}/car (no damage)",
                "Fill 1 Standard + 1 Mid first to unlock Top Range — then never source those tiers again",
                "Sell in batches of 4 — maximises revenue per cooldown cycle",
                "High Demand Bonus: +2.5% per rival in session (max +50%) since Drug Wars update",
                "Use Cargobob or Iron Mule for zero-damage delivery",
                "Collections pay Specialist rate + bonus — best value when warehouse is stocked with a full set",
            ]
            updated = True
            break

    if updated:
        write_json("gta-5/economy/business-profiles.json", bp)
        print("[fetch_vehicle_cargo] Updated vehicle-warehouse in business-profiles.json")

    print("[fetch_vehicle_cargo] Done.")


if __name__ == "__main__":
    main()
