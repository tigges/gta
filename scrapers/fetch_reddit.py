"""
Fetch r/GrandTheftAutoVI community data.

Strategy:
1. PRAW (Python Reddit API Wrapper) — if REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET are set
2. Public JSON endpoint — fallback, no credentials needed but rate-limited on server IPs
3. Seed historical milestones — always present, provides chart baseline

Accumulates subscriber snapshots over time (same pattern as YouTube velocity).
Requires: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT env vars.
"""

import json
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import load_existing, now_iso, write_json

OUT_PATH = "community/reddit.json"

SUBREDDIT = "GrandTheftAutoVI"

# Historical subscriber milestones (curated from Wayback Machine / community records)
HISTORICAL_MILESTONES = [
    {"date": "2020-01-01",  "subscribers": 45000,   "event": None},
    {"date": "2022-02-01",  "subscribers": 280000,  "event": "GTA VI in development confirmed"},
    {"date": "2022-09-18",  "subscribers": 420000,  "event": "Rockstar data breach / leak"},
    {"date": "2023-11-01",  "subscribers": 650000,  "event": "Trailer 1 teased"},
    {"date": "2023-12-04",  "subscribers": 1200000, "event": "Trailer 1 released (90M views in 24h)"},
    {"date": "2024-06-01",  "subscribers": 1450000, "event": None},
    {"date": "2025-01-01",  "subscribers": 1700000, "event": None},
    {"date": "2025-05-06",  "subscribers": 2100000, "event": "Trailer 2 released"},
    {"date": "2026-01-01",  "subscribers": 2400000, "event": None},
]


def fetch_via_praw(client_id: str, client_secret: str, user_agent: str) -> dict | None:
    try:
        import praw
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            read_only=True,
        )
        sub = reddit.subreddit(SUBREDDIT)
        return {
            "subscribers": sub.subscribers,
            "active_users": sub.active_user_count,
            "description": sub.public_description[:200] if sub.public_description else "",
        }
    except Exception as e:
        print(f"  PRAW error: {e}")
        return None


def fetch_via_public_json() -> dict | None:
    try:
        resp = requests.get(
            f"https://www.reddit.com/r/{SUBREDDIT}/about.json",
            headers={"User-Agent": "gtavi.ai/1.0"},
            timeout=15,
        )
        if resp.ok:
            d = resp.json()["data"]
            return {
                "subscribers": d["subscribers"],
                "active_users": d.get("active_user_count", 0),
                "description": d.get("public_description", "")[:200],
            }
        print(f"  Public JSON: HTTP {resp.status_code}")
    except Exception as e:
        print(f"  Public JSON error: {e}")
    return None


def main() -> None:
    print(f"Fetching r/{SUBREDDIT} data...")

    client_id     = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent    = os.getenv("REDDIT_USER_AGENT", f"gtavi.ai/1.0 by u/gtavi_bot")

    live_data: dict | None = None

    if client_id and client_secret:
        print("  Using PRAW (credentials available)...")
        live_data = fetch_via_praw(client_id, client_secret, user_agent)
    else:
        print("  No REDDIT_CLIENT_ID set — trying public JSON endpoint...")
        live_data = fetch_via_public_json()

    # Load existing data to preserve snapshot history
    existing = load_existing(OUT_PATH)
    snapshots: list[dict] = existing.get("snapshots", [])

    if live_data:
        subs = live_data["subscribers"]
        print(f"  Live: {subs:,} subscribers, {live_data.get('active_users',0):,} active")
        last_subs = snapshots[-1]["subscribers"] if snapshots else -1
        if subs != last_subs:
            snapshots.append({
                "timestamp": now_iso(),
                "subscribers": subs,
                "active_users": live_data.get("active_users", 0),
            })
    else:
        print("  Could not fetch live data — using historical seed only")
        print("  → Set REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET secrets to enable live polling")

    payload = {
        "last_updated": now_iso(),
        "subreddit": SUBREDDIT,
        "note": "Live snapshots accumulate over time. Historical milestones seeded from community records.",
        "credentials_required": not bool(client_id),
        "historical_milestones": HISTORICAL_MILESTONES,
        "snapshots": snapshots,
    }

    write_json(OUT_PATH, payload)
    print("Reddit data written.")


if __name__ == "__main__":
    main()
