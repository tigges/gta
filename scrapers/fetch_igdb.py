"""
Fetch GTA franchise metadata from IGDB (Twitch API).

Requires:
  TWITCH_CLIENT_ID     — from dev.twitch.tv (free)
  TWITCH_CLIENT_SECRET — from dev.twitch.tv (free)

Add these as secrets in Cursor Cloud Agent settings.

IGDB provides structured game metadata: release dates, ratings, cover art,
involved companies, platforms, genres, themes — across all GTA titles.
"""

import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import has_changed, now_iso, write_json

OUT_PATH = "franchise/igdb.json"

IGDB_BASE = "https://api.igdb.com/v4"

GTA_IGDB_IDS = {
    "gta-1":  124, "gta-2":  125, "gta-3":  126,
    "gta-vc": 127, "gta-sa": 128, "gta-4":  129,
    "gta-5":  1020, "gta-6": 136189,
}


def get_twitch_token(client_id: str, client_secret: str) -> str | None:
    resp = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("access_token")


def fetch_games(ids: list[int], client_id: str, token: str) -> list[dict]:
    id_str = ",".join(str(i) for i in ids)
    body = f"fields name,first_release_date,aggregated_rating,aggregated_rating_count,rating,rating_count,summary,cover.url,platforms.name; where id = ({id_str});"
    resp = requests.post(
        f"{IGDB_BASE}/games",
        headers={"Client-ID": client_id, "Authorization": f"Bearer {token}"},
        data=body,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    client_id     = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("IGDB: TWITCH_CLIENT_ID or TWITCH_CLIENT_SECRET not set.")
        print("→ Add these as secrets in Cursor Cloud Agent dashboard.")
        print("→ Register at https://dev.twitch.tv/console/apps (free)")
        # Write a placeholder so the site doesn't break
        write_json(OUT_PATH, {
            "last_updated": now_iso(),
            "source": "IGDB (Twitch API)",
            "credentials_required": True,
            "note": "Set TWITCH_CLIENT_ID + TWITCH_CLIENT_SECRET to populate this feed.",
            "games": [],
        })
        return

    print("Fetching IGDB franchise metadata...")
    try:
        token = get_twitch_token(client_id, client_secret)
        game_ids = list(GTA_IGDB_IDS.values())
        games = fetch_games(game_ids, client_id, token)
        print(f"  Fetched {len(games)} games")

        payload = {
            "last_updated": now_iso(),
            "source": "IGDB (Twitch API)",
            "credentials_required": False,
            "games": games,
        }

        if has_changed(payload, OUT_PATH):
            write_json(OUT_PATH, payload)
            print("IGDB data updated.")
        else:
            print("No changes.")
    except Exception as e:
        print(f"  IGDB error: {e}")


if __name__ == "__main__":
    main()
