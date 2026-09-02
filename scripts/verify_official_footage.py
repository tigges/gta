#!/usr/bin/env python3
"""Regression tests for official-footage detect + playbook.

Reproduces the 9317ecb failure mode: YouTube search returns only T1/T2
and must not drop Extended Look from the registry.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scrapers"))
sys.path.insert(0, str(ROOT / "scrapers" / "gtavi"))

from fetch_trailers import (  # noqa: E402
    KNOWN_TRAILERS,
    is_official_footage,
    merge_registry,
)
from fetch_youtube_velocity import load_trailer_list  # noqa: E402
from on_new_official_footage import (  # noqa: E402
    ensure_analysis_stub,
    needs_brief,
    propose_press_stills,
    scan_keywords,
    slug_for,
)
from post_discord_digest import footage_alert_field  # noqa: E402

EL_ID = "tJbzMqJGH4k"
T1_ID = "QdBZY2fkU-0"
T2_ID = "VQRLujxTm3c"

failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    if ok:
        print(f"  ok  {msg}")
    else:
        print(f"  FAIL {msg}")
        failures.append(msg)


def test_title_filter() -> None:
    print("title filter")
    check(is_official_footage("Grand Theft Auto VI Trailer 1"), "T1 matches")
    check(is_official_footage("Grand Theft Auto VI Trailer 2"), "T2 matches")
    check(is_official_footage("Grand Theft Auto VI: An Extended Look"), "EL matches")
    check(is_official_footage("GTA VI Official Gameplay"), "gameplay matches")
    check(not is_official_footage("GTA VI Official Soundtrack"), "soundtrack excluded")
    check(not is_official_footage("Random GTA clip"), "generic title rejected")
    check(not is_official_footage("Red Dead Redemption 2 Trailer"), "other franchise rejected")


def test_union_survives_t1_t2_api() -> None:
    print("9317ecb regression — API returns T1+T2 only")
    existing = [
        {"youtube_id": T1_ID, "title": "T1", "published_at": "2023-12-04"},
        {"youtube_id": T2_ID, "title": "T2", "published_at": "2025-05-06"},
        {
            "youtube_id": EL_ID,
            "title": "Grand Theft Auto VI: An Extended Look",
            "published_at": "2026-08-28",
            "type": "extended_look",
            "duration_sec": 1609,
            "notes": "curated",
        },
    ]
    discovered = [
        {"youtube_id": T1_ID, "title": "Grand Theft Auto VI Trailer 1", "published_at": "2023-12-04"},
        {"youtube_id": T2_ID, "title": "Grand Theft Auto VI Trailer 2", "published_at": "2025-05-06"},
    ]
    merged = merge_registry(discovered, existing=existing)
    ids = [t["youtube_id"] for t in merged]
    check(EL_ID in ids, "EL survives API-only T1+T2")
    check(T1_ID in ids and T2_ID in ids, "T1 and T2 still present")
    el = next(t for t in merged if t["youtube_id"] == EL_ID)
    check(el.get("type") == "extended_look", "curated type preserved")
    check(el.get("duration_sec") == 1609, "curated duration preserved")
    check(el.get("notes") == "curated", "curated notes preserved")


def test_known_floor_without_existing_file() -> None:
    print("known-list floor with empty existing file")
    discovered = [
        {"youtube_id": T1_ID, "title": "Grand Theft Auto VI Trailer 1", "published_at": "2023-12-04"},
    ]
    merged = merge_registry(discovered, existing=[])
    ids = {t["youtube_id"] for t in merged}
    check(ids >= {T1_ID, T2_ID, EL_ID}, "KNOWN_TRAILERS unioned when file empty")
    check(len(KNOWN_TRAILERS) >= 3, "KNOWN_TRAILERS includes EL")


def test_trailers_json_restored() -> None:
    print("trailers.json registry")
    data = json.loads((ROOT / "data/gta-6/trailers.json").read_text())
    ids = [t["youtube_id"] for t in data.get("trailers", [])]
    check(EL_ID in ids, "EL restored in trailers.json")
    check(len(ids) >= 3, f"at least 3 official videos (got {len(ids)})")


def test_velocity_reads_registry() -> None:
    print("velocity source")
    listed = load_trailer_list()
    ids = [t["youtube_id"] for t in listed]
    check(EL_ID in ids, "load_trailer_list includes EL from trailers.json")


def test_playbook_helpers() -> None:
    print("playbook helpers")
    check(slug_for({"title": "Grand Theft Auto VI: An Extended Look", "youtube_id": EL_ID}) == "extended-look", "EL slug")
    check(needs_brief({"youtube_id": "new"}, None), "missing analysis needs brief")
    check(needs_brief({"youtube_id": "new"}, {"events": []}), "empty events needs brief")
    check(not needs_brief({"youtube_id": EL_ID}, {"events": [{"t": 0}]}), "filled analysis quiet")

    analysis = {"trailers": []}
    added = ensure_analysis_stub(
        {"youtube_id": "NEWVID01", "title": "Grand Theft Auto VI Trailer 3", "published_at": "2027-01-01"},
        analysis,
    )
    check(added, "stub added for unknown id")
    check(analysis["trailers"][0].get("stub") is True, "stub flag set")
    check(analysis["trailers"][0]["events"] == [], "stub events empty")
    check(not ensure_analysis_stub({"youtube_id": "NEWVID01", "title": "x"}, analysis), "no duplicate stub")

    hints = scan_keywords(
        "Rockstar showed a 6-star wanted level and Criminal Profile in Leonida.",
        "test",
        "NEWVID01",
    )
    labels = {h["label"] for h in hints}
    check("6-star wanted" in labels, "6-star hint")
    check("criminal profile" in labels, "criminal profile hint")

    inbox = {"seen_press_filenames": []}
    press = {"screenshots": [{"filename": "Vice_Beach_01.jpg", "path": "/assets/screenshots/Vice_Beach_01.jpg"}]}
    proposals, seen = propose_press_stills(inbox, press, {})
    check(proposals == [], "first run baselines press kit (no flood)")
    check("Vice_Beach_01.jpg" in seen, "baseline records current filenames")

    inbox2 = {"seen_press_filenames": ["Old.jpg"]}
    proposals2, _ = propose_press_stills(inbox2, press, {})
    check(any(p["filename"] == "Vice_Beach_01.jpg" for p in proposals2), "new press file proposed")
    check("not a video frame" in (proposals2[0]["attribution"].lower()), "stills labelled as press stills")


def test_discord_alert() -> None:
    print("discord alert")
    quiet = footage_alert_field({"videos": [{"youtube_id": EL_ID, "needs_brief": False}]})
    check(quiet is None, "no alert when all briefs exist")
    alert = footage_alert_field({
        "videos": [{"youtube_id": "NEWVID", "title": "Grand Theft Auto VI Trailer 3", "needs_brief": True}],
        "keyword_hints": [{}],
        "press_still_proposals": [],
    })
    check(alert is not None and "needs brief" in alert["value"].lower(), "alert when new video needs brief")


def main() -> int:
    test_title_filter()
    test_union_survives_t1_t2_api()
    test_known_floor_without_existing_file()
    test_trailers_json_restored()
    test_velocity_reads_registry()
    test_playbook_helpers()
    test_discord_alert()
    print()
    if failures:
        print(f"{len(failures)} failure(s)")
        return 1
    print("OK — official footage detect + playbook")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
