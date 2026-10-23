import type { BusinessProfiles, Business, OnlineHeistsData, OnlineHeist } from "../types/gta";
import businessProfilesRaw from "../../data/gta-5/economy/business-profiles.json";
import onlineHeistsRaw from "../../data/gta-5/economy/online-heists.json";

/** Sources that get a page at /gta-online/income/{id}. */
export const ONLINE_INCOME_SOURCES: (Business | OnlineHeist)[] = (() => {
  const bp = businessProfilesRaw as unknown as BusinessProfiles;
  const hd = onlineHeistsRaw as unknown as OnlineHeistsData;
  const merged: (Business | OnlineHeist)[] = bp.businesses.filter(b => b.net_profit_per_hr > 0);
  hd.heists.forEach(h => { if (!merged.find(b => b.id === h.id)) merged.push(h); });
  return merged;
})();

export const ONLINE_INCOME_PAGE_IDS = new Set(ONLINE_INCOME_SOURCES.map(s => s.id));

export const onlineIncomeHref = (id: string): string | undefined =>
  ONLINE_INCOME_PAGE_IDS.has(id) ? `/gta-online/income/${id}` : undefined;
