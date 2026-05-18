"""
derive_revenue_tiers.py
Derives revenue-tiers.json from business-profiles.json.

Runs after fetch_gta_income.py in nightly CI. Preserves the tier structure
and manually curated stack/meta entries; only updates gta_per_hr values from
the live business-profiles data.
"""
import json
from utils import DATA_DIR, write_json, now_iso, has_changed, load_existing

BIZ_PATH = DATA_DIR / "gta-5/economy/business-profiles.json"
TIERS_PATH = "gta-5/economy/revenue-tiers.json"

# Tier thresholds (net $/hr)
TIER_BANDS = [
    ("S+", 1_600_001, float("inf"), "#22c55e", "God Tier — Stacked Optimal Play"),
    ("S",  800_001,  1_600_000, "#86efac", "S Tier — Top Active Methods"),
    ("A",  400_001,    800_000, "#f59e0b", "A Tier — Strong Performers"),
    ("B",  150_001,    400_000, "#94a3b8", "B Tier — Solid Side Income"),
    ("C",        0,    150_000, "#71717a", "C Tier — Starter / Supplement"),
    ("D", -float("inf"), 0,     "#ef4444", "D Tier — Below Break-Even"),
]


def tier_for(net_hr: float) -> str:
    for tier, low, high, *_ in TIER_BANDS:
        if low <= net_hr <= high:
            return tier
    return "C"


def build_tiers(businesses: list[dict], existing: dict) -> dict:
    # Build a lookup from existing tier sources to preserve manual metadata
    existing_sources: dict[str, dict] = {}
    for t in existing.get("tiers", []):
        for s in t.get("sources", []):
            existing_sources[s["id"]] = s

    # Build tier buckets from live business data
    tier_buckets: dict[str, list[dict]] = {b[0]: [] for b in TIER_BANDS}

    for biz in businesses:
        net = biz.get("net_profit_per_hr", 0)
        tier = tier_for(net)
        existing_s = existing_sources.get(biz["id"], {})
        tier_buckets[tier].append({
            "id":         biz["id"],
            "name":       biz.get("name", biz["id"]),
            "gta_per_hr": net,
            "type":       biz.get("category", "business"),
            "solo":       biz.get("solo", False),
            "setup_gta":  biz.get("setup_cost_full", 0),
            "note":       existing_s.get("note", biz.get("notes", "")),
        })

    # Preserve manually curated stack/meta entries that aren't in business profiles
    for src_id, src in existing_sources.items():
        if src.get("type") == "stack":
            t = tier_for(src.get("gta_per_hr", 0))
            # Only add if not already derived from profiles
            if not any(s["id"] == src_id for s in tier_buckets[t]):
                tier_buckets[t].append(src)

    # Sort each tier by gta_per_hr desc
    for tier in tier_buckets:
        tier_buckets[tier].sort(key=lambda x: x.get("gta_per_hr", 0), reverse=True)

    # Build final tiers list (only include non-empty tiers)
    tiers_list = []
    for tier_id, low, high, color, label in TIER_BANDS:
        sources = tier_buckets.get(tier_id, [])
        if not sources:
            continue
        tiers_list.append({
            "tier":    tier_id,
            "label":   label,
            "color":   color,
            "sources": sources,
        })

    # Preserve optimal_starter_path from existing
    payload = {
        "last_updated":       now_iso(),
        "source":             "Derived from business-profiles.json nightly",
        "note":               "Tier assignments derived from net_profit_per_hr. Stack entries preserved manually.",
        "tiers":              tiers_list,
        "optimal_starter_path": existing.get("optimal_starter_path", []),
    }
    return payload


def main() -> None:
    biz_data = json.loads(BIZ_PATH.read_text())
    businesses = [b for b in biz_data.get("businesses", []) if b.get("net_profit_per_hr", 0) > 0]
    existing = load_existing(TIERS_PATH)

    payload = build_tiers(businesses, existing)
    if has_changed(payload, TIERS_PATH):
        write_json(TIERS_PATH, payload)
        print(f"revenue-tiers.json updated: {sum(len(t['sources']) for t in payload['tiers'])} sources across {len(payload['tiers'])} tiers")
    else:
        print("revenue-tiers.json unchanged")


if __name__ == "__main__":
    main()
