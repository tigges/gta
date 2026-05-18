"""
derive_features.py
Reconciles features.json with the live entity index from GTA Wiki and Leonida Intel.

Updates the `indexed` count per category from entities/index.json and
leonida-intel.json so the Feature Tracker stays in sync after wiki scrapes.
Manually curated `confirmed`, `reported`, `target`, `notes`, `source` are preserved.
"""
import json
from utils import DATA_DIR, write_json, now_iso, has_changed, load_existing

FEATURES_PATH  = "gta-6/features.json"
INDEX_PATH     = DATA_DIR / "gta-6/entities/index.json"
LEONIDA_PATH   = DATA_DIR / "gta-6/entities/leonida-intel.json"

# Map feature category IDs to entity type keys in the index
CATEGORY_TYPE_MAP = {
    "vehicles":   ["vehicle"],
    "characters": ["character"],
    "weapons":    ["weapon"],
    "businesses": ["business"],
    "regions":    ["location"],
    "activities": [],           # no direct entity type — preserve manual count
    "wildlife":   ["animal"],
    "online":     [],           # preserve manual count
}


def main() -> None:
    index   = json.loads(INDEX_PATH.read_text())
    leonida = json.loads(LEONIDA_PATH.read_text())
    existing = load_existing(FEATURES_PATH)

    by_type      = index.get("by_type", {})
    leo_by_cat   = leonida.get("by_category", {})

    # Build category → total indexed count
    cat_indexed: dict[str, int] = {}
    for cat_id, types in CATEGORY_TYPE_MAP.items():
        if not types:
            cat_indexed[cat_id] = 0  # will be skipped (manual only)
            continue
        wiki_count  = sum(by_type.get(t, 0) for t in types)
        leo_key     = cat_id.capitalize()
        leo_count   = leo_by_cat.get(leo_key, 0)
        cat_indexed[cat_id] = max(wiki_count, leo_count)

    updated_cats = []
    for cat in existing.get("categories", []):
        new_indexed = cat_indexed.get(cat["id"], cat.get("indexed", 0))
        if new_indexed > 0:
            cat = {**cat, "indexed": new_indexed}
        updated_cats.append(cat)

    payload = {
        **existing,
        "last_updated": now_iso(),
        "categories":   updated_cats,
    }

    if has_changed(payload, FEATURES_PATH):
        write_json(FEATURES_PATH, payload)
        print(f"features.json updated: {sum(c.get('indexed',0) for c in updated_cats)} total indexed entities")
    else:
        print("features.json unchanged")


if __name__ == "__main__":
    main()
