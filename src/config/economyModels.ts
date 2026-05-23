/**
 * economyModels.ts — domain config for the 6 GTA circular economy model cards.
 *
 * This is a static data array, NOT a registry. These models appear on fixed,
 * known pages — dynamic discovery is never needed. The array is used by
 * /franchise/economics to enumerate all economy models in order.
 *
 * Each entry carries the metadata needed to render the full card contract:
 * GamePill (via game), section header, CardFooter (via anchorId + shareText).
 */

import type { GameId } from "./allCharts";

export interface EconomyModel {
  /** title_id as used in economy-models.json and CircularEconomy component */
  titleId: string;
  /** GTA game identity — drives GamePill */
  game: GameId | "franchise";
  /** Short display name */
  name: string;
  /** Release year */
  year: number;
  /** Era label (e.g. "Score Counter Era", "First Asset Loop") */
  eraLabel: string;
  /** Standalone economy page URL, or null if no dedicated page */
  page: string | null;
  /** Anchor ID for deep-linking and ShareDropdown */
  anchorId: string;
  /** Share copy for ShareDropdown */
  shareText: string;
  /** Cover image for use in /franchise/economics browser */
  cover: string;
}

export const ECONOMY_MODELS: EconomyModel[] = [
  {
    titleId:   "gta-1-2",
    game:      "franchise",
    name:      "GTA 1 & 2",
    year:      1997,
    eraLabel:  "Score Counter Era",
    page:      null,
    anchorId:  "eco-gta-1-2",
    shareText: "GTA 1 & 2 had no economy — just a score counter. The 30-year arc from extraction to full MMT sovereign management starts here.",
    cover:     "/assets/covers/gta-1.jpg",
  },
  {
    titleId:   "gta-3",
    game:      "gta-iii",
    name:      "GTA III",
    year:      2001,
    eraLabel:  "Mission Economy",
    page:      "/gta-iii/economy",
    anchorId:  "eco-gta-iii",
    shareText: "GTA III's economy: earn → spend → gone. No property, no investment, no compound. The franchise baseline that everything else evolved from.",
    cover:     "/assets/covers/gta-3.jpg",
  },
  {
    titleId:   "gta-vc",
    game:      "gta-vc",
    name:      "Vice City",
    year:      2002,
    eraLabel:  "First Asset Loop",
    page:      "/gta-vc/economy",
    anchorId:  "eco-gta-vc",
    shareText: "GTA Vice City invented the asset ownership loop: earn → buy business → receive passive income. The Malibu Club is the conceptual ancestor of the Acid Lab.",
    cover:     "/assets/economy-thumbs/gta-vc.png",
  },
  {
    titleId:   "gta-sa",
    game:      "gta-sa",
    name:      "San Andreas",
    year:      2004,
    eraLabel:  "Multi-Stream Economy",
    page:      "/gta-sa/economy",
    anchorId:  "eco-gta-sa",
    shareText: "GTA San Andreas: 4 simultaneous income streams — missions, property, gang territory, gambling — plus a proto-stock market. The most complex single-player economy before GTA V.",
    cover:     "/assets/economy-thumbs/gta-sa.png",
  },
  {
    titleId:   "gta-4",
    game:      "gta-iv",
    name:      "GTA IV",
    year:      2008,
    eraLabel:  "Narrative Regression",
    page:      "/gta-iv/economy",
    anchorId:  "eco-gta-iv",
    shareText: "GTA IV stripped every economic mechanic for narrative realism. The franchise low point — but TBOGT's nightclub mechanic planted the seed that became GTA Online's entire business empire.",
    cover:     "/assets/covers/gta-4.jpg",
  },
  {
    titleId:   "gta-5",
    game:      "gta-v",
    name:      "GTA V",
    year:      2013,
    eraLabel:  "Capital Market Recovery",
    page:      "/gta-v/economy",
    anchorId:  "eco-gta-v",
    shareText: "GTA V restored the franchise economy: missions, assassination stock market, heists. The $2B strategy is the most sophisticated single-player money system in GTA history.",
    cover:     "/assets/economy-thumbs/gta-5.png",
  },
  {
    titleId:   "gta-online",
    game:      "gta-online",
    name:      "GTA Online",
    year:      2013,
    eraLabel:  "Full MMT Sovereign",
    page:      "/gta-online/economy",
    anchorId:  "eco-gta-online",
    shareText: "GTA Online is the apex of the franchise arc — a full MMT sovereign economy with live monetary policy. 10 years of data, 5 circular flows, the complete economic model.",
    cover:     "/assets/economy-thumbs/gta-online.png",
  },
  {
    titleId:   "gta-6",
    game:      "gta-vi",
    name:      "GTA VI",
    year:      2026,
    eraLabel:  "Predicted: Enhanced Sovereign",
    page:      "/gta-vi/economy",
    anchorId:  "eco-gta-vi",
    shareText: "GTA VI economy: predicted to surpass GTA Online in complexity. Dual protagonists, Leonida setting, and 13 years of GTA Online refinement as the blueprint.",
    cover:     "/assets/economy-thumbs/gta-6.png",
  },
];

/** Quick lookup by titleId */
export function getEconomyModel(titleId: string): EconomyModel | undefined {
  return ECONOMY_MODELS.find(m => m.titleId === titleId);
}
