"""
Fetch Broughy1322 GTA V vehicle performance data from the public Google Sheet CSV export.

Sheet: search "Broughy1322 GTA vehicle spreadsheet" for the current public URL.
Set BROUGHY_SHEET_ID env var to the Google Sheets document ID, or override
BROUGHY_CSV_URL with the full export URL.
"""

import csv
import io
import os
import sys

import requests

from utils import has_changed, now_iso, write_json

SHEET_ID = os.getenv(
    "BROUGHY_SHEET_ID",
    "1nQND3ikiLzS3Ij9kuV-rVkAtoJMwDIhuHHMnpFCRR-k",
)
# GID 0 = first sheet (lap times). Adjust if Broughy restructures the sheet.
CSV_URL = os.getenv(
    "BROUGHY_CSV_URL",
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0",
)

OUT_PATH = "vehicles/performance.json"

# Column names vary between sheet versions — adjust if scrape breaks
COL_MAP = {
    "name": ["Name", "Vehicle", "Car"],
    "class": ["Class"],
    "lap_time": ["Lap Time", "Lap", "Best Lap"],
    "top_speed_mph": ["Top Speed (mph)", "Top Speed", "Speed (mph)"],
    "drivetrain": ["Drive", "Drivetrain", "DR"],
}


def find_col(header_row: list[str], candidates: list[str]) -> int | None:
    for c in candidates:
        for i, h in enumerate(header_row):
            if h.strip().lower() == c.lower():
                return i
    return None


def lap_to_seconds(lap: str) -> float | None:
    lap = lap.strip()
    if not lap or lap == "N/A":
        return None
    try:
        parts = lap.split(":")
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        return float(lap)
    except ValueError:
        return None


def fetch() -> list[dict]:
    resp = requests.get(CSV_URL, timeout=30)
    resp.raise_for_status()

    reader = csv.reader(io.StringIO(resp.text))
    rows = list(reader)

    if not rows:
        raise ValueError("Empty CSV response")

    # Find the header row (first row with "Name" or "Vehicle")
    header_idx = 0
    for i, row in enumerate(rows[:10]):
        if any(c.strip().lower() in ("name", "vehicle", "car") for c in row):
            header_idx = i
            break

    header = rows[header_idx]
    cols = {
        key: find_col(header, candidates)
        for key, candidates in COL_MAP.items()
    }

    vehicles = []
    for row in rows[header_idx + 1 :]:
        if not row or not row[0].strip():
            continue
        try:
            name_idx = cols["name"]
            name = row[name_idx].strip() if name_idx is not None else ""
            if not name:
                continue

            lap_raw = row[cols["lap_time"]].strip() if cols["lap_time"] is not None else ""
            lap_sec = lap_to_seconds(lap_raw)

            speed_raw = row[cols["top_speed_mph"]].strip() if cols["top_speed_mph"] is not None else ""
            try:
                speed = float(speed_raw)
            except (ValueError, TypeError):
                speed = None

            vehicles.append(
                {
                    "name": name,
                    "class": row[cols["class"]].strip() if cols["class"] is not None else "",
                    "lap_time": lap_raw,
                    "lap_seconds": lap_sec,
                    "top_speed_mph": speed,
                    "drivetrain": row[cols["drivetrain"]].strip() if cols["drivetrain"] is not None else "",
                }
            )
        except IndexError:
            continue

    return vehicles


def main() -> None:
    print("Fetching Broughy vehicle data...")
    vehicles = fetch()
    print(f"  Parsed {len(vehicles)} vehicles")

    payload = {
        "last_updated": now_iso(),
        "source": "Broughy1322 GTA Vehicle Performance Spreadsheet",
        "vehicles": vehicles,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("Data updated.")
    else:
        print("No changes detected, skipping write.")


if __name__ == "__main__":
    main()
