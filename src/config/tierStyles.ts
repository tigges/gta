/**
 * tierStyles.ts — single source of truth for confidence tier colours.
 * Used by PredictionCard, IncomePredictionCard, and anywhere confidence
 * tier badges appear. References --c-tier-* tokens from tokens.css.
 */

export interface TierStyle {
  label:   string;
  color:   string;
  bar:     string;
  border:  string;
  badgeBg: string;
}

export const TIER_STYLES: Record<"confirmed" | "reported" | "predicted", TierStyle> = {
  confirmed: {
    label:   "CONFIRMED",
    color:   "text-gta-teal",
    bar:     "bg-gta-teal",
    border:  "border-l-gta-teal",
    badgeBg: "bg-gta-teal/10 border-gta-teal/40 text-gta-teal",
  },
  reported: {
    label:   "REPORTED",
    color:   "text-gta-gold",
    bar:     "bg-gta-gold",
    border:  "border-l-gta-gold",
    badgeBg: "bg-gta-gold/10 border-gta-gold/40 text-gta-gold",
  },
  predicted: {
    label:   "PREDICTED",
    color:   "text-zinc-400",
    bar:     "bg-zinc-500",
    border:  "border-l-zinc-600",
    badgeBg: "bg-zinc-800/50 border-zinc-700/40 text-zinc-400",
  },
};
