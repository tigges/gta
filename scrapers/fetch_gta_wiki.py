"""
Fetch GTA VI entity data from the GTA Fandom Wiki via the MediaWiki API.

Collects vehicles, characters, weapons, businesses, animals, and locations
for GTA VI. Each entity gets a basic confidence_tier assignment based on
whether it has an article (reported) or is just a category stub (indexed).

Output: data/gta-6/entities/{type}.json per entity type
        data/gta-6/entities/index.json — flat list of all entities
"""

import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import has_changed, now_iso, write_json

BASE_URL = "https://gta.fandom.com/api.php"
HEADERS = {"User-Agent": "gtavi.ai/1.0 (data research; not affiliated with Fandom)"}

# Entity types to scrape
ENTITY_TYPES = [
    {"type": "vehicle",   "category": "Vehicles_in_GTA_VI",       "icon": "🚗"},
    {"type": "character", "category": "Characters_in_GTA_VI",      "icon": "👤"},
    {"type": "weapon",    "category": "Weapons_in_GTA_VI",         "icon": "🔫"},
    {"type": "business",  "category": "Businesses_in_GTA_VI",      "icon": "🏢"},
    {"type": "animal",    "category": "Animals_in_GTA_VI",         "icon": "🐊"},
    {"type": "location",  "category": "Locations_in_GTA_VI",       "icon": "📍"},
]

# Entities known to be officially confirmed by Rockstar (trailer / press kit)
CONFIRMED_NAMES = {
    # Vehicles seen in trailers
    "Pegassi Infernus", "Deveste Eight", "Benefactor Schafter",
    "Principe Deveste Eight",
    # Characters
    "Lucia Caminos", "Jason Duval", "Cal Hampton",
    "Boobie Ike", "Dre'Quan Priest", "Real Dimez", "Raul Bautista",
    "Brian Heder",
    # Animals
    "American Alligator", "Hammerhead Shark", "Florida Panther",
    # Businesses
    "Malibu Club", "Port Gellhorn Marina",
    # Locations / regions
    "Vice City", "Port Gellhorn", "Ambrosia", "Mount Kalaga",
    "Leonida Keys", "Kelly County", "Grassrivers",
}

# Franchise debut mapping — best-effort for well-known entities
FRANCHISE_DEBUTS: dict[str, str] = {
    "Pegassi Infernus": "gta-3",
    "Deveste Eight": "gta-5",
    "Benefactor Schafter": "gta-5",
    "Malibu Club": "gta-vc",
    "Vice City": "gta-vc",
    "Port Gellhorn": "gta-6",
    "Lucia Caminos": "gta-6",
    "Jason Duval": "gta-6",
    "Cal Hampton": "gta-6",
}


def fetch_category_members(category: str) -> list[str]:
    """Return all page titles in a MediaWiki category, handling pagination."""
    titles = []
    cmcontinue = None
    while True:
        params: dict = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": 500,
            "cmtype": "page",
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        members = data.get("query", {}).get("categorymembers", [])
        titles.extend(m["title"] for m in members)

        cont = data.get("continue", {})
        cmcontinue = cont.get("cmcontinue")
        if not cmcontinue:
            break
        time.sleep(0.3)

    return titles


def assign_confidence(title: str, has_article: bool) -> str:
    if title in CONFIRMED_NAMES:
        return "confirmed"
    if has_article:
        return "reported"
    return "indexed"


def build_entity(title: str, entity_type: str) -> dict:
    # Strip namespace if present
    name = title.split(":", 1)[-1] if ":" in title else title
    confidence = assign_confidence(name, True)
    franchise_debut = FRANCHISE_DEBUTS.get(name, "gta-6")

    return {
        "id": name.lower().replace(" ", "-").replace("'", "").replace("/", "-"),
        "name": name,
        "type": entity_type,
        "game_version": "gta-6",
        "confidence_tier": confidence,
        "confidence_score": {"confirmed": 85, "reported": 55, "indexed": 30}.get(confidence, 30),
        "franchise_debut": franchise_debut,
        "franchise_lineage": [franchise_debut] if franchise_debut == "gta-6" else [franchise_debut, "gta-6"],
        "source": "GTA Fandom Wiki",
        "wiki_title": title,
    }


def main() -> None:
    print("Fetching GTA VI entity data from Fandom Wiki...")
    all_entities: list[dict] = []
    type_counts: dict[str, int] = {}

    for et in ENTITY_TYPES:
        print(f"  [{et['type']}] fetching Category:{et['category']}...")
        try:
            titles = fetch_category_members(et["category"])
            entities = [build_entity(t, et["type"]) for t in titles]
            type_counts[et["type"]] = len(entities)
            all_entities.extend(entities)
            print(f"    → {len(entities)} entries")

            # Write per-type file
            per_type = {
                "last_updated": now_iso(),
                "type": et["type"],
                "source": "GTA Fandom Wiki (gta.fandom.com)",
                "count": len(entities),
                "entities": entities,
            }
            write_json(f"gta-6/entities/{et['type']}s.json", per_type)
            time.sleep(0.5)

        except Exception as e:
            print(f"    ✗ Error: {e}")

    # Write flat index
    total = len(all_entities)
    confirmed = sum(1 for e in all_entities if e["confidence_tier"] == "confirmed")
    reported  = sum(1 for e in all_entities if e["confidence_tier"] == "reported")
    indexed   = sum(1 for e in all_entities if e["confidence_tier"] == "indexed")

    print(f"\n  Total: {total} entities")
    print(f"  Confirmed: {confirmed} | Reported: {reported} | Indexed: {indexed}")
    print(f"  By type: {type_counts}")

    index_payload = {
        "last_updated": now_iso(),
        "source": "GTA Fandom Wiki (gta.fandom.com)",
        "note": "Confidence tiers auto-assigned. 'confirmed' = Rockstar official material. 'reported' = credible community sources. 'indexed' = listed on wiki, confidence not yet assessed.",
        "total": total,
        "by_type": type_counts,
        "by_confidence": {"confirmed": confirmed, "reported": reported, "indexed": indexed},
        "entities": all_entities,
    }

    if has_changed(index_payload, "gta-6/entities/index.json"):
        write_json("gta-6/entities/index.json", index_payload)
        print("Entity index written.")
    else:
        print("No changes to entity index.")


if __name__ == "__main__":
    main()
