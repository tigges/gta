#!/usr/bin/env python3
"""
fetch_gta_ppi.py — GTA Purchasing Power Index computation + basket price validation

Reads:  data/gta-5/economy/price-basket.json    (basket items + historical prices)
        data/gta-5/economy/meta-history.json     (top GTA$/hr per patch era)
        data/gta-5/economy/item-catalogue.json   (live prices from GTA Wiki, optional)
Writes: data/gta-5/economy/gta-ppi.json         (computed GTA-PPI series)

GTA-PPI = basket_cost / top_hourly_yield
Rising index = players need more hours to buy the same basket = hidden inflation.

When item-catalogue.json is available (produced by fetch_gta_prices.py), this
scraper also computes:
  - current_basket_cost: live price from catalogue vs seeded basket cost
  - price_drift: any items whose current price differs from the seeded value
    (GTA Online prices almost never change — any drift is flagged for review)

Run order in CI:
  1. fetch_gta_prices.py  → item-catalogue.json
  2. fetch_gta_ppi.py     → gta-ppi.json (reads catalogue if available)
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import write_json, has_changed, now_iso

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"


def load(rel: str) -> dict:
    with open(DATA_DIR / rel) as f:
        return json.load(f)


def load_catalogue_prices(basket_items: list[dict]) -> dict[str, int | None]:
    """
    Look up current live prices for basket items from item-catalogue.json.
    Returns {item_id: current_price_or_None}.
    """
    cat_path = DATA_DIR / "gta-5/economy/item-catalogue.json"
    if not cat_path.exists():
        return {}

    with open(cat_path) as f:
        catalogue = json.load(f)

    cat_by_id   = {item["id"]: item for item in catalogue.get("items", [])}
    cat_by_name = {item["name"].lower(): item for item in catalogue.get("items", [])}

    result: dict[str, int | None] = {}
    for basket_item in basket_items:
        item_id   = basket_item["id"]
        item_name = basket_item["name"].lower()
        cat_item  = cat_by_id.get(item_id) or cat_by_name.get(item_name)
        result[item_id] = cat_item["price"] if cat_item else None

    return result


def check_price_drift(
    basket_items: list[dict],
    live_prices: dict[str, int | None],
) -> list[dict]:
    """
    Compare seeded basket prices against live catalogue prices.
    Returns list of items with unexpected price changes.
    """
    drift = []
    for item in basket_items:
        seeded = item.get("current_price")
        live   = live_prices.get(item["id"])
        if live is None or seeded is None:
            continue
        if live != seeded:
            pct = round((live - seeded) / seeded * 100, 1)
            drift.append({
                "id":           item["id"],
                "name":         item["name"],
                "seeded_price": seeded,
                "live_price":   live,
                "change_pct":   pct,
            })
    return drift


def compute_ppi(basket_data: dict, meta_data: dict) -> dict:
    era_prices  = basket_data["era_prices"]
    meta_series = meta_data["meta_history"]
    basket_items = basket_data.get("items", [])

    # Load live catalogue prices (best effort)
    live_prices = load_catalogue_prices(basket_items)
    price_drift = check_price_drift(basket_items, live_prices)

    if price_drift:
        print(f"[gta-ppi] ⚠ Price drift detected in {len(price_drift)} basket items:")
        for d in price_drift:
            print(f"  {d['name']}: seeded ${d['seeded_price']:,} → live ${d['live_price']:,} ({d['change_pct']:+}%)")
    elif live_prices:
        covered = sum(1 for v in live_prices.values() if v is not None)
        print(f"[gta-ppi] Catalogue validation: {covered}/{len(basket_items)} items matched, no price drift")

    yield_by_date: dict[str, int] = {m["date"]: m["top_gta_per_hr"] for m in meta_series}

    def find_yield(target_date: str) -> int | None:
        if target_date in yield_by_date:
            return yield_by_date[target_date]
        candidates = [(d, y) for d, y in yield_by_date.items() if d <= target_date]
        return sorted(candidates)[-1][1] if candidates else None

    base_hours: float | None = None
    series = []

    for era in era_prices:
        top_yield = find_yield(era["date"])
        if not top_yield:
            continue
        basket_cost = era.get("basket_cost_available", 0)
        if basket_cost <= 0:
            continue

        hours = round(basket_cost / top_yield, 2)
        if base_hours is None:
            base_hours = hours

        ppi = round((hours / base_hours) * 100, 1) if base_hours else 100.0

        note_lower = era.get("note", "").lower()
        if "nerf" in note_lower:
            event = "nerf"
        elif any(w in note_lower for w in ["buff", "increase", "doubled", "tripled", "improved"]):
            event = "buff"
        elif "oppressor" in note_lower or "structural break" in note_lower:
            event = "basket_expansion"
        else:
            event = None

        series.append({
            "patch":            era["patch"],
            "date":             era["date"],
            "top_yield":        top_yield,
            "basket_cost":      basket_cost,
            "hours_to_basket":  hours,
            "ppi":              ppi,
            "event":            event,
            "note":             era.get("note", ""),
        })

    for i, s in enumerate(series):
        s["ppi_yoy"] = None if i == 0 else round(s["ppi"] - series[i - 1]["ppi"], 1)

    # Current basket cost using live prices where available
    current_basket_live: int | None = None
    if live_prices and basket_items:
        total = 0
        complete = True
        for item in basket_items:
            live = live_prices.get(item["id"])
            if live is None:
                # Fall back to seeded current price
                live = item.get("current_price")
            if live is None:
                complete = False
                break
            total += live
        if complete:
            current_basket_live = total

    return {
        "schema_version":      "1.0",
        "last_updated":        now_iso(),
        "source":              "Computed from price-basket.json + meta-history.json",
        "note":                (
            "GTA-PPI = hours_to_buy_basket = basket_cost / top_hourly_yield. "
            "Base 100 = launch era. Lower is better. Rising = hidden inflation via payout nerfs."
        ),
        "methodology":         basket_data.get("methodology", ""),
        "base_period":         basket_data.get("base_period", "2013-10-01"),
        "base_hours":          base_hours,
        "current_basket_live": current_basket_live,
        "price_drift":         price_drift,
        "series":              series,
    }


def main() -> None:
    print("[gta-ppi] Loading source data…")
    basket_data = load("gta-5/economy/price-basket.json")
    meta_data   = load("gta-5/economy/meta-history.json")

    result  = compute_ppi(basket_data, meta_data)
    out_rel = "gta-5/economy/gta-ppi.json"

    if has_changed(result, out_rel):
        write_json(out_rel, result)
        print(f"[gta-ppi] ✓ {len(result['series'])} entries written")
    else:
        print(f"[gta-ppi] No change — {out_rel} unchanged")


if __name__ == "__main__":
    main()
