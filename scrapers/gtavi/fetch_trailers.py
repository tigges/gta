"""
Fetch official GTA VI trailer data.

Strategy (attempted in order):
1. YouTube Data API  — if YOUTUBE_API_KEY env var is set (most reliable, gets dates + titles)
2. YouTube search scrape — searches YouTube for "Grand Theft Auto VI Trailer" without an API key
3. Hardcoded fallback  — known-good YouTube IDs for Trailer 1 and Trailer 2

All methods extract YouTube video IDs. Duplicates are removed; order is preserved
so Trailer 1 stays first.
"""

import os
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import has_changed, now_iso, write_json

OUT_PATH = "gta-6/trailers.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

ROCKSTAR_CHANNEL_ID = "UCuKONQfAQZJMKxOvj5XpHbA"
GTA6_KEYWORDS = ["gta vi", "gta 6", "grand theft auto vi", "grand theft auto 6"]
TRAILER_KEYWORDS = ["trailer"]

# Known-good YouTube IDs — update when new trailers are released
KNOWN_TRAILERS = [
    {
        "youtube_id": "QdBZY2fkU-0",
        "title": "Grand Theft Auto VI — Trailer 1",
        "published_at": "2023-12-04",
        "source_url": "https://www.youtube.com/watch?v=QdBZY2fkU-0",
    },
    {
        "youtube_id": "VQRLujxTm3c",
        "title": "Grand Theft Auto VI — Trailer 2",
        "published_at": "2025-05-06",
        "source_url": "https://www.youtube.com/watch?v=VQRLujxTm3c",
    },
]


def _is_gta6_trailer(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in GTA6_KEYWORDS) and any(k in t for k in TRAILER_KEYWORDS)


def _dedup(trailers: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out = []
    for t in trailers:
        if t["youtube_id"] not in seen:
            seen.add(t["youtube_id"])
            out.append(t)
    return out


def fetch_from_youtube_api(api_key: str) -> list[dict]:
    try:
        from googleapiclient.discovery import build
        youtube = build("youtube", "v3", developerKey=api_key)
        response = youtube.search().list(
            part="snippet",
            channelId=ROCKSTAR_CHANNEL_ID,
            q="Grand Theft Auto VI Trailer",
            type="video",
            order="date",
            maxResults=10,
        ).execute()
        trailers = [
            {
                "youtube_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "published_at": item["snippet"]["publishedAt"][:10],
                "source_url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
            }
            for item in response.get("items", [])
            if _is_gta6_trailer(item["snippet"]["title"])
        ]
        if trailers:
            print(f"  YouTube API: found {len(trailers)} trailer(s)")
        return trailers
    except Exception as e:
        print(f"  YouTube API error: {e}")
        return []


OFFICIAL_CHANNEL_NAMES = {"rockstar games", "rockstargames"}


def fetch_from_youtube_search() -> list[dict]:
    """Scrape YouTube search results for GTA VI trailer videos, filtered to official channel."""
    try:
        search_url = (
            "https://www.youtube.com/results"
            "?search_query=Grand+Theft+Auto+VI+Trailer+Rockstar+Games"
        )
        resp = requests.get(search_url, headers=HEADERS, timeout=30)
        if not resp.ok:
            return []

        # YouTube embeds initial data as a JSON blob in a script tag
        match = re.search(r"var ytInitialData = ({.+?});</script>", resp.text, re.DOTALL)
        if not match:
            return []

        import json
        data = json.loads(match.group(1))

        # Walk the contents tree for videoRenderer objects
        def extract_videos(obj):
            if isinstance(obj, dict):
                if "videoId" in obj and "title" in obj and "ownerText" in obj:
                    title_runs = obj.get("title", {}).get("runs", [])
                    title = "".join(r.get("text", "") for r in title_runs)

                    # Extract channel name
                    channel_runs = obj.get("ownerText", {}).get("runs", [])
                    channel = "".join(r.get("text", "") for r in channel_runs).lower()

                    if _is_gta6_trailer(title) and channel in OFFICIAL_CHANNEL_NAMES:
                        yield {
                            "youtube_id": obj["videoId"],
                            "title": title,
                            "published_at": None,
                            "source_url": f"https://www.youtube.com/watch?v={obj['videoId']}",
                        }
                for v in obj.values():
                    yield from extract_videos(v)
            elif isinstance(obj, list):
                for item in obj:
                    yield from extract_videos(item)

        trailers = list(extract_videos(data))
        trailers = _dedup(trailers)
        if trailers:
            print(f"  YouTube search: found {len(trailers)} official trailer(s)")
        return trailers
    except Exception as e:
        print(f"  YouTube search error: {e}")
        return []


def fetch_from_known_ids() -> list[dict]:
    """Verify known YouTube IDs are still accessible and return them."""
    valid = []
    for trailer in KNOWN_TRAILERS:
        try:
            url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={trailer['youtube_id']}&format=json"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.ok:
                data = resp.json()
                valid.append({
                    **trailer,
                    # Use oembed title if it's more descriptive
                    "title": data.get("title", trailer["title"]),
                })
            else:
                # Video may be restricted but still exists — include anyway
                valid.append(trailer)
        except Exception:
            valid.append(trailer)
    if valid:
        print(f"  Known IDs fallback: returning {len(valid)} trailer(s)")
    return valid


def fetch() -> list[dict]:
    api_key = os.getenv("YOUTUBE_API_KEY")
    if api_key:
        trailers = fetch_from_youtube_api(api_key)
        if trailers:
            return _dedup(trailers)

    trailers = fetch_from_youtube_search()
    if trailers:
        return _dedup(trailers)

    return _dedup(fetch_from_known_ids())


def main() -> None:
    print("Fetching GTA VI trailer data...")
    trailers = fetch()

    if not trailers:
        print("  No trailers found — keeping existing data unchanged")
        return

    print(f"  Total: {len(trailers)} trailer(s)")
    for t in trailers:
        print(f"    {t['title']} ({t['youtube_id']}) — {t.get('published_at', 'date unknown')}")

    payload = {
        "last_updated": now_iso(),
        "source": "YouTube / rockstargames.com",
        "trailers": trailers,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("Data updated.")
    else:
        print("No changes detected, skipping write.")


if __name__ == "__main__":
    main()
