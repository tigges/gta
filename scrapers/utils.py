import json
import os
from datetime import datetime, timezone
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data"


def write_json(relative_path: str, payload: dict) -> None:
    out = DATA_DIR / relative_path
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Written: {out}")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_existing(relative_path: str) -> dict:
    out = DATA_DIR / relative_path
    if out.exists():
        with open(out, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def has_changed(new_data: dict, relative_path: str) -> bool:
    existing = load_existing(relative_path)
    # Strip last_updated before comparing so timestamp alone doesn't trigger rebuild
    def strip_ts(d):
        return {k: v for k, v in d.items() if k != "last_updated"}
    return strip_ts(new_data) != strip_ts(existing)
