/**
 * GTAVI.AI — D3 Chart Color Bridge (Layer 3)
 *
 * Reads CSS variables from tokens.css at runtime so every D3 chart
 * automatically responds to design-token changes without touching chart code.
 *
 * Usage (inside any <script> block that runs in the browser):
 *   import { cc } from "../assets/chartColors";
 *   rect.attr("fill", cc.bar);
 *
 * All getters call getPropertyValue() lazily so they capture the current
 * computed value at the moment the chart is drawn (after CSS is applied).
 */

function cssVar(name: string, fallback: string): string {
  if (typeof document === "undefined") return fallback;
  const val = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return val || fallback;
}

export const cc = {
  // ── Chart / D3 internals ───────────────────────────────────
  get axis()    { return cssVar("--c-chart-axis",    "#b4b4cc"); },
  get grid()    { return cssVar("--c-chart-grid",    "#1e1e23"); },
  get bar()     { return cssVar("--c-chart-bar",     "#f59e0b"); },
  get barDim()  { return cssVar("--c-chart-bar-dim", "rgba(245,158,11,0.35)"); },
  get teal()    { return cssVar("--c-chart-teal",    "#0d9488"); },
  get purple()  { return cssVar("--c-chart-purple",  "#a78bfa"); },
  get green()   { return cssVar("--c-chart-green",   "#22c55e"); },
  get red()     { return cssVar("--c-chart-red",     "#ef4444"); },
  get indigo()  { return cssVar("--c-chart-indigo",  "#818cf8"); },

  // ── Surface / border ──────────────────────────────────────
  get bg()      { return cssVar("--c-bg",            "#0e0e11"); },
  get card()    { return cssVar("--c-card",          "#131316"); },
  get border1() { return cssVar("--c-border-1",      "#1e1e23"); },
  get border2() { return cssVar("--c-border-2",      "#2a2a31"); },

  // ── Text hierarchy ────────────────────────────────────────
  get text0()   { return cssVar("--c-text-0",        "#ffffff"); },
  get text1()   { return cssVar("--c-text-1",        "#ebebef"); },
  get text2()   { return cssVar("--c-text-2",        "#d4d4d8"); },
  get text3()   { return cssVar("--c-text-3",        "#b8b8c4"); },
  get text4()   { return cssVar("--c-text-4",        "#9898b8"); },
  get text5()   { return cssVar("--c-text-5",        "#b4b4cc"); },
  get text6()   { return cssVar("--c-text-6",        "#3f3f46"); },
  get text7()   { return cssVar("--c-text-7",        "#27272a"); },

  // ── Brand ─────────────────────────────────────────────────
  get brand()   { return cssVar("--c-brand",         "#f59e0b"); },
  get live()    { return cssVar("--c-live",          "#0d9488"); },
  get alert()   { return cssVar("--c-alert",         "#ef4444"); },

  // ── Category badges ───────────────────────────────────────
  get catFranchise()   { return cssVar("--c-cat-franchise",   "#f59e0b"); },
  get catCommunity()   { return cssVar("--c-cat-community",   "#22c55e"); },
  get catPerformance() { return cssVar("--c-cat-performance", "#ef4444"); },
  get catEconomy()     { return cssVar("--c-cat-economy",     "#818cf8"); },
  get catIntel()       { return cssVar("--c-cat-intel",       "#0d9488"); },
};

/** Convenience: play-type → token color for GTA Online activities */
export const playColor = (type: string): string => {
  const map: Record<string, string> = {
    heist:         cc.indigo,
    passive:       cc.green,
    semi:          cc.bar,
    "semi-passive":cc.bar,
    active:        cc.red,
    mc:            cc.bar,
    ceo:           cc.teal,
    contract:      cc.teal,
    business:      cc.teal,
    smuggling:     cc.teal,
    gunrunning:    cc.bar,
    stack:         cc.green,
    mission:       cc.purple,
  };
  return map[type] ?? cc.text6;
};
