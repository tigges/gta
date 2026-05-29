# AGENTS.md — GTAVI.AI

Agent and developer reference for the [gtavi.ai](https://gtavi.ai) repository.

---

## Project overview

**GTAVI.AI** is a static Astro 4 site providing data-driven intelligence about the GTA franchise and GTA VI.
It is deployed via GitHub Pages on every push to `main`. A nightly GitHub Actions job refreshes live data.

- **Live site:** https://gtavi.ai
- **Current version:** tracked in `src/config/version.ts`
- **Stack:** Astro 4 · TypeScript (strict) · Tailwind CSS · D3.js · Python 3.12 (scrapers)

---

## Repository layout

```
src/
  pages/          Astro pages (one file = one route)
  components/     Shared Astro components
  layouts/        Base.astro — nav, meta, fonts, ops bar
  config/         version.ts, games.ts — static constants
  types/          gta.ts — shared TypeScript interfaces

data/
  gta-5/          GTA V data (vehicles, steam, trends, dlc, businesses, meta)
  gta-6/          GTA VI data (trailers, predictions, trends, entities, delay-timeline)
  franchise/      Cross-game data (sales, metacritic, igdb, cpi, spotify, competitors, ttwo-stock)
  feeds/          News feeds (newswire.json)
  community/      Community data (reddit.json)
  shared/         releases.json — canonical franchise release history

scrapers/
  fetch_*.py      Python scrapers (see table below)
  gtavi/          GTA VI specific scrapers
  utils.py        Shared helpers: write_json, has_changed, load_existing, now_iso

.github/
  workflows/
    static.yml        Build & deploy to GitHub Pages (triggers on push to main)
    fetch-data.yml    Nightly data refresh (cron 03:00 UTC)
```

---

## Local development

```bash
npm install
npm run dev        # dev server at http://localhost:4321
npm run build      # build to dist/
npm run preview    # preview built site
```

Python scrapers (run individually):
```bash
pip install -r requirements.txt
python3 scrapers/fetch_ttwo_stock.py
python3 scrapers/fetch_newswire.py
# etc.
```

---

## Environment variables / secrets

| Secret | Used by | Required |
|--------|---------|----------|
| `BROUGHY_SHEET_ID` | `fetch_vehicles.py` | Yes (vehicle data) |
| `YOUTUBE_API_KEY` | `fetch_trailers.py`, `fetch_youtube_velocity.py` | Yes (trailer/velocity data) |
| `TWITCH_CLIENT_ID` | `fetch_igdb.py` | Yes (IGDB franchise metadata) |
| `TWITCH_CLIENT_SECRET` | `fetch_igdb.py` | Yes (IGDB franchise metadata) |
| `SPOTIFY_CLIENT_ID` | `fetch_spotify.py` | Yes (GTA radio playlists) |
| `SPOTIFY_CLIENT_SECRET` | `fetch_spotify.py` | Yes (GTA radio playlists) |
| `REDDIT_CLIENT_ID` | `fetch_reddit.py` | No — RSS fallback active |
| `REDDIT_CLIENT_SECRET` | `fetch_reddit.py` | No — RSS fallback active |
| `DISCORD_WEBHOOK_URL` | `post_discord_digest.py` | No — digest skipped if absent |
| `RESEND_API_KEY` | `post_weekly_digest_resend.py` | No — digest skipped if absent |
| `RESEND_AUDIENCE_ID` | `post_weekly_digest_resend.py`, `functions/api/subscribe.ts` | No — skipped if absent. Create at resend.com → Audiences |

Secrets are configured in: **GitHub repo → Settings → Secrets and variables → Actions**

For local scraper runs requiring secrets, set them as environment variables:
```bash
export YOUTUBE_API_KEY=...
python3 scrapers/fetch_trailers.py
```

---

## Scrapers reference

| Scraper | Output file | Nightly CI | Notes |
|---------|-------------|:----------:|-------|
| `fetch_vehicles.py` | `gta-5/vehicles/performance.json` | ✅ | Needs `BROUGHY_SHEET_ID` |
| `fetch_steam.py` | `gta-5/meta/steam-players.json` | ✅ | Steam API |
| `fetch_trends.py` | `gta-5/trends/search-interest.json` | ✅ | Google Trends via pytrends |
| `gtavi/fetch_trailers.py` | `gta-6/trailers.json` | ✅ | Needs `YOUTUBE_API_KEY` |
| `gtavi/fetch_search_trends.py` | `gta-6/trends/search-interest.json` | ✅ | Google Trends |
| `fetch_youtube_velocity.py` | `gta-6/trailer-velocity.json` | ✅ | Needs `YOUTUBE_API_KEY`; falls back to page scrape |
| `fetch_ttwo_stock.py` | `franchise/ttwo-stock.json` | ✅ | Yahoo Finance; no API key |
| `fetch_franchise_sales.py` | `franchise/sales.json` | ✅ | Curated seed + VGChartz enrichment |
| `fetch_reddit.py` | `community/reddit.json` | ✅ | Needs Reddit creds for live count; RSS fallback for posts |
| `fetch_newswire.py` | `feeds/newswire.json` | ✅ | Multi-source: Rockstar, EDGAR 8-K, Kotaku, Rockstar Intel, Variety, The Game Business; GTAForums curated seed fallback |
| `fetch_conference_news.py` | `feeds/conference-news.json` | ✅ | YouTube conference channel watcher; needs `YOUTUBE_API_KEY` |
| `fetch_preorder_listings.py` | `feeds/preorder-listings.json` | ✅ | Retailer listing monitor; PS Store wishlist live as of May 2026 |
| `fetch_metacritic.py` | `franchise/metacritic.json` | ❌ | Curated seed — run manually if scores change |
| `fetch_igdb.py` | `franchise/igdb.json` | ✅ | Needs `TWITCH_CLIENT_ID` + `TWITCH_CLIENT_SECRET` |
| `fetch_spotify.py` | `franchise/spotify.json` | ✅ | Needs `SPOTIFY_CLIENT_ID` + `SPOTIFY_CLIENT_SECRET` |
| `fetch_steamdb.py` | `gta-5/meta/steamdb.json` | ❌ | SteamDB blocks server IPs; curated seed |
| `fetch_spotify.py` | `franchise/spotify.json` | ✅ | Needs `SPOTIFY_CLIENT_ID` + `SPOTIFY_CLIENT_SECRET` |
| `fetch_steamdb.py` | `gta-5/meta/steamdb.json` | ❌ | SteamDB blocks server IPs; curated seed |
| `fetch_spotify.py` | `franchise/spotify.json` | ❌ | Curated seed |
| `fetch_boxoffice.py` | `franchise/entertainment-comps.json` | ✅ | Box Office Mojo scrape |
| `fetch_edgar.py` | `franchise/cpi.json`, `revenue-split.json` | ✅ | SEC EDGAR |
| `fetch_vgchartz.py` | `franchise/vgchartz.json` | ❌ | Run manually if data drift |
| `fetch_leonida.py` | `gta-6/entities/leonida-intel.json` | ✅ | Leonida Intel public API; no auth |
| `post_discord_digest.py` | Discord webhook | ✅ | Runs after commit; needs `DISCORD_WEBHOOK_URL`; `continue-on-error: true` |
| `post_weekly_digest_resend.py` | Resend email → subscribers | ✅ | Every Tuesday 10:00 UTC via `weekly-digest.yml`; needs `RESEND_API_KEY` + `RESEND_AUDIENCE_ID` |
| `fetch_gta_wiki.py` | `gta-6/entities/*.json` | ❌ | Run manually after major reveals |
| `fetch_press_assets.py` | `gta-6/press-assets.json` | ❌ | Run manually after press drops |

---

## Release process — MANDATORY, every session, no exceptions

Every agent session that ships code **must** complete all five steps below before the session ends.
Do not wait to be asked. Do not leave main behind. Ship it.

### Steps (execute in order)

1. **Tag current `main`** with `release/v{current_version}` before creating a feature branch.
   ```bash
   git tag release/v1.X.Y origin/main && git push origin release/v1.X.Y
   ```

2. **Create a feature branch**, do work, commit with clear messages.

3. **Bump `src/config/version.ts`** in the feature branch.
   - Patch (`1.5.0 → 1.5.1`) — fixes, data-only, minor UI tweaks
   - Minor (`1.5.0 → 1.6.0`) — new features, pages, charts, scrapers
   - Major (`1.x → 2.0`) — full redesigns
   - Also update `SITE_VERSION_DATE` to today (`YYYY-MM-DD`).
   - Commit: `chore: bump version to v1.X.Y`

4. **Merge to `main` and push** — this triggers GitHub Actions and puts the release live.
   ```bash
   git checkout main
   git merge --no-ff <feature-branch> -m "<release title>"
   git push origin main
   ```
   There is no branch protection on `main`. Do not create a draft PR and stop — always complete the merge.

5. **Verify deploy** — run `gh run list --limit 3` and confirm the Pages deploy is queued or running.

### Example (full flow)

```bash
# 1. Bookmark current main
git tag release/v1.6.0 origin/main && git push origin release/v1.6.0

# 2. Feature branch
git checkout -b cursor/my-feature-c815

# 3. ... do work, commit ...

# 4. Bump version
# src/config/version.ts: SITE_VERSION = "1.7.0", SITE_VERSION_DATE = "2026-05-14"
git commit -m "chore: bump version to v1.7.0"

# 5. Merge and deploy
git checkout main
git merge --no-ff cursor/my-feature-c815 -m "feat: v1.7.0 — description"
git push origin main   # ← triggers GitHub Actions deploy automatically

# 6. Verify
gh run list --limit 3
```

The version is displayed in the ops bar on every page (`Base.astro`) and in the footer — it should read the new version immediately after deploy.

> **MANDATORY — no exceptions:** Every single commit that touches code, data, scrapers, or UI — including bug fixes, one-liners, and CI tweaks — must bump `src/config/version.ts` before being pushed to `main`. Patch bump (x.y.Z+1) for fixes and minor tweaks; minor bump (x.Y+1.0) for new features or charts; major bump (X+1.0.0) for full redesigns. Also update `SITE_VERSION_DATE` to today's date (YYYY-MM-DD). Forgetting the version bump is the most common agent error on this project.

---

## Git & branch conventions

- All agent branches use prefix `cursor/` and suffix `-c815`
  Example: `cursor/my-feature-c815`
- Branch names must be **lowercase**
- One logical change per commit with a descriptive message
- **Every commit to `main` must include a `src/config/version.ts` bump** — patch, minor, or major depending on scope. No exceptions, including single-file bug fixes.
- After merging to main, a PR can optionally be opened for record-keeping, but the merge to main always happens first
- The nightly data bot commits with `[skip ci]` to avoid triggering redundant builds

---

## Data update patterns

### Adding a new scraper to nightly CI

1. Write the scraper in `scrapers/` following the pattern in `utils.py` (`write_json`, `has_changed`, `now_iso`)
2. Test locally: `python3 scrapers/fetch_my_thing.py`
3. Add a step to `.github/workflows/fetch-data.yml` in the appropriate section
4. If a new secret is needed, document it in the table above and in this file

### Adding new charts

Charts live in `src/pages/charts.astro` as self-contained D3 sections.
Import the data file at the top, add an HTML container (`<div id="my-chart">`), and write the D3 initialisation in the `<script>` block using the `data-*` attribute pattern already established.

### GTA VI income predictions

Edit `data/gta-6/income-predictions.json`. Schema version `1.0`. Rendered by `IncomePredictionCard.astro` on `/gta-vi/intel`.

```jsonc
{
  "id": "vi-*",
  "name": "",
  "category": "",              // "heist" | "business" | "passive" | "mission"
  "region": "",                // "vice-city" | "leonida" | "both"
  "confidence_tier": "",       // "confirmed" | "reported" | "predicted"
  "confidence_score": 0,       // 0–100
  "thumbnail": null,           // /assets/gta6/... path
  "trailer_evidence": null,    // "T2 — 0:15" or null
  "predicted_payout_per_run": null,
  "predicted_gta_per_hr": null,
  "analogous_gta_online": null, // business-profiles.json id or null
  "basis": "",
  "prediction_range": { "low": "", "high": "" }
}
```

### Updating predictions

Edit `data/gta-6/predictions.json`. Schema version is `2.0`. Required fields per prediction:

```jsonc
{
  "id": "pred-*",
  "title": "",
  "value": "",
  "unit": null,
  "confidence": 0,           // 0–100
  "confidence_tier": "",     // "confirmed" | "reported" | "predicted"
  "basis": "",
  "trailer_timestamp": null,
  "prediction_method": null,
  "prediction_inputs": [],
  "prediction_range": { "low": "", "high": "" },
  "outcome_verified": false,
  "outcome_actual": null,
  "outcome_date": null,
  "source": "",
  "source_type": ""          // "official" | "reported" | "predicted"
}
```

---

## Central design system — UI components

All pages must use these canonical components. Never rebuild these patterns inline.

### Layout / structure

| Component | Props | Purpose |
|---|---|---|
| `SectionHeader.astro` | `label`, `dotColor?`, `pillHref?`, `pillLabel?` | `// SECTION TITLE` header row used on every section. Automatically switches to `justify-between` split variant when pill is present. `label` must include `// ` prefix. |
| `StatBox.astro` | `value`, `label`, `sub?`, `color?` | Single key-metric card. Used in hero stat strips, Health Monitor, database. |
| `CardFooter.astro` | `chartId?` or `anchorId+sources+shareText` | Standard `source · GTAVI.AI · Share` footer on all cards and chart sections. |
| `CrossLinks.astro` | `context` | Site-wide "Related Intelligence" bottom strip. |

### Chart teasers / content cards

| Component | Props | Purpose |
|---|---|---|
| `ChartBadgeRow.astro` | `game`, `category`, `fullHref?`, `fullLabel?` | `[GamePill] [Category]` header row for all chart teasers. Renders at `text-[9px]`. Full link goes top-right if supplied. |
| `ReadItBlock.astro` | `accentColor?`, `showPrefix?` | Left-border annotation block. Slot = paragraph text. "Read it:" prefix rendered automatically. |
| `GamePill.astro` | `game`, `size?` | Game identity pill. Always `size="xs"` inside cards, `size="sm"` in hero pill row. |
| `ShareDropdown.astro` | `anchorId`, `shareText`, `size?` | Share button. Always `size="sm"`. Part of every card footer. |

### Section header rules (P5)

**Section headers** (`SectionHeader`) use a `w-1.5 h-1.5` round dot.
**CrossLinks strip** uses a `w-1 h-4` rectangular bar — intentionally distinct as it's a cross-page navigation pattern, not a content section header.

### "Full XYZ →" link placement rule (P2)

- **If top-right of the card is free** (no tier pill, no game pill): `Full chart →` goes in `ChartBadgeRow` via `fullHref` prop (top-right of header).
- **If top-right is occupied** (e.g. PredictionCard's tier pill): `Full analysis →` or `Full chart →` goes in the card **footer**, left side of the `GTAVI.AI + Share` bar.
- **Section headers**: `pillLabel` in `SectionHeader` for section-level links (`All N charts →`, `Full model →`, etc.).

### Token rules (P1 — no exceptions)

**Never write a raw hex value anywhere in a component or page template.** If a colour is not yet in the token system, add it to `src/styles/tokens.css` AND `src/config/colors.ts` first.

| Raw value (BANNED) | Token to use |
|---|---|
| `#1e1e23` | `var(--c-border-1)` · Tailwind: `border-border-dim` |
| `#2a2a31` | `var(--c-border-2)` · Tailwind: `border-border-mid` |
| `#131316` | `var(--c-card)` |
| `#1a1a1e` | `var(--c-card-raised)` |
| `#0e0e11` | `var(--c-bg)` |
| `#0a0a0d` | `var(--c-bg-deep)` |
| Any `rgba(...)` that approximates a token | Use `color-mix(in srgb, var(--c-*) N%, transparent)` |

D3/JS runtime colours must come from `src/config/colors.ts` named exports (`C_BRAND`, `C_LIVE`, etc.). Never write hex in a `<script>` block.

### Minimum contrast rule (P1 — no exceptions)

**`--c-text-5` is the dim floor for all readable text.** Nothing goes below it.

- `--c-text-6` has been **removed** from the token system. Do not add it back.
- `--c-watermark` exists solely for D3 SVG watermark stamps (the tiny `GTAVI.AI` corner text in charts). Never use it on HTML text.
- Tailwind `text-zinc-600` and `text-zinc-700` both map to `--c-text-5` — the floor.
- If text would be too dim at `--c-text-5`, **omit the text entirely** rather than dimming it further.

### Minimum font size rule (P1 — no exceptions)

**9px is the minimum font size for any readable text.** Use `text-[9px]` or larger. The 7px and 8px scales are banned for text content. They may only appear in CSS comments, SVG attributes set by D3, or `font-size` properties on non-text decorative SVG elements.

### Pill text size rule (P4)

All pill links in section headers and card footers: **`text-[10px]`**. No exceptions.

---

## Simplified Economy Diagram (SED)

The SED is the **canonical, title-neutral visual representation of GTA's circular economy**.
It is the base model from which per-title variants will be derived. Never game-specific.

**Formula:** `(J) + Y = C + I`

| Symbol | Name | Role | Token | Colour |
|---|---|---|---|---|
| J | Injection | Exogenous — real money → GTA$ (Shark Cards, GTA+) | `--c-flow-injection` | Cyan |
| Y | Income | Earned in-game — missions, passive, heists | `--c-gta-dollar` | Green |
| C | Consumption | Non-returning spend — clothing, ammo | `--c-flow-spending` | Orange |
| I | Investment | Capital spend returning to Y — businesses, property | `--c-economy` | Indigo |
| GTA$ | Currency hub | The shared in-game currency | `--c-gta-dollar` | Green |

**Simplification levels (same diagram, different decomposition of right side):**
```
Income = Expense               ← Level 1 — binary left/right
Y = C + I                      ← Level 2 — three components
(J) + Y = C + I                ← THE SED — full base model, all four dimensions
Per-title variants             ← SED + title-specific actors, complexity, annotations
```

**Component:** `src/components/EconomyCircleSED.astro`
- `EconomyCircle.astro` is retired — use `EconomyCircleSED.astro` everywhere
- Used on hub pages (`/gta-vi`, `/gta-online`) to introduce the economy before the full `CircularEconomy` node graph

**Rules:**
- No game identity colours (`--c-title-online`, `--c-title-vi`, etc.) anywhere in the SED
- J includes "* Only in GTA Online currently" note — honest scope marker
- The SED does not change per title; only per-title variant components do
- `--c-gta-dollar` (green, `#22c55e`) is the canonical GTA$ colour — matches in-game HUD across all titles


## TypeScript types

Shared interfaces live in `src/types/gta.ts`:
- `Trailer`, `TrailersData` — `data/gta-6/trailers.json`
- `Prediction`, `PredictionsData` — `data/gta-6/predictions.json`
- `PredictionRange` — nested in `Prediction`

Import with `import type { ... } from "../types/gta"`.

D3 axis `tickFormat` callbacks require `as any` due to d3 type limitations — this is expected and acceptable.

---

## Deployment

Every push to `main` triggers `.github/workflows/static.yml`:
1. `npm ci && npm run build` → `dist/`
2. Uploaded as GitHub Pages artifact and deployed

Nightly at 03:00 UTC, `.github/workflows/fetch-data.yml` runs all active scrapers and commits any changed JSON with `[skip ci]`.

Bump `src/config/version.ts` when shipping a meaningful release.

---

## Cursor Cloud agent rules

- **No autonomous screenshots or screen recordings.** Never use the `computerUse` subagent, `RecordScreen`, or any screenshot tool on your own initiative. If visual confirmation of a UI change is needed, ask the user to share a screenshot instead — this is faster and cheaper.
- Communicate this rule explicitly in every chat handover note under a "Agent rules" section so the next agent does not repeat the behaviour.

- **Always use the central design token system — no hardcoded values in components.** This rule applies to this project and all other projects. Every visual property — colour, font family, font size, font weight, spacing, and surface — must reference the central token system. Never reach for a raw literal value in a component.

  **Colours:**
  - In `.astro` / CSS: `var(--c-*)` from `src/styles/tokens.css`
  - In Tailwind class strings: mapped utility classes (`text-zinc-*`, `bg-*`) per `tokens.css`
  - In TypeScript / D3 / JS: named exports from `src/config/colors.ts`
  - Never write a raw hex literal (e.g. `#1a1a1e`, `color:#b8b8c4`). If a colour has no token yet, add it to `tokens.css` and `colors.ts` first.

  **Typography (font family, size, weight):**
  - Always use the Tailwind font utilities: `font-sans`, `font-mono`, `font-bold`, `text-sm`, `text-[11px]` etc.
  - Font families are defined in `tokens.css` as `--font-sans` and `--font-mono`. Never write `style="font-family:..."` inline.
  - Font sizes follow the scale defined in `tokens.css` (`--fs-micro` 10px, `--fs-label` 11px, `--fs-body` 14px etc.). Use the corresponding Tailwind class; never write a raw `px` size that isn't in the scale.
  - Never write `style="font-size:..."` or `style="font-weight:..."` inline.

  **General rule:** When touching an existing component that contains any hardcoded visual value (hex colour, raw font size, inline font-family, orphan pixel value), replace it with the correct token reference in the same commit. Do not leave orphaned raw values behind.

- **Version bump — mandatory on every session, no exceptions.** Every session that touches code, data, UI, or scrapers must bump `src/config/version.ts` before merging to `main`. Patch bump (`x.y.Z+1`) for fixes and minor tweaks; minor bump (`x.Y+1.0`) for new features; major bump (`X+1.0.0`) for full redesigns. Also update `SITE_VERSION_DATE` to today (`YYYY-MM-DD`). The version is displayed in the ops bar on every page — it must always reflect the latest release.

- **Tag the previous release before starting work.** At the start of every session, before creating a feature branch, tag the current `staging` branch with `release/v{current_version}` and push the tag. This bookmarks the last known-good state and makes rollback trivial.
  ```bash
  git tag release/vX.Y.Z origin/staging && git push origin release/vX.Y.Z
  ```

- **Handover note version format.** In chat handover scripts only, the current version must be written in the format `GTAVI_AI_v1_75_0` (project prefix + underscores instead of dots). Example: `GTAVI_AI_v1_76_0`. This applies to the version token in the handover note header and any inline version references within the handover text. It does NOT affect `src/config/version.ts`, git tags, commit messages, or any other file — those continue to use the standard `1.76.0` format.

- **New projects: establish version infrastructure first.** If starting a new project that does not yet have a version file, create `src/config/version.ts` (or equivalent for the stack) with `SITE_VERSION`, `SITE_VERSION_DATE`, and `SITE_VERSION_LABEL` constants before any other work. Wire the version into a visible location (footer, ops bar, or page meta) so it is always observable. Document the file path in this `AGENTS.md`.
