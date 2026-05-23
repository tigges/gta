/**
 * chartRegistry.ts — backward-compatibility shim
 *
 * The canonical chart registry has moved to allCharts.ts.
 * This file re-exports CHART_REGISTRY so existing callers
 * (hub pages, charts.astro) continue to work without changes.
 *
 * Phase 3 will migrate all callers to import directly from allCharts.ts,
 * after which this file can be deleted.
 */
export { CHART_REGISTRY } from "./allCharts";
