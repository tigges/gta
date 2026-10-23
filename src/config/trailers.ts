import type { Trailer, TrailerType } from "../types/gta";
import trailersRaw from "../../data/gta-6/trailers.json";

// Mirrors MAIN_TYPES in scrapers/gtavi/fetch_trailers.py. Announcement cards,
// ad spots and alternate uploads are tracked but never counted as trailers.
export const MAIN_TRAILER_TYPES: ReadonlySet<TrailerType> = new Set<TrailerType>([
  "trailer",
  "extended_look",
  "launch_trailer",
  "gameplay",
]);

export const isMainTrailer = (t: Pick<Trailer, "type">): boolean =>
  MAIN_TRAILER_TYPES.has(t.type ?? "trailer");

export const ALL_TRAILERS = trailersRaw.trailers as unknown as Trailer[];
export const MAIN_TRAILERS = ALL_TRAILERS.filter(isMainTrailer);
export const MAIN_TRAILER_IDS = new Set(MAIN_TRAILERS.map((t) => t.youtube_id));
