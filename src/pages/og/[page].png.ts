import type { APIRoute } from "astro";
import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import { readFileSync } from "fs";
import { join } from "path";

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
    badgeColor: "#0d9488",
    badgeBg: "rgba(13,148,136,0.15)",
    title: "GTA VI.AI",
    desc: "Data-driven intelligence across every GTA generation — live signals, franchise analytics, and what the numbers say about GTA VI.",
    image: "assets/gta6/characters/Lucia_Caminos_01.jpg",
    accent: "#f59e0b",
  },
  "vi-intel": {
    badge: "VI Intel",
    badgeColor: "#f59e0b",
    badgeBg: "rgba(245,158,11,0.15)",
    title: "GTA VI Intelligence",
    desc: "Character profiles, location mapping, predictions, and trailer analysis — everything confirmed about GTA VI.",
    image: "assets/gta6/characters/Jason_Duval_01.jpg",
    accent: "#f59e0b",
  },
  charts: {
    badge: "Charts",
    badgeColor: "#818cf8",
    badgeBg: "rgba(129,140,248,0.15)",
    title: "Franchise Charts",
    desc: "D3-powered analytics: YouTube velocity, Google Trends, Take-Two stock, and GTA VI search interest vs every prior launch.",
    image: "assets/gta6/locations/Vice_City_01.jpg",
    accent: "#818cf8",
  },
  database: {
    badge: "Database",
    badgeColor: "#0d9488",
    badgeBg: "rgba(13,148,136,0.15)",
    title: "GTA Database",
    desc: "665 Broughy-tested GTA V vehicles · 1,715 GTA VI entities · news archive and franchise data — all in one place.",
    image: "assets/gta6/characters/Raul_Bautista_01.jpg",
    accent: "#0d9488",
  },
  franchise: {
    badge: "Franchise",
    badgeColor: "#a78bfa",
    badgeBg: "rgba(167,139,250,0.15)",
    title: "Franchise History",
    desc: "30 years of GTA quantified — sales velocity, review scores, map growth, DLC history and the economics behind GTA VI.",
    image: "assets/gta6/locations/Port_Gellhorn_03.jpg",
    accent: "#a78bfa",
  },
  news: {
    badge: "News",
    badgeColor: "#22c55e",
    badgeBg: "rgba(34,197,94,0.15)",
    title: "GTA VI News",
    desc: "Rockstar Newswire headlines and community intelligence — everything that matters about GTA VI, filtered and curated.",
    image: "assets/gta6/locations/Leonida_Keys_01.jpg",
    accent: "#22c55e",
  },
  buy: {
    badge: "Buy GTA VI",
    badgeColor: "#f59e0b",
    badgeBg: "rgba(245,158,11,0.15)",
    title: "Buy GTA VI",
    desc: "GTA VI editions, platforms, retailers, and pre-order bonuses — your complete guide to launch day.",
    image: "assets/gta6/characters/Lucia_Caminos_02.jpg",
    accent: "#f59e0b",
  },
  predictions: {
    badge: "Predictions",
    badgeColor: "#f59e0b",
    badgeBg: "rgba(245,158,11,0.15)",
    title: "GTA VI Predictions",
    desc: "Data-backed predictions for GTA VI — sales trajectory, mechanics, pricing, and launch performance.",
    image: "assets/gta6/characters/Jason_Duval_02.jpg",
    accent: "#f59e0b",
  },
  "gta-v": {
    badge: "GTA V Data",
    badgeColor: "#0d9488",
    badgeBg: "rgba(13,148,136,0.15)",
    title: "GTA V Economics",
    desc: "Mission earnings, heist payouts, assassination stock guide, vehicle benchmarks, and 11 years of Steam data — the blueprint for GTA VI.",
    image: "assets/gta6/locations/Ambrosia_01.jpg",
    accent: "#0d9488",
  },
  "economy": {
    badge: "Macro Model",
    badgeColor: "#818cf8",
    badgeBg: "rgba(129,140,248,0.15)",
    title: "Five Flows. One Economy.",
    desc: "The GTA Online circular economy model — wages, spending, savings, Shark Card injections and the GTA-PPI purchasing power index.",
    image: "assets/gta5/story/gta-v-cover.jpg",
    accent: "#818cf8",
  },
  leaderboard: {
    badge: "Community · Opt-in",
    badgeColor: "#22c55e",
    badgeBg: "rgba(34,197,94,0.15)",
    title: "Income Leaderboard",
    desc: "GTA Online players sharing their personalised $/hr stacks. Built with the GTAVI.AI Income Adviser. Where do you rank?",
    image: "assets/gta6/locations/Vice_City_01.jpg",
    accent: "#22c55e",
  },
  "gta-iii-eco": {
    badge: "GTA III · 2001",
    badgeColor: "#9898b8",
    badgeBg: "rgba(152,152,184,0.12)",
    title: "GTA III Economy",
    desc: "The proto-economy: mission pay → spending. One-way flow, no investment layer, no Shark Cards. The origin of 25 years of GTA economics.",
    image: "assets/gta6/locations/Ambrosia_01.jpg",
    accent: "#9898b8",
  },
  "gta-vc-eco": {
    badge: "Vice City · 2002",
    badgeColor: "#ff2d78",
    badgeBg: "rgba(255,45,120,0.12)",
    title: "Vice City Economy",
    desc: "GTA's first passive income layer — property investment, business ownership and the first circular money flow. The blueprint for GTA Online.",
    image: "assets/gta6/locations/Vice_City_03.jpg",
    accent: "#ff2d78",
  },
  "gta-sa-eco": {
    badge: "San Andreas · 2004",
    badgeColor: "#c0392b",
    badgeBg: "rgba(192,57,43,0.12)",
    title: "San Andreas Economy",
    desc: "Multi-stream income: gang territory, gambling, properties, stock market. The most complex single-player GTA economy before GTA Online.",
    image: "assets/gta6/locations/Grassrivers_01.jpg",
    accent: "#c0392b",
  },
  "gta-iv-eco": {
    badge: "GTA IV · 2008",
    badgeColor: "#6b6b7e",
    badgeBg: "rgba(107,107,126,0.12)",
    title: "GTA IV Economy",
    desc: "The intentional regression — narrative realism over economic complexity. Rockstar stripped 6 years of innovation for Liberty City authenticity.",
    image: "assets/gta6/locations/Port_Gellhorn_01.jpg",
    accent: "#6b6b7e",
  },
  "gta-v-eco": {
    badge: "GTA V Story · 2013",
    badgeColor: "#f59e0b",
    badgeBg: "rgba(245,158,11,0.15)",
    title: "GTA V Economy",
    desc: "Mission earnings, heist payouts, assassination stock guide, and the BAWSAQ market. The story-mode counterpart to GTA Online's live economy.",
    image: "assets/gta5/story/gta-v-cover.jpg",
    accent: "#f59e0b",
  },
  "income-adviser": {
    badge: "GTA Online · Adviser",
    badgeColor: "#0d9488",
    badgeBg: "rgba(13,148,136,0.15)",
    title: "Income Stack Adviser",
    desc: "Select your businesses, get your personalised $/hr total and the highest-ROI next purchase. Built on Broughy benchmarks and community data.",
    image: "assets/gta5/dlc/cayo-perico.jpg",
    accent: "#0d9488",
  },
  "cayo-perico": {
    badge: "GTA Online · S+ Tier",
    badgeColor: "#22c55e",
    badgeBg: "rgba(34,197,94,0.15)",
    title: "Cayo Perico Heist Guide",
    desc: "The best solo money method in GTA Online — $1,200K/hr+. Loot tiers, optimal strategy, setup cost and break-even. Updated 2026.",
    image: "assets/gta5/dlc/cayo-perico.jpg",
    accent: "#22c55e",
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

// ── OG image renderer ────────────────────────────────────────────────────────

export const GET: APIRoute = async ({ params }) => {
  const page = params.page as string;
  const cfg = PAGES[page];
  if (!cfg) {
    return new Response("Not found", { status: 404 });
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
          backgroundColor: "#0e0e11",
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
                        "linear-gradient(to right, #0e0e11 0%, rgba(14,14,17,0.55) 55%, rgba(14,14,17,0.15) 100%)",
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
                        "linear-gradient(to top, #0e0e11 0%, transparent 100%)",
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
                                  color: "#71717a",
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
                                  color: "#f59e0b",
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
                                  color: "#52525b",
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
                            backgroundColor: "#2a2a31",
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
                            color: "#3f3f46",
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
                                  border: `1px solid ${cfg.badgeColor}40`,
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
                            color: "#fafafa",
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
                            color: "#71717a",
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
                                  color: "#52525b",
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
                                  color: "#3f3f46",
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
  const pngBuffer = pngData.asPng();

  return new Response(pngBuffer, {
    headers: {
      "Content-Type": "image/png",
      "Cache-Control": "public, max-age=31536000, immutable",
    },
  });
};
