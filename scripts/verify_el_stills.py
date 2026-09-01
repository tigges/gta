#!/usr/bin/env python3
"""Assert every Extended Look still path exists under public/."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/gta-6/extended-look-stills.json"
PUBLIC = ROOT / "public"


def collect(obj) -> list[str]:
    paths: list[str] = []
    if isinstance(obj, dict):
        if isinstance(obj.get("src"), str):
            paths.append(obj["src"])
        if isinstance(obj.get("cover"), str):
            paths.append(obj["cover"])
        for v in obj.values():
            paths.extend(collect(v))
    elif isinstance(obj, list):
        for item in obj:
            paths.extend(collect(item))
    return paths


def main() -> int:
    data = json.loads(DATA.read_text())
    paths = sorted(set(collect(data)))
    missing = []
    for rel in paths:
        disk = PUBLIC / rel.lstrip("/")
        if not disk.is_file():
            missing.append(rel)
    print(f"checked {len(paths)} unique still paths")
    if missing:
        print("MISSING:")
        for p in missing:
            print(f"  {p}")
        return 1
    print("OK — every Extended Look still is on disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
