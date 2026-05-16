#!/usr/bin/env python3
"""
fetch_gta_ppi.py — GTA Purchasing Power Index computation

Reads:  data/gta-5/economy/price-basket.json   (basket item prices per patch era)
        data/gta-5/economy/meta-history.json    (top GTA$/hr per patch era)
Writes: data/gta-5/economy/gta-ppi.json        (computed GTA-PPI series)

GTA-PPI = basket_cost / top_hourly_yield
Rising index = players need more hours to buy the same basket = hidden inflation.

This scraper is deterministic (no network I/O) — it computes from seeded data.
Run it after updating price-basket.json or meta-history.json with a new patch.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils import write_json, has_changed, now_iso

ROOT = os.path.join(os.path.dirname(__file__), "..")


def load(path: str) -> dict:
    with open(os.path.join(ROOT, path)) as f:
        return json.load(f)


def compute_ppi(basket_data: dict, meta_data: dict) -> dict:
    era_prices = basket_data["era_prices"]
    meta_series = meta_data["meta_history"]

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
            "patch": era["patch"],
            "date": era["date"],
            "top_yield": top_yield,
            "basket_cost": basket_cost,
            "hours_to_basket": hours,
            "ppi": ppi,
            "event": event,
            "note": era.get("note", ""),
        })

    for i, s in enumerate(series):
        s["ppi_yoy"] = None if i == 0 else round(s["ppi"] - series[i - 1]["ppi"], 1)

    return {
        "schema_version": "1.0",
        "last_updated": now_iso(),
        "source": "Computed from price-basket.json + meta-history.json",
        "note": (
            "GTA-PPI = hours_to_buy_basket = basket_cost / top_hourly_yield. "
            "Base 100 = launch era. Lower is better. Rising = hidden inflation via payout nerfs."
        ),
        "methodology": basket_data.get("methodology", ""),
        "base_period": basket_data.get("base_period", "2013-10-01"),
        "base_hours": base_hours,
        "series": series,
    }


def main() -> None:
    print("[gta-ppi] Loading source data…")
    basket_data = load("data/gta-5/economy/price-basket.json")
    meta_data   = load("data/gta-5/economy/meta-history.json")

    result = compute_ppi(basket_data, meta_data)

    # Paths relative to DATA_DIR for write_json / has_changed
    out_rel = "gta-5/economy/gta-ppi.json"

    if has_changed(result, out_rel):
        write_json(out_rel, result)
        print(f"[gta-ppi] ✓ {len(result['series'])} entries written")
    else:
        print(f"[gta-ppi] No change — {out_rel} unchanged")


if __name__ == "__main__":
    main()
