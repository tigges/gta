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
| `fetch_newswire.py` | `feeds/newswire.json` | ✅ | RSS scrape; no API key |
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

---

## Git & branch conventions

- All agent branches use prefix `cursor/` and suffix `-c815`
  Example: `cursor/my-feature-c815`
- Branch names must be **lowercase**
- One logical change per commit with a descriptive message
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
