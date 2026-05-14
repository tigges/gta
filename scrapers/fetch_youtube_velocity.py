"""
Accumulate YouTube view/like counts for GTA VI trailers over time.

Each run appends a timestamped snapshot to the trailer's history.
This builds a view-velocity curve showing how fast each trailer
accumulated views — T1 set a 24h record with 90M views.

Strategy:
1. YouTube Data API v3  — if YOUTUBE_API_KEY is set (accurate)
2. YouTube page scrape  — fallback, parses ytInitialData JSON

Existing snapshots are preserved; new snapshot appended if count changed.
"""

import json
import os
import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import load_existing, now_iso, write_json

OUT_PATH = "gta-6/trailer-velocity.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

TRAILERS = [
    {
        "youtube_id":   "QdBZY2fkU-0",
        "title":        "Grand Theft Auto VI — Trailer 1",
        "published_at": "2023-12-04",
    },
    {
        "youtube_id":   "VQRLujxTm3c",
        "title":        "Grand Theft Auto VI — Trailer 2",
        "published_at": "2025-05-06",
    },
]


def fetch_via_api(video_id: str, api_key: str) -> dict | None:
    url = (
        f"https://www.googleapis.com/youtube/v3/videos"
        f"?part=statistics,snippet&id={video_id}&key={api_key}"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            return None
        stats = items[0]["statistics"]
        return {
            "views":    int(stats.get("viewCount", 0)),
            "likes":    int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
        }
    except Exception as e:
        print(f"    API error for {video_id}: {e}")
        return None


def fetch_via_scrape(video_id: str) -> dict | None:
    """Parse ytInitialData embedded in the YouTube watch page."""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if not resp.ok:
            return None

        # Find the inline JSON data block
        match = re.search(r"var ytInitialData\s*=\s*(\{.+?\});</script>", resp.text, re.DOTALL)
        if not match:
            return None

        data = json.loads(match.group(1))

        # Walk for videoDetails or viewCount
        text = resp.text
        view_match   = re.search(r'"viewCount":\s*\{\s*"videoViewCountRenderer":\s*\{\s*"viewCount":\s*\{"simpleText":"([^"]+)"', text)
        if not view_match:
            # try alternate path
            view_match = re.search(r'"viewCount":"(\d+)"', text)
        like_match   = re.search(r'"label":"([0-9,]+) likes"', text)

        views = 0
        if view_match:
            raw = view_match.group(1).replace(",", "").replace(" views", "").strip()
            try:
                views = int(raw)
            except ValueError:
                pass

        likes = 0
        if like_match:
            try:
                likes = int(like_match.group(1).replace(",", ""))
            except ValueError:
                pass

        if views == 0:
            return None

        return {"views": views, "likes": likes, "comments": 0}

    except Exception as e:
        print(f"    Scrape error for {video_id}: {e}")
        return None


def main() -> None:
    print("Fetching YouTube trailer velocity...")
    api_key = os.getenv("YOUTUBE_API_KEY")

    existing = load_existing(OUT_PATH)
    trailers_out = {t["youtube_id"]: t for t in existing.get("trailers", [])}

    for trailer in TRAILERS:
        vid = trailer["youtube_id"]
        print(f"  [{trailer['title']}]")

        if api_key:
            stats = fetch_via_api(vid, api_key)
            method = "api"
        else:
            stats = fetch_via_scrape(vid)
            method = "scrape"

        if not stats:
            print(f"    Could not fetch stats (method={method}) — keeping existing")
            if vid not in trailers_out:
                trailers_out[vid] = {**trailer, "fetch_method": method, "snapshots": []}
            continue

        print(f"    views={stats['views']:,}  likes={stats['likes']:,}  method={method}")

        if vid not in trailers_out:
            trailers_out[vid] = {**trailer, "fetch_method": method, "snapshots": []}

        snapshots = trailers_out[vid].get("snapshots", [])

        # Only append if count changed since last snapshot
        last_views = snapshots[-1]["views"] if snapshots else -1
        if stats["views"] != last_views:
            snapshots.append({
                "timestamp": now_iso(),
                "views":    stats["views"],
                "likes":    stats["likes"],
                "comments": stats.get("comments", 0),
            })
            trailers_out[vid]["snapshots"] = snapshots
            trailers_out[vid]["fetch_method"] = method

    payload = {
        "last_updated": now_iso(),
        "note": "Snapshots accumulate over time to build a view-velocity curve.",
        "trailers": list(trailers_out.values()),
    }

    write_json(OUT_PATH, payload)
    print("Velocity data updated.")


if __name__ == "__main__":
    main()
