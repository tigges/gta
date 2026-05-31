/**
 * predictions.ts — single source of truth for GTA VI predictions.
 *
 * Loads the curated predictions.json, but for the handful of predictions whose
 * headline value mirrors a canonical franchise fact (price, map size, vehicle
 * count), it DERIVES `value` at build time from data/shared/releases.json — the
 * same file the homepage franchise comparison reads. This guarantees the two
 * can never drift (the bug where the table said ~1,000 vehicles and the
 * prediction said ~700).
 *
 * Only the headline `value` is derived. Curated prose (`basis`), model ranges
 * (`prediction_range`), and every non-numeric prediction stay hand-authored.
 *
 * To change one of these facts, edit it once in releases.json — the franchise
 * table and the prediction both update from it.
 *
 * Consumers should import from here instead of the raw JSON:
 *   import predictionsData from "../config/predictions";
 */
import predictionsRaw from "../../data/gta-6/predictions.json";
import releasesRaw    from "../../data/shared/releases.json";
import type { PredictionsData, Prediction } from "../types/gta";

// ── Canonical GTA VI release record (from releases.json) ─────────────────────
const games: any[] = (releasesRaw as any).games ?? [];
const viRelease: any =
  games.find((g) => g.short === "GTA VI" || /Grand Theft Auto VI/i.test(g.title ?? "")) ?? {};

// ── Derivations: prediction id → headline value computed from canonical fact ──
// Returns null when the source field is absent, leaving the curated value intact.
const DERIVED: Record<string, (vi: any) => string | null> = {
  "pred-launch-price": (vi) =>
    vi.price_usd_estimate != null ? `$${Number(vi.price_usd_estimate).toFixed(2)}` : null,
  "pred-map-size": (vi) =>
    vi.map_size_km2_estimate != null ? `~${vi.map_size_km2_estimate}` : null,
  "pred-vehicles-launch": (vi) =>
    vi.vehicle_count_estimate != null
      ? `~${Number(vi.vehicle_count_estimate).toLocaleString("en-US")}`
      : null,
};

const raw = predictionsRaw as unknown as PredictionsData;

const predictions: Prediction[] = raw.predictions.map((p) => {
  const derived = DERIVED[p.id]?.(viRelease);
  return derived != null ? { ...p, value: derived } : p;
});

const predictionsData: PredictionsData = { ...raw, predictions };

// ── Prediction / poll mixing ─────────────────────────────────────────────────
// A poll is a prediction that carries a `poll_question`. To show a unified feed
// that mixes the two presentations without ever duplicating an id, we render
// most items as predictions and promote one poll-eligible item to a poll after
// every `pollGap` predictions (default 3 → a ~3:1 prediction:poll blend).
export interface FeedItem {
  prediction: Prediction;
  mode: "prediction" | "poll";
}

export function feedWithPolls(list: Prediction[], pollGap = 3): FeedItem[] {
  const out: FeedItem[] = [];
  let sincePoll = 0;
  for (const p of list) {
    const eligible = Boolean((p as any).poll_question);
    if (eligible && sincePoll >= pollGap) {
      out.push({ prediction: p, mode: "poll" });
      sincePoll = 0;
    } else {
      out.push({ prediction: p, mode: "prediction" });
      sincePoll++;
    }
  }
  return out;
}

export { predictions };
export default predictionsData;
