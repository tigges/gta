"""
Fetch Broughy1322 GTA V vehicle performance data from the public Google Sheet CSV export.

Sheet: https://docs.google.com/spreadsheets/d/1nQND3ikiLzS3Ij9kuV-rVkRtoYetb79c52JWyafb4m4
Override BROUGHY_SHEET_ID or BROUGHY_CSV_URL env vars to point to a different export.

The main performance sheet (gid=1299124236) has a two-row header:
  Row 1: Class | Vehicle | Tier | Lap Time (m:ss.000) | Lap Time Position | | Top Speed (mph) | ...
  Row 2:       |         |      |                     | In Class | Overall |               | ...
Data starts at row 3.
"""

import csv
import io
import os

import requests

from utils import has_changed, now_iso, write_json

SHEET_ID = os.getenv(
    "BROUGHY_SHEET_ID",
    "1nQND3ikiLzS3Ij9kuV-rVkRtoYetb79c52JWyafb4m4",
)
# GID 1299124236 = "Times, Speeds & Tiers" sheet (by class, then race tier, then lap time)
CSV_URL = os.getenv(
    "BROUGHY_CSV_URL",
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1299124236",
)

OUT_PATH = "gta-5/vehicles/performance.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

# Fixed column indices for this sheet layout (stable across Broughy's updates)
COL_CLASS     = 0
COL_VEHICLE   = 1
COL_TIER      = 2
COL_LAP_TIME  = 3
COL_TOP_SPEED = 6  # "Top Speed (mph)"


def lap_to_seconds(lap: str) -> float | None:
    lap = lap.strip()
    if not lap or lap in ("-", "N/A", ""):
        return None
    try:
        parts = lap.split(":")
        if len(parts) == 2:
            return round(float(parts[0]) * 60 + float(parts[1]), 3)
        return round(float(lap), 3)
    except ValueError:
        return None


def fetch() -> list[dict]:
    resp = requests.get(CSV_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    reader = csv.reader(io.StringIO(resp.text))
    rows = list(reader)

    if not rows:
        raise ValueError("Empty CSV response")

    # Find the header row (first row whose second cell is "Vehicle")
    header_idx = 1  # default based on known sheet structure
    for i, row in enumerate(rows[:10]):
        if len(row) > 1 and row[1].strip().lower() in ("vehicle", "name", "car"):
            header_idx = i
            break

    # Data starts one row after the (two-part) header
    data_start = header_idx + 2

    vehicles = []
    current_class = ""
    for row in rows[data_start:]:
        if not row or len(row) <= COL_TOP_SPEED:
            continue

        # Class column may repeat only at the first vehicle in each class
        raw_class = row[COL_CLASS].strip()
        if raw_class:
            current_class = raw_class

        name = row[COL_VEHICLE].strip()
        if not name:
            continue

        lap_raw   = row[COL_LAP_TIME].strip()
        lap_sec   = lap_to_seconds(lap_raw)

        speed_raw = row[COL_TOP_SPEED].strip()
        try:
            speed = round(float(speed_raw), 2)
        except (ValueError, TypeError):
            speed = None

        tier = row[COL_TIER].strip() if len(row) > COL_TIER else ""

        vehicles.append(
            {
                "name": name,
                "class": current_class,
                "tier": tier if tier and tier != "-" else None,
                "lap_time": lap_raw if lap_raw and lap_raw != "-" else None,
                "lap_seconds": lap_sec,
                "top_speed_mph": speed,
            }
        )

    return vehicles


def main() -> None:
    print("Fetching Broughy vehicle data...")
    vehicles = fetch()
    print(f"  Parsed {len(vehicles)} vehicles")

    payload = {
        "last_updated": now_iso(),
        "source": "Broughy1322 GTA Vehicle Performance Spreadsheet — https://broughy.com/testing",
        "vehicles": vehicles,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("Data updated.")
    else:
        print("No changes detected, skipping write.")


if __name__ == "__main__":
    main()
