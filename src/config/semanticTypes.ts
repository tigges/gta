/**
 * semanticTypes.ts — Central registry for all semantic type definitions.
 *
 * SINGLE SOURCE OF TRUTH for:
 *   Cluster A: game title identities    (feeds Badge surface=opaque, FilterPill)
 *   Cluster B: confidence/intel tiers  (feeds Badge, FilterPill)
 *   Cluster C: play / activity types   (feeds Badge, ColorLabel)
 *   Cluster D: geographic regions      (feeds Badge, ColorLabel)
 *
 * RULE: Every color is a CSS custom property token — never a raw hex.
 *
 * Rendering primitives:
 *   Badge       — bordered pill, informational, three surfaces (tint/opaque/ghost)
 *   FilterPill  — bordered pill, interactive (inactive/active/hover states)
 *   ColorLabel  — text-only colored inline label, no border or background
 *
 * pillStyle(token, surface) returns the full coordinated style string.
 * Note: position on card is NOT defined here — that is the card's concern.
 */

export interface SemanticType {
  id:          string;
  label:       string;
  colorToken:  string;  // CSS var reference — e.g. "var(--c-title-vi)"
  icon?:       string;  // optional emoji/symbol
}

// ── Utility: generate consistent inline style strings ─────────────────────────

export type BadgeSurface = "tint" | "opaque" | "ghost";

/**
 * Returns a coordinated inline style string for color + border + background.
 *
 * tint   — coloured tint wash. Default. Used in header rows, hero strips, card body.
 * opaque — dark fixed bg (#0a0a0d) with coloured ring. Used over thumbnails/images.
 * ghost  — transparent bg, white-tint border. Used over complex/varied image surfaces.
 */
export function pillStyle(colorToken: string, surface: BadgeSurface = "tint"): string {
  if (surface === "opaque") {
    return [
      `color:${colorToken}`,
      `border-color:${colorToken}55`,
      `background:rgba(10,10,13,0.88)`,
    ].join(";");
  }
  if (surface === "ghost") {
    return [
      `color:${colorToken}`,
      `border-color:rgba(255,255,255,0.2)`,
      `background:transparent`,
    ].join(";");
  }
  // tint (default)
  return [
    `color:${colorToken}`,
    `border-color:color-mix(in srgb,${colorToken} 40%,transparent)`,
    `background:color-mix(in srgb,${colorToken} 12%,transparent)`,
  ].join(";");
}

/** Inactive FilterPill — neutral, no color emphasis */
export const FILTER_INACTIVE_STYLE =
  "color:var(--c-text-5);border-color:var(--c-border-2);background:transparent";

/** Hover style for inactive FilterPill buttons */
export const FILTER_HOVER_STYLE =
  "color:var(--c-text-2);border-color:var(--c-text-5);background:transparent";

// ── Cluster A: Game title identities ─────────────────────────────────────────

export const GAME_TYPES: SemanticType[] = [
  { id: "gta-vi",      label: "GTA VI",      colorToken: "var(--c-title-vi)"          },
  { id: "gta-online",  label: "GTA Online",  colorToken: "var(--c-title-online)"      },
  { id: "gta-v",       label: "GTA V",       colorToken: "var(--c-title-v)"           },
  { id: "franchise",   label: "Franchise",   colorToken: "var(--c-brand)"             },
  { id: "gta-sa",      label: "GTA SA",      colorToken: "var(--c-title-sa)"          },
  { id: "gta-vc",      label: "GTA VC",      colorToken: "var(--c-title-vc)"          },
  { id: "gta-iv",      label: "GTA IV",      colorToken: "var(--c-title-iv)"          },
  { id: "gta-iii",     label: "GTA III",     colorToken: "var(--c-title-iii)"         },
  // Filter-only aliases
  { id: "all",         label: "All",         colorToken: "var(--c-text-4)"            },
  { id: "gta-6",       label: "GTA VI",      colorToken: "var(--c-title-vi)"          },
  { id: "gta-5",       label: "GTA V",       colorToken: "var(--c-title-v)"           },
];

export const GAME_TYPE_MAP: Record<string, SemanticType> = Object.fromEntries(
  GAME_TYPES.map(t => [t.id, t])
);

export function getGameType(id: string): SemanticType {
  return GAME_TYPE_MAP[id] ?? { id, label: id, colorToken: "var(--c-text-4)" };
}

// ── Cluster B: Confidence / intelligence tiers ────────────────────────────────
// Keys: confirmed | reported | predicted
// "indexed" (DB entities) is an alias for "predicted" — same visual treatment.

export const CONFIDENCE_TYPES: SemanticType[] = [
  { id: "confirmed",  label: "Confirmed",  colorToken: "var(--c-tier-confirmed)" },
  { id: "reported",   label: "Reported",   colorToken: "var(--c-tier-reported)"  },
  { id: "predicted",  label: "Predicted",  colorToken: "var(--c-tier-predicted)" },
  { id: "indexed",    label: "Indexed",    colorToken: "var(--c-text-5)" },
];

export const CONFIDENCE_TYPE_MAP: Record<string, SemanticType> = Object.fromEntries(
  CONFIDENCE_TYPES.map(t => [t.id, t])
);

export function getConfidenceType(id: string): SemanticType {
  // "indexed" aliases to "predicted" visual treatment
  const key = id === "indexed" ? "predicted" : id;
  return CONFIDENCE_TYPE_MAP[key] ?? CONFIDENCE_TYPE_MAP["predicted"]!;
}

// ── Cluster C: Play / activity types ─────────────────────────────────────────
// Rendered as colored dot + inline text — NOT as a pill.
// Same tokens also used in D3 charts via chartColors.ts playColor().

export const PLAY_TYPES: SemanticType[] = [
  { id: "passive",       label: "Passive",       colorToken: "var(--c-play-passive)",  icon: "◉" },
  { id: "active",        label: "Active",         colorToken: "var(--c-play-active)",   icon: "◉" },
  { id: "semi-passive",  label: "Semi-passive",   colorToken: "var(--c-play-semi)",     icon: "◉" },
  { id: "hybrid",        label: "Hybrid",         colorToken: "var(--c-play-semi)",     icon: "◉" },
  { id: "heist",         label: "Heist",          colorToken: "var(--c-play-heist)",    icon: "◉" },
  { id: "mission",       label: "Mission",        colorToken: "var(--c-play-mission)",  icon: "◉" },
  { id: "mc",            label: "MC Business",    colorToken: "var(--c-play-semi)",     icon: "◉" },
  { id: "ceo",           label: "CEO/VIP",        colorToken: "var(--c-live)",          icon: "◉" },
  { id: "contract",      label: "Contract",       colorToken: "var(--c-live)",          icon: "◉" },
  { id: "business",      label: "Business",       colorToken: "var(--c-live)",          icon: "◉" },
];

export const PLAY_TYPE_MAP: Record<string, SemanticType> = Object.fromEntries(
  PLAY_TYPES.map(t => [t.id, t])
);

export function getPlayType(id: string): SemanticType {
  return PLAY_TYPE_MAP[id] ?? { id, label: id, colorToken: "var(--c-text-4)" };
}

/** Convenience: returns just the color token for a play type (D3/runtime use) */
export function playTypeColor(id: string): string {
  return getPlayType(id).colorToken;
}

// ── Cluster D: Geographic regions  (GTA VI) ──────────────────────────────────
// Rendered as a subtle location indicator — NOT as a pill.

export const REGION_TYPES: SemanticType[] = [
  { id: "vice-city", label: "Vice City",    colorToken: "var(--c-title-vi,#ff6b9d)",   icon: "🏙" },
  { id: "leonida",   label: "Leonida",      colorToken: "var(--c-growth,#22c55e)",     icon: "🌿" },
  { id: "both",      label: "VC + Leonida", colorToken: "var(--c-text-4,#9898b8)",     icon: "●"  },
];

export const REGION_TYPE_MAP: Record<string, SemanticType> = Object.fromEntries(
  REGION_TYPES.map(t => [t.id, t])
);

export function getRegionType(id: string): SemanticType {
  return REGION_TYPE_MAP[id] ?? { id, label: id, colorToken: "var(--c-text-4)" };
}

/** Derive region from a mission name using keyword heuristics */
export function regionFromName(name: string): SemanticType {
  const n = name.toLowerCase();
  if (n.includes("vice city") || n.includes("ocean") || n.includes("casino")
   || n.includes("liquor")    || n.includes("roller") || n.includes("wheels")
   || n.includes("connections")|| n.includes("collection") || n.includes("race"))
    return getRegionType("vice-city");
  if (n.includes("leonida")   || n.includes("swamp")  || n.includes("fishing")
   || n.includes("tourist")   || n.includes("grassriver") || n.includes("keys")
   || n.includes("kalaga")    || n.includes("gator")   || n.includes("bayou"))
    return getRegionType("leonida");
  return getRegionType("both");
}
