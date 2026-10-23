"""
Fetch official GTA VI footage (trailers, Extended Look, gameplay).

Strategy (results are always unioned — never replace-only):
1. YouTube Data API search on the Rockstar channel
2. YouTube Data API videos.list for known + already-stored IDs
   (age-restricted uploads are missing from search but resolvable by ID)
3. Rockstar channel RSS feed (keyless, always runs — last 15 uploads)
4. YouTube search scrape if no API key
5. KNOWN_TRAILERS + existing trailers.json as a permanent registry floor

Before 2026-09-02 a successful API hit that returned only T1/T2
overwrote trailers.json and dropped Extended Look (9317ecb). This file
now unions; it never deletes a known or previously stored youtube_id.

Every row carries a `type`. Only MAIN_TYPES count as trailers on the
site; announcement cards, ad spots and alternate uploads are tracked
but never counted, charted or briefed.
"""

import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import has_changed, load_existing, now_iso, write_json

OUT_PATH = "gta-6/trailers.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

ROCKSTAR_CHANNEL_ID = "UC6VcWc1rAoWdBCM0JxrRQ3A"
CHANNEL_RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={ROCKSTAR_CHANNEL_ID}"
GTA6_KEYWORDS = ["gta vi", "gta 6", "grand theft auto vi", "grand theft auto 6"]
# Title must look like official video — not a merch/audio drop.
FOOTAGE_KEYWORDS = [
    "trailer",
    "extended look",
    "gameplay",
    "official look",
    "official gameplay",
    "cover art reveal",
    "now playing",
]

MAIN_TYPES = {"trailer", "extended_look", "launch_trailer", "gameplay"}
SECONDARY_TYPES = {"announcement", "spot", "alternate"}
EXCLUDE_KEYWORDS = [
    "soundtrack",
    "playlist",
    "podcast",
    "merch",
    "store",
    "audio only",
]

# Known-good YouTube IDs — update when new official footage is released.
# This list is a floor, not a last-resort fallback.
KNOWN_TRAILERS = [
    {
        "youtube_id": "QdBZY2fkU-0",
        "title": "Grand Theft Auto VI — Trailer 1",
        "published_at": "2023-12-04",
        "source_url": "https://www.youtube.com/watch?v=QdBZY2fkU-0",
        "type": "trailer",
    },
    {
        "youtube_id": "VQRLujxTm3c",
        "title": "Grand Theft Auto VI — Trailer 2",
        "published_at": "2025-05-06",
        "source_url": "https://www.youtube.com/watch?v=VQRLujxTm3c",
        "type": "trailer",
    },
    {
        "youtube_id": "tJbzMqJGH4k",
        "title": "Grand Theft Auto VI: An Extended Look",
        "published_at": "2026-08-28",
        "source_url": "https://www.youtube.com/watch?v=tJbzMqJGH4k",
        "type": "extended_look",
        "duration_sec": 1609,
        "notes": (
            "26m 49s. Netflix premiere Aug 27 at 3PM ET; YouTube at 9PM ET. "
            "Rockstar official channel. Age-restricted on YouTube — YouTube "
            "search.list omits it; videos.list by ID still resolves it."
        ),
    },
    {
        "youtube_id": "qq76pQsI1iw",
        "title": "Grand Theft Auto VI: An Extended Look Coming August 27",
        "published_at": "2026-08-06",
        "source_url": "https://www.youtube.com/watch?v=qq76pQsI1iw",
        "type": "announcement",
        "duration_sec": 25,
        "notes": (
            "25s premiere-date card for An Extended Look (Netflix Aug 27, "
            "YouTube 9PM ET). No new footage — no visual brief needed."
        ),
    },
    {
        "youtube_id": "rz1B4B2yBZY",
        "title": "Grand Theft Auto VI Launch Trailer",
        "published_at": "2026-10-15",
        "source_url": "https://www.youtube.com/watch?v=rz1B4B2yBZY",
        "type": "launch_trailer",
        "duration_sec": 90,
        "notes": (
            "90s, captured entirely in-game on PS5. Debuts Justice — "
            "'Flower in a Hurricane' feat. Tame Impala, SZA and King Gizzard "
            "& The Lizard Wizard. Age-restricted on YouTube."
        ),
    },
    {
        "youtube_id": "INjHGpMRjRA",
        "title": "Grand Theft Auto VI: Official Cover Art Reveal",
        "published_at": "2026-06-18",
        "source_url": "https://www.youtube.com/watch?v=INjHGpMRjRA",
        "type": "announcement",
        "notes": "Official box art reveal ahead of pre-orders. No gameplay footage — no visual brief needed.",
    },
    {
        "youtube_id": "EiQEBYDox_k",
        "title": "Grand Theft Auto VI: Official Cover Art Reveal",
        "published_at": "2026-06-18",
        "source_url": "https://www.youtube.com/watch?v=EiQEBYDox_k",
        "type": "alternate",
        "notes": "Second upload of the Cover Art Reveal on the Rockstar channel.",
    },
    {
        "youtube_id": "YmzCydc4qOk",
        "title": "Grand Theft Auto VI: An Extended Look Coming August 27",
        "published_at": "2026-08-06",
        "source_url": "https://www.youtube.com/watch?v=YmzCydc4qOk",
        "type": "alternate",
        "notes": "Second upload of the Extended Look premiere-date card.",
    },
    *[
        {
            "youtube_id": vid,
            "title": "Grand Theft Auto VI: An Extended Look — Now Playing",
            "published_at": "2026-08-28",
            "source_url": f"https://www.youtube.com/watch?v={vid}",
            "type": "spot",
            "notes": (
                f"'Now Playing' ad spot {n} of 6 cut from An Extended Look. "
                "Re-edited existing footage — no new visual brief."
            ),
        }
        for n, vid in enumerate(
            ["MJOrsRRa9GM", "53C6gUqRpK4", "mAfR_ybf5WM", "L-9NI3mHZVo", "GVTE_MuInQg", "Xzxv75FjMJk"],
            start=1,
        )
    ],
    {
        "youtube_id": "icy-lhqJhMQ",
        "title": "Grand Theft Auto VI Launch Trailer",
        "published_at": "2026-10-15",
        "source_url": "https://www.youtube.com/watch?v=icy-lhqJhMQ",
        "type": "alternate",
        "notes": "4:3 cut of the Launch Trailer (rz1B4B2yBZY). Same footage.",
    },
]

CURATED_KEYS = ("type", "duration_sec", "notes")


def infer_type(title: str) -> str:
    """Best-guess type for a newly discovered upload with no curated row."""
    t = (title or "").lower()
    if "now playing" in t:
        return "spot"
    if "coming" in t or "reveal" in t or "premiere" in t:
        return "announcement"
    if "launch trailer" in t:
        return "launch_trailer"
    if re.search(r"an extended look\s*$", t):
        return "extended_look"
    if "gameplay" in t:
        return "gameplay"
    return "trailer"


def is_official_footage(title: str) -> bool:
    """True for official GTA VI video titles (trailer / EL / gameplay)."""
    t = (title or "").lower()
    if not any(k in t for k in GTA6_KEYWORDS):
        return False
    if any(k in t for k in EXCLUDE_KEYWORDS):
        return False
    return any(k in t for k in FOOTAGE_KEYWORDS)


# Back-compat alias used by older call sites / notes
_is_gta6_trailer = is_official_footage


def _dedup(trailers: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out = []
    for t in trailers:
        vid = t.get("youtube_id")
        if vid and vid not in seen:
            seen.add(vid)
            out.append(t)
    return out


def _as_trailer(youtube_id: str, title: str, published_at: str | None) -> dict:
    return {
        "youtube_id": youtube_id,
        "title": title,
        "published_at": published_at,
        "source_url": f"https://www.youtube.com/watch?v={youtube_id}",
    }


def merge_registry(discovered: list[dict], existing: list[dict] | None = None) -> list[dict]:
    """
    Union discovered results with KNOWN_TRAILERS and the existing JSON file.

    Never drops a known or previously stored youtube_id. Curated fields
    (type, duration_sec, notes) on an existing row survive an API refresh
    that only returns title / date / url.
    """
    by_id: dict[str, dict] = {}

    if existing is None:
        existing = load_existing(OUT_PATH).get("trailers", [])
    for t in existing:
        vid = t.get("youtube_id")
        if vid:
            by_id[vid] = dict(t)

    for t in KNOWN_TRAILERS:
        vid = t["youtube_id"]
        if vid not in by_id:
            by_id[vid] = dict(t)
        else:
            for key, val in t.items():
                if val in (None, "") and by_id[vid].get(key) not in (None, ""):
                    continue
                if key in CURATED_KEYS and key in by_id[vid] and key not in t:
                    continue
                if key in CURATED_KEYS and key in by_id[vid]:
                    continue
                if key not in by_id[vid] or by_id[vid].get(key) in (None, ""):
                    by_id[vid][key] = val

    for t in discovered:
        vid = t.get("youtube_id")
        if not vid:
            continue
        prev = by_id.get(vid, {})
        merged = dict(prev)
        for key, val in t.items():
            if val in (None, ""):
                continue
            if key in CURATED_KEYS and key in prev:
                continue
            merged[key] = val
        for key in CURATED_KEYS:
            if key in prev:
                merged[key] = prev[key]
        by_id[vid] = merged

    ordered: list[dict] = []
    seen: set[str] = set()
    for t in KNOWN_TRAILERS:
        vid = t["youtube_id"]
        if vid in by_id:
            ordered.append(by_id[vid])
            seen.add(vid)
    extras = [by_id[k] for k in by_id if k not in seen]
    extras.sort(key=lambda x: x.get("published_at") or "")
    rows = ordered + extras

    main_titles: set[str] = {
        _norm_title(r.get("title")) for r in rows if r.get("type") in MAIN_TYPES
    }
    for r in rows:
        if r.get("type"):
            continue
        inferred = infer_type(r.get("title") or "")
        key = _norm_title(r.get("title"))
        if inferred in MAIN_TYPES and key in main_titles:
            inferred = "alternate"
        r["type"] = inferred
        if inferred in MAIN_TYPES:
            main_titles.add(key)
    return rows


def _norm_title(title: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def is_main(trailer: dict) -> bool:
    return trailer.get("type") in MAIN_TYPES


def fetch_from_youtube_api(api_key: str) -> list[dict]:
    try:
        from googleapiclient.discovery import build
        youtube = build("youtube", "v3", developerKey=api_key)
        response = youtube.search().list(
            part="snippet",
            channelId=ROCKSTAR_CHANNEL_ID,
            q="Grand Theft Auto VI",
            type="video",
            order="date",
            maxResults=15,
        ).execute()
        trailers = [
            _as_trailer(
                item["id"]["videoId"],
                item["snippet"]["title"],
                item["snippet"]["publishedAt"][:10],
            )
            for item in response.get("items", [])
            if is_official_footage(item["snippet"]["title"])
        ]
        if trailers:
            print(f"  YouTube API search: found {len(trailers)} official video(s)")
        return trailers
    except Exception as e:
        print(f"  YouTube API search error: {e}")
        return []


def fetch_ids_via_api(api_key: str, youtube_ids: list[str]) -> list[dict]:
    """videos.list resolves age-restricted IDs that search.list omits."""
    ids = [vid for vid in youtube_ids if vid]
    if not ids:
        return []
    try:
        from googleapiclient.discovery import build
        youtube = build("youtube", "v3", developerKey=api_key)
        found: list[dict] = []
        for i in range(0, len(ids), 50):
            chunk = ids[i:i + 50]
            response = youtube.videos().list(
                part="snippet",
                id=",".join(chunk),
            ).execute()
            for item in response.get("items", []):
                title = item["snippet"]["title"]
                found.append(_as_trailer(
                    item["id"],
                    title,
                    item["snippet"]["publishedAt"][:10],
                ))
        if found:
            print(f"  YouTube API videos.list: resolved {len(found)} known id(s)")
        return found
    except Exception as e:
        print(f"  YouTube API videos.list error: {e}")
        return []


RSS_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}


def parse_channel_rss(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    out = []
    for entry in root.findall("atom:entry", RSS_NS):
        vid = entry.findtext("yt:videoId", default="", namespaces=RSS_NS)
        title = entry.findtext("atom:title", default="", namespaces=RSS_NS)
        published = entry.findtext("atom:published", default="", namespaces=RSS_NS)[:10] or None
        if vid and is_official_footage(title):
            out.append(_as_trailer(vid, title, published))
    return out


def fetch_from_channel_rss() -> list[dict]:
    """Keyless: the channel's public Atom feed lists its 15 latest uploads."""
    try:
        resp = requests.get(CHANNEL_RSS_URL, headers=HEADERS, timeout=20)
        if not resp.ok:
            print(f"  Channel RSS: HTTP {resp.status_code}")
            return []
        trailers = parse_channel_rss(resp.text)
        print(f"  Channel RSS: found {len(trailers)} official GTA VI video(s)")
        return trailers
    except Exception as e:
        print(f"  Channel RSS error: {e}")
        return []


OFFICIAL_CHANNEL_NAMES = {"rockstar games", "rockstargames"}


def fetch_from_youtube_search() -> list[dict]:
    """Scrape YouTube search results for official GTA VI footage."""
    try:
        search_url = (
            "https://www.youtube.com/results"
            "?search_query=Grand+Theft+Auto+VI+Rockstar+Games"
        )
        resp = requests.get(search_url, headers=HEADERS, timeout=30)
        if not resp.ok:
            return []

        match = re.search(r"var ytInitialData = ({.+?});</script>", resp.text, re.DOTALL)
        if not match:
            return []

        import json
        data = json.loads(match.group(1))

        def extract_videos(obj):
            if isinstance(obj, dict):
                if "videoId" in obj and "title" in obj and "ownerText" in obj:
                    title_runs = obj.get("title", {}).get("runs", [])
                    title = "".join(r.get("text", "") for r in title_runs)
                    channel_runs = obj.get("ownerText", {}).get("runs", [])
                    channel = "".join(r.get("text", "") for r in channel_runs).lower()
                    if is_official_footage(title) and channel in OFFICIAL_CHANNEL_NAMES:
                        yield _as_trailer(obj["videoId"], title, None)
                for v in obj.values():
                    yield from extract_videos(v)
            elif isinstance(obj, list):
                for item in obj:
                    yield from extract_videos(item)

        trailers = _dedup(list(extract_videos(data)))
        if trailers:
            print(f"  YouTube search: found {len(trailers)} official video(s)")
        return trailers
    except Exception as e:
        print(f"  YouTube search error: {e}")
        return []


def fetch_from_known_ids() -> list[dict]:
    """Verify known YouTube IDs are still accessible and return them."""
    valid = []
    for trailer in KNOWN_TRAILERS:
        try:
            url = (
                "https://www.youtube.com/oembed"
                f"?url=https://www.youtube.com/watch?v={trailer['youtube_id']}"
                "&format=json"
            )
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.ok:
                data = resp.json()
                valid.append({
                    **trailer,
                    "title": data.get("title", trailer["title"]),
                })
            else:
                valid.append(trailer)
        except Exception:
            valid.append(trailer)
    if valid:
        print(f"  Known IDs: returning {len(valid)} video(s)")
    return valid


def registry_ids() -> list[str]:
    existing = [t.get("youtube_id") for t in load_existing(OUT_PATH).get("trailers", [])]
    known = [t["youtube_id"] for t in KNOWN_TRAILERS]
    return list(dict.fromkeys([vid for vid in existing + known if vid]))


def fetch() -> list[dict]:
    """Discover official videos, then union with the permanent registry."""
    api_key = os.getenv("YOUTUBE_API_KEY")
    discovered: list[dict] = []

    if api_key:
        discovered.extend(fetch_from_youtube_api(api_key))
        discovered.extend(fetch_ids_via_api(api_key, registry_ids()))
    else:
        discovered.extend(fetch_from_youtube_search())
        discovered.extend(fetch_from_known_ids())
    discovered.extend(fetch_from_channel_rss())

    return merge_registry(discovered)


def main() -> None:
    print("Fetching GTA VI official footage...")
    trailers = fetch()

    if not trailers:
        print("  No videos found — keeping existing data unchanged")
        return

    main_count = sum(1 for t in trailers if is_main(t))
    print(f"  Total: {len(trailers)} official video(s), {main_count} counted as trailers")
    for t in trailers:
        print(f"    [{t.get('type')}] {t['title']} ({t['youtube_id']}) — {t.get('published_at', 'date unknown')}")

    payload = {
        "last_updated": now_iso(),
        "source": "YouTube / rockstargames.com",
        "trailers": trailers,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("Data updated.")
    else:
        print("No changes detected, skipping write.")


if __name__ == "__main__":
    main()
