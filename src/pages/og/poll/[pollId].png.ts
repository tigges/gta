import type { APIRoute } from "astro";
import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import { readFileSync } from "fs";
import { join } from "path";
import type { PredictionsData } from "../../../types/gta";
import predRaw from "../../../../data/gta-6/predictions.json";

const predData = predRaw as unknown as PredictionsData;

// ── Font loading ──────────────────────────────────────────────────────────────

let fontBold: ArrayBuffer | null = null;
let fontRegular: ArrayBuffer | null = null;

function getFonts(): { bold: ArrayBuffer; regular: ArrayBuffer } {
  if (!fontBold)    fontBold    = readFileSync(join(process.cwd(), "src/assets/fonts/Inter-Bold.ttf")).buffer;
  if (!fontRegular) fontRegular = readFileSync(join(process.cwd(), "src/assets/fonts/Inter-Regular.ttf")).buffer;
  return { bold: fontBold, regular: fontRegular };
}

// ── Static paths — one image per poll-enabled prediction ─────────────────────

export function getStaticPaths() {
  return predData.predictions
    .filter((p: any) => p.poll_question)
    .map((p: any) => ({ params: { pollId: p.id } }));
}

// ── OG renderer ──────────────────────────────────────────────────────────────

export const GET: APIRoute = async ({ params }) => {
  const pollId = params.pollId as string;
  const pred   = predData.predictions.find((p: any) => p.id === pollId) as any;
  if (!pred?.poll_question) return new Response("Not found", { status: 404 });

  const question  = pred.poll_question as string;
  const options   = (pred.poll_options ?? ["Yes", "No"]) as string[];
  const tier      = pred.confidence_tier as string;
  const confidence = pred.confidence as number;

  // Tier colours
  const TIER_COLORS: Record<string, { text: string; bg: string }> = {
    confirmed: { text: "#0d9488", bg: "rgba(13,148,136,0.18)" },
    reported:  { text: "#f59e0b", bg: "rgba(245,158,11,0.18)" },
    predicted: { text: "#b4b4cc", bg: "rgba(180,180,204,0.12)" },
  };
  const tc = TIER_COLORS[tier] ?? TIER_COLORS.predicted;

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
          flexDirection: "column",
          padding: "64px 80px",
          gap: "0px",
        },
        children: [
          // ── Top row: badges ──────────────────────────────────────────
          {
            type: "div",
            props: {
              style: { display: "flex", alignItems: "center", gap: "12px", marginBottom: "28px" },
              children: [
                // GTA VI pill
                {
                  type: "div",
                  props: {
                    style: {
                      display: "flex", padding: "4px 12px", borderRadius: "6px",
                      background: "rgba(255,107,157,0.18)", border: "1.5px solid rgba(255,107,157,0.45)",
                      fontSize: "13px", fontWeight: "700", color: "#ff6b9d",
                      letterSpacing: "0.1em", textTransform: "uppercase",
                    },
                    children: "GTA VI",
                  },
                },
                // Community Vote badge
                {
                  type: "div",
                  props: {
                    style: {
                      display: "flex", padding: "4px 12px", borderRadius: "6px",
                      background: "rgba(245,158,11,0.15)", border: "1.5px solid rgba(245,158,11,0.35)",
                      fontSize: "13px", fontWeight: "700", color: "#f59e0b",
                      letterSpacing: "0.1em", textTransform: "uppercase",
                    },
                    children: "Community Vote",
                  },
                },
                // Confidence tier
                {
                  type: "div",
                  props: {
                    style: {
                      display: "flex", padding: "4px 12px", borderRadius: "6px",
                      background: tc.bg, border: `1.5px solid ${tc.text}55`,
                      fontSize: "13px", fontWeight: "700", color: tc.text,
                      letterSpacing: "0.1em", textTransform: "uppercase",
                    },
                    children: `${tier} · ${confidence}%`,
                  },
                },
              ],
            },
          },

          // ── Question ──────────────────────────────────────────────────
          {
            type: "div",
            props: {
              style: {
                display: "flex",
                fontSize: question.length > 60 ? "40px" : "48px",
                fontWeight: "700",
                color: "#ebebef",
                lineHeight: "1.2",
                marginBottom: "40px",
                maxWidth: "900px",
              },
              children: question,
            },
          },

          // ── Option pills ──────────────────────────────────────────────
          {
            type: "div",
            props: {
              style: { display: "flex", flexWrap: "wrap", gap: "12px", marginBottom: "auto" },
              children: options.map(opt => ({
                type: "div",
                props: {
                  style: {
                    display: "flex", padding: "10px 20px", borderRadius: "8px",
                    background: "#1a1a1e", border: "1.5px solid #2a2a31",
                    fontSize: "18px", fontWeight: "700", color: "#b4b4cc",
                    fontFamily: "Inter",
                  },
                  children: opt,
                },
              })),
            },
          },

          // ── Bottom bar ────────────────────────────────────────────────
          {
            type: "div",
            props: {
              style: {
                display: "flex", alignItems: "center", justifyContent: "space-between",
                marginTop: "40px",
                borderTop: "1px solid #1e1e23",
                paddingTop: "24px",
              },
              children: [
                {
                  type: "div",
                  props: {
                    style: { display: "flex", fontSize: "16px", color: "#52525b", letterSpacing: "0.1em" },
                    children: "gtavi.ai/community/polls",
                  },
                },
                {
                  type: "div",
                  props: {
                    style: {
                      display: "flex", alignItems: "baseline", gap: "4px",
                      fontSize: "22px", fontWeight: "700",
                    },
                    children: [
                      { type: "span", props: { style: { color: "#ffffff" }, children: "GTA" } },
                      { type: "span", props: { style: { color: "#f59e0b" }, children: "VI" } },
                      { type: "span", props: { style: { color: "#ffffff", fontSize: "16px", border: "2px solid rgba(235,235,239,0.7)", borderRadius: "4px", padding: "1px 5px", marginLeft: "4px" }, children: ".AI" } },
                    ],
                  },
                },
              ],
            },
          },
        ],
      },
    },
    {
      width: 1200,
      height: 630,
      fonts: [
        { name: "Inter", data: bold,    weight: 700, style: "normal" },
        { name: "Inter", data: regular, weight: 400, style: "normal" },
      ],
    }
  );

  const resvg = new Resvg(svg, { fitTo: { mode: "width", value: 1200 } });
  const png   = resvg.render().asPng();

  return new Response(png, {
    headers: {
      "Content-Type": "image/png",
      "Cache-Control": "public, max-age=86400",
    },
  });
};
