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
    color:   "text-emerald-300",
    bar:     "bg-emerald-400",
    border:  "border-l-gta-teal",
    badgeBg: "bg-emerald-900/20 border-emerald-500/60 text-emerald-200",
  },
  reported: {
    label:   "REPORTED",
    color:   "text-amber-300",
    bar:     "bg-amber-400",
    border:  "border-l-gta-gold",
    badgeBg: "bg-amber-900/20 border-amber-500/60 text-amber-200",
  },
  predicted: {
    label:   "PREDICTED",
    color:   "text-zinc-200",
    bar:     "bg-zinc-400",
    border:  "border-l-zinc-500",
    badgeBg: "bg-zinc-700/30 border-zinc-400/50 text-zinc-100",
  },
};
