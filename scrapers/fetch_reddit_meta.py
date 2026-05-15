#!/usr/bin/env python3
"""
fetch_reddit_meta.py — Monitors r/gtaonline for meta-shift signals.

Watches for posts about nerfs, buffs, and patch changes. When a "Cayo nerfed"
post goes hot, it flags the relevant business in business-profiles.json
with an updated last_nerfed date before any site updates it.

Also tracks weekly "What to play" and "Money method" posts for $/hr validation.

Output: data/gta-5/economy/reddit-signals.json
        (also writes flags back to business-profiles.json when nerf detected)

Usage:
  REDDIT_CLIENT_ID=... REDDIT_CLIENT_SECRET=... python3 scrapers/fetch_reddit_meta.py
"""

import json
import re
import sys
import os
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from utils import write_json, has_changed, load_existing, now_iso

REDDIT_CLIENT_ID     = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
OUTPUT_PATH          = "gta-5/economy/reddit-signals.json"
BIZ_PROFILES_PATH    = "gta-5/economy/business-profiles.json"

# Keywords that indicate a meta shift / nerf / buff
NERF_KEYWORDS  = ["nerfed", "nerf", "reduced", "patched", "fixed", "nerfing", "buff removed"]
BUFF_KEYWORDS  = ["buffed", "buff", "increased", "boosted", "doubled", "tripled"]
META_KEYWORDS  = ["meta", "best money", "money method", "$/hr", "per hour", "income"]

# Activity name → business ID mapping for auto-flagging
ACTIVITY_MAP = {
    "cayo perico":       "cayo-perico",
    "casino heist":      "diamond-casino-heist",
    "acid lab":          "acid-lab",
    "nightclub":         "nightclub",
    "bunker":            "bunker",
    "auto shop":         "auto-shop",
    "agency":            "agency-vip-contract",
    "payphone":          "payphone-hits",
    "terrorbyte":        "terrorbyte-oppressor",
    "oppressor":         "terrorbyte-oppressor",
    "vip work":          "vip-work",
    "contact mission":   "contact-missions",
}

try:
    import requests
except ImportError:
    print("[fetch_reddit_meta] requests missing")
    requests = None


def get_reddit_token(session) -> str | None:
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        return None
    try:
        r = session.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": "gtavi-ai-meta-monitor/1.0"},
            timeout=10,
        )
        return r.json().get("access_token")
    except Exception as e:
        print(f"  [warn] Reddit auth failed: {e}")
        return None


def fetch_hot_posts(session, token: str, limit: int = 50) -> list[dict]:
    try:
        r = session.get(
            "https://oauth.reddit.com/r/gtaonline/hot.json",
            headers={"Authorization": f"bearer {token}", "User-Agent": "gtavi-ai-meta-monitor/1.0"},
            params={"limit": limit},
            timeout=15,
        )
        return r.json().get("data", {}).get("children", [])
    except Exception as e:
        print(f"  [warn] Reddit hot posts failed: {e}")
        return []


def rss_fallback(session) -> list[dict]:
    """Fallback: use the RSS feed if no Reddit credentials."""
    try:
        import xml.etree.ElementTree as ET
        r = session.get(
            "https://www.reddit.com/r/gtaonline/hot.rss",
            headers={"User-Agent": "gtavi-ai-meta-monitor/1.0"},
            timeout=15,
        )
        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = []
        for entry in root.findall("atom:entry", ns)[:50]:
            title = entry.findtext("atom:title", default="", namespaces=ns)
            link  = entry.findtext("atom:id", default="", namespaces=ns)
            entries.append({"data": {"title": title, "url": link, "score": 0}})
        return entries
    except Exception as e:
        print(f"  [warn] RSS fallback failed: {e}")
        return []


def classify_post(title: str) -> dict:
    tl = title.lower()
    signals = {
        "is_nerf":   any(k in tl for k in NERF_KEYWORDS),
        "is_buff":   any(k in tl for k in BUFF_KEYWORDS),
        "is_meta":   any(k in tl for k in META_KEYWORDS),
        "activities": [],
    }
    for activity_kw, biz_id in ACTIVITY_MAP.items():
        if activity_kw in tl:
            signals["activities"].append(biz_id)
    return signals


def update_business_nerf(biz_id: str, date_str: str, note: str) -> bool:
    """Auto-update last_nerfed on a business profile when detected."""
    try:
        profiles = load_existing(BIZ_PROFILES_PATH)
        for biz in profiles.get("businesses", []):
            if biz["id"] == biz_id:
                current = biz.get("last_nerfed")
                if not current or current < date_str:
                    biz["last_nerfed"] = date_str
                    biz["last_nerfed_notes"] = f"Auto-detected via r/gtaonline: {note[:100]}"
                    write_json(BIZ_PROFILES_PATH, profiles)
                    print(f"  ⚠ Auto-flagged nerf: {biz_id} on {date_str}")
                    return True
        return False
    except Exception as e:
        print(f"  [warn] Could not update nerf flag: {e}")
        return False


def main():
    if not requests:
        print("[fetch_reddit_meta] requests missing")
        return

    session = requests.Session()
    print("[fetch_reddit_meta] Fetching r/gtaonline hot posts...")

    token = get_reddit_token(session) if REDDIT_CLIENT_ID else None
    posts = fetch_hot_posts(session, token) if token else rss_fallback(session)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    signals = []
    nerf_detections = []

    for post in posts:
        data  = post.get("data", post)
        title = data.get("title", "")
        score = data.get("score", 0)
        url   = data.get("url", "")

        cls = classify_post(title)
        if not any([cls["is_nerf"], cls["is_buff"], cls["is_meta"]]):
            continue

        sig = {
            "title":      title,
            "score":      score,
            "url":        url,
            "is_nerf":    cls["is_nerf"],
            "is_buff":    cls["is_buff"],
            "activities": cls["activities"],
            "date":       today,
        }
        signals.append(sig)

        # Auto-flag nerfs with high confidence (multiple activities mentioned, high score)
        if cls["is_nerf"] and cls["activities"] and score > 100:
            for biz_id in cls["activities"]:
                if update_business_nerf(biz_id, today, title):
                    nerf_detections.append({"biz_id": biz_id, "post": title, "score": score})

    result = {
        "last_updated": now_iso(),
        "source": "r/gtaonline (Reddit)",
        "posts_scanned": len(posts),
        "meta_signals": len(signals),
        "nerf_detections": nerf_detections,
        "signals": signals[:20],  # keep top 20
    }

    if has_changed(result, OUTPUT_PATH):
        write_json(OUTPUT_PATH, result)
        print(f"[fetch_reddit_meta] {len(signals)} signals, {len(nerf_detections)} nerf detections")
    else:
        print("[fetch_reddit_meta] No changes")


if __name__ == "__main__":
    main()
