/**
 * GTAVI.AI — D3 Chart Color Bridge
 *
 * Reads CSS variables from tokens.css at runtime so every D3 chart
 * automatically responds to design-token changes without touching chart code.
 *
 * Usage (inside any <script> block that runs in the browser):
 *   import { cc } from "../../assets/chartColors";
 *   rect.attr("fill", cc.bar);
 *
 * All getters call getPropertyValue() lazily so they capture the current
 * computed value at the moment the chart is drawn (after CSS is applied).
 *
 * For server-side / frontmatter colour use, import from src/config/colors.ts.
 */

function cssVar(name: string, fallback: string): string {
  if (typeof document === "undefined") return fallback;
  const val = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return val || fallback;
}

export const cc = {
  // ── Functional accents ────────────────────────────────────
  get bar()     { return cssVar("--c-chart-bar",     "#f59e0b"); }, // amber
  get barDim()  { return cssVar("--c-chart-bar-dim", "rgba(245,158,11,0.35)"); },
  get bright()  { return cssVar("--c-brand-bright",  "#fbbf24"); }, // bright amber
  get teal()    { return cssVar("--c-chart-teal",    "#0d9488"); },
  get green()   { return cssVar("--c-growth",        "#22c55e"); },
  get red()     { return cssVar("--c-alert",         "#ef4444"); },
  get indigo()  { return cssVar("--c-chart-indigo",  "#818cf8"); },
  get purple()  { return cssVar("--c-chart-purple",  "#a78bfa"); },
  get orange()  { return cssVar("--c-flow-spending", "#f97316"); }, // economy flow only
  get brand()   { return cssVar("--c-brand",         "#f59e0b"); },
  get live()    { return cssVar("--c-live",          "#0d9488"); },
  get alert()   { return cssVar("--c-alert",         "#ef4444"); },

  // ── Axis / grid ────────────────────────────────────────────
  get axis()    { return cssVar("--c-chart-axis",    "#b4b4cc"); },
  get grid()    { return cssVar("--c-chart-grid",    "#1e1e23"); },

  // ── Surfaces ───────────────────────────────────────────────
  get bg()         { return cssVar("--c-bg",          "#0e0e11"); },
  get bgDeep()     { return cssVar("--c-bg-deep",     "#0a0a0d"); },
  get card()       { return cssVar("--c-card",        "#131316"); },
  get cardRaised() { return cssVar("--c-card-raised", "#1a1a1e"); },

  // ── Borders ────────────────────────────────────────────────
  get border1() { return cssVar("--c-border-1", "#1e1e23"); }, // = grid
  get border2() { return cssVar("--c-border-2", "#2a2a31"); },

  // ── Text hierarchy ─────────────────────────────────────────
  get text0()   { return cssVar("--c-text-0", "#ffffff"); },
  get text1()   { return cssVar("--c-text-1", "#ebebef"); },
  get text2()   { return cssVar("--c-text-2", "#d4d4d8"); },
  get text3()   { return cssVar("--c-text-3", "#b8b8c4"); },
  get text4()   { return cssVar("--c-text-4", "#9898b8"); }, // muted labels
  get text5()   { return cssVar("--c-text-5", "#b4b4cc"); }, // label floor — minimum for readable text
  // text6 removed — --c-text-6 retired. Use text5 as the minimum readable floor.
  get watermark()   { return cssVar("--c-watermark", "#3f3f46"); }, // SVG watermarks only — never for text

  // ── Category badges ────────────────────────────────────────
  get catFranchise()   { return cssVar("--c-cat-franchise",   "#f59e0b"); },
  get catCommunity()   { return cssVar("--c-cat-community",   "#22c55e"); },
  get catPerformance() { return cssVar("--c-cat-performance", "#ef4444"); },
  get catEconomy()     { return cssVar("--c-cat-economy",     "#818cf8"); },
  get catIntel()       { return cssVar("--c-cat-intel",       "#0d9488"); },

  // ── Title identity (use sparingly — data context only) ─────
  get vi()     { return cssVar("--c-title-vi",     "#ff6b9d"); }, // GTA VI data
  get online() { return cssVar("--c-title-online", "#00d4e8"); }, // GTA Online data
};

/** Convenience: play-type → token color for GTA Online activities */
export const playColor = (type: string): string => {
  const map: Record<string, string> = {
    heist:          cc.indigo,
    passive:        cc.green,
    semi:           cc.bar,
    "semi-passive": cc.bar,
    active:         cc.red,
    mc:             cc.bar,
    ceo:            cc.teal,
    contract:       cc.teal,
    business:       cc.teal,
    smuggling:      cc.teal,
    gunrunning:     cc.bar,
    stack:          cc.green,
    mission:        cc.purple,
  };
  return map[type] ?? cc.text6;
};

/**
 * Element opacity scale — for interactive STATE on whole elements.
 * Use for inactive pills, faded images, disabled controls, unselected covers.
 * NEVER apply to text — use cc.text* colour tokens for text dimming instead.
 * Mirrors --o-* tokens in tokens.css.
 */
export const op = {
  primary:   1.00,  // fully visible — default for all intentional content
  secondary: 0.75,  // present but not dominant — secondary labels, legend swatches
  tertiary:  0.55,  // clearly subordinate — inactive tabs, placeholder states
  muted:     0.35,  // intentionally backgrounded — watermarks, ghost elements
} as const;
