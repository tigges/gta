/**
 * GTAVI.AI — Category Badge Style
 *
 * Single neutral style for all taxonomy category badges across the site.
 * Colour = data meaning, never taxonomy. Category labels use neutral zinc.
 *
 * --c-badge-text   (#d4d4d8)  near-white — clearly readable label text
 * --c-badge-border (#6b6b7e)  visible without loud — frames the pill
 *
 * The --c-cat-* tokens in tokens.css are preserved for filter button
 * active states, chart legend items, and D3 data series — NOT for static badges.
 */

export const CATEGORY_BADGE_CLASSES =
  "border border-badge-border text-badge-text bg-transparent text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded";

/** Human-readable label for each chart data-category value */
export const CATEGORY_LABEL: Record<string, string> = {
  "Economy-IG":  "IG Economy",
  "Economy-RL":  "RL Economy",
  "Community":   "Community",
  "Performance": "Performance",
  "History":     "History",
  "Promotions":  "Promotions",
};
