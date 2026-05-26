"""
Scrape GTA V PC concurrent player history from SteamCharts.
Also fetches live current player count from the Steam Web API (no key required).
URL: https://steamcharts.com/app/271590
"""

import requests
import cloudscraper
from bs4 import BeautifulSoup

from utils import has_changed, now_iso, write_json

URL = "https://steamcharts.com/app/271590"
LIVE_URL = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid=271590"
OUT_PATH = "gta-5/meta/steam-players.json"


def parse_number(raw: str) -> int | None:
    clean = raw.strip().replace(",", "")
    try:
        return int(float(clean))
    except (ValueError, TypeError):
        return None


def find_col_index(headers: list[str], *candidates: str) -> int | None:
    """Return the index of the first header cell matching any candidate (case-insensitive)."""
    normalised = [h.strip().lower() for h in headers]
    for candidate in candidates:
        c = candidate.strip().lower()
        if c in normalised:
            return normalised.index(c)
    return None


def fetch_current_players() -> int | None:
    """Fetch live concurrent player count from the Steam Web API (no key needed)."""
    try:
        resp = requests.get(LIVE_URL, timeout=10)
        resp.raise_for_status()
        return resp.json().get("response", {}).get("player_count")
    except Exception as e:
        print(f"  Warning: could not fetch live player count: {e}")
        return None


def fetch() -> list[dict]:
    scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows"})
    resp = scraper.get(URL, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    # Try the known table ID first, then fall back to the first table on the page
    table = soup.find("table", {"id": "main-chart-table"}) or soup.find("table")
    if not table:
        raise ValueError("Could not find player data table on SteamCharts page")

    rows = table.find_all("tr")
    if not rows:
        raise ValueError("Player data table is empty")

    # Detect column positions from the header row
    header_cells = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
    print(f"  Table headers: {header_cells}")

    month_idx = find_col_index(header_cells, "Month", "Date")
    avg_idx   = find_col_index(header_cells, "Avg. Players", "Avg Players", "Average")
    peak_idx  = find_col_index(header_cells, "Peak Players", "Peak", "Max Players")

    if month_idx is None or avg_idx is None or peak_idx is None:
        raise ValueError(
            f"Could not locate required columns in headers: {header_cells}"
        )

    data = []
    for row in rows[1:]:
        cells = row.find_all("td")
        if len(cells) <= max(month_idx, avg_idx, peak_idx):
            continue

        month_year = cells[month_idx].get_text(strip=True)  # e.g. "March 2020"
        avg_raw    = cells[avg_idx].get_text(strip=True)
        peak_raw   = cells[peak_idx].get_text(strip=True)

        # Skip summary / incomplete rows (e.g. "Last 30 Days")
        parts = month_year.rsplit(" ", 1)
        if len(parts) != 2:
            continue
        month, year_str = parts
        try:
            year = int(year_str)
        except ValueError:
            continue

        avg  = parse_number(avg_raw)
        peak = parse_number(peak_raw)

        if avg is None:
            continue

        # Sanity-check: peak must be positive and >= avg
        if peak is not None and peak < 0:
            peak = None

        data.append(
            {
                "year": year,
                "month": month,
                "avg_players": avg,
                "peak_players": peak,
            }
        )

    # SteamCharts returns newest-first; reverse for chronological order
    data.reverse()
    return data


def main() -> None:
    print("Fetching SteamCharts player data...")
    data = fetch()
    print(f"  Parsed {len(data)} monthly records")

    current = fetch_current_players()
    if current:
        print(f"  Live current players: {current:,}")

    payload = {
        "last_updated": now_iso(),
        "source": "SteamCharts + Steam Web API (no key required)",
        "current_players": current,
        "current_players_updated": now_iso() if current else None,
        "data": data,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("Data updated.")
    else:
        print("No changes detected, skipping write.")


if __name__ == "__main__":
    main()
