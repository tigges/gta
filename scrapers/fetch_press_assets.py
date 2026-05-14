"""
Download official GTA VI press assets from Rockstar's public CDN.

Rockstar releases press kits (screenshots, artwork, wallpapers) publicly
at rockstargames.com/VI/downloads. These are intended for media and fan
coverage of the game.

Usage:
    python3 scrapers/fetch_press_assets.py

Outputs:
    public/assets/screenshots/*.jpg   — official screenshot images
    public/assets/artwork/*.jpg        — official artwork / wallpapers
    data/gta-6/press-assets.json       — index of all downloaded assets
"""

import hashlib
import io
import os
import zipfile
from pathlib import Path

import requests

from utils import now_iso, write_json

BASE_DIR = Path(__file__).parent.parent

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.rockstargames.com/",
}

ASSET_PACKS = [
    {
        "name": "screenshots",
        "zip_url": "https://media-rockstargames-com.akamaized.net/VI/downloads/screenshots/GTAVI_Screenshots.zip",
        "out_dir": BASE_DIR / "public" / "assets" / "screenshots",
        "out_key": "screenshots",
    },
    {
        "name": "artwork",
        "zip_url": "https://media-rockstargames-com.akamaized.net/VI/downloads/artwork/GTAVI_Artwork.zip",
        "out_dir": BASE_DIR / "public" / "assets" / "artwork",
        "out_key": "artwork",
    },
]

OUT_PATH = "gta-6/press-assets.json"


def download_and_extract(pack: dict) -> list[dict]:
    """Download a zip, extract image files, return list of asset metadata."""
    out_dir: Path = pack["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Fetching {pack['name']} zip...")
    try:
        resp = requests.get(pack["zip_url"], headers=HEADERS, timeout=60, stream=True)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"  ✗ {pack['name']}: HTTP {e.response.status_code} — skipping")
        return []
    except Exception as e:
        print(f"  ✗ {pack['name']}: {e} — skipping")
        return []

    content = resp.content
    assets = []

    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
        for name in zf.namelist():
            if not name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue
            # Flatten directory structure
            filename = Path(name).name
            out_path = out_dir / filename
            with zf.open(name) as src, open(out_path, "wb") as dst:
                data = src.read()
                dst.write(data)
            assets.append(
                {
                    "filename": filename,
                    "path": f"/assets/{pack['out_key']}/{filename}",
                    "size_bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest()[:12],
                }
            )
        print(f"  ✓ {pack['name']}: {len(assets)} images extracted")
    except Exception as e:
        print(f"  ✗ Failed to read zip for {pack['name']}: {e}")

    return assets


def main() -> None:
    print("Fetching Rockstar GTA VI press assets...")
    print("Attribution: © Rockstar Games / Take-Two Interactive. All rights reserved.")

    all_assets: dict[str, list[dict]] = {}

    for pack in ASSET_PACKS:
        assets = download_and_extract(pack)
        all_assets[pack["out_key"]] = assets

    total = sum(len(v) for v in all_assets.values())
    print(f"  Total assets downloaded: {total}")

    payload = {
        "last_updated": now_iso(),
        "source": "Rockstar Games Official Press Kit — rockstargames.com/VI/downloads",
        "attribution": "© Rockstar Games / Take-Two Interactive. All rights reserved.",
        "note": "Assets used for fan/media commentary under Rockstar's community guidelines.",
        **all_assets,
    }

    write_json(OUT_PATH, payload)
    print("Asset index written.")


if __name__ == "__main__":
    main()
