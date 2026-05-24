"""
Gaming conference YouTube channel watcher.

Monitors official YouTube channels for gaming conferences and publishers
that are likely venues for GTA VI marketing events:
  - Summer Game Fest
  - PlayStation (State of Play / Showcase)
  - Xbox (Xbox Showcase)
  - Nintendo (not GTA VI, but context)
  - Rockstar Games (already tracked by fetch_trailers.py — included for completeness)
  - Take-Two Interactive (investor presentations)

Looks for GTA VI-related uploads. Output appended to feeds/newswire.json
as "official" tier items (when from publisher channels) or "press" tier
(when from conference channels).

Requires: YOUTUBE_API_KEY env var
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import has_changed, now_iso, write_json, load_existing

import requests

API_KEY  = os.environ.get("YOUTUBE_API_KEY", "")
OUT_PATH = "feeds/conference-news.json"

GTA_KEYWORDS = [
    "gta", "grand theft auto", "gta 6", "gta vi",
    "gta online", "rockstar", "take-two",
]

# Official channels to monitor
# Each entry: channel_id, display_name, tier
CHANNELS = [
    ("UCsbjFG2UrM_L3AIc0GBiKSA", "Summer Game Fest",    "press"),
    ("UC-2Y8dQb0S6DtpxNgAKoaKQ", "PlayStation",         "press"),
    ("UCbubu1nMGMXYpMNMTh8ruhQ", "Xbox",                "press"),
    ("UCO-pFAiMsvFpMVQhpSlgFpw", "Rockstar Games",      "official"),
    ("UCvnS1c4T_E8UnBkzgDRR-nw", "Take-Two Interactive","official"),
]

HEADERS = {"Accept": "application/json"}


def is_gta_related(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in GTA_KEYWORDS)


def fetch_channel_uploads(channel_id: str, name: str, tier: str) -> list[dict]:
    if not API_KEY:
        print(f"  ✗ {name}: YOUTUBE_API_KEY not set")
        return []
    try:
        # Get uploads playlist ID from channel
        ch_resp = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "contentDetails", "id": channel_id, "key": API_KEY},
            headers=HEADERS, timeout=15,
        )
        if not ch_resp.ok:
            print(f"  ✗ {name}: channel HTTP {ch_resp.status_code}")
            return []

        ch_data = ch_resp.json()
        items = ch_data.get("items", [])
        if not items:
            print(f"  ✗ {name}: channel not found")
            return []

        uploads_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

        # Fetch recent uploads (last 10)
        pl_resp = requests.get(
            "https://www.googleapis.com/youtube/v3/playlistItems",
            params={
                "part": "snippet",
                "playlistId": uploads_id,
                "maxResults": 10,
                "key": API_KEY,
            },
            headers=HEADERS, timeout=15,
        )
        if not pl_resp.ok:
            print(f"  ✗ {name}: playlist HTTP {pl_resp.status_code}")
            return []

        results = []
        for item in pl_resp.json().get("items", []):
            snip  = item.get("snippet", {})
            title = snip.get("title", "")
            desc  = snip.get("description", "")[:200]
            vid   = snip.get("resourceId", {}).get("videoId", "")
            date  = snip.get("publishedAt", "")[:10]

            # For publisher channels (Rockstar, Take-Two): include all uploads
            # For conference channels: filter to GTA-related content only
            if tier == "press" and not is_gta_related(title + " " + desc):
                continue

            results.append({
                "source_id":    f"youtube-{channel_id[:8]}",
                "source_name":  name,
                "tier":         tier,
                "title":        title,
                "url":          f"https://www.youtube.com/watch?v={vid}",
                "published_at": f"{date}T00:00:00Z" if date else None,
                "summary":      desc.strip(),
            })

        print(f"  ✓ {name}: {len(results)} GTA-relevant upload(s)")
        return results

    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return []


def main() -> None:
    if not API_KEY:
        print("YOUTUBE_API_KEY not set — skipping conference news fetch")
        return

    print("Fetching gaming conference & publisher YouTube uploads...")
    all_items: list[dict] = []

    for channel_id, name, tier in CHANNELS:
        all_items.extend(fetch_channel_uploads(channel_id, name, tier))

    # Deduplicate by URL
    seen: set[str] = set()
    unique = []
    for item in all_items:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    gta_count  = sum(1 for i in unique if is_gta_related(i.get("title","") + " " + i.get("summary","")))
    official   = [i for i in unique if i["tier"] == "official"]
    print(f"  Total: {len(unique)} uploads ({gta_count} GTA-related, {len(official)} official channels)")

    payload = {
        "last_updated": now_iso(),
        "channels_monitored": len(CHANNELS),
        "items": unique,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("Conference news updated.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
