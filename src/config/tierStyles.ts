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
    color:  "text-gta-teal",
    bar:    "bg-gta-teal",
    border: "border-l-gta-teal",
  },
  reported: {
    label:  "REPORTED",
    color:  "text-gta-gold",
    bar:    "bg-gta-gold",
    border: "border-l-gta-gold",
  },
  predicted: {
    label:  "PREDICTED",
    color:  "text-zinc-300",
    bar:    "bg-zinc-400",
    border: "border-l-zinc-500",
  },
};
