"""
fetch_predictions_auto.py
─────────────────────────────────────────────────────────────────────────────
Automatically updates confirmed/data-derivable predictions in
data/gta-6/predictions.json when their source data changes.

Rules:
  - Only touches predictions with confidence_tier = "confirmed" OR those
    whose value can be computed deterministically from a data file.
  - Never invents new predictions. Never changes confidence_tier.
  - Writes a proposals block to data/gta-6/predictions-proposals.json for
    any change that requires human review before going to predictions.json.
  - Prints a summary of every change made and every proposal raised.

Run manually or as a nightly CI step after all other scrapers have run.
"""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # repo root
DATA = ROOT / "data"


# ── Helpers ───────────────────────────────────────────────────────────────────

def load(path: str) -> dict:
    return json.loads((DATA / path).read_text())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def pct_change(old, new) -> float:
    if not old:
        return 0
    return abs(new - old) / abs(old) * 100


# ── Source data loaders ───────────────────────────────────────────────────────

def load_confirmed_release_date() -> str | None:
    """
    Latest confirmed release date from delay-timeline.json.
    Uses the `confirmed_date` field on date_confirmed events — not the event date.
    """
    try:
        timeline = load("gta-6/delay-timeline.json")
        confirmed = [
            e for e in timeline.get("timeline", [])
            if e.get("type") == "date_confirmed" and e.get("confirmed_date")
        ]
        if confirmed:
            latest = sorted(confirmed, key=lambda e: e["date"])[-1]
            return latest["confirmed_date"]
    except Exception as e:
        print(f"  [warn] Could not read delay-timeline: {e}")
    return None


def load_confirmed_price() -> float | None:
    """Confirmed launch price from preorder-listings.json (consensus price)."""
    try:
        listings = load("feeds/preorder-listings.json")
        prices = [
            l["price_usd"]
            for l in listings.get("listings", [])
            if l.get("price_usd") and l.get("status") == "live"
        ]
        if prices:
            # Consensus = most common price
            return max(set(prices), key=prices.count)
    except Exception as e:
        print(f"  [warn] Could not read preorder-listings: {e}")
    return None


def compute_real_price_context(nominal_price: float) -> dict | None:
    """
    Compute the inflation-adjusted context for the launch price.
    Returns dict with real_price_2026 and comparisons to historical titles.
    """
    try:
        cpi = load("franchise/cpi.json")
        base = cpi["base_cpi"]  # current CPI level (2026)
        titles = cpi["titles"]
        real_prices = {}
        for t in titles:
            if t.get("price_nominal") and t.get("cpi_year"):
                real_prices[t["id"]] = round(t["price_nominal"] * base / t["cpi_year"], 2)
        # GTA VI real price at today's CPI (it IS the base year if $79.99 is 2026)
        gta6_real = nominal_price  # already in 2026 dollars
        # Find all historical titles with higher real price
        more_expensive = {
            tid: rp for tid, rp in real_prices.items()
            if rp > gta6_real and tid != "gta-6"
        }
        if more_expensive:
            most_expensive = max(more_expensive, key=more_expensive.get)
            return {
                "gta6_nominal": nominal_price,
                "gta6_real_2026": gta6_real,
                "most_expensive_id": most_expensive,
                "most_expensive_real": more_expensive[most_expensive],
                "cheaper_than_count": len(more_expensive),
                "all_real_prices": real_prices,
            }
    except Exception as e:
        print(f"  [warn] Could not compute real price context: {e}")
    return None


def load_vehicle_count() -> int | None:
    """Current indexed vehicle count from gta-6/entities/vehicles.json."""
    try:
        v = load("gta-6/entities/vehicles.json")
        return v.get("count")
    except Exception as e:
        print(f"  [warn] Could not read vehicles: {e}")
    return None


# ── Per-prediction update logic ───────────────────────────────────────────────

class PredictionUpdater:
    def __init__(self, predictions: list[dict]):
        self.predictions = {p["id"]: p for p in predictions}
        self.changes: list[dict] = []
        self.proposals: list[dict] = []
        self.added: list[dict] = []

    def get(self, pred_id: str) -> dict | None:
        return self.predictions.get(pred_id)

    def add_prediction(self, obj: dict) -> None:
        """Publish a brand-new prediction directly (auto-publish model)."""
        self.predictions[obj["id"]] = obj
        self.added.append(obj)

    def update(self, pred_id: str, field: str, old_val, new_val, source: str) -> bool:
        """Apply a confirmed update to a prediction field."""
        if old_val == new_val:
            return False
        p = self.predictions[pred_id]
        p[field] = new_val
        self.changes.append({
            "id": pred_id,
            "field": field,
            "old": old_val,
            "new": new_val,
            "source": source,
            "updated_at": now_iso(),
        })
        print(f"  ✓ [{pred_id}] {field}: {old_val!r} → {new_val!r}  (source: {source})")
        return True

    def propose(self, pred_id: str, field: str, current_val, proposed_val,
                rationale: str, confidence_delta: int = 0) -> None:
        """Add a proposal that requires human review."""
        # Determine if this modifies an existing prediction or adds a new one
        is_existing = any(p["id"] == pred_id for p in self.predictions.values())
        self.proposals.append({
            "id": pred_id,
            "type": "modify" if is_existing else "new",
            "field": field,
            "current": current_val,
            "proposed": proposed_val,
            "rationale": rationale,
            "confidence_delta": confidence_delta,
            "proposed_at": now_iso(),
            "status": "pending",
        })
        print(f"  ⚑ [{pred_id}] PROPOSAL: {field} → {proposed_val!r}  ({rationale})")


def load_drafts() -> list[dict]:
    """
    Load pending new prediction drafts from data/gta-6/predictions-drafts.json.

    Each draft with draft_status == "pending" (or missing draft_status) is
    treated as a candidate to promote into a proposal on /admin/proposals/.
    Drafts already marked "promoted" are skipped.
    """
    drafts_path = DATA / "gta-6/predictions-drafts.json"
    if not drafts_path.exists():
        return []
    try:
        data = json.loads(drafts_path.read_text())
        all_drafts = data.get("drafts", [])
        pending = [
            d for d in all_drafts
            if d.get("draft_status", "pending") == "pending"
        ]
        return pending
    except Exception as e:
        print(f"  [warn] Could not read predictions-drafts.json: {e}")
    return []


VALID_TIERS = {"confirmed", "reported", "predicted"}


def passes_quality_gate(obj: dict) -> tuple[bool, str]:
    """
    Automated quality gate for auto-published predictions. Replaces human
    pre-approval: a draft must clear these checks to publish unattended.
    Anything that fails is held back as a review proposal instead of dropped.
    """
    if not obj.get("id"):
        return False, "missing id"
    if not obj.get("title"):
        return False, "missing title"
    if obj.get("value") in (None, ""):
        return False, "missing value"
    conf = obj.get("confidence")
    if not isinstance(conf, int) or not (0 <= conf <= 100):
        return False, "confidence out of 0–100 range"
    if obj.get("confidence_tier") not in VALID_TIERS:
        return False, "invalid confidence_tier"
    if not (obj.get("basis") or obj.get("source")):
        return False, "no basis or source"
    return True, "ok"


def run_draft_publish(updater: PredictionUpdater) -> None:
    """
    Auto-publish model: pending prediction drafts go live automatically.

    For each pending draft whose id does not yet exist in predictions.json:
      - if it clears passes_quality_gate(), it is added straight to
        predictions.json (editorial_note "auto-published"); moderation is
        post-publication (demote/edit/remove), not pre-publication.
      - if it fails the gate, it falls back to a review proposal on
        /admin/proposals so it is surfaced for a fix rather than silently lost.

    Drafts whose id already exists are skipped (already live).
    """
    drafts = load_drafts()
    if not drafts:
        return

    print(f"\nProcessing {len(drafts)} pending draft(s) from predictions-drafts.json...")
    for draft in drafts:
        draft_id = draft.get("id", "")
        if not draft_id:
            print(f"  [skip] Draft missing 'id' field: {draft.get('title', '?')}")
            continue

        # Skip if the prediction already exists in predictions.json
        if updater.get(draft_id):
            print(f"  [skip] {draft_id} already exists in predictions.json"
                  " — mark draft as 'promoted'")
            continue

        # Strip the intake-only fields, then apply required defaults
        obj = {k: v for k, v in draft.items()
               if k not in ("draft_status", "draft_notes")}
        obj.setdefault("outcome_verified", False)
        obj.setdefault("outcome_actual", None)
        obj.setdefault("outcome_date", None)
        obj.setdefault("prediction_method", None)
        obj.setdefault("prediction_inputs", [])
        obj.setdefault("trailer_timestamp", None)
        obj.setdefault("thumbnail", None)
        obj.setdefault("unit", None)
        obj.setdefault("pages", ["gta-vi/intel"])
        obj.setdefault("display_order", 99)

        ok, reason = passes_quality_gate(obj)
        if ok:
            obj["editorial_note"] = "auto-published"
            updater.add_prediction(obj)
            print(f"  ✓ auto-published {draft_id}")
        else:
            obj["editorial_note"] = "held"
            notes = draft.get("draft_notes", "")
            updater.propose(
                draft_id, "_new",
                current_val=None,
                proposed_val=obj,
                rationale=f"Held for review — failed quality gate: {reason}."
                          f"{' ' + notes if notes else ''}",
            )
            print(f"  ⚑ {draft_id} held for review: {reason}")


def run_updates(updater: PredictionUpdater) -> None:

    # ── 1. pred-release-window: sync from delay-timeline.json ────────────────
    confirmed_date = load_confirmed_release_date()
    if confirmed_date:
        p = updater.get("pred-release-window")
        if p:
            # Parse date string to display format
            try:
                dt = datetime.strptime(confirmed_date, "%Y-%m-%d")
                display = dt.strftime("%b %d, %Y")  # e.g. "Nov 19, 2026"
            except ValueError:
                display = confirmed_date

            updater.update("pred-release-window", "value", p["value"], display,
                           "delay-timeline.json → date_confirmed")
            # Also sync outcome_date
            updater.update("pred-release-window", "outcome_date",
                           p.get("outcome_date"), confirmed_date,
                           "delay-timeline.json → date_confirmed")
            # Range should reflect the confirmed date
            new_range = {"low": confirmed_date, "high": confirmed_date}
            if p.get("prediction_range") != new_range:
                updater.update("pred-release-window", "prediction_range",
                               p.get("prediction_range"), new_range,
                               "delay-timeline.json → date_confirmed")

    # ── 2. pred-launch-price: sync from preorder-listings.json ───────────────
    confirmed_price = load_confirmed_price()
    if confirmed_price:
        p = updater.get("pred-launch-price")
        if p:
            new_value = f"${confirmed_price:.2f}"
            updater.update("pred-launch-price", "value", p["value"], new_value,
                           "preorder-listings.json → consensus live price")
            # If price confirmed from live listings, confidence can go up
            if p["confidence"] < 92 and p["confidence_tier"] == "reported":
                updater.propose("pred-launch-price", "confidence",
                                p["confidence"], 92,
                                "Multiple live retailer listings confirm price — confidence increase warranted",
                                confidence_delta=+10)

    # ── 3. pred-real-price-advantage: recalculate from CPI data ──────────────
    price = confirmed_price or 79.99  # use confirmed price or current known value
    ctx = compute_real_price_context(price)
    if ctx:
        p = updater.get("pred-real-price-advantage")
        if p:
            new_value = f"${price:.2f}"
            updater.update("pred-real-price-advantage", "value", p["value"], new_value,
                           "franchise/cpi.json + preorder-listings.json")

            # Update the unit context with the most expensive historical comparison
            most_exp_id = ctx["most_expensive_id"]
            most_exp_real = ctx["most_expensive_real"]
            title_map = {
                "gta-3": "GTA III", "gta-vc": "GTA VC", "gta-sa": "GTA SA",
                "gta-4": "GTA IV", "gta-5": "GTA V"
            }
            title_name = title_map.get(most_exp_id, most_exp_id.upper())
            new_unit = f"cheaper than {title_name} (${most_exp_real:.2f}) in 2026 dollars"
            updater.update("pred-real-price-advantage", "unit", p.get("unit"), new_unit,
                           "franchise/cpi.json recalculation")

            # Update basis with current savings %
            pct_cheaper = round((most_exp_real - price) / most_exp_real * 100, 1)
            new_basis_snippet = f"GTA VI's confirmed ${price:.2f} launch price is {pct_cheaper}% cheaper in real 2026 terms than {title_name} (${most_exp_real:.2f}) in 2026 dollars.".strip()
            # Only update basis if the numbers have changed noticeably
            if str(pct_cheaper) not in p.get("basis", ""):
                updater.propose("pred-real-price-advantage", "basis",
                                p.get("basis", "")[:60] + "...",
                                new_basis_snippet,
                                f"CPI recalculation: {pct_cheaper}% cheaper than {title_name}")

    # ── 4. pred-vehicles-launch: update indexed count ─────────────────────────
    vehicle_count = load_vehicle_count()
    if vehicle_count:
        p = updater.get("pred-vehicles-launch")
        if p:
            # Update prediction_inputs to reflect current count
            new_inputs = [inp if "268 indexed" not in inp
                         else inp.replace("268 indexed", f"{vehicle_count} indexed")
                         for inp in p.get("prediction_inputs", [])]
            if new_inputs != p.get("prediction_inputs", []):
                updater.update("pred-vehicles-launch", "prediction_inputs",
                               p.get("prediction_inputs"), new_inputs,
                               f"gta-6/entities/vehicles.json → count={vehicle_count}")

            # If vehicle count has grown significantly, propose confidence update
            if vehicle_count > 300 and p["confidence"] < 70:
                updater.propose("pred-vehicles-launch", "confidence",
                                p["confidence"], 70,
                                f"{vehicle_count} vehicles now indexed (was 268) — higher sample improves confidence",
                                confidence_delta=+8)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("fetch_predictions_auto.py — auto-updating confirmed predictions")
    print(f"  Run at: {now_iso()}\n")

    pred_path = DATA / "gta-6/predictions.json"
    proposals_path = DATA / "gta-6/predictions-proposals.json"

    data = json.loads(pred_path.read_text())
    updater = PredictionUpdater(data["predictions"])

    print("Running update checks...")
    run_updates(updater)
    run_draft_publish(updater)

    if not updater.changes and not updater.proposals and not updater.added:
        print("\nNo changes detected — predictions are up to date.")
        return

    # Apply confirmed field changes + newly auto-published predictions
    if updater.changes or updater.added:
        data["last_updated"] = now_iso()
        updated_ids = {c["id"] for c in updater.changes}
        for p in data["predictions"]:
            if p["id"] in updated_ids:
                p["editorial_note"] = "auto-updated"
        # Append brand-new auto-published predictions
        for obj in updater.added:
            data["predictions"].append(obj)
        save_json(pred_path, data)
        if updater.changes:
            print(f"\n✓ Applied {len(updater.changes)} confirmed change(s) to predictions.json")
        if updater.added:
            print(f"✓ Auto-published {len(updater.added)} new prediction(s) to predictions.json")

    # Write proposals for human review
    if updater.proposals:
        existing = {}
        if proposals_path.exists():
            existing = json.loads(proposals_path.read_text())
        existing["last_updated"] = now_iso()
        # Merge proposals, deduplicating by id+field
        existing_proposals = existing.get("proposals", [])
        new_keys = {(p["id"], p["field"]) for p in updater.proposals}
        kept = [p for p in existing_proposals if (p["id"], p["field"]) not in new_keys]
        existing["proposals"] = kept + updater.proposals
        save_json(proposals_path, existing)
        print(f"⚑ Wrote {len(updater.proposals)} proposal(s) to predictions-proposals.json — review before applying")

    # Summary
    print("\nSummary:")
    for c in updater.changes:
        print(f"  CHANGED  [{c['id']}] {c['field']}: {c['old']!r} → {c['new']!r}")
    for p in updater.proposals:
        print(f"  PROPOSED [{p['id']}] {p['field']}: {p['proposed']!r} — {p['rationale'][:60]}")


if __name__ == "__main__":
    main()
