"""
derive_sale_frequency.py — Derive sale-frequency.json from bonus-history.json.

Aggregates the promotional time series into per-activity and per-item statistics:
  - How many times each activity received a bonus multiplier
  - How many times each item appeared in a sale
  - Average discount percentage
  - Most recent bonus/sale date
  - Estimated next bonus window (simple frequency-based projection)

Output: data/gta-5/economy/sale-frequency.json

Run after fetch_bonus_history.py or fetch_weekly_bonuses.py.
Also runs nightly in CI as a derived step.

Usage:
  python3 scrapers/derive_sale_frequency.py
"""

import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import write_json, has_changed, load_existing, now_iso

HISTORY_PATH  = "gta-5/economy/bonus-history.json"
OUTPUT_PATH   = "gta-5/economy/sale-frequency.json"


def iso_to_dt(s: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            dt = datetime.strptime(s[:19], fmt[:len(s[:19])])
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def main() -> None:
    existing = load_existing(HISTORY_PATH)
    weeks: list[dict] = existing.get("weeks", [])

    if not weeks:
        print("[derive_sale_frequency] No history data found — run fetch_bonus_history.py first")
        return

    print(f"[derive_sale_frequency] Processing {len(weeks)} weeks of history…")

    today = datetime.now(timezone.utc)

    # ── Per-activity bonus stats ──────────────────────────────────────────────
    activity_stats: dict[str, dict] = defaultdict(lambda: {
        "activity_id": "",
        "bonus_weeks": [],
        "bonus_count": 0,
        "max_multiplier_seen": 1,
        "avg_multiplier": 1.0,
        "last_bonus_date": None,
        "days_since_last_bonus": None,
        "avg_gap_weeks": None,
        "estimated_next_bonus": None,
    })

    for week in weeks:
        ws = week.get("week_start", "")
        for bonus in week.get("bonuses", []):
            aid = bonus.get("activity_id", "")
            mult = bonus.get("multiplier", 2)
            if not aid:
                continue
            s = activity_stats[aid]
            s["activity_id"] = aid
            s["bonus_weeks"].append(ws)
            s["bonus_count"] += 1
            if mult > s["max_multiplier_seen"]:
                s["max_multiplier_seen"] = mult

    # Compute derived stats for activities
    for aid, s in activity_stats.items():
        dates = sorted([iso_to_dt(w) for w in s["bonus_weeks"] if iso_to_dt(w)])
        if dates:
            s["last_bonus_date"] = dates[-1].strftime("%Y-%m-%d")
            s["days_since_last_bonus"] = (today - dates[-1]).days

            if len(dates) >= 2:
                gaps = [(dates[i + 1] - dates[i]).days / 7 for i in range(len(dates) - 1)]
                avg_gap = sum(gaps) / len(gaps)
                s["avg_gap_weeks"] = round(avg_gap, 1)
                next_dt = dates[-1] + timedelta(weeks=avg_gap)
                s["estimated_next_bonus"] = next_dt.strftime("%Y-%m-%d")

    # ── Per-item sale stats ───────────────────────────────────────────────────
    item_stats: dict[str, dict] = defaultdict(lambda: {
        "item_key": "",
        "sale_weeks": [],
        "sale_count": 0,
        "avg_discount_pct": 0.0,
        "max_discount_pct": 0,
        "last_sale_date": None,
        "days_since_last_sale": None,
        "avg_gap_weeks": None,
        "estimated_next_sale": None,
        "item_id": None,
        "item_name": None,
    })

    for week in weeks:
        ws = week.get("week_start", "")
        for sale in week.get("sales", []):
            desc = sale.get("item_description", "") or sale.get("item_name", "")
            if not desc:
                continue
            key = desc.lower()[:40].strip()
            pct = sale.get("discount_pct", 0)
            s = item_stats[key]
            s["item_key"] = key
            s["item_name"] = desc
            if sale.get("item_id"):
                s["item_id"] = sale["item_id"]
            s["sale_weeks"].append(ws)
            s["sale_count"] += 1
            if pct > s["max_discount_pct"]:
                s["max_discount_pct"] = pct

    # Compute derived stats for items
    for key, s in item_stats.items():
        pcts = []
        for week in weeks:
            for sale in week.get("sales", []):
                d = (sale.get("item_description", "") or "").lower()[:40]
                if d.strip() == key:
                    pcts.append(sale.get("discount_pct", 0))
        s["avg_discount_pct"] = round(sum(pcts) / len(pcts), 1) if pcts else 0

        dates = sorted([iso_to_dt(w) for w in s["sale_weeks"] if iso_to_dt(w)])
        if dates:
            s["last_sale_date"] = dates[-1].strftime("%Y-%m-%d")
            s["days_since_last_sale"] = (today - dates[-1]).days
            if len(dates) >= 2:
                gaps = [(dates[i + 1] - dates[i]).days / 7 for i in range(len(dates) - 1)]
                avg_gap = sum(gaps) / len(gaps)
                s["avg_gap_weeks"] = round(avg_gap, 1)
                next_dt = dates[-1] + timedelta(weeks=avg_gap)
                s["estimated_next_sale"] = next_dt.strftime("%Y-%m-%d")

    # Sort by most frequently promoted
    activities_list = sorted(
        [dict(v) for v in activity_stats.values() if v["bonus_count"] > 0],
        key=lambda x: x["bonus_count"], reverse=True
    )
    items_list = sorted(
        [dict(v) for v in item_stats.values() if v["sale_count"] > 0],
        key=lambda x: x["sale_count"], reverse=True
    )

    total_weeks = len(weeks)
    date_range = {
        "earliest": weeks[0]["week_start"] if weeks else None,
        "latest":   weeks[-1]["week_start"] if weeks else None,
        "total_weeks_tracked": total_weeks,
    }

    output = {
        "last_updated": now_iso(),
        "source": "Derived from bonus-history.json",
        "note": (
            "Per-activity and per-item promotional statistics. "
            "estimated_next_bonus/sale is a frequency-based projection — accuracy improves with more history. "
            "Rebuild nightly: python3 scrapers/derive_sale_frequency.py"
        ),
        "date_range": date_range,
        "activity_bonuses": activities_list,
        "item_sales": items_list,
    }

    # Print summary
    print(f"  Date range: {date_range['earliest']} → {date_range['latest']} ({total_weeks} weeks)")
    print(f"  Activities tracked: {len(activities_list)}")
    print(f"  Items tracked: {len(items_list)}")
    print(f"\nTop 5 most-bonused activities:")
    for a in activities_list[:5]:
        last = a.get("last_bonus_date", "?")
        gap  = f"{a['avg_gap_weeks']}w avg" if a.get("avg_gap_weeks") else "only once"
        print(f"  {a['activity_id']:40} × {a['bonus_count']} times  {gap}  last={last}")

    print(f"\nTop 5 most-discounted items:")
    for i in items_list[:5]:
        last = i.get("last_sale_date", "?")
        print(f"  {i['item_name'][:40]:40} × {i['sale_count']} times  avg={i['avg_discount_pct']}%  last={last}")

    if has_changed(output, OUTPUT_PATH):
        write_json(OUTPUT_PATH, output)
        print(f"\n[derive_sale_frequency] ✓ Saved sale-frequency.json")
    else:
        print(f"\n[derive_sale_frequency] No change")


if __name__ == "__main__":
    main()
