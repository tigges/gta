"""
fetch_gta5_mission_thumbs.py — Mission-specific thumbnails for GTA V heists
and assassination stock missions.

Sources each mission's lead image from the GTA Fandom Wiki (MediaWiki
pageimages API), downloads it to public/assets/gta5/story/, and writes the
local path back into:
  data/gta-5/missions/heists.json            → heists[*].thumbnail
  data/gta-5/economy/assassination-stocks.json → guide_order[*].thumbnail

All saved assets stay under public/assets/gta5/ — never mixed with GTA VI
assets (public/assets/gta6/).

Usage:
  python3 scrapers/fetch_gta5_mission_thumbs.py
"""

import os
import sys
import time
import json
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import has_changed, load_existing, now_iso, write_json

WIKI_API   = "https://gta.fandom.com/api.php"
HEADERS    = {"User-Agent": "gtavi.ai-bot/1.0 (+https://gtavi.ai; mission-thumbnails)"}
THUMB_W    = 400
DELAY      = 0.6          # seconds between Wiki API calls

STORY_DIR  = Path("public/assets/gta5/story")

# ── Mission → wiki page title mapping ────────────────────────────────────────

HEIST_WIKI: dict[str, str] = {
    "jewel-store-job":    "The Jewel Store Job",
    "merryweather-heist": "The Merryweather Heist",
    "blitz-play":         "Blitz Play",
    "bureau-raid":        "The Bureau Raid",
    "the-big-score":      "The Big Score (GTA V)",
}

ASSASSINATION_WIKI: dict[str, str] = {
    "hotel-assassination":        "The Hotel Assassination",
    "multi-target-assassination": "The Multi Target Assassination",
    "vice-assassination":         "The Vice Assassination",
    "bus-assassination":          "The Bus Assassination",
    "construction-assassination": "The Construction Assassination",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def fetch_thumb_url(session: requests.Session, wiki_title: str) -> str | None:
    """Return the Wikia CDN thumbnail URL for a wiki page, or None."""
    params = {
        "action":    "query",
        "titles":    wiki_title,
        "prop":      "pageimages",
        "pithumbsize": THUMB_W,
        "pilimit":   1,
        "format":    "json",
    }
    try:
        resp = session.get(WIKI_API, params=params, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        pages = resp.json().get("query", {}).get("pages", {})
        for page in pages.values():
            return page.get("thumbnail", {}).get("source")
    except Exception as exc:
        print(f"  [warn] Wiki API failed for '{wiki_title}': {exc}")
    return None


def download(session: requests.Session, url: str, dest: Path) -> bool:
    """Download url → dest. Returns True on success."""
    try:
        r = session.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200 and len(r.content) > 4000:
            dest.write_bytes(r.content)
            return True
    except Exception as exc:
        print(f"  [warn] Download failed ({url}): {exc}")
    return False


def fetch_and_record(
    session: requests.Session,
    mission_id: str,
    wiki_title: str,
    already_has: bool,
) -> str | None:
    """Fetch wiki thumbnail, download to story dir, return local path or None."""
    dest = STORY_DIR / f"{mission_id}.jpg"

    if dest.exists() and dest.stat().st_size > 4000 and already_has:
        path = f"/assets/gta5/story/{mission_id}.jpg"
        print(f"  ✓ {mission_id} (cached)")
        return path

    print(f"  → {mission_id}: querying wiki for '{wiki_title}'…", end=" ", flush=True)
    thumb_url = fetch_thumb_url(session, wiki_title)
    time.sleep(DELAY)

    if not thumb_url:
        print("no image found")
        return None

    if download(session, thumb_url, dest):
        print(f"saved ({dest.stat().st_size // 1024}KB)")
        return f"/assets/gta5/story/{mission_id}.jpg"
    else:
        print("download failed")
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    STORY_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    # ── 1. Heists ─────────────────────────────────────────────────────────────
    print("[fetch_gta5_mission_thumbs] Processing GTA V story heists…")
    heists_raw = load_existing("gta-5/missions/heists.json")
    heists: list[dict] = heists_raw.get("heists", [])

    changed_heists = False
    for h in heists:
        hid = h.get("id", "")
        if hid not in HEIST_WIKI:
            continue
        already = bool(h.get("thumbnail"))
        path = fetch_and_record(session, hid, HEIST_WIKI[hid], already)
        if path and path != h.get("thumbnail"):
            h["thumbnail"] = path
            changed_heists = True

    if changed_heists:
        payload = {**heists_raw, "last_updated": now_iso(), "heists": heists}
        write_json("gta-5/missions/heists.json", payload)
        print("  → heists.json updated")
    else:
        print("  → heists.json unchanged")

    # ── 2. Assassination Stock Guide ──────────────────────────────────────────
    print("[fetch_gta5_mission_thumbs] Processing assassination stock missions…")
    stocks_raw = load_existing("gta-5/economy/assassination-stocks.json")
    guide: list[dict] = stocks_raw.get("guide_order", [])

    changed_stocks = False
    for step in guide:
        mid = step.get("mission_id", "")
        if mid not in ASSASSINATION_WIKI:
            continue
        already = bool(step.get("thumbnail"))
        path = fetch_and_record(session, mid, ASSASSINATION_WIKI[mid], already)
        if path and path != step.get("thumbnail"):
            step["thumbnail"] = path
            changed_stocks = True

    if changed_stocks:
        payload = {**stocks_raw, "last_updated": now_iso(), "guide_order": guide}
        write_json("gta-5/economy/assassination-stocks.json", payload)
        print("  → assassination-stocks.json updated")
    else:
        print("  → assassination-stocks.json unchanged")

    print("[fetch_gta5_mission_thumbs] Done.")


if __name__ == "__main__":
    main()
