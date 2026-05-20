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
  color_schema: ColorSchema;
}

// ── Economy color schema (economy-models.json top-level) ────────────────────

export interface ColorToken {
  border: string;
  text: string;
  hex: string;
}

export interface FlowAnimationToken {
  dir: string;
  duration_s: number;
}

export interface ColorSchema {
  _note?: string;
  sovereign: Record<string, string>;
  node_tokens: Record<string, ColorToken>;
  flow_animation: Record<string, FlowAnimationToken>;
}

// ── Weekly bonuses (weekly-bonuses.json) ────────────────────────────────────

export interface WeeklySale {
  item_id?: string;
  item_name?: string;
  item_description?: string;
  discount_pct: number;
  source_title?: string;
  pub_date?: string;
}

export interface WeeklyBonusEntry {
  activity_id: string;
  multiplier: number;
  keyword_found?: string;
  source_title?: string;
  pub_date?: string;
}

export interface WeeklyBonusesData {
  last_updated: string;
  source: string;
  week_start: string;
  note?: string;
  bonuses: WeeklyBonusEntry[];
  sales?: WeeklySale[];
}

// ── Item catalogue (item-catalogue.json) ────────────────────────────────────

export interface CatalogueItem {
  id: string;
  name: string;
  price: number;
  trade_price?: number | null;
  dlc: string;
  dlc_date?: string;
  dlc_code?: string;
  store: string;
  manufacturer?: string;
  catalogue_type?: string;
}

export interface ItemCatalogueData {
  schema_version: string;
  last_updated: string;
  source: string;
  note?: string;
  item_count: number;
  items: CatalogueItem[];
}

// ── Online heists (online-heists.json) ──────────────────────────────────────

export interface HeistApproach {
  name: string;
  player_max_cut?: number;
  total_take?: number;
  optimal_crew?: Record<string, string>;
  difficulty?: string;
}

export interface HeistLootTier {
  loot: string;
  value: number;
  frequency: string;
}

export interface OnlineHeist {
  id: string;
  title: string;
  dlc: string;
  min_players: number;
  max_players: number;
  solo: boolean;
  prerequisite?: string;
  setup_cost?: number;
  approaches: HeistApproach[];
  loot_tiers?: HeistLootTier[];
  player_cut_per_player?: number;
  avg_run_time_min?: number;
  cooldown_min?: number;
  gta_per_hr?: number;
  difficulty?: string;
  notes?: string;
}

export interface OnlineHeistsData {
  last_updated: string;
  source: string;
  note?: string;
  schema_version?: string;
  heists: OnlineHeist[];
}

// ── Story missions (story-missions.json) ────────────────────────────────────

export interface StoryMission {
  id: string;
  title: string;
  chapter?: number | string;
  protagonist?: string;
  payout: number;
  notes?: string;
  thumbnail?: string;
  stock_mission?: boolean;
}

export interface StoryMissionsData {
  last_updated: string;
  source: string;
  note?: string;
  schema_version?: string;
  missions: StoryMission[];
}

// ── Story heists (heists.json) ───────────────────────────────────────────────

export interface StoryHeistApproach {
  name: string;
  player_max_cut?: number;
  total_take?: number;
  optimal_crew?: Record<string, string>;
}

export interface StoryHeist {
  id: string;
  title: string;
  chapter?: number | string;
  protagonists?: string[];
  approaches: StoryHeistApproach[];
  gold_medal_bonus?: number;
  difficulty?: string;
  replay_value?: string;
  thumbnail?: string;
  notes?: string;
}

export interface StoryHeistsData {
  last_updated?: string;
  source?: string;
  heists: StoryHeist[];
}

// ── Franchise sales (sales.json) ─────────────────────────────────────────────

export interface FranchiseSalesTitle {
  id: string;
  short: string;
  full_title: string;
  year: number;
  launch_units_m?: number | null;
  year1_units_m?: number | null;
  total_units_m: number;
  total_source?: string;
  is_prediction?: boolean;
}

export interface FranchiseSalesData {
  last_updated: string;
  note?: string;
  titles: FranchiseSalesTitle[];
}

// ── Passive stack (passive-stack.json) ──────────────────────────────────────

export interface PassiveStackBusiness {
  id: string;
  name: string;
  color_token: string;
  launched: string;
}

export interface PassiveStackPoint {
  date: string;
  patch?: string;
  passive_gta_per_hr: number;
  businesses?: string[];
}

export interface PassiveStackData {
  schema_version?: string;
  source: string;
  note?: string;
  businesses: PassiveStackBusiness[];
  series: PassiveStackPoint[];
}

// ── Shark cards (shark-cards.json) ───────────────────────────────────────────

export interface SharkCard {
  id: string;
  name: string;
  gta_dollars: number;
  price_usd: number;
  price_gbp?: number;
  gta_per_usd: number;
  notes?: string;
}

export interface SharkCardsData {
  last_updated: string;
  source: string;
  note?: string;
  best_value_card?: string;
  best_gta_per_usd?: number;
  cards: SharkCard[];
}

// ── Per-source history (per-source-history.json) ─────────────────────────────

export interface SourceTimelinePoint {
  date: string;
  patch?: string;
  gta_per_hr: number;
  notes?: string;
}

export interface SourceHistory {
  id: string;
  name: string;
  category: string;
  timeline: SourceTimelinePoint[];
}

export interface PerSourceHistoryData {
  last_updated: string;
  source: string;
  note?: string;
  source_count?: number;
  snapshot_count?: number;
  sources: SourceHistory[];
}

// ── Vehicles performance (performance.json) ──────────────────────────────────

export interface Vehicle {
  name: string;
  class: string;
  tier: string | null;
  lap_time: string | null;
  lap_seconds: number | null;
  top_speed_mph: number | null;
  position_in_class?: number | null;
}

export interface VehiclesData {
  last_updated: string;
  source: string;
  vehicles: Vehicle[];
}

// ── Leonida Intel entities (leonida-intel.json) ───────────────────────────────

export interface LeonidaEntity {
  name: string;
  category: string;
  type?: string;
  href?: string;
  confirmed: boolean;
  confidence_tier?: string;
  url?: string;
}

export interface LeonidaEntityStats {
  total: number;
  confirmed: number;
  indexed: number;
}

export interface LeonidaData {
  last_updated: string;
  source: string;
  total?: number;
  total_entities?: number;
  confirmed?: number;
  by_category?: Record<string, number>;
  entities: LeonidaEntity[];
  entity_stats?: LeonidaEntityStats;
}

// ── Online missions (online-top.json) ────────────────────────────────────────

export interface OnlineMission {
  id: string;
  title: string;
  contact?: string;
  gta_per_hr?: number;
  avg_completion_min?: number;
  payout?: number;
  min_players?: number;
  difficulty?: string;
  notes?: string;
}

export interface OnlineMissionsData {
  last_updated: string;
  source: string;
  note?: string;
  schema_version?: string;
  missions: OnlineMission[];
}

// ── Assassination stocks (assassination-stocks.json) ─────────────────────────

export interface AssassinStep {
  step: number;
  mission_id: string;
  title: string;
  when: string;
  payout_direct?: number;
  protagonist?: string;
  strategy?: string;
  combined_return_pct?: number;
  max_profit_note?: string;
  thumbnail?: string;
}

export interface AssassinStocksData {
  last_updated: string;
  source: string;
  note?: string;
  guide_order: AssassinStep[];
  optimal_sequence_note?: string;
}

// ── Spending distribution (spending-distribution.json) ───────────────────────

export interface SpendingEra {
  era: string;
  date: string;
  label: string;
  vehicles_pct: number;
  properties_pct: number;
  weapons_pct: number;
  [key: string]: string | number;
}

export interface SpendingDistributionData {
  schema_version?: string;
  source: string;
  note?: string;
  confidence?: string;
  categories: { id: string; label: string; color_token: string; note?: string }[];
  eras: SpendingEra[];
}

// ── Savings profile (savings-profile.json) ───────────────────────────────────

export interface SavingsStage {
  stage: number;
  label: string;
  rank_range?: string;
  estimated_balance?: number;
  note?: string;
}

export interface SavingsRatePoint {
  year: number;
  rate: number;
  note?: string;
}

export interface SavingsProfileData {
  schema_version?: string;
  source: string;
  note?: string;
  confidence?: string;
  maze_bank_cap?: number;
  maze_bank_cap_label?: string;
  stages: SavingsStage[];
  savings_rate_history: SavingsRatePoint[];
}

// ── Revenue split (revenue-split.json) ───────────────────────────────────────

export interface RevenueSplitYear {
  fy: string;
  calendar_year: number;
  total_bn: number;
  game_sales_bn: number;
  recurrent_bn: number;
  pct_recurrent: number;
}

export interface RevenueSplitData {
  source: string;
  note?: string;
  years: RevenueSplitYear[];
}

// ── Price basket (price-basket.json) ─────────────────────────────────────────

export interface PriceBasketItem {
  id: string;
  name: string;
  category: string;
  weight: number;
  rationale?: string;
  available_from?: string;
}

export interface PriceBasketEra {
  patch: string;
  date: string;
  [key: string]: string | number;
}

export interface PriceBasketData {
  schema_version?: string;
  source: string;
  note?: string;
  methodology?: string;
  base_period?: string;
  base_label?: string;
  items: PriceBasketItem[];
  era_prices: PriceBasketEra[];
}

// ── Trailer velocity (trailer-velocity.json) ─────────────────────────────────

export interface TrailerVelocitySnapshot {
  fetched_at: string;
  views: number;
  likes?: number;
  comments?: number;
}

export interface TrailerVelocityEntry {
  youtube_id: string;
  title: string;
  published_at?: string;
  fetch_method?: string;
  snapshots: TrailerVelocitySnapshot[];
}

export interface TrailerVelocityData {
  last_updated: string;
  note?: string;
  trailers: TrailerVelocityEntry[];
}

// ── Trailer analysis (trailer-analysis.json) ─────────────────────────────────

export interface TrailerAnalysisEvent {
  t: number;
  type: string;
  entity: string;
  confidence?: string;
  note?: string;
}

export interface TrailerAnalysisEntry {
  id: string;
  youtube_id: string;
  title: string;
  published_at?: string;
  duration_sec: number;
  total_entities?: number;
  events: TrailerAnalysisEvent[];
}

export interface TrailerAnalysisData {
  source?: string;
  note?: string;
  trailers: TrailerAnalysisEntry[];
}

// ── Newswire feed (newswire.json) ─────────────────────────────────────────────

export interface NewswireItem {
  source_id: string;
  source_name: string;
  tier?: string;
  title: string;
  url: string;
  published_at: string;
  summary?: string;
}

export interface NewswireData {
  last_updated: string;
  sources?: unknown[];
  items: NewswireItem[];
}

// ── Reddit feed (reddit.json) ─────────────────────────────────────────────────

export interface RedditPost {
  title: string;
  url: string;
  score?: number;
  comments?: number;
  published_at?: string;
  flair?: string;
}

export interface RedditData {
  last_updated: string;
  source?: string;
  recent_posts?: RedditPost[];
  subscriber_count?: number;
}

// ── Releases (releases.json) ──────────────────────────────────────────────────

export interface ReleaseEntry {
  title: string;
  short: string;
  release_year: number;
  release_date?: string;
  developer?: string;
  publisher?: string;
  platforms?: string[];
  price_usd_launch?: number | null;
  price_usd_estimate?: number | null;
  map_size_km2?: number | null;
  map_size_km2_estimate?: number | null;
  vehicle_count?: number | null;
  vehicle_count_estimate?: number | null;
  gap_years_from_prev?: number | null;
  gap_years_from_prev_estimate?: number | null;
  trailer_youtube_id?: string | null;
  is_prediction?: boolean;
  release_date_estimate?: string | null;
}

export interface ReleasesData {
  last_updated: string;
  source?: string;
  games: ReleaseEntry[];
}




