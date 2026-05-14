"""
Post a nightly intelligence digest to a Discord channel via webhook.

Reads the latest scraped data from:
  - data/feeds/newswire.json   → top press articles
  - data/community/reddit.json → top community posts
  - data/gta-6/predictions.json → live prediction snapshot

Requires: DISCORD_WEBHOOK_URL environment variable.

Called by .github/workflows/fetch-data.yml after nightly scrape + commit.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
DATA = Path(__file__).parent.parent / "data"
SITE_URL = "https://gtavi.ai"


def load(path: str) -> dict:
    p = DATA / path
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def build_embed() -> dict:
    news    = load("feeds/newswire.json")
    reddit  = load("community/reddit.json")
    preds   = load("gta-6/predictions.json")

    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    # Top 3 press items
    press_items = (news.get("items") or [])[:3]
    press_lines = "\n".join(
        f"• **[{i['title'][:72]}]({i['url']})** — {i['source_name']}"
        for i in press_items
    ) or "_No press items today_"

    # Top 3 Reddit posts
    reddit_posts = (reddit.get("recent_posts") or [])[:3]
    reddit_lines = "\n".join(
        f"• **[{p['title'][:72]}]({p['url']})**"
        for p in reddit_posts
    ) or "_No community posts today_"

    # Prediction snapshot
    predictions = (preds.get("predictions") or [])
    pred_lines = "\n".join(
        f"• **{p['title']}** — {p['value']} {p.get('unit') or ''} _{p['confidence']}% {p['confidence_tier']}_"
        for p in predictions
    ) or "_No predictions data_"

    return {
        "username": "GTAVI.AI Intelligence Bot",
        "avatar_url": f"https://img.youtube.com/vi/VQRLujxTm3c/mqdefault.jpg",
        "embeds": [
            {
                "title": f"📡 GTAVI.AI — Daily Intel Digest · {today}",
                "url": f"{SITE_URL}/news",
                "color": 0xF59E0B,  # gta-gold
                "fields": [
                    {
                        "name": "📰 Press Coverage",
                        "value": press_lines,
                        "inline": False,
                    },
                    {
                        "name": "🔴 r/GTA6 Community Signal",
                        "value": reddit_lines,
                        "inline": False,
                    },
                    {
                        "name": "📊 Live Signal Predictions",
                        "value": pred_lines,
                        "inline": False,
                    },
                ],
                "footer": {
                    "text": f"gtavi.ai — Data-driven GTA intelligence · Updated nightly",
                    "icon_url": f"https://img.youtube.com/vi/QdBZY2fkU-0/mqdefault.jpg",
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }


def main() -> None:
    if not WEBHOOK_URL:
        print("DISCORD_WEBHOOK_URL not set — skipping digest post.")
        sys.exit(0)

    payload = build_embed()

    resp = requests.post(WEBHOOK_URL, json=payload, timeout=15)
    if resp.status_code in (200, 204):
        print("Discord digest posted successfully.")
    else:
        print(f"Discord post failed: {resp.status_code} — {resp.text[:200]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
