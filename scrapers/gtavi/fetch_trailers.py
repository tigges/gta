"""
Fetch official GTA VI trailer data from Rockstar sources.

Strategy (attempted in order):
1. YouTube Data API  — if YOUTUBE_API_KEY env var is set (most reliable)
2. Rockstar GTA VI page — scrape embedded YouTube iframes
3. Rockstar Newswire RSS — parse trailer announcement posts

All three methods extract YouTube video IDs. Duplicates are removed;
order preserved so Trailer 1 stays first.
"""

import os
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scrapers"))
from utils import has_changed, now_iso, write_json

OUT_PATH = "gta-6/trailers.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

ROCKSTAR_PAGES = [
    "https://www.rockstargames.com/VI",
    "https://www.rockstargames.com/games/grand-theft-auto-VI",
]

NEWSWIRE_FEEDS = [
    "https://www.rockstargames.com/newswire/feed",
    "https://www.rockstargames.com/newswire/rss",
]

# Matches youtube.com/embed/ID, youtube.com/watch?v=ID, youtu.be/ID
YT_ID_RE = re.compile(
    r"(?:youtube\.com/(?:embed/|watch\?(?:[^&\"' ]*&)*v=)|youtu\.be/)([a-zA-Z0-9_-]{11})"
)

ROCKSTAR_CHANNEL_ID = "UCuKONQfAQZJMKxOvj5XpHbA"

GTA6_KEYWORDS = ["gta vi", "gta 6", "grand theft auto vi", "grand theft auto 6"]
TRAILER_KEYWORDS = ["trailer"]


def _extract_yt_ids(text: str) -> list[str]:
    return list(dict.fromkeys(YT_ID_RE.findall(text)))


def _is_gta6_trailer(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in GTA6_KEYWORDS) and any(k in t for k in TRAILER_KEYWORDS)


def fetch_from_rockstar_pages() -> list[dict]:
    for url in ROCKSTAR_PAGES:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if not resp.ok:
                continue
            ids = _extract_yt_ids(resp.text)
            if not ids:
                continue
            trailers = [
                {
                    "youtube_id": yt_id,
                    "title": f"Grand Theft Auto VI — Trailer {i + 1}" if i > 0 else "Grand Theft Auto VI — Trailer 1",
                    "source_url": url,
                    "published_at": None,
                }
                for i, yt_id in enumerate(ids)
            ]
            print(f"  Rockstar page: found {len(trailers)} trailer(s)")
            return trailers
        except Exception as e:
            print(f"  Rockstar page error ({url}): {e}")
    return []


def fetch_from_newswire() -> list[dict]:
    for feed_url in NEWSWIRE_FEEDS:
        try:
            resp = requests.get(feed_url, headers=HEADERS, timeout=30)
            if not resp.ok:
                continue
            soup = BeautifulSoup(resp.text, "lxml-xml")
            items = soup.find_all("item")
            trailers = []
            for item in items:
                title_tag = item.find("title")
                title = title_tag.get_text(strip=True) if title_tag else ""
                if not _is_gta6_trailer(title):
                    continue
                pub_tag = item.find("pubDate")
                pub_raw = pub_tag.get_text(strip=True) if pub_tag else ""
                pub_date = pub_raw[:10] if len(pub_raw) >= 10 else None
                for yt_id in _extract_yt_ids(str(item)):
                    trailers.append({
                        "youtube_id": yt_id,
                        "title": title,
                        "published_at": pub_date,
                        "source_url": feed_url,
                    })
            if trailers:
                print(f"  Newswire: found {len(trailers)} trailer(s)")
                return trailers
        except Exception as e:
            print(f"  Newswire error ({feed_url}): {e}")
    return []


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


def fetch() -> list[dict]:
    api_key = os.getenv("YOUTUBE_API_KEY")
    if api_key:
        trailers = fetch_from_youtube_api(api_key)
        if trailers:
            return trailers

    trailers = fetch_from_rockstar_pages()
    if trailers:
        return trailers

    return fetch_from_newswire()


def main() -> None:
    print("Fetching GTA VI trailer data...")
    trailers = fetch()

    if not trailers:
        print("  No trailers found — keeping existing data unchanged")
        return

    print(f"  Total: {len(trailers)} trailer(s)")

    payload = {
        "last_updated": now_iso(),
        "source": "rockstargames.com + YouTube",
        "trailers": trailers,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("Data updated.")
    else:
        print("No changes detected, skipping write.")


if __name__ == "__main__":
    main()
