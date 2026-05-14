"""
Scrape GTA V PC concurrent player history from SteamCharts.
URL: https://steamcharts.com/app/271590
"""

import cloudscraper
from bs4 import BeautifulSoup

from utils import has_changed, now_iso, write_json

URL = "https://steamcharts.com/app/271590"
OUT_PATH = "meta/steam-players.json"


def parse_number(raw: str) -> int | None:
    clean = raw.strip().replace(",", "")
    try:
        return int(float(clean))
    except (ValueError, TypeError):
        return None


def fetch() -> list[dict]:
    scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows"})
    resp = scraper.get(URL, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    table = soup.find("table", {"id": "main-chart-table"})
    if not table:
        # Fallback: find any table with month/average columns
        table = soup.find("table")
    if not table:
        raise ValueError("Could not find player data table on SteamCharts page")

    rows = table.find_all("tr")
    data = []

    for row in rows[1:]:  # skip header
        cells = row.find_all("td")
        if len(cells) < 4:
            continue

        month_year = cells[0].get_text(strip=True)  # e.g. "March 2020"
        avg_raw = cells[1].get_text(strip=True)
        peak_raw = cells[2].get_text(strip=True)

        parts = month_year.rsplit(" ", 1)
        if len(parts) != 2:
            continue
        month, year_str = parts
        try:
            year = int(year_str)
        except ValueError:
            continue

        avg = parse_number(avg_raw)
        peak = parse_number(peak_raw)

        if avg is None:
            continue

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

    payload = {
        "last_updated": now_iso(),
        "source": "SteamCharts — https://steamcharts.com/app/271590",
        "data": data,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        print("Data updated.")
    else:
        print("No changes detected, skipping write.")


if __name__ == "__main__":
    main()
