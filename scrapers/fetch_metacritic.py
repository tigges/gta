"""
Fetch Metacritic review scores for mainline GTA titles.

Strategy:
1. Attempt JSON-LD extraction from Metacritic game pages
2. Fall back to curated seed data (scores are immutable historical records)

The critic-vs-user delta is the story: GTA IV has the widest gap (98 critic,
7.6 user) — the first title to introduce aggressive monetisation. GTA SA has
the tightest (95 critic, 9.5 user) — the community high-water mark.
"""

import json
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from utils import has_changed, now_iso, write_json

OUT_PATH = "franchise/metacritic.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

# Canonical seed — Metacritic scores are permanent historical records
# Scores are the highest-platform version (PS2 era) or PS3/360 (HD era)
SEED = [
    {
        "id": "gta-3", "short": "GTA III",
        "year": 2001, "platform": "PS2",
        "critic_score": 97, "user_score": 8.6,
        "critic_count": 23, "user_count": None,
        "url": "https://www.metacritic.com/game/grand-theft-auto-iii/",
    },
    {
        "id": "gta-vc", "short": "GTA VC",
        "year": 2002, "platform": "PS2",
        "critic_score": 95, "user_score": 9.0,
        "critic_count": 42, "user_count": None,
        "url": "https://www.metacritic.com/game/grand-theft-auto-vice-city/",
    },
    {
        "id": "gta-sa", "short": "GTA SA",
        "year": 2004, "platform": "PS2",
        "critic_score": 95, "user_score": 9.5,
        "critic_count": 53, "user_count": None,
        "url": "https://www.metacritic.com/game/grand-theft-auto-san-andreas/",
    },
    {
        "id": "gta-4", "short": "GTA IV",
        "year": 2008, "platform": "PS3",
        "critic_score": 98, "user_score": 7.6,
        "critic_count": 86, "user_count": None,
        "url": "https://www.metacritic.com/game/grand-theft-auto-iv/",
        "note": "Highest critic score in franchise. Lowest user score — first title with aggressive monetisation signals.",
    },
    {
        "id": "gta-5", "short": "GTA V",
        "year": 2013, "platform": "PS3",
        "critic_score": 97, "user_score": 8.1,
        "critic_count": 50, "user_count": None,
        "url": "https://www.metacritic.com/game/grand-theft-auto-v/",
    },
]


def try_scrape_score(entry: dict) -> dict:
    """Attempt live scrape; return updated entry or original on failure."""
    try:
        resp = requests.get(entry["url"], headers=HEADERS, timeout=15)
        if not resp.ok:
            return entry

        soup = BeautifulSoup(resp.text, "lxml")

        # JSON-LD is the most reliable extraction path
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if not isinstance(data, dict):
                    continue
                rating = data.get("aggregateRating", {})
                raw = rating.get("ratingValue")
                count = rating.get("ratingCount")
                if raw:
                    score = round(float(str(raw).replace(",", "")), 1)
                    # Metacritic critic scores are 0-100; user scores 0-10
                    if score > 10:
                        entry = {**entry, "critic_score": int(score)}
                        if count:
                            entry["critic_count"] = int(str(count).replace(",", ""))
                        return entry
            except Exception:
                continue

    except Exception as e:
        print(f"    scrape error ({entry['short']}): {e}")

    return entry


def main() -> None:
    print("Building Metacritic scores dataset...")
    titles = []

    for seed_entry in SEED:
        print(f"  [{seed_entry['short']}] attempting live scrape...")
        entry = try_scrape_score(dict(seed_entry))
        delta = round(entry["critic_score"] - entry["user_score"] * 10, 1)
        entry["critic_user_delta"] = delta
        titles.append(entry)
        print(f"    critic={entry['critic_score']}  user={entry['user_score']}  delta={delta:+.0f}")

    payload = {
        "last_updated": now_iso(),
        "source": "Metacritic.com",
        "note": "Critic scores /100. User scores /10. Delta = critic - (user×10). Positive delta = critics rated higher than users.",
        "titles": titles,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("Metacritic data updated.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
