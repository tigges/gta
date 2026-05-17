/**
 * /og/online/[id].png — Per-card OG image for GTA Online businesses
 *
 * Generated at build time for each business in business-profiles.json.
 * Shows: DLC thumbnail · tier badge · business name · $/hr · play type
 * Used by: /gta-v/online/[id] share pages
 */

import type { APIRoute } from "astro";
import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

import bizProfilesRaw  from "../../../../data/gta-5/economy/business-profiles.json";
import revTiersRaw     from "../../../../data/gta-5/economy/revenue-tiers.json";

const bizProfiles = (bizProfilesRaw as any).businesses as any[];
const tiers       = (revTiersRaw as any).tiers as any[];

// Build tier lookup: id → {tier, color}
const TIER_MAP: Record<string, { tier: string; color: string }> = {};
tiers.forEach((t: any) => {
  t.sources.forEach((s: any) => {
    TIER_MAP[s.id] = { tier: t.tier, color: t.color };
  });
});

// DLC thumbnail map (same as database.astro BIZ_THUMBS)
const BIZ_THUMBS: Record<string, string> = {
  "cayo-perico":            "assets/gta5/dlc/cayo-perico.jpg",
  "kosatka-nightclub-stack":"assets/gta5/dlc/cayo-perico.jpg",
  "diamond-casino-heist":   "assets/gta5/dlc/diamond-casino-heist.jpg",
  "agency-vip-contract":    "assets/gta5/dlc/agency.jpg",
  "payphone-hits":          "assets/gta5/dlc/the-contract.jpg",
  "special-cargo":          "assets/gta5/dlc/import-export.jpg",
  "acid-lab":               "assets/gta5/dlc/acid-lab.jpg",
  "auto-shop":              "assets/gta5/dlc/auto-shop.jpg",
  "terrorbyte-oppressor":   "assets/gta5/dlc/terrorbyte.jpg",
  "garment-factory":        "assets/gta5/dlc/chop-shop.jpg",
  "nightclub":              "assets/gta5/dlc/after-hours.jpg",
  "bunker":                 "assets/gta5/dlc/gunrunning.jpg",
  "salvage-yard":           "assets/gta5/dlc/salvage-yard.jpg",
  "security-contracts":     "assets/gta5/dlc/security-contracts.jpg",
  "exotic-exports":         "assets/gta5/dlc/exotic-exports.jpg",
  "vehicle-warehouse":      "assets/gta5/dlc/import-export.jpg",
  "vip-work":               "assets/gta5/dlc/the-contract.jpg",
  "mc-cocaine":             "assets/gta5/dlc/bikers.jpg",
  "hangar":                 "assets/gta5/dlc/smugglers-run.jpg",
  "ceo-crates":             "assets/gta5/dlc/finance-felony.jpg",
  "casino-missions":        "assets/gta5/dlc/casino-work.jpg",
};

const PLAY_COLOR: Record<string, string> = {
  passive:         "#22c55e",
  "semi-passive":  "#f59e0b",
  active:          "#ef4444",
  heist:           "#818cf8",
  contract:        "#0d9488",
  mission:         "#0d9488",
  stack:           "#22c55e",
};

let fontBold: ArrayBuffer | null = null;
let fontReg:  ArrayBuffer | null = null;

function getFonts() {
  if (!fontBold) fontBold = readFileSync(join(process.cwd(), "src/assets/fonts/Inter-Bold.ttf")).buffer;
  if (!fontReg)  fontReg  = readFileSync(join(process.cwd(), "src/assets/fonts/Inter-Regular.ttf")).buffer;
  return { bold: fontBold, regular: fontReg };
}

function imageToDataUri(relativePath: string): string | null {
  const abs = join(process.cwd(), "public", relativePath);
  if (!existsSync(abs)) return null;
  const buf = readFileSync(abs);
  const ext = relativePath.endsWith(".png") ? "png" : "jpeg";
  return `data:image/${ext};base64,${buf.toString("base64")}`;
}

export function getStaticPaths() {
  // Include all profiled businesses that have a net_profit_per_hr
  return bizProfiles
    .filter((b: any) => b.net_profit_per_hr > 0)
    .map((b: any) => ({ params: { id: b.id } }));
}

export const GET: APIRoute = async ({ params }) => {
  const id  = params.id as string;
  const biz = bizProfiles.find((b: any) => b.id === id);
  if (!biz) return new Response("Not found", { status: 404 });

  const tierInfo  = TIER_MAP[id] ?? { tier: "B", color: "#0d9488" };
  const khr       = Math.round(biz.net_profit_per_hr / 1000);
  const playColor = PLAY_COLOR[biz.play_type ?? biz.category] ?? "#71717a";
  const thumbPath = BIZ_THUMBS[id];
  const thumbUri  = thumbPath ? imageToDataUri(thumbPath) : null;

  const { bold, regular } = getFonts();

  const svg = await satori(
    {
      type: "div",
      props: {
        style: {
          display: "flex",
          width: "1200px",
          height: "630px",
          backgroundColor: "#0e0e11",
          fontFamily: "Inter",
          position: "relative",
          overflow: "hidden",
        },
        children: [
          // Background thumbnail (right side)
          thumbUri && {
            type: "div",
            props: {
              style: {
                position: "absolute",
                right: "0px",
                top: "0px",
                width: "580px",
                height: "630px",
                display: "flex",
                overflow: "hidden",
              },
              children: [
                { type: "img", props: { src: thumbUri, style: { width: "580px", height: "630px", objectFit: "cover" } } },
                { type: "div", props: { style: { position: "absolute", inset: "0", background: "linear-gradient(to right, #0e0e11 0%, rgba(14,14,17,0.6) 50%, rgba(14,14,17,0.2) 100%)", display: "flex" } } },
              ],
            },
          },

          // Left content
          {
            type: "div",
            props: {
              style: {
                position: "absolute",
                left: "0px",
                top: "0px",
                width: "700px",
                height: "630px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                padding: "64px 56px",
                gap: "0px",
              },
              children: [
                // Eyebrow
                { type: "div", props: { style: { display: "flex", alignItems: "center", gap: "12px", marginBottom: "20px" }, children: [
                  { type: "div", props: { style: { fontSize: "11px", color: "#9898b8", letterSpacing: "0.2em", textTransform: "uppercase", fontWeight: 400 }, children: "GTA Online · Income Database" } },
                ] } },

                // Tier badge + play type
                { type: "div", props: { style: { display: "flex", alignItems: "center", gap: "12px", marginBottom: "20px" }, children: [
                  { type: "div", props: { style: { fontSize: "40px", fontWeight: 900, color: tierInfo.color, lineHeight: 1 }, children: tierInfo.tier } },
                  { type: "div", props: { style: { fontSize: "11px", color: playColor, background: `${playColor}22`, border: `1px solid ${playColor}55`, padding: "4px 10px", borderRadius: "4px", letterSpacing: "0.15em", textTransform: "uppercase", fontWeight: 700 }, children: (biz.play_type ?? biz.category ?? "").toUpperCase() } },
                  biz.solo && { type: "div", props: { style: { fontSize: "10px", color: "#0d9488", background: "rgba(13,148,136,0.12)", border: "1px solid rgba(13,148,136,0.3)", padding: "4px 10px", borderRadius: "4px", letterSpacing: "0.15em", textTransform: "uppercase", fontWeight: 700 }, children: "SOLO" } },
                ].filter(Boolean) } },

                // Business name
                { type: "div", props: { style: { fontSize: "46px", fontWeight: 900, color: "#ffffff", lineHeight: 1.1, marginBottom: "24px" }, children: biz.name } },

                // $/hr
                { type: "div", props: { style: { display: "flex", alignItems: "baseline", gap: "8px", marginBottom: "16px" }, children: [
                  { type: "span", props: { style: { fontSize: "56px", fontWeight: 900, color: tierInfo.color, lineHeight: 1 }, children: `$${khr}K` } },
                  { type: "span", props: { style: { fontSize: "20px", color: "#9898b8", fontWeight: 400 }, children: "/hr" } },
                ] } },

                // Setup cost if available
                biz.setup_cost_full && {
                  type: "div",
                  props: { style: { fontSize: "14px", color: "#71717a" }, children: `Setup: $${(biz.setup_cost_full / 1_000_000).toFixed(1)}M` },
                },

                // Spacer + watermark
                { type: "div", props: { style: { marginTop: "32px", display: "flex", alignItems: "center", gap: "8px" }, children: [
                  { type: "div", props: { style: { width: "32px", height: "2px", background: tierInfo.color, borderRadius: "2px", display: "flex" } } },
                  { type: "div", props: { style: { fontSize: "12px", color: "#3f3f46", letterSpacing: "0.15em" }, children: "GTAVI.AI" } },
                ] } },
              ].filter(Boolean),
            },
          },
        ].filter(Boolean),
      },
    },
    {
      width: 1200,
      height: 630,
      fonts: [
        { name: "Inter", data: bold,    weight: 900, style: "normal" },
        { name: "Inter", data: regular, weight: 400, style: "normal" },
      ],
    }
  );

  const resvg = new Resvg(svg, { fitTo: { mode: "width", value: 1200 } });
  const png   = resvg.render().asPng();

  return new Response(png, {
    status: 200,
    headers: {
      "Content-Type":  "image/png",
      "Cache-Control": "public, max-age=86400",
    },
  });
};
