"""
New official-footage playbook.

Runs after fetch_trailers.py (and press assets) in nightly CI.

Does:
  - Detect official videos in trailers.json that have no analysis events
  - Stub an empty trailer-analysis.json block (flagged stub: true)
  - Ensure trailer-velocity.json has a series row (snapshots filled later)
  - Scan YouTube description + newswire for keyword hints (drafts only)
  - Diff new press-kit filenames and propose stills (never as video frames)
  - Write data/gta-6/official-footage-inbox.json for Discord + /admin

Never:
  - Flips confidence_tier
  - Auto-publishes predictions
  - Rips YouTube / Netflix frames
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import DATA_DIR, has_changed, load_existing, now_iso, write_json

TRAILERS_PATH = "gta-6/trailers.json"
ANALYSIS_PATH = "gta-6/trailer-analysis.json"
VELOCITY_PATH = "gta-6/trailer-velocity.json"
INBOX_PATH = "gta-6/official-footage-inbox.json"
NEWSWIRE_PATH = "feeds/newswire.json"
PRESS_PATH = "gta-6/press-assets.json"
STILLS_PATH = "gta-6/extended-look-stills.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

CHECKLIST = [
    "Fill trailer-analysis.json events from official footage + press stills",
    "Do not rip YouTube or Netflix frames",
    "Match press stills to chapters; label them as press stills",
    "Nav teaser / CrossLinks if this becomes a first-class section",
    "Review keyword hints before drafting any prediction",
    "Never auto-flip predicted → confirmed",
]

# Phrase → hint label. Conservative; description mention ≠ confirmation.
HINT_TERMS = [
    ("extended look", "official extended look"),
    ("6-star", "6-star wanted"),
    ("six-star", "6-star wanted"),
    ("six star", "6-star wanted"),
    ("criminal profile", "criminal profile"),
    ("waink", "WAINK app"),
    ("bullet time", "bullet time"),
    ("relationship", "relationship system"),
    ("hunting", "hunting"),
    ("scuba", "scuba / diving"),
    ("basketball", "basketball"),
    ("trunk", "trunk storage"),
    ("map size", "map size"),
    ("twice the size", "map size (~2×)"),
    ("vice city", "Vice City"),
    ("leonida", "Leonida"),
    ("vice beach", "Vice Beach"),
]


def slug_for(trailer: dict) -> str:
    title = (trailer.get("title") or "").lower()
    if "extended look" in title:
        return "extended-look"
    m = re.search(r"trailer\s*(\d+)", title)
    if m:
        return f"trailer-{m.group(1)}"
    vid = trailer.get("youtube_id") or "unknown"
    return f"official-{vid[:8]}"


def analysis_by_id(analysis: dict) -> dict[str, dict]:
    return {
        t.get("youtube_id"): t
        for t in analysis.get("trailers", [])
        if t.get("youtube_id")
    }


def needs_brief(trailer: dict, analysis_row: dict | None) -> bool:
    if not analysis_row:
        return True
    events = analysis_row.get("events") or []
    return len(events) == 0


def ensure_analysis_stub(trailer: dict, analysis: dict) -> bool:
    """Append an empty analysis block. Returns True if a stub was added."""
    by_id = analysis_by_id(analysis)
    vid = trailer["youtube_id"]
    if vid in by_id:
        return False
    analysis.setdefault("trailers", []).append({
        "id": slug_for(trailer),
        "youtube_id": vid,
        "title": trailer.get("title") or vid,
        "published_at": trailer.get("published_at"),
        "duration_sec": trailer.get("duration_sec") or 0,
        "total_entities": 0,
        "events": [],
        "stub": True,
        "note": (
            "Auto-stubbed by on_new_official_footage.py. Fill events from "
            "official footage and Rockstar press stills. Do not rip YouTube frames."
        ),
    })
    return True


def ensure_velocity_row(trailer: dict, velocity: dict) -> bool:
    rows = velocity.setdefault("trailers", [])
    if any(t.get("youtube_id") == trailer["youtube_id"] for t in rows):
        return False
    rows.append({
        "youtube_id": trailer["youtube_id"],
        "title": trailer.get("title") or trailer["youtube_id"],
        "published_at": trailer.get("published_at"),
        "fetch_method": None,
        "snapshots": [],
    })
    return True


def fetch_description(youtube_id: str, api_key: str | None) -> str:
    if not api_key:
        return ""
    try:
        url = (
            "https://www.googleapis.com/youtube/v3/videos"
            f"?part=snippet&id={youtube_id}&key={api_key}"
        )
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            return ""
        return items[0].get("snippet", {}).get("description") or ""
    except Exception as e:
        print(f"  [warn] description fetch failed for {youtube_id}: {e}")
        return ""


def scan_keywords(text: str, source: str, youtube_id: str | None) -> list[dict]:
    blob = (text or "").lower()
    if not blob:
        return []
    hints = []
    for term, label in HINT_TERMS:
        if term in blob:
            idx = blob.find(term)
            start = max(0, idx - 60)
            end = min(len(text), idx + len(term) + 60)
            snippet = re.sub(r"\s+", " ", text[start:end]).strip()
            hints.append({
                "term": term,
                "label": label,
                "source": source,
                "youtube_id": youtube_id,
                "snippet": snippet,
                "note": (
                    "Keyword hit only — not a confirmation. Review before "
                    "drafting a prediction. draft_status must stay needs_review."
                ),
            })
    return hints


def collect_used_still_paths(stills: dict) -> set[str]:
    used: set[str] = set()

    def walk(obj):
        if isinstance(obj, dict):
            for key in ("src", "cover"):
                if isinstance(obj.get(key), str):
                    used.add(obj[key].rsplit("/", 1)[-1])
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(stills)
    return used


def propose_press_stills(inbox: dict, press: dict, stills: dict) -> tuple[list[dict], list[str]]:
    """
    First run baselines current filenames (no flood). Later runs propose
    newly appeared screenshots that are not already in the visual brief.
    """
    current = [a.get("filename") for a in press.get("screenshots", []) if a.get("filename")]
    seen = list(inbox.get("seen_press_filenames") or [])
    used = collect_used_still_paths(stills)
    if not seen:
        return [], current

    proposals = []
    for asset in press.get("screenshots", []):
        fn = asset.get("filename")
        if not fn or fn in seen or fn in used:
            continue
        stem = Path(fn).stem.replace("_", " ")
        proposals.append({
            "filename": fn,
            "path": asset.get("path"),
            "suggested_entity": stem,
            "attribution": "Official Rockstar press still — not a video frame",
            "note": "New press-kit file since last inbox baseline. Match to a chapter if it belongs.",
        })
    return proposals, current


def build_inbox(
    trailers: list[dict],
    analysis: dict,
    previous: dict,
    keyword_hints: list[dict],
    still_proposals: list[dict],
    seen_press: list[str],
    stubbed_ids: list[str],
) -> dict:
    by_id = analysis_by_id(analysis)
    videos = []
    for t in trailers:
        vid = t.get("youtube_id")
        if not vid:
            continue
        row = by_id.get(vid)
        brief = needs_brief(t, row)
        videos.append({
            "youtube_id": vid,
            "title": t.get("title"),
            "published_at": t.get("published_at"),
            "needs_brief": brief,
            "analysis_stubbed": vid in stubbed_ids or bool((row or {}).get("stub")),
            "event_count": len((row or {}).get("events") or []),
            "checklist": CHECKLIST if brief else [],
        })

    return {
        "schema_version": "1.0",
        "last_updated": now_iso(),
        "note": (
            "Draft inbox only. Scrapers detect and propose; humans/agents "
            "write the brief. Never treat keyword hits as confirmed."
        ),
        "videos": videos,
        "needs_brief_count": sum(1 for v in videos if v["needs_brief"]),
        "keyword_hints": keyword_hints,
        "press_still_proposals": still_proposals,
        "seen_press_filenames": seen_press,
        "previous_needs_brief": previous.get("needs_brief_count", 0),
    }


def run(api_key: str | None = None) -> dict:
    trailers_data = load_existing(TRAILERS_PATH)
    trailers = trailers_data.get("trailers", [])
    analysis = load_existing(ANALYSIS_PATH)
    if not analysis:
        analysis = {
            "source": "Frame-by-frame analysis of official Rockstar trailers and Extended Look",
            "note": "Timestamps approximate.",
            "trailers": [],
        }
    velocity = load_existing(VELOCITY_PATH)
    previous = load_existing(INBOX_PATH)
    newswire = load_existing(NEWSWIRE_PATH)
    press = load_existing(PRESS_PATH)
    stills = load_existing(STILLS_PATH)

    stubbed: list[str] = []
    analysis_changed = False
    velocity_changed = False

    for t in trailers:
        if not t.get("youtube_id"):
            continue
        if ensure_analysis_stub(t, analysis):
            stubbed.append(t["youtube_id"])
            analysis_changed = True
            print(f"  stubbed analysis for {t['youtube_id']} ({t.get('title')})")
        if ensure_velocity_row(t, velocity):
            velocity_changed = True
            print(f"  added velocity series for {t['youtube_id']}")

    keyword_hints: list[dict] = []
    pending = [
        t for t in trailers
        if t.get("youtube_id") and needs_brief(t, analysis_by_id(analysis).get(t["youtube_id"]))
    ]
    for t in pending:
        desc = fetch_description(t["youtube_id"], api_key)
        keyword_hints.extend(scan_keywords(desc, "youtube_description", t["youtube_id"]))

    # Newswire keyword pass only when a video still needs a brief — otherwise
    # every nightly EL headline would flood the inbox.
    if pending:
        for item in (newswire.get("items") or [])[:12]:
            blob = f"{item.get('title') or ''} {item.get('summary') or ''}"
            keyword_hints.extend(scan_keywords(blob, f"newswire:{item.get('source_name')}", None))

    # Dedup hints by term+source+youtube_id
    seen_hint = set()
    unique_hints = []
    for h in keyword_hints:
        key = (h["term"], h["source"], h.get("youtube_id"))
        if key in seen_hint:
            continue
        seen_hint.add(key)
        unique_hints.append(h)

    still_proposals, seen_press = propose_press_stills(previous, press, stills)

    inbox = build_inbox(
        trailers, analysis, previous, unique_hints, still_proposals, seen_press, stubbed
    )

    if analysis_changed and has_changed(analysis, ANALYSIS_PATH):
        write_json(ANALYSIS_PATH, analysis)
    if velocity_changed:
        velocity["last_updated"] = now_iso()
        write_json(VELOCITY_PATH, velocity)

    write_json(INBOX_PATH, inbox)
    print(
        f"  inbox: {inbox['needs_brief_count']} need brief, "
        f"{len(unique_hints)} keyword hints, "
        f"{len(still_proposals)} new press stills"
    )
    return inbox


def main() -> None:
    print("Official footage playbook...")
    run(api_key=os.getenv("YOUTUBE_API_KEY"))
    print("Playbook done.")


if __name__ == "__main__":
    main()
