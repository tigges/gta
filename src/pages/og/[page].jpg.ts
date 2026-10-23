import type { APIRoute } from "astro";
import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import sharp from "sharp";
import { readFileSync } from "fs";
import { join } from "path";
import {
  C_BG, C_BG_DEEP, C_BORDER_2, C_BRAND, C_CHART_PURPLE, C_ECONOMY, C_GROWTH, C_LIVE, C_LIVE_BRIGHT,
  C_TEXT_0, C_TEXT_1, C_TEXT_2, C_TEXT_3, C_TEXT_4, C_TEXT_5,
  C_TITLE_III, C_TITLE_IV, C_TITLE_SA, C_TITLE_VC, withAlpha,
} from "../../config/colors";

// ── Per-page config ──────────────────────────────────────────────────────────

interface PageConfig {
  badge: string;
  badgeColor: string;
  badgeBg: string;
  title: string;
  desc: string;
  image: string; // relative to public/
  accent: string;
}

const PAGES: Record<string, PageConfig> = {
  home: {
    badge: "Live Intelligence",
    badgeColor: C_LIVE,
    badgeBg: withAlpha(C_LIVE, 0.15),
    title: "GTA VI.AI",
    desc: "Data-driven intelligence across every GTA generation — live signals, franchise analytics, and what the numbers say about GTA VI.",
    image: "assets/gta6/characters/Lucia_Caminos_01.jpg",
    accent: C_BRAND,
  },
  "vi-intel": {
    badge: "VI Intel",
    badgeColor: C_BRAND,
    badgeBg: withAlpha(C_BRAND, 0.15),
    title: "GTA VI Intelligence",
    desc: "Character profiles, location mapping, predictions, and trailer analysis — everything confirmed about GTA VI.",
    image: "assets/gta6/characters/Jason_Duval_01.jpg",
    accent: C_BRAND,
  },
  charts: {
    badge: "Charts",
    badgeColor: C_ECONOMY,
    badgeBg: withAlpha(C_ECONOMY, 0.15),
    title: "Franchise Charts",
    desc: "D3-powered analytics: YouTube velocity, Google Trends, Take-Two stock, and GTA VI search interest vs every prior launch.",
    image: "assets/gta6/locations/Vice_City_01.jpg",
    accent: C_ECONOMY,
  },
  database: {
    badge: "Database",
    badgeColor: C_LIVE,
    badgeBg: withAlpha(C_LIVE, 0.15),
    title: "GTA Database",
    desc: "665 Broughy-tested GTA V vehicles · 1,715 GTA VI entities · news archive and franchise data — all in one place.",
    image: "assets/gta6/characters/Raul_Bautista_01.jpg",
    accent: C_LIVE,
  },
  franchise: {
    badge: "Franchise",
    badgeColor: C_CHART_PURPLE,
    badgeBg: withAlpha(C_CHART_PURPLE, 0.15),
    title: "Franchise History",
    desc: "30 years of GTA quantified — sales velocity, review scores, map growth, DLC history and the economics behind GTA VI.",
    image: "assets/gta6/locations/Port_Gellhorn_03.jpg",
    accent: C_CHART_PURPLE,
  },
  news: {
    badge: "News",
    badgeColor: C_GROWTH,
    badgeBg: withAlpha(C_GROWTH, 0.15),
    title: "GTA VI News",
    desc: "Rockstar Newswire headlines and community intelligence — everything that matters about GTA VI, filtered and curated.",
    image: "assets/gta6/locations/Leonida_Keys_01.jpg",
    accent: C_GROWTH,
  },
  buy: {
    badge: "Buy GTA VI",
    badgeColor: C_BRAND,
    badgeBg: withAlpha(C_BRAND, 0.15),
    title: "Buy GTA VI",
    desc: "GTA VI editions, platforms, retailers, and pre-order bonuses — your complete guide to launch day.",
    image: "assets/gta6/characters/Lucia_Caminos_02.jpg",
    accent: C_BRAND,
  },
  predictions: {
    badge: "Predictions",
    badgeColor: C_BRAND,
    badgeBg: withAlpha(C_BRAND, 0.15),
    title: "GTA VI Predictions",
    desc: "Data-backed predictions for GTA VI — sales trajectory, mechanics, pricing, and launch performance.",
    image: "assets/gta6/characters/Jason_Duval_02.jpg",
    accent: C_BRAND,
  },
  "gta-v": {
    badge: "GTA V Data",
    badgeColor: C_LIVE,
    badgeBg: withAlpha(C_LIVE, 0.15),
    title: "GTA V Economics",
    desc: "Mission earnings, heist payouts, assassination stock guide, vehicle benchmarks, and 11 years of Steam data — the blueprint for GTA VI.",
    image: "assets/gta6/locations/Ambrosia_01.jpg",
    accent: C_LIVE,
  },
  "economy": {
    badge: "Macro Model",
    badgeColor: C_ECONOMY,
    badgeBg: withAlpha(C_ECONOMY, 0.15),
    title: "Five Flows. One Economy.",
    desc: "The GTA Online circular economy model — wages, spending, savings, Shark Card injections and the GTA-PPI purchasing power index.",
    image: "assets/gta5/story/gta-v-cover.jpg",
    accent: C_ECONOMY,
  },
  "gta-iii-eco": {
    badge: "GTA III · 2001",
    badgeColor: C_TITLE_III,
    badgeBg: withAlpha(C_TITLE_III, 0.12),
    title: "GTA III Economy",
    desc: "The proto-economy: mission pay → spending. One-way flow, no investment layer, no Shark Cards. The origin of 25 years of GTA economics.",
    image: "assets/gta6/locations/Ambrosia_01.jpg",
    accent: C_TITLE_III,
  },
  "gta-vc-eco": {
    badge: "Vice City · 2002",
    badgeColor: C_TITLE_VC,
    badgeBg: withAlpha(C_TITLE_VC, 0.12),
    title: "Vice City Economy",
    desc: "GTA's first passive income layer — property investment, business ownership and the first circular money flow. The blueprint for GTA Online.",
    image: "assets/gta6/locations/Vice_City_03.jpg",
    accent: C_TITLE_VC,
  },
  "gta-sa-eco": {
    badge: "San Andreas · 2004",
    badgeColor: C_TITLE_SA,
    badgeBg: withAlpha(C_TITLE_SA, 0.12),
    title: "San Andreas Economy",
    desc: "Multi-stream income: gang territory, gambling, properties, stock market. The most complex single-player GTA economy before GTA Online.",
    image: "assets/gta6/locations/Grassrivers_01.jpg",
    accent: C_TITLE_SA,
  },
  "gta-iv-eco": {
    badge: "GTA IV · 2008",
    badgeColor: C_TITLE_IV,
    badgeBg: withAlpha(C_TITLE_IV, 0.12),
    title: "GTA IV Economy",
    desc: "The intentional regression — narrative realism over economic complexity. Rockstar stripped 6 years of innovation for Liberty City authenticity.",
    image: "assets/gta6/locations/Port_Gellhorn_01.jpg",
    accent: C_TITLE_IV,
  },
  "gta-v-eco": {
    badge: "GTA V Story · 2013",
    badgeColor: C_BRAND,
    badgeBg: withAlpha(C_BRAND, 0.15),
    title: "GTA V Economy",
    desc: "Mission earnings, heist payouts, assassination stock guide, and the BAWSAQ market. The story-mode counterpart to GTA Online's live economy.",
    image: "assets/gta5/story/gta-v-cover.jpg",
    accent: C_BRAND,
  },
  "income-adviser": {
    badge: "GTA Online · Adviser",
    badgeColor: C_LIVE,
    badgeBg: withAlpha(C_LIVE, 0.15),
    title: "Income Stack Adviser",
    desc: "Select your businesses, get your personalised $/hr total and the highest-ROI next purchase. Built on Broughy benchmarks and community data.",
    image: "assets/gta5/dlc/cayo-perico.jpg",
    accent: C_LIVE,
  },
  "cayo-perico": {
    badge: "GTA Online · S+ Tier",
    badgeColor: C_GROWTH,
    badgeBg: withAlpha(C_GROWTH, 0.15),
    title: "Cayo Perico Heist Guide",
    desc: "The best solo money method in GTA Online — $1,200K/hr+. Loot tiers, optimal strategy, setup cost and break-even. Updated 2026.",
    image: "assets/gta5/dlc/cayo-perico.jpg",
    accent: C_GROWTH,
  },
};

// ── Font loading (cached) ────────────────────────────────────────────────────

let fontBold: ArrayBuffer | null = null;
let fontRegular: ArrayBuffer | null = null;

function getFonts(): { bold: ArrayBuffer; regular: ArrayBuffer } {
  if (!fontBold) {
    fontBold = readFileSync(
      join(process.cwd(), "src/assets/fonts/Inter-Bold.ttf")
    ).buffer;
  }
  if (!fontRegular) {
    fontRegular = readFileSync(
      join(process.cwd(), "src/assets/fonts/Inter-Regular.ttf")
    ).buffer;
  }
  return { bold: fontBold, regular: fontRegular };
}

// ── Image loading as data URI ────────────────────────────────────────────────

function imageToDataUri(relativePath: string): string {
  const absPath = join(process.cwd(), "public", relativePath);
  const buf = readFileSync(absPath);
  return `data:image/jpeg;base64,${buf.toString("base64")}`;
}

// ── Static paths ─────────────────────────────────────────────────────────────

export function getStaticPaths() {
  return Object.keys(PAGES).map((page) => ({ params: { page } }));
}

// ── Home hero card ───────────────────────────────────────────────────────────
// Full-bleed Lucia + Jason duo (mirrors the /gta-vi hero) with centred branding,
// so the share preview reads well as a full banner AND as a square crop (the
// layout chat apps like WhatsApp fall back to). Exported as a small JPEG.
const HOME_TAGLINE =
  "30 years of GTA's in-game and real-world economy — tracked, predicted and visualised. Confidence-scored data on everything GTA VI.";

async function renderHomeHero(): Promise<Response> {
  const { bold, regular } = getFonts();
  const luciaUri = imageToDataUri("assets/gta6/characters/Lucia_Caminos_03.jpg");
  const jasonUri = imageToDataUri("assets/gta6/characters/Jason_Duval_02.jpg");

  const span = (children: string, style: Record<string, unknown>) => ({
    type: "span",
    props: { style: { fontFamily: "Inter", ...style }, children },
  });
  const box = (style: Record<string, unknown>, children: unknown[]) => ({
    type: "div",
    props: { style: { display: "flex", ...style }, children },
  });

  const svg = await satori(
    {
      type: "div",
      props: {
        style: {
          width: "1200px",
          height: "630px",
          display: "flex",
          position: "relative",
          fontFamily: "Inter",
          backgroundColor: C_BG,
          overflow: "hidden",
        },
        children: [
          // Two protagonist halves
          box(
            { position: "absolute", top: "0px", left: "0px", width: "1200px", height: "630px" },
            [
              box({ width: "600px", height: "630px", overflow: "hidden" }, [
                { type: "img", props: { src: luciaUri, style: { width: "600px", height: "630px", objectFit: "cover", objectPosition: "top" } } },
              ]),
              box({ width: "600px", height: "630px", overflow: "hidden" }, [
                { type: "img", props: { src: jasonUri, style: { width: "600px", height: "630px", objectFit: "cover", objectPosition: "top" } } },
              ]),
            ]
          ),
          // Top + bottom darkening for legibility
          box(
            {
              position: "absolute", top: "0px", left: "0px", width: "1200px", height: "630px",
              background:
                `linear-gradient(to bottom, ${withAlpha(C_BG_DEEP, 0.78)} 0%, ${withAlpha(C_BG_DEEP, 0.12)} 24%, ${withAlpha(C_BG_DEEP, 0.12)} 44%, ${withAlpha(C_BG_DEEP, 0.74)} 76%, ${withAlpha(C_BG_DEEP, 0.97)} 100%)`,
            },
            []
          ),
          // Centre seam scrim so centred text stays readable over both faces
          box(
            {
              position: "absolute", top: "0px", left: "0px", width: "1200px", height: "630px",
              background:
                `linear-gradient(to right, transparent 0%, ${withAlpha(C_BG_DEEP, 0.42)} 36%, ${withAlpha(C_BG_DEEP, 0.55)} 50%, ${withAlpha(C_BG_DEEP, 0.42)} 64%, transparent 100%)`,
            },
            []
          ),
          // Content
          box(
            {
              position: "absolute", top: "0px", left: "0px", width: "1200px", height: "630px",
              flexDirection: "column", justifyContent: "space-between", alignItems: "center", padding: "46px 56px",
            },
            [
              // Top ops wordmark
              box({ alignItems: "center", gap: "10px" }, [
                box({ alignItems: "baseline" }, [
                  span("GTA", { fontSize: "20px", fontWeight: 700, color: C_TEXT_1, letterSpacing: "-0.5px" }),
                  span("VI", { fontSize: "20px", fontWeight: 700, color: C_BRAND, letterSpacing: "-0.5px" }),
                  span(".AI", { fontSize: "11px", fontWeight: 400, color: C_TEXT_4, marginLeft: "4px", letterSpacing: "0.1em" }),
                ]),
                box({ width: "1px", height: "14px", backgroundColor: C_BORDER_2 }, []),
                span("DATA INTELLIGENCE", { fontSize: "11px", fontWeight: 400, color: C_TEXT_4, letterSpacing: "0.15em", textTransform: "uppercase" }),
              ]),
              // Bottom brand block
              box({ flexDirection: "column", alignItems: "center", gap: "16px" }, [
                box(
                  { padding: "5px 12px", borderRadius: "4px", backgroundColor: withAlpha(C_LIVE, 0.18), border: `1px solid ${withAlpha(C_LIVE, 0.5)}` },
                  [span("GTA VI INTELLIGENCE", { fontSize: "12px", fontWeight: 700, color: C_LIVE_BRIGHT, letterSpacing: "0.18em", textTransform: "uppercase" })]
                ),
                box({ alignItems: "baseline", justifyContent: "center" }, [
                  span("GTA", { fontSize: "86px", fontWeight: 700, color: C_TEXT_0, letterSpacing: "-3px" }),
                  span("VI", { fontSize: "86px", fontWeight: 700, color: C_BRAND, letterSpacing: "-3px" }),
                  span(".AI", { fontSize: "40px", fontWeight: 700, color: C_TEXT_2, marginLeft: "8px", letterSpacing: "-1px" }),
                ]),
                box(
                  { fontSize: "22px", fontWeight: 400, color: C_TEXT_1, textAlign: "center", maxWidth: "880px", lineHeight: "1.45", justifyContent: "center" },
                  [HOME_TAGLINE]
                ),
                box({ width: "44px", height: "3px", backgroundColor: C_BRAND, borderRadius: "2px", marginTop: "2px" }, []),
                box({ alignItems: "baseline" }, [
                  span("gtavi.ai", { fontSize: "15px", fontWeight: 400, color: C_TEXT_4, letterSpacing: "0.05em" }),
                  span(" · GTA VI launch Nov 19, 2026", { fontSize: "13px", fontWeight: 400, color: C_TEXT_4, letterSpacing: "0.05em" }),
                ]),
              ]),
            ]
          ),
        ],
      },
    },
    {
      width: 1200,
      height: 630,
      fonts: [
        { name: "Inter", data: bold, weight: 700, style: "normal" },
        { name: "Inter", data: regular, weight: 400, style: "normal" },
      ],
    }
  );

  const resvg = new Resvg(svg, { fitTo: { mode: "width", value: 1200 } });
  const jpgBuffer = await sharp(resvg.render().asPng()).jpeg({ quality: 82, mozjpeg: true }).toBuffer();

  return new Response(jpgBuffer, {
    headers: {
      "Content-Type": "image/jpeg",
      "Cache-Control": "public, max-age=31536000, immutable",
    },
  });
}

// ── OG image renderer ────────────────────────────────────────────────────────

export const GET: APIRoute = async ({ params }) => {
  const page = params.page as string;
  const cfg = PAGES[page];
  if (!cfg) {
    return new Response("Not found", { status: 404 });
  }

  if (page === "home") {
    return renderHomeHero();
  }

  const { bold, regular } = getFonts();
  const imgDataUri = imageToDataUri(cfg.image);

  const svg = await satori(
    {
      type: "div",
      props: {
        style: {
          display: "flex",
          width: "1200px",
          height: "630px",
          backgroundColor: C_BG,
          fontFamily: "Inter",
          position: "relative",
          overflow: "hidden",
        },
        children: [
          // ── Right: character/location image ──────────────────────────
          {
            type: "div",
            props: {
              style: {
                position: "absolute",
                right: "0px",
                top: "0px",
                width: "560px",
                height: "630px",
                overflow: "hidden",
                display: "flex",
              },
              children: [
                {
                  type: "img",
                  props: {
                    src: imgDataUri,
                    style: {
                      width: "560px",
                      height: "630px",
                      objectFit: "cover",
                      objectPosition: "center top",
                    },
                  },
                },
                // Left-to-right gradient overlay (fades image into bg)
                {
                  type: "div",
                  props: {
                    style: {
                      position: "absolute",
                      top: "0px",
                      left: "0px",
                      width: "560px",
                      height: "630px",
                      background:
                        `linear-gradient(to right, ${C_BG} 0%, ${withAlpha(C_BG, 0.55)} 55%, ${withAlpha(C_BG, 0.15)} 100%)`,
                      display: "flex",
                    },
                  },
                },
                // Bottom gradient overlay
                {
                  type: "div",
                  props: {
                    style: {
                      position: "absolute",
                      bottom: "0px",
                      left: "0px",
                      width: "560px",
                      height: "200px",
                      background:
                        `linear-gradient(to top, ${C_BG} 0%, transparent 100%)`,
                      display: "flex",
                    },
                  },
                },
              ],
            },
          },

          // ── Left: content ─────────────────────────────────────────────
          {
            type: "div",
            props: {
              style: {
                position: "absolute",
                left: "0px",
                top: "0px",
                width: "680px",
                height: "630px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                padding: "56px",
              },
              children: [
                // Top: wordmark
                {
                  type: "div",
                  props: {
                    style: {
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                    },
                    children: [
                      {
                        type: "div",
                        props: {
                          style: {
                            display: "flex",
                            alignItems: "baseline",
                            gap: "0px",
                          },
                          children: [
                            {
                              type: "span",
                              props: {
                                style: {
                                  fontFamily: "Inter",
                                  fontWeight: 700,
                                  fontSize: "22px",
                                  letterSpacing: "-0.5px",
                                  color: C_TEXT_4,
                                },
                                children: "GTA",
                              },
                            },
                            {
                              type: "span",
                              props: {
                                style: {
                                  fontFamily: "Inter",
                                  fontWeight: 700,
                                  fontSize: "22px",
                                  letterSpacing: "-0.5px",
                                  color: C_BRAND,
                                },
                                children: "VI",
                              },
                            },
                            {
                              type: "span",
                              props: {
                                style: {
                                  fontFamily: "Inter",
                                  fontWeight: 400,
                                  fontSize: "11px",
                                  color: C_TEXT_5,
                                  marginLeft: "4px",
                                  letterSpacing: "0.1em",
                                },
                                children: ".AI",
                              },
                            },
                          ],
                        },
                      },
                      // Separator
                      {
                        type: "div",
                        props: {
                          style: {
                            width: "1px",
                            height: "16px",
                            backgroundColor: C_BORDER_2,
                            marginLeft: "8px",
                            display: "flex",
                          },
                        },
                      },
                      // "Data intelligence" tagline
                      {
                        type: "span",
                        props: {
                          style: {
                            fontFamily: "Inter",
                            fontWeight: 400,
                            fontSize: "11px",
                            color: C_TEXT_5,
                            letterSpacing: "0.15em",
                            textTransform: "uppercase",
                            marginLeft: "8px",
                          },
                          children: "Data Intelligence",
                        },
                      },
                    ],
                  },
                },

                // Middle: badge + title + description
                {
                  type: "div",
                  props: {
                    style: {
                      display: "flex",
                      flexDirection: "column",
                      gap: "20px",
                    },
                    children: [
                      // Badge
                      {
                        type: "div",
                        props: {
                          style: {
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                          },
                          children: [
                            {
                              type: "div",
                              props: {
                                style: {
                                  display: "flex",
                                  padding: "4px 10px",
                                  borderRadius: "4px",
                                  backgroundColor: cfg.badgeBg,
                                  border: `1px solid ${withAlpha(cfg.badgeColor, 0.25)}`,
                                },
                                children: [
                                  {
                                    type: "span",
                                    props: {
                                      style: {
                                        fontFamily: "Inter",
                                        fontWeight: 700,
                                        fontSize: "11px",
                                        color: cfg.badgeColor,
                                        letterSpacing: "0.15em",
                                        textTransform: "uppercase",
                                      },
                                      children: cfg.badge,
                                    },
                                  },
                                ],
                              },
                            },
                          ],
                        },
                      },

                      // Title
                      {
                        type: "div",
                        props: {
                          style: {
                            fontFamily: "Inter",
                            fontWeight: 700,
                            fontSize: "52px",
                            color: C_TEXT_0,
                            lineHeight: "1.1",
                            letterSpacing: "-1.5px",
                          },
                          children: cfg.title,
                        },
                      },

                      // Description
                      {
                        type: "div",
                        props: {
                          style: {
                            fontFamily: "Inter",
                            fontWeight: 400,
                            fontSize: "17px",
                            color: C_TEXT_3,
                            lineHeight: "1.55",
                            maxWidth: "560px",
                          },
                          children: cfg.desc,
                        },
                      },
                    ],
                  },
                },

                // Bottom: domain + accent line
                {
                  type: "div",
                  props: {
                    style: {
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                    },
                    children: [
                      // Divider
                      {
                        type: "div",
                        props: {
                          style: {
                            width: "40px",
                            height: "2px",
                            backgroundColor: cfg.accent,
                            borderRadius: "2px",
                            display: "flex",
                          },
                        },
                      },
                      // Domain
                      {
                        type: "div",
                        props: {
                          style: {
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                          },
                          children: [
                            {
                              type: "span",
                              props: {
                                style: {
                                  fontFamily: "Inter",
                                  fontWeight: 400,
                                  fontSize: "13px",
                                  color: C_TEXT_5,
                                  letterSpacing: "0.05em",
                                },
                                children: "gtavi.ai",
                              },
                            },
                            {
                              type: "span",
                              props: {
                                style: {
                                  fontFamily: "Inter",
                                  fontWeight: 400,
                                  fontSize: "11px",
                                  color: C_TEXT_5,
                                  letterSpacing: "0.1em",
                                },
                                children: "· GTA VI launch Nov 19, 2026",
                              },
                            },
                          ],
                        },
                      },
                    ],
                  },
                },
              ],
            },
          },

          // ── Subtle vertical grid lines ────────────────────────────────
          {
            type: "div",
            props: {
              style: {
                position: "absolute",
                top: "0px",
                left: "0px",
                width: "1200px",
                height: "630px",
                display: "flex",
                pointerEvents: "none",
                opacity: 0.3,
              },
              children: [
                // Thin accent line along left edge
                {
                  type: "div",
                  props: {
                    style: {
                      position: "absolute",
                      left: "0px",
                      top: "0px",
                      width: "3px",
                      height: "630px",
                      backgroundColor: cfg.accent,
                      opacity: 0.6,
                      display: "flex",
                    },
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
        {
          name: "Inter",
          data: bold,
          weight: 700,
          style: "normal",
        },
        {
          name: "Inter",
          data: regular,
          weight: 400,
          style: "normal",
        },
      ],
    }
  );

  const resvg = new Resvg(svg, {
    fitTo: { mode: "width", value: 1200 },
  });
  const pngData = resvg.render();
  const jpgBuffer = await sharp(pngData.asPng()).jpeg({ quality: 82, mozjpeg: true }).toBuffer();

  return new Response(jpgBuffer, {
    headers: {
      "Content-Type": "image/jpeg",
      "Cache-Control": "public, max-age=31536000, immutable",
    },
  });
};
