"""
Download official GTA VI press assets from Rockstar's public CDN.

Rockstar releases press kits (screenshots, artwork, wallpapers) publicly
at rockstargames.com/VI/downloads. These are intended for media and fan
coverage of the game.

Usage:
    python3 scrapers/fetch_press_assets.py

Also pulls SITE_ASSETS — official in-engine screenshots and key art that
Rockstar published on rockstargames.com/VI pages and Newswire posts but
never added to the zips (resized to MAX_EDGE). Rows from earlier runs are
kept when a source is unreachable.

Outputs:
    public/assets/screenshots/*.jpg   — official screenshot images
    public/assets/artwork/*.jpg        — official artwork / wallpapers
    data/gta-6/press-assets.json       — index of all downloaded assets
"""

import hashlib
import io
import re
import zipfile
from pathlib import Path

import requests

from utils import load_existing, now_iso, write_json

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

SITE_BASE = "https://www.rockstargames.com"
SITE_PAGES = ["/VI", "/VI/music", "/VI/downloads"]
NEWSWIRE_CDN = "https://media-rockstargames-com.akamaized.net/tina-uploads/posts"
RADIO_POST = "https://www.rockstargames.com/newswire/article/o3982oa93a23k4/the-music-of-grand-theft-auto-vi-in-game-radio-stations"
MAX_EDGE = 2560

# Official images published on rockstargames.com/VI pages and Newswire posts
# but not in the press-kit zips. `site_basename` is resolved against the
# site's Next.js asset manifest each run because the hash suffix rotates.
SITE_ASSETS = [
    {
        "site_basename": "hero-background-desktop",
        "out_key": "screenshots",
        "filename": "Music_Vice_City_Causeway.jpg",
        "title": "Traffic on a Vice City causeway with the downtown skyline behind",
        "released": "2026-10-08",
        "source_page": "https://www.rockstargames.com/VI/music",
    },
    {
        "site_basename": "album-background-desktop",
        "out_key": "screenshots",
        "filename": "Music_Ocean_Drive_Night.jpg",
        "title": "Neon Ocean Drive at night after rain — Hotel Dixon and a Grotti supercar",
        "released": "2026-10-08",
        "source_page": "https://www.rockstargames.com/VI/music",
    },
    {
        "site_basename": "radio-background-desktop",
        "out_key": "screenshots",
        "filename": "Music_Street_Party.jpg",
        "title": "Late-night street meet outside a Conch King — lowriders and a crowd",
        "released": "2026-10-08",
        "source_page": "https://www.rockstargames.com/VI/music",
    },
    {
        "site_basename": "score-background-desktop",
        "out_key": "screenshots",
        "filename": "Music_Grassrivers_Floatplane.jpg",
        "title": "Brian Heder's floatplane over the Grassrivers at sunset",
        "released": "2026-10-15",
        "source_page": "https://www.rockstargames.com/VI/music",
    },
    {
        "site_basename": "Jason_Lucia_Lock_And_Load_landscape",
        "out_key": "artwork",
        "filename": "Jason_Lucia_Lock_And_Load.jpg",
        "title": "Jason and Lucia: Lock and Load — Launch Trailer key art",
        "released": "2026-10-15",
        "source_page": "https://www.rockstargames.com/VI/downloads",
    },
    {
        "site_basename": "The_Album_Cover_Art_landscape",
        "out_key": "artwork",
        "filename": "The_Album_Cover_Art.jpg",
        "title": "Grand Theft Auto VI: The Album — cover art",
        "released": "2026-10-08",
        "source_page": "https://www.rockstargames.com/VI/downloads",
    },
    {
        "site_basename": "Official_Cover_Art_landscape",
        "out_key": "artwork",
        "filename": "Official_Cover_Art.jpg",
        "title": "Grand Theft Auto VI — official cover art",
        "released": "2026-06-18",
        "source_page": "https://www.rockstargames.com/VI/downloads",
    },
    *[
        {
            "url": f"{NEWSWIRE_CDN}/o3982oa93a23k4/{sha}.jpg",
            "out_key": "artwork",
            "filename": f"Radio_{re.sub(r'[^A-Za-z0-9]+', '_', name).strip('_')}.jpg",
            "title": f"{name} — radio station key art",
            "released": "2026-10-08",
            "source_page": RADIO_POST,
        }
        for name, sha in [
            ("Cocoteo FM", "7ff9f9118130d6fcf9cd052fae3338f10b398ef1"),
            ("Back Country Radio", "31eb656fc0c1a639ace98c6427abecb7d771b6c1"),
            ("Afrobank FM", "696cf4278d5c13498c4d94b25987a7384823ced2"),
            ("The Chamber 106.6", "8470d1f8f71e2f8d38501ab88687b67568d1d17c"),
            ("Flash FM", "8850fd9b2849e0a4c1295949cea7a6dfa201a46d"),
            ("Dirty South Classics", "3eee2e23a4869a2d0af975593a8bf17c7a382cf0"),
        ]
    ],
]

MEDIA_RE = re.compile(r"/VI/_next/static/media/([A-Za-z0-9_~.\-]+?)\.([A-Za-z0-9_~.\-]+)\.(jpg|jpeg|png|webp)")


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


def resolve_site_media() -> dict[str, str]:
    """Map asset basename → current hashed URL from the /VI pages and their JS chunks."""
    blobs: list[str] = []
    chunk_paths: set[str] = set()
    for page in SITE_PAGES:
        try:
            resp = requests.get(SITE_BASE + page, headers=HEADERS, timeout=30)
            if resp.ok:
                blobs.append(resp.text)
                chunk_paths.update(re.findall(r'/VI/_next/static/chunks/[^"\']+\.js', resp.text))
        except Exception as e:
            print(f"  ✗ site page {page}: {e}")
    for path in sorted(chunk_paths):
        try:
            resp = requests.get(SITE_BASE + path, headers=HEADERS, timeout=30)
            if resp.ok:
                blobs.append(resp.text)
        except Exception:
            continue
    found: dict[str, str] = {}
    for blob in blobs:
        for m in MEDIA_RE.finditer(blob):
            found.setdefault(m.group(1), SITE_BASE + m.group(0))
    print(f"  Site manifest: {len(found)} media files across {len(chunk_paths)} chunks")
    return found


def downscale(data: bytes) -> bytes:
    from PIL import Image

    im = Image.open(io.BytesIO(data)).convert("RGB")
    if max(im.size) > MAX_EDGE:
        im.thumbnail((MAX_EDGE, MAX_EDGE))
    out = io.BytesIO()
    im.save(out, format="JPEG", quality=85, optimize=True, progressive=True)
    return out.getvalue()


def fetch_site_assets() -> dict[str, list[dict]]:
    media = resolve_site_media() if any("site_basename" in a for a in SITE_ASSETS) else {}
    out: dict[str, list[dict]] = {}
    for spec in SITE_ASSETS:
        url = spec.get("url") or media.get(spec.get("site_basename", ""))
        if not url:
            print(f"  ✗ {spec['filename']}: not found on site")
            continue
        try:
            resp = requests.get(url, headers=HEADERS, timeout=60)
            resp.raise_for_status()
            data = downscale(resp.content)
        except Exception as e:
            print(f"  ✗ {spec['filename']}: {e}")
            continue
        out_dir = BASE_DIR / "public" / "assets" / spec["out_key"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / spec["filename"]).write_bytes(data)
        out.setdefault(spec["out_key"], []).append({
            "filename": spec["filename"],
            "path": f"/assets/{spec['out_key']}/{spec['filename']}",
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()[:12],
            "title": spec["title"],
            "released": spec["released"],
            "source_page": spec["source_page"],
            "source_url": url,
        })
    total = sum(len(v) for v in out.values())
    print(f"  ✓ site assets: {total}/{len(SITE_ASSETS)} downloaded")
    return out


def union_by_filename(*lists: list[dict]) -> list[dict]:
    by_name: dict[str, dict] = {}
    for items in lists:
        for item in items:
            fn = item.get("filename")
            if fn:
                by_name[fn] = {**by_name.get(fn, {}), **item}
    return list(by_name.values())


def main() -> None:
    print("Fetching Rockstar GTA VI press assets...")
    print("Attribution: © Rockstar Games / Take-Two Interactive. All rights reserved.")

    existing = load_existing(OUT_PATH)
    site = fetch_site_assets()
    all_assets: dict[str, list[dict]] = {}

    for pack in ASSET_PACKS:
        key = pack["out_key"]
        zipped = download_and_extract(pack)
        previous = existing.get(key, [])
        if not zipped:
            # A failed or 404 zip must not wipe rows from earlier runs.
            zipped = [a for a in previous if "source_page" not in a]
        site_prev = [
            a for a in previous
            if "source_page" in a and (BASE_DIR / "public" / a["path"].lstrip("/")).exists()
        ]
        all_assets[key] = union_by_filename(zipped, site_prev, site.get(key, []))

    total = sum(len(v) for v in all_assets.values())
    print(f"  Total assets downloaded: {total}")

    payload = {
        "last_updated": now_iso(),
        "source": "Rockstar Games Official Press Kit — rockstargames.com/VI/downloads + /VI pages and Newswire",
        "attribution": "© Rockstar Games / Take-Two Interactive. All rights reserved.",
        "note": "Assets used for fan/media commentary under Rockstar's community guidelines.",
        **all_assets,
    }

    write_json(OUT_PATH, payload)
    print("Asset index written.")


if __name__ == "__main__":
    main()
