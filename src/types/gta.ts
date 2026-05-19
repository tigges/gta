// Shared TypeScript types for GTA data models

export interface Trailer {
  youtube_id: string;
  title: string;
  published_at: string | null;
  source_url: string;
}

export interface TrailersData {
  last_updated: string;
  source: string;
  trailers: Trailer[];
}

export interface PredictionRange {
  low: string;
  high: string;
}

export interface Prediction {
  id: string;
  title: string;
  value: string;
  unit: string | null;
  confidence: number;
  confidence_tier: "confirmed" | "reported" | "predicted";
  basis: string;
  trailer_timestamp: string | null;
  prediction_method: string | null;
  prediction_inputs: string[];
  prediction_range: PredictionRange | null;
  outcome_verified: boolean;
  outcome_actual: string | null;
  outcome_date: string | null;
  source: string;
  source_type: "official" | "reported" | "predicted";
}

export interface PredictionsData {
  last_updated: string;
  note: string;
  schema_version: string;
  predictions: Prediction[];
}

// ── Business / Income types ─────────────────────────────────────────────────

export interface PatchHistoryEntry {
  date: string;
  patch: string;
  change: string;
  net_profit_per_hr_after: number;
}

export interface Business {
  id: string;
  name: string;
  category: string;
  play_type: "active" | "passive" | "mixed";
  min_players: number;
  solo: boolean;
  dlc: string;
  prerequisite: string;
  setup_cost_min: number;
  setup_cost_full: number;
  setup_cost_notes: string;
  gross_profit_per_hr: number;
  resupply_cost_per_hr: number;
  net_profit_per_hr: number;
  net_profit_per_hr_notes: string;
  break_even_hrs: number;
  payout_per_run_min: number;
  payout_per_run_max: number;
  avg_run_time_min: number;
  risk: "low" | "medium" | "high";
  last_nerfed: string | null;
  last_nerfed_notes: string | null;
  patch_history: PatchHistoryEntry[];
  tips: string[];
  notes: string;
  loot_tiers?: { loot: string; value: number; frequency: string }[];
  thumbnail?: string;
}

export interface BusinessProfiles {
  last_updated: string;
  source: string;
  businesses: Business[];
}

// ── Revenue tiers ───────────────────────────────────────────────────────────

export interface TierSource {
  id: string;
  name: string;
  gta_per_hr: number;
  type: string;
  solo: boolean;
  setup_gta: number;
  note: string;
}

export interface RevenueTier {
  tier: string;
  label: string;
  color: string;
  sources: TierSource[];
}

export interface RevenueTiersData {
  last_updated: string;
  source: string;
  note: string;
  tiers: RevenueTier[];
  optimal_starter_path: string[];
}

// ── GTA-PPI / meta-history ──────────────────────────────────────────────────

export interface PpiDataPoint {
  date: string;
  patch: string;
  gta_cpi: number;
  real_cpi: number;
  ppi_ratio: number;
  notes: string;
}

export interface GtaPpiData {
  last_updated: string;
  source: string;
  series: PpiDataPoint[];
}

export interface MetaHistoryEntry {
  patch: string;
  date: string;
  top_method: string;
  top_gta_per_hr: number;
  notes: string;
}

export interface MetaHistoryData {
  last_updated: string;
  source: string;
  note: string;
  meta_history: MetaHistoryEntry[];
}

// ── Weekly bonuses ──────────────────────────────────────────────────────────

export interface WeeklyBonus {
  activity_id: string;
  activity_name: string;
  multiplier: number;
  week_start: string;
  week_end: string;
  source: string;
}

export interface WeeklyBonusesData {
  last_updated: string;
  source: string;
  bonuses: WeeklyBonus[];
}

// ── Sale frequency ──────────────────────────────────────────────────────────

export interface ActivityBonusFreq {
  activity_id: string;
  activity_name: string;
  bonus_count: number;
  last_bonus_date: string | null;
  avg_weeks_between: number | null;
}

export interface SaleFrequencyData {
  last_updated: string;
  source: string;
  activity_bonuses: ActivityBonusFreq[];
}

// ── GTA VI entities ─────────────────────────────────────────────────────────

export interface Gta6EntityEntry {
  id: string;
  name: string;
  type: string;
  confidence: "confirmed" | "reported" | "indexed";
  source: string;
  description?: string;
  image_url?: string;
}

export interface EntityIndex {
  last_updated: string;
  source: string;
  total: number;
  by_type: Record<string, number>;
  by_confidence: Record<string, number>;
  entities: Gta6EntityEntry[];
}

// ── Features tracker ────────────────────────────────────────────────────────

export interface FeatureCategory {
  id: string;
  label: string;
  icon: string;
  confirmed: number;
  reported: number;
  indexed: number;
  target: number;
  confidence_pct: number;
  notes: string;
  source: string;
}

export interface FeaturesData {
  last_updated: string;
  source: string;
  categories: FeatureCategory[];
}


// ── Economy model types ─────────────────────────────────────────────────────

export type FlowType = "wages" | "spending" | "passive" | "investment" | "capital-return" | "injection" | "savings";
export type SovereignType = "fixed-release" | "narrative-first" | "mixed" | "live-mmt" | "projected-mmt";
export type CircularFlowLevel = "none" | "one-way" | "proto" | "partial" | "partial-4" | "full" | "full+regional";
export type LayoutTemplate = "one-way" | "proto" | "loop" | "multi-stream" | "full-mmt" | "dual-territory";

export interface EconomyNode {
  id: string;
  label: string;
  type: "sovereign" | "player" | "income" | "asset" | "capital" | "savings" | "injection" | "destination" | "region" | "bridge";
  detail: string;
  color_token: string;
  projected: boolean;
  data_source: string | null;
}

export interface EconomyFlow {
  id: string;
  from: string;
  to: string;
  label: string;
  type: FlowType;
  bidirectional: boolean;
  active: boolean;
  projected: boolean;
  color_token: string;
  chart_link: string | null;
}

export interface EconomyDimensions {
  circular_flow: CircularFlowLevel;
  capital_market: string;
  passive_income: string | false;
  inflation: string | false;
  sovereign_type: SovereignType;
}

export interface EconomyDimensionScores {
  circular_flow: number;    // 0–4
  capital_market: number;   // 0–4
  passive_income: number;   // 0–4
  inflation: number;        // 0–4
  sovereign_complexity: number; // 0–4
}

export interface EconomyModel {
  title_id: string;
  title_name: string;
  short: string;
  year: string;
  era: number;
  era_label: string;
  era_badge_color: string;
  economy_type: string;
  real_world_analogue: string;
  key_innovation: string | null;
  key_innovation_note: string;
  innovation_stars: number;
  complexity_score: number;
  layout_template: LayoutTemplate;
  dimensions: EconomyDimensions;
  dimension_scores: EconomyDimensionScores;
  projected: boolean;
  regression_era: boolean;
  regression_note?: string;
  nodes: EconomyNode[];
  flows: EconomyFlow[];
  inflation_channels: string[];
  sovereign_levers: string[];
  data_coverage: Record<string, { file: string; status: "live" | "static" | "stub" | "none" }>;
  gta_vi_lineage: string;
  summary: string;
}

export interface EconomyModelsData {
  schema_version: string;
  last_updated: string;
  note: string;
  economies: EconomyModel[];
  franchise_arc_summary: string;
  complexity_chart_note: string;
  layout_templates: Record<string, string>;
  flow_color_map: Record<string, string>;
}
