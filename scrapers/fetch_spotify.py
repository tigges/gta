"""
Fetch GTA radio station playlist data from Spotify.

Requires:
  SPOTIFY_CLIENT_ID     — from developer.spotify.com (free)
  SPOTIFY_CLIENT_SECRET — from developer.spotify.com (free)

Add these as secrets in Cursor Cloud Agent settings.

Collects: GTA V radio station playlists, GTA VI teased songs (Hot Together,
Love Is a Long Road from trailers), estimated soundtrack track counts.
"""

import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import has_changed, now_iso, write_json

OUT_PATH = "franchise/spotify.json"

# GTA V radio stations on Spotify (official Rockstar playlists)
GTA5_STATION_QUERIES = [
    "GTA V Los Santos Rock Radio",
    "GTA V Radio Mirror Park",
    "GTA V Vinewood Boulevard Radio",
    "GTA V East Los FM",
    "GTA V West Coast Classics",
]

# Songs confirmed in GTA VI trailers
GTA6_CONFIRMED_SONGS = [
    {"title": "Love Is a Long Road", "artist": "Tom Petty",           "trailer": "Trailer 1", "year": 1989},
    {"title": "Hot Together",        "artist": "The Pointer Sisters", "trailer": "Trailer 2", "year": 1986},
]


def get_token(client_id: str, client_secret: str) -> str | None:
    import base64
    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {creds}"},
        data={"grant_type": "client_credentials"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("access_token")


def search_playlist(query: str, token: str) -> dict | None:
    resp = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": query, "type": "playlist", "limit": 1},
        timeout=15,
    )
    if not resp.ok:
        return None
    items = resp.json().get("playlists", {}).get("items", [])
    return items[0] if items else None


def main() -> None:
    client_id     = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("Spotify: SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not set.")
        print("→ Add these as secrets in Cursor Cloud Agent dashboard.")
        print("→ Register at https://developer.spotify.com/dashboard (free)")
        write_json(OUT_PATH, {
            "last_updated": now_iso(),
            "source": "Spotify Web API",
            "credentials_required": True,
            "note": "Set SPOTIFY_CLIENT_ID + SPOTIFY_CLIENT_SECRET to populate.",
            "confirmed_songs": GTA6_CONFIRMED_SONGS,
            "playlists": [],
        })
        return

    print("Fetching Spotify GTA data...")
    try:
        token = get_token(client_id, client_secret)
    except Exception as e:
        print(f"  Spotify auth failed: {e}")
        print("  → Check SPOTIFY_CLIENT_ID + SPOTIFY_CLIENT_SECRET are correct.")
        return
    playlists = []

    for query in GTA5_STATION_QUERIES:
        pl = search_playlist(query, token)
        if pl:
            playlists.append({
                "name": pl["name"],
                "id": pl["id"],
                "tracks": pl.get("tracks", {}).get("total", 0),
                "url": pl["external_urls"].get("spotify"),
                "owner": pl["owner"]["display_name"],
            })
            print(f"  Found: {pl['name']} ({pl.get('tracks',{}).get('total',0)} tracks)")

    payload = {
        "last_updated": now_iso(),
        "source": "Spotify Web API",
        "credentials_required": False,
        "confirmed_songs": GTA6_CONFIRMED_SONGS,
        "playlists": playlists,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("Spotify data updated.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
