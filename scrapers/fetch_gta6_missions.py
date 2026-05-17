#!/usr/bin/env python3
"""
fetch_gta6_missions.py — GTA VI story mission data from GTA Fandom Wiki

Day-1 ready: handles empty/pre-launch state gracefully.
When GTA VI launches and the wiki populates, this scraper auto-fills
data/gta-6/missions/story-missions.json with no code changes needed.

Sources (populated at launch):
  https://gta.fandom.com/wiki/Missions_in_GTA_VI
  https://gta.fandom.com/wiki/Category:Missions_in_GTA_VI

Output:
  data/gta-6/missions/story-missions.json

Schema mirrors data/gta-5/missions/story-missions.json exactly so all
downstream consumers (economy page, charts) work without modification.

Usage:
  python3 scrapers/fetch_gta6_missions.py            # live scrape
  python3 scrapers/fetch_gta6_missions.py --dry-run  # print without writing
"""

import re
import sys
import os
import time
import argparse
import json

sys.path.insert(0, os.path.dirname(__file__))
from utils import write_json, has_changed, load_existing, now_iso

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[fetch_gta6_missions] requests/bs4 not installed")
    requests = None
    BeautifulSoup = None

WIKI_API   = "https://gta.fandom.com/api.php"
WIKI_BASE  = "https://gta.fandom.com"
OUT_PATH   = "gta-6/missions/story-missions.json"
HEADERS    = {"User-Agent": "gtavi.ai/1.0 (GTA VI mission scraper; +https://gtavi.ai)"}
PAYOUT_RE  = re.compile(r"GTA\$?\s*([\d,]+)|\$([\d,]+)", re.IGNORECASE)


def parse_payout(text: str) -> int | None:
    if not text:
        return None
    for m in PAYOUT_RE.finditer(text.replace(",", "")):
        val = int(m.group(1) or m.group(2))
        if 1000 <= val <= 100_000_000:
            return val
    return None


def title_to_id(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def fetch_category_members(session: "requests.Session") -> list[dict]:
    """Get all pages in Category:Missions_in_GTA_VI via MediaWiki API."""
    members = []
    params: dict = {
        "action": "query", "list": "categorymembers",
        "cmtitle": "Category:Missions_in_GTA_VI",
        "cmlimit": 500, "cmtype": "page", "format": "json",
    }
    while True:
        r = session.get(WIKI_API, params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        members.extend(data["query"]["categorymembers"])
        cont = data.get("continue", {}).get("cmcontinue")
        if not cont:
            break
        params["cmcontinue"] = cont
        time.sleep(0.5)
    return members


def fetch_mission_page(session: "requests.Session", title: str) -> dict | None:
    """Fetch a single mission page and extract payout, protagonist, chapter."""
    params = {
        "action": "query", "prop": "revisions",
        "rvprop": "content", "rvslots": "main",
        "format": "json", "titles": title, "redirects": 1,
    }
    try:
        r = session.get(WIKI_API, params=params, headers=HEADERS, timeout=12)
        r.raise_for_status()
        data = r.json()
        page = list(data["query"]["pages"].values())[0]
        if "revisions" not in page:
            return None
        content = page["revisions"][0]["slots"]["main"]["*"]
    except Exception as e:
        print(f"    [warn] {title}: {e}")
        return None

    # Extract fields from infobox
    payout_match     = re.search(r"\|reward\s*=\s*(.+?)(?=\n\||\n}})", content, re.DOTALL)
    protagonist_match = re.search(r"\|protagonist\s*=\s*(.+?)(?=\n\||\n}})", content, re.DOTALL)
    prev_match       = re.search(r"\|previous\s*=\s*(.+?)(?=\n\||\n}})", content, re.DOTALL)
    next_match       = re.search(r"\|next\s*=\s*(.+?)(?=\n\||\n}})", content, re.DOTALL)

    payout = parse_payout(payout_match.group(1) if payout_match else "")

    def clean(raw: str | None) -> list[str]:
        if not raw:
            return []
        return [p.strip() for p in re.sub(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", r"\1", raw).split(",")
                if p.strip() and len(p.strip()) > 1]

    protagonist = clean(protagonist_match.group(1) if protagonist_match else "")

    return {
        "id":          title_to_id(title),
        "title":       title,
        "chapter":     None,  # populated manually or from wiki chapter infobox
        "protagonist": protagonist,
        "payout":      payout,
        "prev":        prev_match.group(1).strip()[:60] if prev_match else None,
        "next":        next_match.group(1).strip()[:60] if next_match else None,
    }


def build_result(missions: list[dict]) -> dict:
    return {
        "schema_version": "1.0",
        "last_updated":   now_iso(),
        "source":         "GTA Fandom Wiki (gta.fandom.com) · Category:Missions_in_GTA_VI",
        "note":           (
            "GTA VI story mission data. Populated automatically from GTA Fandom Wiki "
            "when the game launches and the wiki is updated. Pre-launch: empty schema stub."
        ),
        "game":           "gta-6",
        "missions":       missions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    existing  = load_existing(OUT_PATH)
    seed_map  = {m["id"]: m for m in existing.get("missions", [])}

    if requests is None:
        print("[fetch_gta6_missions] deps missing — writing existing data")
        write_json(OUT_PATH, build_result(list(seed_map.values())))
        return

    session = requests.Session()

    print("[fetch_gta6_missions] Checking Category:Missions_in_GTA_VI on GTA Wiki…")
    try:
        members = fetch_category_members(session)
    except Exception as e:
        print(f"[fetch_gta6_missions] Wiki unreachable: {e} — preserving existing data")
        result = build_result(list(seed_map.values()))
        if not args.dry_run:
            write_json(OUT_PATH, result)
        return

    if not members:
        print("[fetch_gta6_missions] Category empty — GTA VI missions not yet on wiki (pre-launch)")
        print(f"  Existing seed: {len(seed_map)} missions")
        result = build_result(list(seed_map.values()))
        if args.dry_run:
            print(f"  [dry-run] Would write {len(result['missions'])} missions")
            return
        if has_changed(result, OUT_PATH):
            write_json(OUT_PATH, result)
            print(f"[fetch_gta6_missions] Written stub ({len(result['missions'])} missions)")
        else:
            print("[fetch_gta6_missions] No change")
        return

    print(f"[fetch_gta6_missions] Found {len(members)} mission pages — LAUNCH DATA AVAILABLE!")
    missions_out: dict[str, dict] = dict(seed_map)

    for i, member in enumerate(members):
        title = member["title"]
        mid   = title_to_id(title)
        print(f"  [{i+1}/{len(members)}] {title}")

        page_data = fetch_mission_page(session, title)
        if page_data:
            missions_out[mid] = page_data

        time.sleep(0.8)

    result = build_result(list(missions_out.values()))
    print(f"[fetch_gta6_missions] Compiled {len(result['missions'])} GTA VI missions")

    if args.dry_run:
        print("[dry-run] Sample:", json.dumps(result["missions"][:2], indent=2))
        return

    if has_changed(result, OUT_PATH):
        write_json(OUT_PATH, result)
        print(f"[fetch_gta6_missions] ✓ Written to data/{OUT_PATH}")
    else:
        print("[fetch_gta6_missions] No change")


if __name__ == "__main__":
    main()
