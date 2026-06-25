/**
 * tierStyles.ts — confidence tier styling for card non-badge elements.
 * Used for bar colors, left border accents, and chart bar fills.
 * Badge rendering uses Badge.astro — badgeBg is removed.
 */

export interface TierStyle {
  label:   string;
  /** Tailwind text color class — for bar labels, value text */
  color:   string;
  /** Tailwind bg class — for confidence/earnings bar fill */
  bar:     string;
  /** Tailwind border-left class — for card left accent border */
  border:  string;
}

export const TIER_STYLES: Record<"confirmed" | "reported" | "predicted", TierStyle> = {
  confirmed: {
    label:  "CONFIRMED",
    color:  "text-tier-confirmed",
    bar:    "bg-tier-confirmed",
    border: "border-l-tier-confirmed",
  },
  reported: {
    label:  "REPORTED",
    color:  "text-tier-reported",
    bar:    "bg-tier-reported",
    border: "border-l-tier-reported",
  },
  predicted: {
    label:  "PREDICTED",
    color:  "text-tier-predicted",
    bar:    "bg-tier-predicted",
    border: "border-l-tier-predicted",
  },
};
