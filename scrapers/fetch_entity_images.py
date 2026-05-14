"""
Fetch thumbnail image URLs for GTA VI entities from the GTA Fandom Wiki.

Uses the MediaWiki Action API to retrieve the first image on each entity's
wiki page, resized to a 400px thumbnail URL. Reads entities from
data/gta-6/entities/index.json and enriches them with image_url fields,
writing the result back to the same file (updating in-place).

No API key required. Rate-limited to ~2 req/s to be a good citizen.
"""

import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import has_changed, load_existing, now_iso, write_json

WIKI_API = "https://gta.fandom.com/api.php"
THUMB_WIDTH = 400
OUT_PATH = "gta-6/entities/index.json"
HEADERS = {"User-Agent": "gtavi.ai research@gtavi.ai"}
BATCH_SIZE = 50
DELAY = 0.5  # seconds between batches


def fetch_images_batch(titles: list[str]) -> dict[str, str | None]:
    """Return {wiki_title: image_url | None} for a batch of page titles."""
    params = {
        "action": "query",
        "titles": "|".join(titles),
        "prop": "pageimages",
        "pithumbsize": THUMB_WIDTH,
        "pilimit": BATCH_SIZE,
        "format": "json",
    }
    try:
        resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"  Warning: batch request failed — {exc}")
        return {t: None for t in titles}

    result: dict[str, str | None] = {}
    for page in data.get("query", {}).get("pages", {}).values():
        title = page.get("title", "")
        thumb = page.get("thumbnail", {}).get("source")
        result[title] = thumb

    # Pages not returned (missing/redirect) get None
    for t in titles:
        if t not in result:
            result[t] = None

    return result


def main() -> None:
    existing = load_existing(OUT_PATH)
    entities: list[dict] = existing.get("entities", [])

    if not entities:
        print("No entities found in index.json — run fetch_gta_wiki.py first.")
        sys.exit(1)

    # Only process entities that have a wiki_title and no image_url yet
    needs_image = [e for e in entities if e.get("wiki_title") and not e.get("image_url")]
    already_have = len(entities) - len(needs_image)
    print(f"Entities: {len(entities)} total, {already_have} already have images, "
          f"{len(needs_image)} to fetch")

    if not needs_image:
        print("All entities already have images — nothing to do.")
        return

    image_map: dict[str, str | None] = {}
    batches = [needs_image[i:i + BATCH_SIZE] for i in range(0, len(needs_image), BATCH_SIZE)]

    for idx, batch in enumerate(batches):
        titles = [e["wiki_title"] for e in batch]
        print(f"  Batch {idx + 1}/{len(batches)}: {len(titles)} titles…", end=" ", flush=True)
        result = fetch_images_batch(titles)
        found = sum(1 for v in result.values() if v)
        print(f"{found}/{len(titles)} found")
        image_map.update(result)
        if idx < len(batches) - 1:
            time.sleep(DELAY)

    # Apply to entities
    updated = 0
    for e in entities:
        wt = e.get("wiki_title")
        if wt and wt in image_map and image_map[wt]:
            e["image_url"] = image_map[wt]
            updated += 1

    total_with_images = sum(1 for e in entities if e.get("image_url"))
    print(f"Updated {updated} entities — {total_with_images}/{len(entities)} now have images")

    payload = {**existing, "last_updated": now_iso(), "entities": entities}
    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
    else:
        print("No change to write.")


if __name__ == "__main__":
    main()
