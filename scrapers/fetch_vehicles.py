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
# GID 1399962921 = simplified export (Position, Car, Class, Position in class, Time)
# GID 1299124236 = legacy "Times, Speeds & Tiers" multi-header format
CSV_URL = os.getenv(
    "BROUGHY_CSV_URL",
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1399962921",
)

OUT_PATH = "gta-5/vehicles/performance.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

# Column indices — resolved at runtime via header detection (see fetch())
COL_CLASS     = 0
COL_VEHICLE   = 1
COL_TIER      = 2
COL_LAP_TIME  = 3
COL_TOP_SPEED = 6  # optional — may not exist in simplified export


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

    # Auto-detect column positions from the header row
    # Supports both the simplified export and the legacy multi-header format
    header_idx = 0
    for i, row in enumerate(rows[:10]):
        if len(row) > 1 and row[1].strip().lower() in ("vehicle", "name", "car"):
            header_idx = i
            break

    header = [h.strip().lower() for h in rows[header_idx]]

    def col(names):
        for name in names:
            for i, h in enumerate(header):
                if name in h:
                    return i
        return None

    c_vehicle   = col(["car", "vehicle", "name"])
    c_class     = col(["class"])
    c_tier      = col(["tier"])
    c_lap       = col(["time", "lap time"])
    c_speed     = col(["top speed", "speed"])
    c_pos_class = col(["position in class", "pos in class"])

    # Data starts the row after the header (simplified format: +1, legacy: +2)
    # Check if next row looks like data or a second header row
    data_start = header_idx + 1
    if data_start < len(rows):
        sample = rows[data_start]
        # If second row has no numbers it's likely a sub-header — skip it
        if all(not any(c.isdigit() for c in cell) for cell in sample[:4] if cell):
            data_start += 1

    vehicles = []
    current_class = ""
    for row in rows[data_start:]:
        if not row or len(row) < 3:
            continue

        # Class — use detected column, fall back to tracking current class
        raw_class = row[c_class].strip() if c_class is not None and c_class < len(row) else ""
        if raw_class and raw_class.lower() not in ("class", ""):
            current_class = raw_class

        name = row[c_vehicle].strip() if c_vehicle is not None and c_vehicle < len(row) else ""
        if not name or name.lower() in ("car", "vehicle", "name", ""):
            continue

        lap_raw = row[c_lap].strip() if c_lap is not None and c_lap < len(row) else ""
        lap_sec = lap_to_seconds(lap_raw)

        speed_raw = row[c_speed].strip() if c_speed is not None and c_speed < len(row) else ""
        try:
            speed = round(float(speed_raw), 2)
        except (ValueError, TypeError):
            speed = None

        tier = row[c_tier].strip() if c_tier is not None and c_tier < len(row) else ""

        # Position in class (if available)
        pos_class = None
        if c_pos_class is not None and c_pos_class < len(row):
            try:
                pos_class = int(row[c_pos_class].strip())
            except (ValueError, TypeError):
                pass

        vehicles.append({
            "name": name,
            "class": current_class,
            "tier": tier if tier and tier not in ("-", "") else None,
            "lap_time": lap_raw if lap_raw and lap_raw != "-" else None,
            "lap_seconds": lap_sec,
            "top_speed_mph": speed,
            "position_in_class": pos_class,
        })

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
