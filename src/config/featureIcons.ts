/**
 * featureIcons.ts — GTA VI feature-tracker category → HudIcon name.
 *
 * Maps each features.json category id to a brand HUD pictogram (HudIcon),
 * replacing the emoji icons. Single source of truth so the homepage teaser
 * and the full /gta-vi/intel tracker stay in sync.
 */
export const FEATURE_CATEGORY_ICON: Record<string, string> = {
  regions:    "map-pin",     // location pin
  vehicles:   "car",
  characters: "users",
  weapons:    "ammo",        // ammunition / weapon
  businesses: "briefcase",
  activities: "star",        // activities / events
  wildlife:   "shark",       // animal (brand HUD icon)
  online:     "hub",         // online layer / overview
};
