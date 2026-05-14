"""
Fetch GTA VI entity index from the Leonida Intel public API.

Endpoint: https://leonida-intel.com/api/search-index/?locale=en
Returns 1,715+ entities with name, category, href, and confirmed flag.
No auth required. Single HTTP call.

Output: data/gta-6/entities/leonida-intel.json
"""

import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import has_changed, now_iso, write_json

API_URL = "https://leonida-intel.com/api/search-index/?locale=en"
OUT_PATH = "gta-6/entities/leonida-intel.json"
HEADERS = {"User-Agent": "gtavi.ai research@gtavi.ai"}

# Map Leonida Intel categories to our canonical entity types
CATEGORY_TYPE_MAP = {
    "Vehicles": "vehicle",
    "Characters": "character",
    "Weapons": "weapon",
    "Locations": "location",
    "Animals": "animal",
    "Businesses": "business",
    "Missions": "mission",
    "Activities": "activity",
    "Properties": "property",
    "Radio": "radio",
    "Evidence": "evidence",
    "Map Intel": "location",
    "Trailer Frames": "trailer_frame",
    "Trailers": "trailer",
    "Tools": "tool",
    "PC Tools": "tool",
}

# Categories that represent actual GTA VI world entities (not site tools/UI)
ENTITY_CATEGORIES = {
    "Vehicles", "Characters", "Weapons", "Locations", "Animals",
    "Businesses", "Missions", "Activities", "Properties", "Radio",
}


def fetch_index() -> list[dict]:
    resp = requests.get(API_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def build_payload(raw: list[dict]) -> dict:
    entities = []
    by_category: dict[str, int] = {}
    confirmed_count = 0

    for item in raw:
        cat = item.get("category", "")
        by_category[cat] = by_category.get(cat, 0) + 1

        entity_type = CATEGORY_TYPE_MAP.get(cat, cat.lower())
        confirmed = bool(item.get("confirmed", False))
        if confirmed:
            confirmed_count += 1

        entities.append({
            "name": item["name"],
            "category": cat,
            "type": entity_type,
            "href": item.get("href", ""),
            "confirmed": confirmed,
            "confidence_tier": "confirmed" if confirmed else "indexed",
            "url": f"https://leonida-intel.com{item.get('href', '')}",
        })

    # Summary stats
    entity_only = [e for e in entities if e["category"] in ENTITY_CATEGORIES]
    entity_confirmed = sum(1 for e in entity_only if e["confirmed"])

    return {
        "last_updated": now_iso(),
        "source": "Leonida Intel — leonida-intel.com/api/search-index/?locale=en",
        "total": len(raw),
        "total_entities": len(entity_only),
        "confirmed": confirmed_count,
        "by_category": by_category,
        "entities": entities,
        "entity_stats": {
            "total": len(entity_only),
            "confirmed": entity_confirmed,
            "indexed": len(entity_only) - entity_confirmed,
        },
    }


def main():
    print("Fetching Leonida Intel search index…")
    raw = fetch_index()
    print(f"  Received {len(raw)} items")

    payload = build_payload(raw)
    print(f"  {payload['total_entities']} world entities, {payload['entity_stats']['confirmed']} confirmed")

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("  Data updated.")
    else:
        print("  No change — skipping write.")


if __name__ == "__main__":
    main()
