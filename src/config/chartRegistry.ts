/**
 * chartRegistry.ts
 * Maps chart IDs (from chart-config.json) to their Astro components.
 * Import this in any page to get dynamic component rendering from config.
 *
 * Usage:
 *   import { CHART_REGISTRY } from "../config/chartRegistry";
 *   import chartConfig from "../../data/config/chart-config.json";
 *   const featured = chartConfig.gta_vi.featured.map(id => CHART_REGISTRY[id]);
 */

// ── GTA VI charts ─────────────────────────────────────────────────────────
import ChartTrailerVelocity      from "../components/charts/ChartTrailerVelocity.astro";
import ChartTrailerDiscovery     from "../components/charts/ChartTrailerDiscovery.astro";
import ChartDelayTimeline        from "../components/charts/ChartDelayTimeline.astro";
import ChartRegionHeatmap        from "../components/charts/ChartRegionHeatmap.astro";
import ChartCommunity            from "../components/charts/ChartCommunity.astro";
import ChartPrelaunchComparison  from "../components/charts/ChartPrelaunchComparison.astro";
import ChartEntertainmentComp    from "../components/charts/ChartEntertainmentComp.astro";

// ── GTA Online economy charts ─────────────────────────────────────────────
import ChartIncomeLeaderboard    from "../components/charts/ChartIncomeLeaderboard.astro";
import ChartMetaEvolution        from "../components/charts/ChartMetaEvolution.astro";
import ChartGtaPpi               from "../components/charts/ChartGtaPpi.astro";
import ChartPassiveStack         from "../components/charts/ChartPassiveStack.astro";
import ChartRoiScatter           from "../components/charts/ChartRoiScatter.astro";
import ChartSharkCard            from "../components/charts/ChartSharkCard.astro";
import ChartHeistComparison      from "../components/charts/ChartHeistComparison.astro";
import ChartIncomeHistory        from "../components/charts/ChartIncomeHistory.astro";
import ChartVehicleTco           from "../components/charts/ChartVehicleTco.astro";
import ChartPropertyCost         from "../components/charts/ChartPropertyCost.astro";
import ChartPropertyDailyFee     from "../components/charts/ChartPropertyDailyFee.astro";
import ChartSpendingDistribution from "../components/charts/ChartSpendingDistribution.astro";
import ChartPriceHistory         from "../components/charts/ChartPriceHistory.astro";
import ChartBonusHeatmap         from "../components/charts/ChartBonusHeatmap.astro";
import ChartIeTiers              from "../components/charts/ChartIeTiers.astro";

// ── GTA V charts ──────────────────────────────────────────────────────────
import ChartAssassinationReturns from "../components/charts/ChartAssassinationReturns.astro";
import ChartDlcPlayerHistory     from "../components/charts/ChartDlcPlayerHistory.astro";
import ChartVehiclePerformance   from "../components/charts/ChartVehiclePerformance.astro";
import ChartMissionEarnings      from "../components/charts/ChartMissionEarnings.astro";
import PlayerChart               from "../components/PlayerChart.astro";
import TrendsChart               from "../components/TrendsChart.astro";

// ── Franchise charts ──────────────────────────────────────────────────────
import ChartFranchiseSales       from "../components/charts/ChartFranchiseSales.astro";
import ChartCpiPricing           from "../components/charts/ChartCpiPricing.astro";
import ChartCriticDivergence     from "../components/charts/ChartCriticDivergence.astro";
import ChartDlcCadence           from "../components/charts/ChartDlcCadence.astro";
import ChartRevenueSplit         from "../components/charts/ChartRevenueSplit.astro";
import ChartTtwoStock            from "../components/charts/ChartTtwoStock.astro";
import ChartCompetitors          from "../components/charts/ChartCompetitors.astro";
import ChartFranchiseComplexity  from "../components/charts/ChartFranchiseComplexity.astro";
import ChartFranchiseEarnings    from "../components/charts/ChartFranchiseEarnings.astro";

// ── Registry ──────────────────────────────────────────────────────────────
export const CHART_REGISTRY: Record<string, any> = {
  // GTA VI
  "trailer-velocity":           ChartTrailerVelocity,
  "trailer-discovery-chart":    ChartTrailerDiscovery,
  "delay-timeline-chart":       ChartDelayTimeline,
  "region-heatmap":             ChartRegionHeatmap,
  "community-chart":            ChartCommunity,
  "prelaunch-comparison-chart": ChartPrelaunchComparison,
  "entertainment-chart":        ChartEntertainmentComp,

  // GTA Online
  "income-leaderboard-chart":     ChartIncomeLeaderboard,
  "meta-evolution-chart":         ChartMetaEvolution,
  "gta-ppi-chart":                ChartGtaPpi,
  "passive-stack-chart":          ChartPassiveStack,
  "roi-scatter-chart":            ChartRoiScatter,
  "shark-card-chart":             ChartSharkCard,
  "heist-comparison-chart":       ChartHeistComparison,
  "income-history-chart":         ChartIncomeHistory,
  "vehicle-tco-chart":            ChartVehicleTco,
  "property-cost-chart":          ChartPropertyCost,
  "property-daily-fee-chart":     ChartPropertyDailyFee,
  "spending-distribution-chart":  ChartSpendingDistribution,
  "price-history-chart":          ChartPriceHistory,
  "bonus-heatmap":                ChartBonusHeatmap,
  "ie-tiers-chart":               ChartIeTiers,

  // GTA V
  "assassination-returns-chart":  ChartAssassinationReturns,
  "dlc-player-chart":             ChartDlcPlayerHistory,
  "perf-chart":                   ChartVehiclePerformance,
  "mission-earnings-chart":       ChartMissionEarnings,
  "player-chart":                 PlayerChart,
  "trends-chart":                 TrendsChart,

  // Franchise
  "sales-chart":                  ChartFranchiseSales,
  "cpi-chart":                    ChartCpiPricing,
  "divergence-chart":             ChartCriticDivergence,
  "dlc-cadence-chart":            ChartDlcCadence,
  "revenue-split-chart":          ChartRevenueSplit,
  "ttwo-stock-chart":             ChartTtwoStock,
  "competitors-chart":            ChartCompetitors,
  "franchise-complexity-chart":   ChartFranchiseComplexity,
  "franchise-earnings-chart":     ChartFranchiseEarnings,
};
