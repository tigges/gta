#!/usr/bin/env python3
"""
fetch_gtaonline_dlc_art.py — Fetches official GTA Online DLC trailer thumbnails.

Uses the YouTube Data API to find official Rockstar Games DLC trailers,
then downloads the maxresdefault thumbnails into /assets/gta5/dlc/.

This gives us legitimate, game-appropriate thumbnails for GTA Online
business and heist profile cards (replacing the GTA V cover fallback).

Output: public/assets/gta5/dlc/{dlc-id}.jpg
        data/gta-5/economy/dlc-trailers.json (ID registry)

Usage:
  YOUTUBE_API_KEY=... python3 scrapers/fetch_gtaonline_dlc_art.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from utils import write_json, has_changed, load_existing, now_iso

try:
    import requests
except ImportError:
    print("[fetch_gtaonline_dlc_art] requests not available")
    requests = None

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
OUTPUT_JSON = "data/gta-5/economy/dlc-trailers.json"
ASSET_DIR   = "public/assets/gta5/dlc"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; gtavi-ai-bot/1.0; +https://gtavi.ai)"}

# Official DLC search terms → asset ID
# Search Rockstar's official channel (UCob6ZOo5qY6BEjPS9cGOe9A) for these terms
DLC_SEARCHES = [
    { "id": "cayo-perico",          "query": "GTA Online The Cayo Perico Heist Trailer",    "channel": "UCob6ZOo5qY6BEjPS9cGOe9A" },
    { "id": "diamond-casino-heist", "query": "GTA Online The Diamond Casino Heist Trailer",  "channel": "UCob6ZOo5qY6BEjPS9cGOe9A" },
    { "id": "the-contract",         "query": "GTA Online The Contract Trailer",              "channel": "UCob6ZOo5qY6BEjPS9cGOe9A" },
    { "id": "after-hours",          "query": "GTA Online After Hours Trailer",               "channel": "UCob6ZOo5qY6BEjPS9cGOe9A" },
    { "id": "gunrunning",           "query": "GTA Online Gunrunning Trailer",                "channel": "UCob6ZOo5qY6BEjPS9cGOe9A" },
    { "id": "acid-lab",             "query": "GTA Online Los Santos Drug Wars Trailer",      "channel": "UCob6ZOo5qY6BEjPS9cGOe9A" },
    { "id": "auto-shop",            "query": "GTA Online Los Santos Tuners Trailer",         "channel": "UCob6ZOo5qY6BEjPS9cGOe9A" },
    { "id": "chop-shop",            "query": "GTA Online The Chop Shop Trailer",             "channel": "UCob6ZOo5qY6BEjPS9cGOe9A" },
    { "id": "agency-vip-contract",  "query": "GTA Online The Contract Trailer Franklin",     "channel": "UCob6ZOo5qY6BEjPS9cGOe9A" },
]


def search_youtube(session, query: str, channel_id: str) -> str | None:
    """Search YouTube API for a video ID matching the query on the Rockstar channel."""
    if not YOUTUBE_API_KEY:
        return None
    
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key":        YOUTUBE_API_KEY,
        "q":          query,
        "channelId":  channel_id,
        "type":       "video",
        "part":       "snippet",
        "maxResults": 3,
        "order":      "relevance",
    }
    try:
        resp = session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        if items:
            vid_id = items[0]["id"]["videoId"]
            title  = items[0]["snippet"]["title"]
            print(f"  Found: {title} → {vid_id}")
            return vid_id
    except Exception as e:
        print(f"  [warn] YouTube search failed for '{query}': {e}")
    return None


def download_thumbnail(session, video_id: str, dest_path: str) -> bool:
    """Download the best available YouTube thumbnail."""
    for quality in ["maxresdefault", "hqdefault", "mqdefault"]:
        url = f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
        try:
            resp = session.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 5000:
                with open(dest_path, "wb") as f:
                    f.write(resp.content)
                return True
        except Exception:
            pass
    return False


def main():
    if not requests:
        print("[fetch_gtaonline_dlc_art] requests not available — skipping")
        return
    
    if not YOUTUBE_API_KEY:
        print("[fetch_gtaonline_dlc_art] YOUTUBE_API_KEY not set — skipping")
        return

    os.makedirs(ASSET_DIR, exist_ok=True)
    existing = load_existing(OUTPUT_JSON)
    registry = existing.get("trailers", {})
    
    session = requests.Session()
    downloaded = 0
    
    for dlc in DLC_SEARCHES:
        dlc_id   = dlc["id"]
        dest     = os.path.join(ASSET_DIR, f"{dlc_id}.jpg")
        
        # Skip if already downloaded
        if os.path.exists(dest) and os.path.getsize(dest) > 5000:
            if dlc_id not in registry:
                registry[dlc_id] = {"path": f"/assets/gta5/dlc/{dlc_id}.jpg", "source": "cached"}
            continue
        
        print(f"[fetch_gtaonline_dlc_art] Searching for: {dlc['id']}")
        vid_id = search_youtube(session, dlc["query"], dlc["channel"])
        
        if vid_id:
            if download_thumbnail(session, vid_id, dest):
                registry[dlc_id] = {
                    "youtube_id": vid_id,
                    "path": f"/assets/gta5/dlc/{dlc_id}.jpg",
                    "query": dlc["query"],
                    "source": "youtube",
                }
                downloaded += 1
                print(f"  ✓ Downloaded {dlc_id}.jpg")
            else:
                print(f"  ✗ Could not download thumbnail for {dlc_id}")
        
        time.sleep(0.5)  # polite delay

    result = {
        "last_updated": now_iso(),
        "source": "YouTube Data API — official Rockstar Games channel",
        "note": "Use paths in registry to populate BIZ_THUMBS in database.astro",
        "trailers": registry,
    }

    if has_changed(result, OUTPUT_JSON):
        write_json(OUTPUT_JSON, result)
        print(f"[fetch_gtaonline_dlc_art] Downloaded {downloaded} thumbnails. Registry saved.")
    else:
        print("[fetch_gtaonline_dlc_art] No changes.")


if __name__ == "__main__":
    main()
