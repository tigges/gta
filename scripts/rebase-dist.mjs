#!/usr/bin/env node
/**
 * Rehost a built `dist/` under a sub-path, e.g. https://tigges.github.io/gta/.
 *
 * The site is authored for the domain root (gtavi.ai): ~1,100 root-relative
 * paths across src/ and data/. Rather than threading Astro's `base` through all
 * of them, this rewrites the build output in place:
 *   - absolute https://gtavi.ai URLs (plain, URL-encoded, and the
 *     protocol-less share-link text) → PAGES_ORIGIN + PAGES_BASE
 *   - root-relative "/<top-level entry>" paths → PAGES_BASE + "/<entry>"
 *   - href="/" (home links) → PAGES_BASE + "/"
 *   - dist/CNAME is dropped so the artifact doesn't claim the custom domain
 *   - optional PAGES_HIDE_HOSTS (comma-separated): every page gets a tiny
 *     head script that hides the document when loaded on one of those hosts
 *     (or a subdomain), so a parked domain still pointing here shows nothing
 *
 * Only paths whose first segment is a real top-level entry of dist/ are
 * rewritten, so external URLs and protocol-relative URLs are left alone.
 *
 * Usage: PAGES_BASE=/gta PAGES_ORIGIN=https://tigges.github.io PAGES_HIDE_HOSTS=gtavi.ai \
 *          node scripts/rebase-dist.mjs [dist]
 * A no-op when PAGES_BASE is unset, empty or "/".
 */
import fs from "node:fs";
import path from "node:path";

const DIST = path.resolve(process.argv[2] ?? "dist");
const BASE = (process.env.PAGES_BASE ?? "").replace(/\/+$/, "");
const ORIGIN = (process.env.PAGES_ORIGIN ?? "").replace(/\/+$/, "");

if (!BASE) {
  console.log("rebase-dist: PAGES_BASE not set — leaving dist/ at the domain root");
  process.exit(0);
}
if (!BASE.startsWith("/")) {
  console.error(`rebase-dist: PAGES_BASE must start with "/" (got "${BASE}")`);
  process.exit(1);
}

const TEXT_EXT = new Set([".html", ".js", ".mjs", ".css", ".xml", ".json", ".txt", ".svg", ".webmanifest"]);
const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const tops = fs.readdirSync(DIST).filter((n) => n !== "CNAME");
const topAlt = tops.sort((a, b) => b.length - a.length).map(escapeRe).join("|");

// A root-relative path starts right after a quote, backtick, "(", "=", ",",
// whitespace or an HTML-escaped quote, and its first segment must end at a
// path/URL/string boundary so "/gta-vi" never matches a "/gta-vi-foo" entry.
const PREFIX = String.raw`(["'\x60(=,\s]|&quot;|&#34;|&#39;|&#x27;)`;
const rootRel = new RegExp(`${PREFIX}/(${topAlt})(?=[/"'\x60?#)\\s&,;]|$)`, "g");
const homeHref = /(\bhref=)(["'])\/\2/g;
const absSite = /https?:\/\/(?:www\.)?gtavi\.ai(?=[/"'\x60?#)\s&,;<]|$)/g;
const absSiteEncoded = /https?%3A%2F%2F(?:www\.)?gtavi\.ai/gi;
// ShareDropdown prints the share URL without its protocol as link text.
const displaySite = />gtavi\.ai\//g;
const target = `${ORIGIN}${BASE}`;

const hideHosts = (process.env.PAGES_HIDE_HOSTS ?? "").split(",").map((h) => h.trim().toLowerCase()).filter(Boolean);
const hideGuard = hideHosts.length
  ? `<script>if(/(^|\\.)(${hideHosts.map(escapeRe).join("|")})$/i.test(location.hostname))document.documentElement.style.display="none"</script>`
  : "";
const headOpen = /<head(\s[^>]*)?>/i;
const doctype = /^<!doctype html>/i;
const targetDisplay = target.replace(/^https?:\/\//, "");

let filesChanged = 0;
let replacements = 0;

function rewrite(file) {
  const src = fs.readFileSync(file, "utf8");
  let n = 0;
  let out = src.replace(rootRel, (_m, pre, top) => { n++; return `${pre}${BASE}/${top}`; });
  out = out.replace(homeHref, (_m, attr, q) => { n++; return `${attr}${q}${BASE}/${q}`; });
  if (ORIGIN) {
    out = out.replace(absSite, () => { n++; return target; });
    out = out.replace(absSiteEncoded, () => { n++; return encodeURIComponent(target); });
    out = out.replace(displaySite, () => { n++; return `>${targetDisplay}/`; });
  }
  if (hideGuard && file.endsWith(".html")) {
    if (headOpen.test(out)) out = out.replace(headOpen, (m) => m + hideGuard);
    else if (doctype.test(out)) out = out.replace(doctype, (m) => m + hideGuard);
    else out = hideGuard + out;
    n++;
  }
  if (out !== src) {
    fs.writeFileSync(file, out);
    filesChanged++;
    replacements += n;
  }
}

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(p);
    else if (TEXT_EXT.has(path.extname(entry.name).toLowerCase())) rewrite(p);
  }
}

walk(DIST);
fs.rmSync(path.join(DIST, "CNAME"), { force: true });

console.log(`rebase-dist: ${replacements} rewrites in ${filesChanged} files → ${target || BASE}/`);
