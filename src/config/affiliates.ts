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
  amazon_uk:  "gtaviai-21",   // Amazon.co.uk — active
  amazon_de:  "gtaviai0e-21",         // Amazon.de    — active (covers AT)
  amazon_fr:  "gtaviai08-21",         // Amazon.fr    — active
  amazon_jp:  "",             // Amazon.co.jp — join: affiliate.amazon.co.jp
  amazon_br:  "",             // Amazon.com.br — join: associados.amazon.com.br
  amazon_au:  "",             // Amazon.com.au — join: affiliate-program.amazon.com.au
  amazon_ca:  "gtaviai02-20",         // Amazon.ca    — active
  amazon_it:  "gtaviai07-21",         // Amazon.it    — active
  amazon_es:  "gtaviai00-21",         // Amazon.es    — active (covers PT)
  amazon_nl:  "",             // Amazon.nl    — join: partner.amazon.nl
  amazon_mx:  "",             // Amazon.com.mx — join: afiliados.amazon.com.mx
  amazon_in:  "",             // Amazon.in    — join: affiliate-program.amazon.in
  amazon_se:  "",             // Amazon.se    — join: partner.amazon.se
  amazon_pl:  "",             // Amazon.pl    — join: partner.amazon.pl
  amazon_tr:  "",             // Amazon.com.tr — join: gelir-ortakligi.amazon.com.tr
  amazon_sa:  "",             // Amazon.sa    — join: affiliate-program.amazon.sa
  amazon_ae:  "",             // Amazon.ae    — join: affiliate-program.amazon.ae
  amazon_be:  "",             // Amazon.com.be — join: partenaires.amazon.com.be
  amazon_za:  "",             // Amazon.co.za — join: affiliate-program.amazon.co.za

  // ── VPN ────────────────────────────────────────────────────────────────
  nord_vpn:  "150614",  // NordVPN via NordPartners — active
  nord_pass: "150614",  // NordPass via NordPartners — same aff_id, different offer

  // ── Future programmes (add IDs once approved) ─────────────────────────
  // impact_playstation: "",  // via impact.com
  // impact_xbox:        "",  // via impact.com
  // rakuten_game_uk:    "",  // GAME.co.uk via Rakuten Advertising

  // ── FiveM / GTA-RP hosting ────────────────────────────────────────────
  zap_hosting: "tigges-a-4754",  // ZAP-Hosting — active. 50% order commission + 10% renewal
} as const;

/**
 * Specific product affiliate links.
 * Use pre-shortened amzn.to URLs — the affiliate tag is already embedded.
 * Add UK/DE/etc. variants as separate keys when available.
 */
export const PRODUCT_LINKS = {
  /** GTA V – PlayStation 5 (US, Amazon, gtaviai-20) */
  gta5_ps5_us:   "https://amzn.to/4vanPHp",

  /** GTA VI – PlayStation 5 (US, Amazon, tag embedded in amzn.to) */
  gtavi_ps5_us:  "https://amzn.to/4oYu1An",

  /** GTA VI – Xbox Series X|S (US, Amazon, tag embedded in amzn.to) */
  gtavi_xbox_us: "https://amzn.to/4vwccuP",
} as const;

/**
 * GTA VI digital storefronts — direct product URLs by locale.
 *
 * These are official Rockstar / PlayStation / Xbox storefronts; no affiliate
 * tag is appended (the platform programmes — PS Direct via Partnerize,
 * Xbox via Microsoft Affiliate — are still pending). Skimlinks (loaded
 * globally in Base.astro) auto-monetises any commerce link until those
 * direct programmes are wired.
 *
 * Confirmed Xbox product ID for GTA VI is 9nl3wwnzlzzn.
 */
export const GTAVI_STOREFRONTS: Record<string, { ps5: string; xbox: string }> = {
  "en-US": { ps5: "https://www.playstation.com/en-us/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/en-US/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "en-GB": { ps5: "https://www.playstation.com/en-gb/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/en-GB/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "en-CA": { ps5: "https://www.playstation.com/en-ca/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/en-CA/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "en-AU": { ps5: "https://www.playstation.com/en-au/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/en-AU/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "en-IN": { ps5: "https://www.playstation.com/en-in/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/en-IN/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "en-ZA": { ps5: "https://www.playstation.com/en-za/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/en-ZA/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "de":    { ps5: "https://www.playstation.com/de-de/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/de-DE/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "de-AT": { ps5: "https://www.playstation.com/de-at/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/de-AT/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "de-CH": { ps5: "https://www.playstation.com/de-ch/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/de-CH/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "fr":    { ps5: "https://www.playstation.com/fr-fr/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/fr-FR/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "fr-BE": { ps5: "https://www.playstation.com/fr-be/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/fr-BE/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "it":    { ps5: "https://www.playstation.com/it-it/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/it-IT/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "es":    { ps5: "https://www.playstation.com/es-es/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/es-ES/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "es-MX": { ps5: "https://www.playstation.com/es-mx/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/es-MX/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "es-AR": { ps5: "https://www.playstation.com/es-ar/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/es-AR/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "nl":    { ps5: "https://www.playstation.com/nl-nl/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/nl-NL/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "pt":    { ps5: "https://www.playstation.com/pt-br/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/pt-BR/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "pt-PT": { ps5: "https://www.playstation.com/pt-pt/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/pt-PT/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "ja":    { ps5: "https://www.playstation.com/ja-jp/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/ja-JP/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "ko":    { ps5: "https://www.playstation.com/ko-kr/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/ko-KR/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "zh":    { ps5: "https://www.playstation.com/zh-hans-cn/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/zh-CN/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "zh-TW": { ps5: "https://www.playstation.com/zh-hant-tw/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/zh-TW/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "pl":    { ps5: "https://www.playstation.com/pl-pl/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/pl-PL/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "sv":    { ps5: "https://www.playstation.com/sv-se/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/sv-SE/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "tr":    { ps5: "https://www.playstation.com/tr-tr/games/grand-theft-auto-vi/", xbox: "https://www.xbox.com/tr-TR/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "ar-SA": { ps5: "https://store.playstation.com/en-sa/search/Grand%20Theft%20Auto%20VI",  xbox: "https://www.xbox.com/ar-SA/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
  "ar-AE": { ps5: "https://store.playstation.com/en-ae/search/Grand%20Theft%20Auto%20VI",  xbox: "https://www.xbox.com/ar-AE/games/store/grand-theft-auto-vi/9nl3wwnzlzzn" },
};

/** Rockstar Games Store — single global product page. */
export const ROCKSTAR_STORE_URL = "https://www.rockstargames.com/VI";

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
  "www.amazon.ca":     AFFILIATE_IDS.amazon_ca,
  "www.amazon.it":     AFFILIATE_IDS.amazon_it,
  "www.amazon.es":     AFFILIATE_IDS.amazon_es,
  "www.amazon.nl":     AFFILIATE_IDS.amazon_nl,
  "www.amazon.com.mx": AFFILIATE_IDS.amazon_mx,
  "www.amazon.in":     AFFILIATE_IDS.amazon_in,
  "www.amazon.se":     AFFILIATE_IDS.amazon_se,
  "www.amazon.pl":     AFFILIATE_IDS.amazon_pl,
  "www.amazon.com.tr": AFFILIATE_IDS.amazon_tr,
  "www.amazon.sa":     AFFILIATE_IDS.amazon_sa,
  "www.amazon.ae":     AFFILIATE_IDS.amazon_ae,
  "www.amazon.com.be": AFFILIATE_IDS.amazon_be,
  "www.amazon.co.za":  AFFILIATE_IDS.amazon_za,
};

/** Build a ZAP-Hosting affiliate URL with the coupon code embedded. */
export function zapLink(path: string = ""): string {
  const base = `https://zap-hosting.com${path || "/en/gameserver/fivem-server/"}`;
  return `${base}?aff=${AFFILIATE_IDS.zap_hosting}`;
}

/**
 * Build a NordVPN affiliate tracking URL.
 * offer_id=15, url_id=902 (specific landing page for best conversion).
 * Falls back to nordvpn.com if ID is not configured.
 */
export function nordLink(): string {
  const id = AFFILIATE_IDS.nord_vpn;
  if (!id) return "https://nordvpn.com/";
  return `https://go.nordvpn.net/aff_c?offer_id=15&aff_id=${id}&url_id=902`;
}

/**
 * Build a NordPass affiliate tracking URL.
 * offer_id=488, url_id=9356 — NordPass password manager.
 * Falls back to nordpass.com if ID is not configured.
 */
export function nordPassLink(): string {
  const id = AFFILIATE_IDS.nord_pass;
  if (!id) return "https://nordpass.com/";
  return `https://go.nordpass.io/aff_c?offer_id=488&aff_id=${id}&url_id=9356`;
}

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

/**
 * Locale-aware Amazon search URL for GTA VI.
 *
 * Each entry is PRE-TAGGED at the source so that even if client JS fails
 * to run (and the static HTML is the final user link), the affiliate
 * attribution survives. Markets without a direct Associates ID stay
 * untagged here and are monetised via Skimlinks at click time.
 *
 * Defined AFTER `tagAmazonUrl` so the IIFE's reference to `AMAZON_TAG_MAP`
 * is out of TDZ at module-eval time.
 */
export const GTAVI_AMAZON: Record<string, string> = (() => {
  const base: Record<string, string> = {
    "en-US": "https://www.amazon.com/s?k=Grand+Theft+Auto+VI",
    "en-GB": "https://www.amazon.co.uk/s?k=Grand+Theft+Auto+VI",
    "en-CA": "https://www.amazon.ca/s?k=Grand+Theft+Auto+VI",
    "en-AU": "https://www.amazon.com.au/s?k=Grand+Theft+Auto+VI",
    "en-IN": "https://www.amazon.in/s?k=Grand+Theft+Auto+VI",
    "en-ZA": "https://www.amazon.co.za/s?k=Grand+Theft+Auto+VI",
    "de":    "https://www.amazon.de/s?k=Grand+Theft+Auto+VI",
    "de-AT": "https://www.amazon.de/s?k=Grand+Theft+Auto+VI",
    "fr":    "https://www.amazon.fr/s?k=Grand+Theft+Auto+VI",
    "fr-BE": "https://www.amazon.com.be/s?k=Grand+Theft+Auto+VI",
    "it":    "https://www.amazon.it/s?k=Grand+Theft+Auto+VI",
    "es":    "https://www.amazon.es/s?k=Grand+Theft+Auto+VI",
    "es-MX": "https://www.amazon.com.mx/s?k=Grand+Theft+Auto+VI",
    "nl":    "https://www.amazon.nl/s?k=Grand+Theft+Auto+VI",
    "pt":    "https://www.amazon.com.br/s?k=Grand+Theft+Auto+VI",
    "pt-PT": "https://www.amazon.es/s?k=Grand+Theft+Auto+VI",
    "ja":    "https://www.amazon.co.jp/s?k=Grand+Theft+Auto+VI",
    "pl":    "https://www.amazon.pl/s?k=Grand+Theft+Auto+VI",
    "sv":    "https://www.amazon.se/s?k=Grand+Theft+Auto+VI",
    "tr":    "https://www.amazon.com.tr/s?k=Grand+Theft+Auto+VI",
    "ar-SA": "https://www.amazon.sa/s?k=Grand+Theft+Auto+VI",
    "ar-AE": "https://www.amazon.ae/s?k=Grand+Theft+Auto+VI",
  };
  const tagged: Record<string, string> = {};
  for (const [k, v] of Object.entries(base)) tagged[k] = tagAmazonUrl(v);
  return tagged;
})();
