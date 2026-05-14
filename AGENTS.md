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
| `fetch_igdb.py` | `franchise/igdb.json` | ❌ | Needs IGDB client creds |
| `fetch_steamdb.py` | `gta-5/meta/steamdb.json` | ❌ | SteamDB blocks server IPs; curated seed |
| `fetch_spotify.py` | `franchise/spotify.json` | ❌ | Curated seed |
| `fetch_boxoffice.py` | `franchise/entertainment-comps.json` | ❌ | Curated seed |
| `fetch_edgar.py` | `franchise/cpi.json`, `revenue-split.json` | ❌ | SEC EDGAR; run manually |
| `fetch_vgchartz.py` | `franchise/vgchartz.json` | ❌ | Run manually if data drift |
| `fetch_gta_wiki.py` | `gta-6/entities/*.json` | ❌ | Run manually after major reveals |
| `fetch_press_assets.py` | `gta-6/press-assets.json` | ❌ | Run manually after press drops |

---

## Git & branch conventions

- All agent branches use prefix `cursor/` and suffix `-38ec`
  Example: `cursor/my-feature-38ec`
- Branch names must be **lowercase**
- One logical change per commit with a descriptive message
- PRs are created as drafts targeting `main`
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
