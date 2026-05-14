# AGENTS.md

## Cursor Cloud specific instructions

This is a static Astro site (GTAVI.AI) with Python data scrapers. No backend, no database.

### Services

| Service | Command | Notes |
|---------|---------|-------|
| Astro dev server | `npm run dev` | Runs on port 4321. Use `--host 0.0.0.0` for network access. |
| Build | `npm run build` | Outputs to `dist/`. Also serves as the lint/type check (strict TS). |
| Preview | `npm run preview` | Serves the built `dist/` directory. |

### Key points

- **No ESLint or separate lint tool** — `npm run build` is the validation check (TypeScript strict mode via Astro).
- **No test framework** — there are no automated tests configured. Validate changes with `npm run build`.
- **Data is pre-committed** — all JSON data in `data/` is checked into git. Scrapers (`scrapers/`) are optional and require external API keys.
- **Python scrapers** are optional for development. They refresh `data/` JSON files but require secrets like `YOUTUBE_API_KEY`.
- `astro check` requires installing `@astrojs/check` and `typescript` (not in `package.json` by default). Use `npm run build` instead for validation.
