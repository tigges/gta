/**
 * GTAVI.AI — Runtime Colour Constants  (D3 / JS mirror of tokens.css)
 *
 * This file MIRRORS src/styles/tokens.css for use in D3 charts, inline
 * style props, and any TypeScript/JavaScript runtime code that cannot
 * use CSS classes.
 *
 * ── RULE ─────────────────────────────────────────────────────────────────
 *   When you change a hex value here, update the matching CSS var in
 *   tokens.css and vice-versa. These two files are the only two sources
 *   of colour truth — no third source anywhere in the codebase.
 */

// ── Functional accents (site-wide) ────────────────────────────────────────
export const C_BRAND        = "#f59e0b";   // amber   — franchise authority
export const C_BRAND_BRIGHT = "#fbbf24";   // bright  — hero h1, passive flows
export const C_LIVE         = "#0d9488";   // teal    — confirmed / live
export const C_ALERT        = "#ef4444";   // red     — nerf / danger / regression
export const C_GROWTH       = "#22c55e";   // green   — positive / passive income
export const C_ECONOMY      = "#818cf8";   // indigo  — capital / complexity
export const C_ROCKSTAR     = "#003087";   // Rockstar Social Club brand navy

// ── Title identity (nav dot · section dot · border-left only) ─────────────
export const C_TITLE_VI       = "#ff6b9d";  // GTA VI pink-coral (gradient start)
export const C_TITLE_VI_ALT   = "#ff4060";  // GTA VI pink-coral (gradient end)
export const C_TITLE_ONLINE   = "#00d4e8";  // GTA Online vivid cyan
export const C_TITLE_SA       = "#c0392b";  // GTA SA street red
export const C_TITLE_VC       = "#ff2d78";  // GTA VC neon pink
export const C_TITLE_IV       = "#6b6b7e";  // GTA IV steel-grey — Liberty City, subdued
export const C_TITLE_III      = "#9898b8";  // GTA III muted lavender — 3D era
// GTA V + Franchise → C_BRAND (amber, intentional overlap)
// ── Economy semantic aliases ──────────────────────────────────────────────
export const C_INCOME       = C_LIVE;    // Y-axis income = teal
export const C_EXPENDITURE  = C_BRAND;   // C+I expenditure = gold

// ── Confidence tier constants ────────────────────────────────────────────
export const C_TIER_CONFIRMED = "#34d399";  // emerald-400
export const C_TIER_REPORTED  = C_BRAND;    // gold
export const C_TIER_PREDICTED = "#d4d4d8";  // = C_TEXT_2 — near-white; matches --c-tier-predicted in tokens.css

// ── Play type constants ──────────────────────────────────────────────────
export const C_PLAY_PASSIVE = C_GROWTH;   // green
export const C_PLAY_SEMI    = C_BRAND;    // gold
export const C_PLAY_ACTIVE  = C_ALERT;    // red
export const C_PLAY_HEIST   = C_ECONOMY;  // indigo
export const C_PLAY_MISSION = C_LIVE;     // teal
// GTA IV → C_TITLE_IV (steel-grey, Liberty City)
// GTA III → C_TITLE_III (muted lavender, 3D era)

// ── Surfaces ──────────────────────────────────────────────────────────────
export const C_BG         = "#0e0e11";
export const C_BG_DEEP    = "#0a0a0d";
export const C_CARD       = "#131316";
export const C_CARD_RAISED= "#1a1a1e";

// ── Borders ───────────────────────────────────────────────────────────────
export const C_BORDER_1   = "#1e1e23";
export const C_BORDER_2   = "#2a2a31";

// ── Text (4 readable levels + 1 watermark-only) ───────────────────────────
export const C_TEXT_0     = "#ffffff";   // hero headings, active state
export const C_TEXT_1     = "#ebebef";   // card titles, primary values
export const C_TEXT_2     = "#d4d4d8";   // strong secondary body
export const C_TEXT_3     = "#b8b8c4";   // body text, descriptions
export const C_TEXT_4     = "#9898b8";   // muted labels, nav links
export const C_TEXT_5     = "#b4b4cc";   // section labels
export const C_TEXT_6     = "#6b6b7e";   // source footnotes (minimum)
export const C_TEXT_7     = "#3f3f46";   // SVG watermarks ONLY

// ── Neutral label / badge ─────────────────────────────────────────────────
export const C_BADGE_TEXT   = "#d4d4d8";  // near-white — taxonomy label text
export const C_BADGE_BORDER = "#6b6b7e";  // visible neutral border

// ── Chart / D3 specific ───────────────────────────────────────────────────
export const C_CHART_AXIS    = C_TEXT_5;
export const C_CHART_GRID    = C_BORDER_1;
export const C_CHART_BAR     = C_BRAND;
export const C_CHART_BAR_DIM = "rgba(245,158,11,0.35)";
export const C_CHART_TEAL    = C_LIVE;
export const C_CHART_PURPLE  = "#a78bfa";
export const C_CHART_GREEN   = C_GROWTH;
export const C_CHART_RED     = C_ALERT;
export const C_CHART_INDIGO  = C_ECONOMY;
export const C_WATERMARK     = C_TEXT_7;

// ── Economy diagram flows (CircularEconomy component only) ────────────────
export const C_GTA_DOLLAR     = "#22c55e";  // GTA$ — canonical green HUD money counter colour across all titles; mirrors --c-gta-dollar
export const C_FLOW_INJECTION = "#00d4e8";  // J — exogenous injection (Shark Cards, GTA+); mirrors --c-flow-injection
export const C_FLOW_EXPENSE   = "#f97316";  // Expense (C+I combined) — Level 1 SED; mirrors --c-flow-expense
export const C_FLOW_SPENDING  = "#f97316";  // C — consumption; mirrors --c-flow-spending
export const C_FLOW_PASSIVE   = "#fbbf24";
export const C_FLOW_CAPITAL  = "#a78bfa";
export const C_FLOW_STOCKS   = "#d97706";

// ── Convenience maps ──────────────────────────────────────────────────────

/** Map economy node color_token → hex. Used by CircularEconomy. */
export const NODE_COLOR_MAP: Record<string, string> = {
  amber:  C_BRAND,
  orange: C_FLOW_SPENDING,
  teal:   C_LIVE,
  green:  C_GROWTH,
  purple: C_CHART_PURPLE,
  blue:   C_ECONOMY,
  zinc:   C_TEXT_4,
  gold:   C_BRAND_BRIGHT,
  yellow: C_FLOW_STOCKS,
  red:    C_ALERT,
  indigo: C_BRAND,
};

/** Map era_badge_color → identity hex for per-title contexts. */
export const ERA_IDENTITY_MAP: Record<string, string> = {
  zinc:     C_TEXT_4,
  amber:    C_BRAND,
  red:      C_ALERT,
  green:    C_GROWTH,
  teal:     C_LIVE,
  gold:     C_TITLE_VI,
};

/** Map title_id → identity colour hex. */
export const TITLE_IDENTITY_MAP: Record<string, string> = {
  "gta-1-2":    C_TITLE_III,
  "gta-3":      C_TITLE_III,
  "gta-vc":     C_TITLE_VC,
  "gta-sa":     C_TITLE_SA,
  "gta-4":      C_TITLE_IV,
  "gta-5":      C_BRAND,
  "gta-online": C_TITLE_ONLINE,
  "gta-6":      C_TITLE_VI,
};
