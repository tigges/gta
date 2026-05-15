#!/usr/bin/env python3
"""
fetch_newswire_images.py — Downloads hero images from Rockstar Newswire articles.

Extends the base newswire scraper by:
1. Fetching the OG/hero image from each Newswire article page
2. Tagging newswire.json items with img_url (for news card thumbnails)
3. Saving DLC key art into /public/assets/gta5/dlc/ for business profile cards

Run after fetch_newswire.py (or as a standalone enrichment pass).

Output:
  data/feeds/newswire.json  — enriched with img_url per item
  public/assets/gta5/dlc/  — DLC key art for new GTA Online updates
  public/assets/gta5/news/ — general GTA news hero images

Usage:
  python3 scrapers/fetch_newswire_images.py
"""

import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(__file__))
from utils import write_json, has_changed, load_existing, now_iso

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[fetch_newswire_images] deps missing")
    requests = None
    BeautifulSoup = None

NEWSWIRE_PATH = "feeds/newswire.json"

ASSET_DIRS = {
    "dlc":  "public/assets/gta5/dlc",
    "news": "public/assets/gta5/news",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; gtavi-ai-bot/1.0; +https://gtavi.ai)",
    "Accept-Language": "en-US,en;q=0.9",
}

# Keywords that indicate a DLC-specific article worth storing as DLC art
DLC_KEYWORDS = [
    "out now", "now available", "heist", "update", "dlc",
    "cayo perico", "diamond casino", "contract", "after hours",
    "gunrunning", "acid lab", "tuners", "chop shop", "drug wars",
    "bunker", "doomsday",
]

# Map title keywords to DLC asset IDs
DLC_ID_MAP = [
    (["cayo perico"],            "cayo-perico"),
    (["diamond casino heist"],   "diamond-casino-heist"),
    (["the contract"],           "the-contract"),
    (["after hours"],            "after-hours"),
    (["gunrunning"],             "gunrunning"),
    (["drug wars", "acid lab"],  "acid-lab"),
    (["los santos tuners"],      "auto-shop"),
    (["chop shop"],              "chop-shop"),
    (["doomsday"],               "doomsday"),
]


def title_to_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:60]


def detect_dlc_id(title: str) -> str | None:
    tl = title.lower()
    for keywords, dlc_id in DLC_ID_MAP:
        if any(k in tl for k in keywords):
            return dlc_id
    return None


def fetch_og_image(session, url: str) -> str | None:
    """Fetch the og:image or hero image from an article page."""
    try:
        resp = session.get(url, headers=HEADERS, timeout=12)
        if not resp.ok:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Priority: og:image > twitter:image > first large img
        for meta_prop in ["og:image", "twitter:image", "og:image:secure_url"]:
            tag = soup.find("meta", property=meta_prop) or soup.find("meta", attrs={"name": meta_prop})
            if tag and tag.get("content"):
                img_url = tag["content"].strip()
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                return img_url
        
        # Fallback: first large image in article body
        for img in soup.find_all("img"):
            src = img.get("src", "") or img.get("data-src", "")
            if src and ("newswire" in src or "rockstar" in src.lower()):
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/"):
                    src = "https://www.rockstargames.com" + src
                return src
                
        return None
    except Exception as e:
        print(f"  [warn] OG image fetch failed for {url}: {e}")
        return None


def download_image(session, img_url: str, dest_path: str) -> bool:
    """Download an image to dest_path. Returns True on success."""
    try:
        resp = session.get(img_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 5000:
            with open(dest_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        print(f"  [warn] Download failed: {e}")
    return False


def main():
    if not requests or not BeautifulSoup:
        print("[fetch_newswire_images] deps missing — skipping")
        return

    for d in ASSET_DIRS.values():
        os.makedirs(d, exist_ok=True)

    existing = load_existing(NEWSWIRE_PATH)
    items = existing.get("items", [])
    if not items:
        print("[fetch_newswire_images] No newswire items — run fetch_newswire.py first")
        return

    session = requests.Session()
    enriched = 0
    downloaded = 0

    print(f"[fetch_newswire_images] Enriching {len(items)} items with images...")

    for item in items:
        # Skip if already has image
        if item.get("img_url"):
            continue
        
        url = item.get("url", "")
        if not url or "rockstargames.com" not in url:
            # Also enrich press sources with their OG images
            img_url = fetch_og_image(session, url) if url else None
            if img_url:
                item["img_url"] = img_url
                enriched += 1
            continue

        img_url = fetch_og_image(session, url)
        if not img_url:
            continue

        item["img_url"] = img_url
        enriched += 1
        title = item.get("title", "")
        
        # Determine where to save the image
        dlc_id = detect_dlc_id(title)
        if dlc_id:
            dest = os.path.join(ASSET_DIRS["dlc"], f"{dlc_id}-newswire.jpg")
            # Only download if we don't have a better YouTube version
            youtube_path = os.path.join(ASSET_DIRS["dlc"], f"{dlc_id}.jpg")
            if not os.path.exists(youtube_path):
                if download_image(session, img_url, dest):
                    print(f"  ✓ DLC art: {dlc_id} → {dest}")
                    downloaded += 1
        else:
            # Save as general news image
            slug = title_to_slug(title)
            dest = os.path.join(ASSET_DIRS["news"], f"{slug}.jpg")
            if not os.path.exists(dest):
                if download_image(session, img_url, dest):
                    downloaded += 1

        time.sleep(0.8)  # polite delay per request

    # Write enriched items back
    existing["items"] = items
    existing["last_updated"] = now_iso()
    write_json(NEWSWIRE_PATH, existing)

    print(f"[fetch_newswire_images] Enriched {enriched} items, downloaded {downloaded} images")


if __name__ == "__main__":
    main()
