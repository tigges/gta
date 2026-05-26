/**
 * GTAVI.AI — Affiliate link configuration.
 *
 * Affiliate IDs per programme. Add a country's tag once you join that
 * programme — until then the helper returns the base URL unmodified so
 * links stay live and functional.
 *
 * Amazon Associates IDs are region-specific; join each country's
 * programme separately at affiliate-program.amazon.[tld].
 *
 * FTC / ASA disclosure: all pages that render affiliate links must
 * include the disclosure statement. The AffiliateDisclosure component
 * handles this — import and render it on any page with affiliate links.
 */

export const AFFILIATE_IDS = {
  // ── Amazon Associates ──────────────────────────────────────────────────
  amazon_us:  "gtaviai-20",   // Amazon.com   — active
  amazon_uk:  "",             // Amazon.co.uk — join: affiliate-program.amazon.co.uk
  amazon_de:  "",             // Amazon.de    — join: affiliate-program.amazon.de
  amazon_fr:  "",             // Amazon.fr    — join: partenaires.amazon.fr
  amazon_jp:  "",             // Amazon.co.jp — join: affiliate.amazon.co.jp
  amazon_br:  "",             // Amazon.com.br — join: associados.amazon.com.br
  amazon_au:  "",             // Amazon.com.au — join: affiliate-program.amazon.com.au

  // ── Future programmes (add IDs once approved) ─────────────────────────
  // impact_playstation: "",  // via impact.com
  // impact_xbox:        "",  // via impact.com
  // rakuten_game_uk:    "",  // GAME.co.uk via Rakuten Advertising
} as const;

/** Append an Amazon affiliate tag to a URL if an ID is configured. */
export function amazonLink(url: string, tag: string): string {
  if (!tag) return url;           // no tag → return clean URL (still functional)
  const u = new URL(url);
  u.searchParams.set("tag", tag);
  return u.toString();
}

/**
 * Map from Amazon store hostname to affiliate tag.
 * Used to auto-tag any Amazon URL on the buy page.
 */
export const AMAZON_TAG_MAP: Record<string, string> = {
  "www.amazon.com":    AFFILIATE_IDS.amazon_us,
  "www.amazon.co.uk":  AFFILIATE_IDS.amazon_uk,
  "www.amazon.de":     AFFILIATE_IDS.amazon_de,
  "www.amazon.fr":     AFFILIATE_IDS.amazon_fr,
  "www.amazon.co.jp":  AFFILIATE_IDS.amazon_jp,
  "www.amazon.com.br": AFFILIATE_IDS.amazon_br,
  "www.amazon.com.au": AFFILIATE_IDS.amazon_au,
};

/** Apply the correct affiliate tag to any Amazon URL automatically. */
export function tagAmazonUrl(url: string): string {
  try {
    const u = new URL(url);
    const tag = AMAZON_TAG_MAP[u.hostname];
    return tag ? amazonLink(url, tag) : url;
  } catch {
    return url;
  }
}
