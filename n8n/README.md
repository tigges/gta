# GTAVI.AI — n8n Workflows

Import these JSON files into [tigges.app.n8n.cloud](https://tigges.app.n8n.cloud/) to automate GTAVI.AI social media and newsletter publishing.

## Workflows

| File | Trigger | Purpose |
|------|---------|---------|
| `main-pipeline.json` | Monday 08:00 UTC (cron) | Weekly poll → copy → Publer (X/IG/Reddit) + Beehiiv draft + Discord digest |
| `preorder-blast.json` | Manual | One-shot pre-order launch blast to all channels |

## How to import

1. Open [tigges.app.n8n.cloud](https://tigges.app.n8n.cloud/)
2. **Workflows** → **Add Workflow** → **Import from file**
3. Select the JSON file
4. Fill in all `REPLACE_*` placeholders (see `meta.placeholders` in each file)
5. Set up credentials (see below)
6. Activate

## Credentials to configure in n8n

| Credential | n8n type | Where to get |
|------------|----------|-------------|
| Anthropic API key | Anthropic | console.anthropic.com → API Keys |
| Publer token | HTTP Header Auth | publer.io → Settings → API |
| Beehiiv API key | HTTP Header Auth | beehiiv.com → Settings → API Keys |
| Discord webhook | HTTP Request URL | Discord → Server Settings → Integrations → Webhooks |

## Placeholder map

All `REPLACE_*` values that must be set before activating:

```
REPLACE_PUBLER_TOKEN          Publer API token
REPLACE_PROFILE_ID_X          Publer X (Twitter) profile ID
REPLACE_PROFILE_ID_IG         Publer Instagram profile ID
REPLACE_PROFILE_ID_REDDIT     Publer Reddit profile ID
REPLACE_BEEHIIV_PUBLICATION_ID  Beehiiv publication ID
REPLACE_BEEHIIV_API_KEY       Beehiiv API key
REPLACE_DISCORD_WEBHOOK_URL   Discord webhook URL
REPLACE_GTA6_AMAZON_US        Amazon US affiliate link (preorder blast only)
REPLACE_GTA6_AMAZON_UK        Amazon UK affiliate link (preorder blast only)
REPLACE_CDKEYS_AFFILIATE      CDKeys affiliate link (preorder blast only)
REPLACE_ENEBA_AFFILIATE       Eneba affiliate link (preorder blast only)
```

## Affiliate priority

For pre-order links, use this priority order (best commission first):
1. **CDKeys** — 5–8% commission, apply at cdkeys.com/affiliates
2. **Eneba** — 5–8% commission, apply at eneba.com/affiliate
3. Amazon Associates — 1–3% commission, fallback only

## Admin dashboard

Full strategy reference: [staging.gtavi.ai/admin/social](https://staging.gtavi.ai/admin/social)
