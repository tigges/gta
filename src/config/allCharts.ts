/**
 * allCharts.ts — GTAVI.AI Unified Chart Registry
 *
 * Single source of truth for every chart on the site.
 * All metadata (game, category, label, badge, sources, shareText) lives here.
 *
 * Phase 1: Registry defined. chartRegistry.ts re-exports CHART_REGISTRY from here.
 * Phase 2: ChartSection.astro reads ChartMeta to auto-generate section headers.
 * Phase 3: Hub pages derive featured/preview slots from CHARTS_PAGE_ORDER / HUB_CONFIG.
 * Phase 4: CardFooter reads sources/shareText from this registry by chartId.
 * Phase 5: Eco charts gain pages: ["charts"] — appear in the full /charts catalogue.
 *
 * ADDING A CHART:
 *   1. Write the chart component in src/components/charts/
 *   2. Import it here
 *   3. Add a ChartMeta entry to ALL_CHARTS
 *   4. Add the id to CHARTS_PAGE_ORDER (if it appears on /charts)
 *   5. Add the id to HUB_CONFIG featured/preview (if it appears on a hub page)
 *   That's it — headers, footers, anchors, share, and filter are automatic.
 */

// ── Types ─────────────────────────────────────────────────────────────────────

export type GameId   = "gta-vi" | "gta-online" | "gta-v" | "franchise";
export type Category = "Economy-IG" | "Economy-RL" | "Community" | "History" | "Performance" | "Promotions";

/**
 * Pages a chart can appear on.
 * "charts"            = /charts full catalogue
 * "gta-vi"            = /gta-vi hub featured/preview slot
 * "gta-online"        = /gta-online hub featured/preview slot
 * "gta-v"             = /gta-v hub (directly rendered or via registry slot)
 * "gta-online/economy"= /gta-online/economy deep-dive page
 */
export type PageSlug = "charts" | "gta-vi" | "gta-online" | "gta-v" | "gta-online/economy";

export interface ChartMeta {
  /** Canonical ID — section anchor is id="section-{id}" */
  id: string;

  /** Astro component reference */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  component: any;

  /** GTA title this chart belongs to */
  game: GameId;

  /** Data category — drives the filter system on /charts */
  category: Category;

  /** Human-readable badge label rendered in the section header */
  badge: string;

  /** Section label rendered after // in the header */
  label: string;

  /**
   * Right-aligned metadata string in the section header.
   *   null  = no right-side element (either not needed, or dynamic —
   *           dynamic values are passed as a prop override in ChartSection in Phase 2)
   *   string = rendered as static text
   */
  meta: string | null;

  /** Source citation rendered in CardFooter */
  sources: string;

  /** Pre-written share copy for ShareDropdown */
  shareText: string;

  /** Pages this chart appears on */
  pages: PageSlug[];

  /**
   * For eco-page variants that overlap with a main chart.
   * Points to the canonical chart ID this one is a narrative variant of.
   */
  relatedId?: string;

  /**
   * Editorial promotion weight (default 0).
   * Used to bubble charts to the top of discovery surfaces (hub page teasers,
   * homepage, future demand-ordered /charts).
   *   0    = standard order (CHARTS_PAGE_ORDER or demand score)
   *   50   = newly published — gets a visibility boost for ~30 days
   *   100  = actively promoted by editorial decision
   * When Plausible demand scores are added (Stream 3 Phase B), final sort =
   *   weight + demandScore descending within each title group.
   */
  weight?: number;
}

// ── Chart component imports ────────────────────────────────────────────────────

// GTA VI
import ChartTrailerVelocity      from "../components/charts/ChartTrailerVelocity.astro";
import ChartGta6SearchTrends   from "../components/charts/ChartGta6SearchTrends.astro";
import ChartTrailerDiscovery     from "../components/charts/ChartTrailerDiscovery.astro";
import ChartExtendedLookTimeline from "../components/charts/ChartExtendedLookTimeline.astro";
import ChartDelayTimeline        from "../components/charts/ChartDelayTimeline.astro";
import ChartRegionHeatmap        from "../components/charts/ChartRegionHeatmap.astro";
import ChartCommunity            from "../components/charts/ChartCommunity.astro";
import ChartPrelaunchComparison  from "../components/charts/ChartPrelaunchComparison.astro";
import ChartEntertainmentComp    from "../components/charts/ChartEntertainmentComp.astro";
import ChartCompetitors          from "../components/charts/ChartCompetitors.astro";

// GTA Online — main charts
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

// GTA Online — economy deep-dive variants (first-class charts, pages: ["gta-online/economy"])
import ChartEcoWages             from "../components/charts/ChartEcoWages.astro";
import ChartEcoPpi               from "../components/charts/ChartEcoPpi.astro";
import ChartEcoHealth            from "../components/charts/ChartEcoHealth.astro";
import ChartEcoSpending          from "../components/charts/ChartEcoSpending.astro";
import ChartEcoSharkCards        from "../components/charts/ChartEcoSharkCards.astro";

// GTA V
import ChartAssassinationReturns from "../components/charts/ChartAssassinationReturns.astro";
import ChartDlcPlayerHistory     from "../components/charts/ChartDlcPlayerHistory.astro";
import ChartVehiclePerformance   from "../components/charts/ChartVehiclePerformance.astro";
import ChartMissionEarnings      from "../components/charts/ChartMissionEarnings.astro";
import PlayerChart               from "../components/PlayerChart.astro";
import TrendsChart               from "../components/TrendsChart.astro";

// Franchise
import ChartFranchiseSales       from "../components/charts/ChartFranchiseSales.astro";
import ChartCpiPricing           from "../components/charts/ChartCpiPricing.astro";
import ChartCriticDivergence     from "../components/charts/ChartCriticDivergence.astro";
import ChartDlcCadence           from "../components/charts/ChartDlcCadence.astro";
import ChartRevenueSplit         from "../components/charts/ChartRevenueSplit.astro";
import ChartTtwoStock            from "../components/charts/ChartTtwoStock.astro";
import ChartFranchiseComplexity  from "../components/charts/ChartFranchiseComplexity.astro";
import ChartFranchiseEarnings    from "../components/charts/ChartFranchiseEarnings.astro";

// ── Registry ──────────────────────────────────────────────────────────────────

export const ALL_CHARTS: ChartMeta[] = [

  // ════════════════════════════════════════════════════════
  // GTA VI
  // ════════════════════════════════════════════════════════

  {
    id:        "trailer-velocity",
    component: ChartTrailerVelocity,
    game:      "gta-vi",
    category:  "Community",
    badge:     "Community",
    label:     "GTA VI Trailer View Velocity",
    meta:      null, // no right-side element for this chart
    sources:   "Source: YouTube Data API · polled nightly",
    shareText: "GTA VI Trailer 1 holds the 24-hour YouTube record. 179M views and counting. The hype is unlike anything in gaming.",
    pages:     ["charts", "gta-vi"],
  },

  {
    id:        "gta6-search-trends-chart",
    component: ChartGta6SearchTrends,
    game:      "gta-vi",
    category:  "Community",
    badge:     "Community",
    label:     "GTA VI Search Signal — Google Trends 2020–2026",
    meta:      null,  // dynamic: total data points in chart
    sources:   "Source: Google Trends via pytrends · worldwide · 0–100 scale",
    shareText: "GTA VI search interest is at an all-time high and still climbing. T1 (Dec 2023) and T2 (May 2025) peaks visible in worldwide data.",
    pages:     ["charts", "gta-vi"],
  },

  {
    id:        "trailer-discovery-chart",
    component: ChartTrailerDiscovery,
    game:      "gta-vi",
    category:  "Community",
    badge:     "Community",
    label:     "Trailer Discovery Density — What Every Second Revealed",
    meta:      null,
    sources:   "Source: GTAVI.AI frame-by-frame analysis · official Rockstar trailers",
    shareText: "GTA VI Trailer 2 is the most information-dense Rockstar trailer ever made. Frame-by-frame entity analysis across all official releases.",
    pages:     ["charts", "gta-vi"],
  },

  {
    id:        "el-timeline-chart",
    component: ChartExtendedLookTimeline,
    game:      "gta-vi",
    category:  "Community",
    badge:     "Community",
    label:     "Extended Look — Chapter-by-Chapter Entity Timeline",
    meta:      "52 entities · 6 chapters · 26m 49s",
    sources:   "Source: GTAVI.AI frame-by-frame analysis · GTA VI: An Extended Look (Aug 27, 2026)",
    shareText: "52 entities confirmed in GTA VI's 27-minute Extended Look — mapped chapter by chapter. Analysis on GTAVI.AI.",
    pages:     ["charts", "gta-vi"],
    weight:    95,
  },

  {
    id:        "delay-timeline-chart",
    component: ChartDelayTimeline,
    game:      "gta-vi",
    category:  "History",
    badge:     "History",
    label:     "GTA VI Development & Delay Timeline",
    meta:      null, // dynamic: total_delays + timeline.length from delay-timeline.json
    sources:   "Sources: SEC EDGAR Take-Two 8-K filings · Rockstar Games official announcements",
    shareText: "GTA VI has been delayed twice. The full timeline — and what it signals for the Nov 19, 2026 release date.",
    pages:     ["charts", "gta-vi"],
  },

  {
    id:        "region-heatmap",
    component: ChartRegionHeatmap,
    game:      "gta-vi",
    category:  "Community",
    badge:     "Community",
    label:     "Leonida Region Evidence Heatmap",
    meta:      null, // dynamic: confirmed regions count from regions-evidence.json
    sources:   "Sources: Rockstar press kit · Trailer analysis · Leonida Intel community mapping",
    shareText: "Every confirmed GTA VI region from official trailer analysis. The Leonida map is the largest open world Rockstar has ever built.",
    pages:     ["charts", "gta-vi"],
  },

  {
    id:        "community-chart",
    component: ChartCommunity,
    game:      "gta-vi",
    category:  "Community",
    badge:     "Community",
    label:     "Community Anticipation Curve",
    meta:      "r/GTAVI · Google Trends overlay",
    sources:   "Sources: r/GrandTheftAutoVI community records · Google Trends via pytrends",
    shareText: "r/GrandTheftAutoVI hit 1.5M+ subscribers before launch. The community growth curve looks unlike any prior game release.",
    pages:     ["charts", "gta-vi"],
  },

  {
    id:        "prelaunch-comparison-chart",
    component: ChartPrelaunchComparison,
    game:      "gta-vi",
    category:  "History",
    badge:     "History",
    label:     "Pre-launch Hype — GTA V (2013) vs GTA VI (2026)",
    meta:      "both normalised to months before launch",
    sources:   "Sources: Google Trends via pytrends · r/GrandTheftAutoVI community records",
    shareText: "GTA VI is running 4.8× hotter than GTA V at the same pre-launch moment. Three signals, one conclusion.",
    pages:     ["charts", "gta-vi", "gta-v"],
  },

  {
    id:        "entertainment-chart",
    component: ChartEntertainmentComp,
    game:      "gta-vi",
    category:  "Economy-RL",
    badge:     "RL Economy",
    label:     "GTA VI vs Global Entertainment",
    meta:      "revenue billions USD",
    sources:   "Sources: Box Office Mojo (worldwide lifetime) · Take-Two IR · Spotify IR · DFC Intelligence · *projected",
    shareText: "GTA VI is projected to outgross the biggest movie openings in history. The entertainment revenue comparison is staggering.",
    pages:     ["charts"],
  },

  {
    id:        "competitors-chart",
    component: ChartCompetitors,
    game:      "gta-vi",
    category:  "Economy-RL",
    badge:     "RL Economy",
    label:     "GTA VI vs Major Game Launches — Year 1 Sales & Pre-launch Hype",
    meta:      null, // dynamic: competitorData.games.length
    sources:   "Sources: Publisher earnings · VGChartz · Metacritic · Google Trends · DFC Intelligence (GTA VI) · *predicted",
    shareText: "GTA VI projected year-1 vs the biggest game launches of the last decade. Every metric points to an unprecedented release.",
    pages:     ["charts"],
  },

  // ════════════════════════════════════════════════════════
  // GTA Online — main charts
  // ════════════════════════════════════════════════════════

  {
    id:        "income-leaderboard-chart",
    component: ChartIncomeLeaderboard,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "GTA Online Income Leaderboard — All Sources Ranked",
    meta:      null, // link override: "Full profiles →" /database (handled by ChartSection metaHref in Phase 2)
    sources:   "Source: GTABase.com · community benchmarks · net after costs · 2024 patches",
    shareText: "GTA Online income ranked S→C tier by net GTA$/hr. Cayo Perico $340k solo. Full profiles and tips in the Database.",
    pages:     ["charts", "gta-online"],
  },

  {
    id:        "meta-evolution-chart",
    component: ChartMetaEvolution,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "Meta Ceiling — Top $/hr Method at Each Major DLC (2013–2023)",
    meta:      null, // dynamic: meta_history.length patches tracked
    sources:   "Source: GTAForums · GTA Wiki · community archives · GTABase",
    shareText: "10 years of GTA Online money metas charted: from $250k/hr contact missions in 2013 to $2M/hr Cayo Perico in 2020 — one update changed everything.",
    pages:     ["charts", "gta-online"],
  },

  {
    id:        "gta-ppi-chart",
    component: ChartGtaPpi,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "GTA-PPI — In-Game Inflation Index (hours to buy standard basket)",
    meta:      null, // dynamic: series.length patches · base 100 = Oct 2013
    sources:   "Source: computed from price-basket.json + meta-history.json · GTAForums patch notes archives",
    shareText: "GTA Online's inflation index: it now takes 207% of 2013 effort to buy the same basket of content. Cayo Perico was the only deflationary event.",
    pages:     ["charts", "gta-online"],
  },

  {
    id:        "passive-stack-chart",
    component: ChartPassiveStack,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "Passive Income Stack — How Idle GTA$/hr Grew From 0 to $1.24M",
    meta:      null, // dynamic: 4 streams · $X.XM GTA$ setup
    sources:   "Source: GTABase.com · business-profiles.json · GTAForums patch notes · community benchmarks",
    shareText: "GTA Online passive income history: from $0 in 2013 to $1.24M/hr AFK in 2022. The Acid Lab was the last major passive income leap before GTA VI.",
    pages:     ["charts", "gta-online"],
  },

  {
    id:        "roi-scatter-chart",
    component: ChartRoiScatter,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "Setup Cost vs $/hr — What's Actually Worth Buying?",
    meta:      null, // link override: "Full profiles →" /database
    sources:   "Source: GTABase.com · community benchmarks · 2024 patches · bubble = break-even hours",
    shareText: "GTA Online setup cost vs $/hr: Kosatka is top-right (high cost, highest return, fast payback). Some businesses are expensive traps. The ROI chart.",
    pages:     ["charts", "gta-online"],
  },

  {
    id:        "shark-card-chart",
    component: ChartSharkCard,
    game:      "gta-online",
    category:  "Economy-RL",
    badge:     "RL Economy",
    label:     "Shark Card Purchasing Power — 12 Years of In-Game Inflation",
    meta:      null, // dynamic: years_span + purchasing_power_ratio from shark-cards.json
    sources:   "Real-money figures = endgame GTA$ ÷ Megalodon rate ($80k GTA$/USD). Shark Card prices unchanged since 2013 launch.",
    shareText: "It now costs 3× more in real USD to buy GTA Online's endgame via Shark Cards than it did in 2013. 12 years of purchasing power erosion charted.",
    pages:     ["charts", "gta-online"],
  },

  {
    id:        "heist-comparison-chart",
    component: ChartHeistComparison,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "Heist Comparison — $/hr vs Setup Cost vs Run Time",
    meta:      null, // dynamic: heists.length
    sources:   "Source: GTA Wiki · GTABase.com · community records · 2024 patches · Hard difficulty",
    shareText: "All GTA Online heists compared: Cayo Perico wins on $/hr despite being solo. Casino Heist is the best group heist. Data-driven answer to which heist is worth doing.",
    pages:     ["charts"],
  },

  {
    id:        "income-history-chart",
    component: ChartIncomeHistory,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "Income Source Price History — Nerfs, Buffs, DLC Launches",
    meta:      null, // dynamic: source_count + snapshot_count
    sources:   "Source: GTAForums patch notes archives + Rockstar Newswire · community benchmarks",
    shareText: "GTA Online income source history — every major nerf, buff, and DLC launch charted. Cayo Perico was nerfed 40% in 2021 then partially restored.",
    pages:     ["charts"],
  },

  {
    id:        "vehicle-tco-chart",
    component: ChartVehicleTco,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "Meta Vehicle TCO — What Does Going Full Meta Actually Cost?",
    meta:      null, // dynamic: vehicle_count
    sources:   "Source: GTABase.com · Broughy1322 · standard shop prices · trade prices shown where unlockable",
    shareText: "GTA Online meta vehicle costs — Oppressor Mk2 costs $5.1M fully kitted. Akula helicopter $4.8M. What going full meta actually requires.",
    pages:     ["charts"],
  },

  {
    id:        "property-cost-chart",
    component: ChartPropertyCost,
    game:      "gta-online",
    category:  "Economy-RL",
    badge:     "RL Economy",
    label:     "GTA Online Property Costs — Full Expense Registry",
    meta:      null, // dynamic: property_count
    sources:   "Source: GTA Fandom Wiki · community records",
    shareText: "GTA Online complete property cost guide — apartments to Kosatka submarine. Every purchasable property and what it actually costs.",
    pages:     ["charts"],
  },

  {
    id:        "property-daily-fee-chart",
    component: ChartPropertyDailyFee,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "Property Daily Fees — Ownership Has Ongoing Costs",
    meta:      "charged daily · applies offline",
    sources:   "Source: GTA Wiki · GTABase.com · GTA Online daily utility fee system",
    shareText: "GTA Online property daily fees — the Nightclub charges $2,100/day even when you're offline. The full ownership cost breakdown.",
    pages:     ["charts"],
  },

  {
    id:        "spending-distribution-chart",
    component: ChartSpendingDistribution,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "Spending Mix — Where GTA$ Goes Over the Years",
    meta:      null, // dynamic: eras.length
    sources:   "Source: community surveys · GTAForums spending analysis · modelled estimates · confidence: medium",
    shareText: "How GTA Online players spend their money: vehicles dominated 2013–14, properties peaked 2016–17 (Bunker update), then Oppressor drove vehicles back up.",
    pages:     ["charts"],
  },

  {
    id:        "price-history-chart",
    component: ChartPriceHistory,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "Price & Payout History — Every Nerf, Buff, and Launch Since 2013",
    meta:      null, // dynamic: change_count + item_count
    sources:   "Source: Rockstar Newswire · GTAForums patch notes archives",
    shareText: "GTA Online price change history — every documented nerf, buff, and property launch. Contact missions were nerfed 70% in 2014 then slowly buffed back.",
    pages:     ["charts"],
  },

  {
    id:        "bonus-heatmap",
    component: ChartBonusHeatmap,
    game:      "gta-online",
    category:  "Promotions",
    badge:     "Promotions",
    label:     "GTA Online Weekly Bonus Calendar — Activity Multiplier History",
    meta:      null, // dynamic: entry_count weeks tracked
    sources:   "Source: Rockstar Newswire · community archives · curated seed back to 2020 · live capture every Thursday",
    shareText: "GTA Online bonus calendar — which activities Rockstar has promoted most often. The promotional pattern is more predictable than you'd think.",
    pages:     ["charts", "gta-online"],
  },

  {
    id:        "ie-tiers-chart",
    component: ChartIeTiers,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "Import/Export Sell Tiers — Why Top-Range Vehicles Are 3× More Valuable",
    meta:      "3 tiers · 3 delivery types",
    sources:   "Source: GTABase.com · GTA Wiki · community records · no-damage assumption · net of setup mods",
    shareText: "GTA Online Import/Export sell prices: top-range specialist delivers 5× more than standard private. Always prioritise top-range sources.",
    pages:     ["charts"],
  },

  // ════════════════════════════════════════════════════════
  // GTA Online — economy deep-dive variants
  // Phase 5 will add "charts" to their pages array.
  // ════════════════════════════════════════════════════════

  {
    id:        "eco-wages",
    component: ChartEcoWages,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "Income Ceiling per Patch — Best $/hr Across 10 Years",
    meta:      "meta ceiling · 2013–2024",
    sources:   "Source: community benchmarks · meta-history.json · revenue-tiers.json · updated nightly",
    shareText: "GTA Online income ceiling charted across every major patch: from $250k/hr in 2013 to $2M/hr today. One update — Cayo Perico — changed everything.",
    pages:     ["charts", "gta-online", "gta-online/economy"],
    relatedId: "meta-evolution-chart",
  },

  {
    id:        "eco-ppi",
    component: ChartEcoPpi,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "GTA-PPI — Purchasing Power Index 2013–2026",
    meta:      "base 100 = Oct 2013",
    sources:   "Source: computed from price-basket.json + meta-history.json · GTAForums patch notes archives",
    shareText: "GTA Online's purchasing power index peaked at 207 in 2020 — it cost twice as many hours to buy the same content. Cayo Perico was the only deflationary event.",
    pages:     ["charts", "gta-online", "gta-online/economy"],
    relatedId: "gta-ppi-chart",
  },

  {
    id:        "eco-health",
    component: ChartEcoHealth,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "GTA Online Economy Health — Composite Index",
    meta:      "4 signals · normalised 0–1",
    sources:   "Source: composite of gta-ppi, meta-history, revenue-split, passive-stack · community data",
    shareText: "GTA Online economy health: a composite of 4 normalised signals. The post-Cayo era is the healthiest the economy has ever been for active players.",
    pages:     ["charts", "gta-online", "gta-online/economy"],
  },

  {
    id:        "eco-spending",
    component: ChartEcoSpending,
    game:      "gta-online",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "GTA$ Spending Distribution — How Player Money Flows Over the Years",
    meta:      "vehicles · properties · weapons",
    sources:   "Source: community surveys · GTAForums spending analysis · modelled estimates",
    shareText: "Where GTA$ actually goes: properties overtook vehicles in 2016 and never looked back. The Bunker era reshaped how GTA Online players spend.",
    pages:     ["charts", "gta-online/economy"],
    relatedId: "spending-distribution-chart",
  },

  {
    id:        "eco-sharkcards",
    component: ChartEcoSharkCards,
    game:      "gta-online",
    category:  "Economy-RL",
    badge:     "RL Economy",
    label:     "GTA Online Endgame Cost — Real USD via Shark Cards 2013–2026",
    meta:      "Megalodon rate · $80k GTA$/USD",
    sources:   "Source: Megalodon Shark Card rate ($80k GTA$/USD) · revenue-split.json · passive-stack.json",
    shareText: "In 2013 you could buy the GTA Online endgame for ~$200 in Shark Cards. In 2026 the same endgame costs $1,400+. 12 years of card inflation charted.",
    pages:     ["charts", "gta-online/economy"],
    relatedId: "shark-card-chart",
  },

  // ════════════════════════════════════════════════════════
  // GTA V
  // ════════════════════════════════════════════════════════

  {
    id:        "assassination-returns-chart",
    component: ChartAssassinationReturns,
    game:      "gta-v",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "GTA V Assassination Stock Returns — Optimal Sequence",
    meta:      null, // link override: "Full stock guide →" /gta-v
    sources:   "Source: GTA Wiki · community guides · LCN/BAWSAQ exchange data · 2024 verified",
    shareText: "GTA V assassination missions ranked by combined stock return. Multi-Target (Debonaire + Redwood) delivers 380% combined — the best single play in the game.",
    pages:     ["charts", "gta-v"],
  },

  {
    id:        "dlc-player-chart",
    component: ChartDlcPlayerHistory,
    game:      "gta-v",
    category:  "Community",
    badge:     "Community",
    label:     "GTA V Steam Players — DLC Events Overlay",
    meta:      null, // dynamic: steamData.data.length months · DLC annotated
    sources:   "Sources: SteamCharts · Rockstar Games official announcements · updated nightly",
    shareText: "GTA V still pulls tens of thousands of concurrent Steam players, 11 years after launch. Every DLC spike visible in the data.",
    pages:     ["charts", "gta-v"],
  },

  {
    id:        "player-chart",
    component: PlayerChart,
    game:      "gta-v",
    category:  "Community",
    badge:     "Community",
    label:     "GTA V Steam Player Count — Monthly Avg & Peak",
    meta:      null, // no right-side element
    sources:   "Source: SteamCharts · updated nightly",
    shareText: "GTA V has been online for 11 years. Steam player count: still pulling 100k+ concurrent monthly. The franchise benchmark.",
    pages:     ["charts", "gta-v"],
  },

  {
    id:        "trends-chart",
    component: TrendsChart,
    game:      "gta-v",
    category:  "Community",
    badge:     "Community",
    label:     "GTA V + GTA VI Google Trends 2013–2026",
    meta:      null, // no right-side element
    sources:   "Source: Google Trends via pytrends · updated nightly",
    shareText: "GTA V + GTA VI Google Trends 2013–2026. GTA VI search interest is at an all-time high — dramatically outpacing GTA V at the equivalent pre-launch moment.",
    pages:     ["charts", "gta-v"],
  },

  {
    id:        "mission-earnings-chart",
    component: ChartMissionEarnings,
    game:      "gta-v",
    category:  "Economy-IG",
    badge:     "IG Economy",
    label:     "Story Mission Earnings — Full Arc",
    meta:      "GTA V · story arc earnings",
    sources:   "Source: GTA Wiki (Fandom) · community records",
    shareText: "GTA V story mission earnings from start to finish. $250 at Repossession to $41.6M at The Big Score. The earning curve tells the whole story.",
    pages:     ["charts", "gta-v"],
  },

  {
    id:        "perf-chart",
    component: ChartVehiclePerformance,
    game:      "gta-v",
    category:  "Performance",
    badge:     "Performance",
    label:     "Vehicle Performance — Broughy1322 Lap Times",
    meta:      null, // dynamic: vehicleData.vehicles.length + " vehicles · Broughy1322"
    sources:   "Source: Broughy1322 GTA Vehicle Performance Spreadsheet · updated nightly",
    shareText: "665 Broughy-tested GTA V vehicles ranked. Top speed vs lap time — the actual performance data, not guesswork.",
    pages:     ["charts", "gta-v"],
  },

  // ════════════════════════════════════════════════════════
  // Franchise
  // ════════════════════════════════════════════════════════

  {
    id:        "sales-chart",
    component: ChartFranchiseSales,
    game:      "franchise",
    category:  "Economy-RL",
    badge:     "RL Economy",
    label:     "GTA Franchise Sales Velocity",
    meta:      null, // dynamic: salesData.last_updated.slice(0,10)
    sources:   "Sources: Take-Two IR · DFC Intelligence (GTA VI projection)",
    shareText: "GTA V sold 225M copies. Here's how every GTA title stacks up — franchise sales velocity charted.",
    pages:     ["charts"],
  },

  {
    id:        "cpi-chart",
    component: ChartCpiPricing,
    game:      "gta-vi",
    category:  "Economy-RL",
    badge:     "RL Economy",
    label:     "GTA Launch Price — Nominal vs Inflation-Adjusted",
    meta:      "US CPI-U · all prices in 2026 dollars",
    sources:   "Source: US Bureau of Labor Statistics CPI-U · Nominal prices from Rockstar/Take-Two",
    shareText: "GTA VI at $79.99 is actually cheaper than GTA III in 2001, in real inflation-adjusted dollars. The data says it's not overpriced.",
    pages:     ["charts", "gta-vi"],
  },

  {
    id:        "divergence-chart",
    component: ChartCriticDivergence,
    game:      "franchise",
    category:  "History",
    badge:     "History",
    label:     "Critic vs User Score Divergence — The Monetisation Story",
    meta:      "Metacritic · critic /100 · user ×10",
    sources:   "Source: Metacritic.com · GTA VI prediction based on franchise trajectory",
    shareText: "GTA SA had perfect critic/user alignment. GTA IV opened a 22-point gap. Will GTA VI close it? The historical pattern.",
    pages:     ["charts"],
  },

  {
    id:        "dlc-cadence-chart",
    component: ChartDlcCadence,
    game:      "gta-vi",
    category:  "History",
    badge:     "History",
    label:     "GTA Online DLC Cadence → GTA VI Online Prediction",
    meta:      null, // dynamic: major updates count
    sources:   "Source: Rockstar Games official announcements · GTA Online update history 2013–2024",
    shareText: "GTA Online had 38 major content drops over 11 years. The predicted GTA VI Online cadence based on historical patterns.",
    pages:     ["charts"],
  },

  {
    id:        "revenue-split-chart",
    component: ChartRevenueSplit,
    game:      "gta-vi",
    category:  "Economy-RL",
    badge:     "RL Economy",
    label:     "GTA V Revenue Model — Game Sales vs Online Economy",
    meta:      "13 fiscal years · game → recurrent shift",
    sources:   "Sources: Take-Two IR quarterly earnings · Wedbush Securities analyst estimates · DFC Intelligence (GTA VI)",
    shareText: "Shark Cards have generated billions for Take-Two. The revenue shift that fundamentally changed how Rockstar makes games.",
    pages:     ["charts", "gta-vi"],
  },

  {
    id:        "ttwo-stock-chart",
    component: ChartTtwoStock,
    game:      "gta-vi",
    category:  "Economy-RL",
    badge:     "RL Economy",
    label:     "Take-Two (TTWO) Stock Price vs GTA VI Milestones",
    meta:      null, // dynamic: prices.length months · Yahoo Finance
    sources:   "Source: Yahoo Finance (TTWO) · Not investment advice · Updated nightly",
    shareText: "Take-Two stock tracks GTA announcement cycles almost perfectly. The market reaction to every trailer and delay, charted.",
    pages:     ["charts"],
  },

  {
    id:        "franchise-complexity-chart",
    component: ChartFranchiseComplexity,
    game:      "gta-vi",
    category:  "History",
    badge:     "History",
    label:     "GTA Economic Complexity — 25 Years of Evolution",
    meta:      null, // dynamic: title_count + " titles · 1997 → 2026"
    sources:   "Source: curated research · GTAForums · GTA Fandom Wiki · complexity score = count of active economic mechanics",
    shareText: "GTA's economic complexity charted across 25 years. From 2-mechanic GTA III to 9-mechanic GTA Online. GTA VI is predicted to reach 10.",
    pages:     ["charts"],
  },

  {
    id:        "franchise-earnings-chart",
    component: ChartFranchiseEarnings,
    game:      "franchise",
    category:  "History",
    badge:     "History",
    label:     "Cross-Title Earnings — Max $/hr + Hours to Endgame",
    meta:      "GTA II → GTA Online · normalised effort",
    sources:   "Source: hours_to_aspirational = aspirational_price ÷ best_hourly_rate · community records · GTA Fandom Wiki",
    shareText: "GTA franchise earnings across titles: GTA Online takes 180 hours to reach endgame at the meta ceiling. GTA III takes 10. The grind has grown 18×.",
    pages:     ["charts"],
  },
];

// ── Lookup helpers ─────────────────────────────────────────────────────────────

/** O(1) lookup by chart ID */
const _byId = new Map<string, ChartMeta>(ALL_CHARTS.map(c => [c.id, c]));

export function getAllCharts(): ChartMeta[] {
  return ALL_CHARTS;
}

export function getChart(id: string): ChartMeta | undefined {
  return _byId.get(id);
}

export function getChartsForPage(page: PageSlug): ChartMeta[] {
  return ALL_CHARTS.filter(c => c.pages.includes(page));
}

// ── /charts page order ────────────────────────────────────────────────────────
/**
 * Canonical display order for the /charts catalogue page.
 * Narrative flow: GTA VI → GTA Online → GTA V → Franchise.
 * Edit this list to reorder — no other files need to change.
 */
export const CHARTS_PAGE_ORDER: string[] = [
  // GTA VI
  "trailer-discovery-chart",
  "el-timeline-chart",
  "delay-timeline-chart",
  "region-heatmap",
  "community-chart",
  "prelaunch-comparison-chart",
  "entertainment-chart",
  "competitors-chart",
  "trailer-velocity",           // view velocity moved to end of GTA VI block
  // GTA Online
  "meta-evolution-chart",
  "gta-ppi-chart",
  "passive-stack-chart",
  "roi-scatter-chart",
  "shark-card-chart",
  "heist-comparison-chart",
  "income-history-chart",
  "vehicle-tco-chart",
  "property-cost-chart",
  "property-daily-fee-chart",
  "spending-distribution-chart",
  "price-history-chart",
  "bonus-heatmap",
  "ie-tiers-chart",
  // GTA Online — economy deep-dive charts (first-class on /charts from Phase 5)
  "eco-wages",
  "eco-ppi",
  "eco-health",
  "eco-spending",
  "eco-sharkcards",
  "income-leaderboard-chart",   // moved to end of GTA Online block
  // GTA V
  "assassination-returns-chart",
  "dlc-player-chart",
  "player-chart",
  "trends-chart",
  "mission-earnings-chart",
  "perf-chart",
  // Franchise
  "sales-chart",
  "cpi-chart",
  "divergence-chart",
  "dlc-cadence-chart",
  "revenue-split-chart",
  "franchise-complexity-chart", // complexity moved before TTWO stock
  "ttwo-stock-chart",
  "franchise-earnings-chart",
];

// ── Hub page configuration ────────────────────────────────────────────────────
/**
 * Featured and preview chart IDs per hub page.
 * Replaces gta_vi / gta_online / gta_v sections of chart-config.json.
 * Edit here to change what appears on hub pages.
 */
export const HUB_CONFIG = {
  "gta-vi": {
    featured: ["trailer-velocity", "delay-timeline-chart", "region-heatmap", "trailer-discovery-chart"],
    preview:  ["prelaunch-comparison-chart", "community-chart"],
  },
  "gta-online": {
    featured: ["meta-evolution-chart", "income-leaderboard-chart", "gta-ppi-chart"],
    preview:  ["bonus-heatmap", "roi-scatter-chart", "passive-stack-chart", "shark-card-chart"],
  },
  "gta-v": {
    featured: ["player-chart", "perf-chart"],
    preview:  ["assassination-returns-chart", "dlc-player-chart", "prelaunch-comparison-chart"],
  },
} as const;

// ── Backward-compat CHART_REGISTRY ────────────────────────────────────────────
/**
 * Drop-in replacement for the old chartRegistry.ts CHART_REGISTRY.
 * Phase 3 removes all callers and this export can be deleted.
 */
export const CHART_REGISTRY: Record<string, ChartMeta["component"]> =
  Object.fromEntries(ALL_CHARTS.map(c => [c.id, c.component]));
