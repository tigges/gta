#!/usr/bin/env python3
"""
fetch_gta5_assets.py — Downloads GTA V story mode and character assets.

Sources:
  - YouTube Data API: Official Rockstar GTA V trailers (story + character)
  - GTA Wiki (Fandom): Character/location OG images

Output:
  public/assets/gta5/characters/  — Michael, Trevor, Franklin official art
  public/assets/gta5/locations/   — Los Santos, Blaine County art
  public/assets/gta5/story/       — Story DLC and heist key art
  data/gta-5/assets-registry.json — Full registry of all sourced assets

Usage:
  YOUTUBE_API_KEY=... python3 scrapers/fetch_gta5_assets.py
"""

import os
import sys
import time
import json

sys.path.insert(0, os.path.dirname(__file__))
from utils import write_json, has_changed, load_existing, now_iso

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[fetch_gta5_assets] requests/bs4 missing")
    requests = None
    BeautifulSoup = None

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
OUTPUT_REGISTRY = "gta-5/assets-registry.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; gtavi-ai-bot/1.0; +https://gtavi.ai)"}

ASSET_DIRS = {
    "characters": "public/assets/gta5/characters",
    "locations":  "public/assets/gta5/locations",
    "story":      "public/assets/gta5/story",
    "dlc":        "public/assets/gta5/dlc",
}

# ── YouTube searches for official Rockstar GTA V content ─────────────────────
YOUTUBE_SEARCHES = [
    # Story mode trailers (characters in official footage)
    { "id": "michael",          "folder": "characters", "query": "GTA V Michael De Santa Official Trailer Rockstar" },
    { "id": "trevor",           "folder": "characters", "query": "GTA V Trevor Philips Official Trailer Rockstar" },
    { "id": "franklin",         "folder": "characters", "query": "GTA V Franklin Clinton Official Trailer Rockstar" },
    { "id": "gta-v-launch",     "folder": "story",      "query": "Grand Theft Auto V Official Launch Trailer Rockstar" },
    { "id": "heists",           "folder": "story",      "query": "GTA Online Heists Official Trailer Rockstar 2015" },
    { "id": "los-santos",       "folder": "locations",  "query": "GTA V Los Santos Official Trailer Rockstar Games" },
    # GTA V anniversary / promotional content
    { "id": "gta-v-cover",      "folder": "story",      "query": "GTA V Grand Theft Auto 5 Official Gameplay Trailer Rockstar" },
]

# ── GTA Wiki pages with good OG images ───────────────────────────────────────
WIKI_PAGES = [
    { "id": "michael-wiki",   "folder": "characters", "url": "https://gta.fandom.com/wiki/Michael_De_Santa" },
    { "id": "trevor-wiki",    "folder": "characters", "url": "https://gta.fandom.com/wiki/Trevor_Philips" },
    { "id": "franklin-wiki",  "folder": "characters", "url": "https://gta.fandom.com/wiki/Franklin_Clinton" },
    { "id": "los-santos-wiki","folder": "locations",  "url": "https://gta.fandom.com/wiki/Los_Santos_(HD_Universe)" },
    { "id": "grove-st-wiki",  "folder": "locations",  "url": "https://gta.fandom.com/wiki/Grove_Street" },
]


def youtube_search(session, query: str) -> tuple[str, str] | None:
    """Returns (video_id, title) or None."""
    if not YOUTUBE_API_KEY:
        return None
    try:
        r = session.get("https://www.googleapis.com/youtube/v3/search", params={
            "key": YOUTUBE_API_KEY, "q": query, "type": "video",
            "part": "snippet", "maxResults": 1, "order": "relevance"
        }, timeout=10)
        items = r.json().get("items", [])
        if items:
            return items[0]["id"]["videoId"], items[0]["snippet"]["title"]
    except Exception as e:
        print(f"  [warn] YouTube search failed: {e}")
    return None


def fetch_og_image(session, url: str) -> str | None:
    """Extract og:image from a page."""
    try:
        resp = session.get(url, headers=HEADERS, timeout=12)
        if not resp.ok:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        tag = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
        if tag and tag.get("content"):
            img = tag["content"].strip()
            return ("https:" + img) if img.startswith("//") else img
    except Exception as e:
        print(f"  [warn] OG fetch failed for {url}: {e}")
    return None


def download_yt_thumbnail(session, video_id: str, dest: str) -> bool:
    for quality in ["maxresdefault", "hqdefault"]:
        url = f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
        try:
            r = session.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200 and len(r.content) > 8000:
                with open(dest, "wb") as f:
                    f.write(r.content)
                return True
        except Exception:
            pass
    return False


def download_image(session, url: str, dest: str) -> bool:
    try:
        r = session.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200 and len(r.content) > 5000:
            with open(dest, "wb") as f:
                f.write(r.content)
            return True
    except Exception:
        pass
    return False


def main():
    if not requests:
        print("[fetch_gta5_assets] requests missing — skipping")
        return

    for d in ASSET_DIRS.values():
        os.makedirs(d, exist_ok=True)

    existing = load_existing(OUTPUT_REGISTRY)
    registry = existing.get("assets", {})
    session = requests.Session()
    downloaded = 0

    # ── YouTube thumbnails for story trailers ─────────────────────────────────
    if YOUTUBE_API_KEY:
        print("[fetch_gta5_assets] Fetching GTA V story assets via YouTube API...")
        for item in YOUTUBE_SEARCHES:
            dest = os.path.join(ASSET_DIRS[item["folder"]], f"{item['id']}.jpg")
            if os.path.exists(dest) and os.path.getsize(dest) > 5000:
                registry.setdefault(item["id"], {"path": f"/assets/gta5/{item['folder']}/{item['id']}.jpg", "source": "cached"})
                continue

            result = youtube_search(session, item["query"])
            if result:
                vid_id, title = result
                if download_yt_thumbnail(session, vid_id, dest):
                    registry[item["id"]] = {
                        "youtube_id": vid_id,
                        "path": f"/assets/gta5/{item['folder']}/{item['id']}.jpg",
                        "title": title[:60],
                        "source": "youtube",
                        "game": "gta-5",
                    }
                    downloaded += 1
                    print(f"  ✓ {item['id']}: {title[:50]}")
            time.sleep(0.4)
    else:
        print("[fetch_gta5_assets] No YOUTUBE_API_KEY — skipping YouTube sources")

    # ── GTA Wiki OG images for characters/locations ───────────────────────────
    print("[fetch_gta5_assets] Fetching GTA Wiki character/location images...")
    for item in WIKI_PAGES:
        dest = os.path.join(ASSET_DIRS[item["folder"]], f"{item['id']}.jpg")
        if os.path.exists(dest) and os.path.getsize(dest) > 5000:
            registry.setdefault(item["id"], {"path": f"/assets/gta5/{item['folder']}/{item['id']}.jpg", "source": "cached"})
            continue

        img_url = fetch_og_image(session, item["url"])
        if img_url:
            if download_image(session, img_url, dest):
                registry[item["id"]] = {
                    "path": f"/assets/gta5/{item['folder']}/{item['id']}.jpg",
                    "source_url": item["url"],
                    "source": "gta-wiki",
                    "game": "gta-5",
                }
                downloaded += 1
                print(f"  ✓ {item['id']} from GTA Wiki")
        time.sleep(1.0)  # polite delay for wiki

    result = {
        "last_updated": now_iso(),
        "source": "YouTube Data API + GTA Wiki (Fandom)",
        "note": "GTA V story mode and character assets. Game-separated from GTA VI press kit.",
        "assets": registry,
    }

    if has_changed(result, OUTPUT_REGISTRY):
        write_json(OUTPUT_REGISTRY, result)
        print(f"[fetch_gta5_assets] Downloaded {downloaded} assets. Registry saved.")
    else:
        print("[fetch_gta5_assets] No changes.")


if __name__ == "__main__":
    main()
