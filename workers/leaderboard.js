/**
 * GTAVI.AI — Community Income Leaderboard Worker
 *
 * Cloudflare Worker backed by KV storage.
 * Players opt in from the IncomeAdviser, submitting their income stack.
 * The leaderboard ranks all submissions by total GTA$/hr.
 *
 * Endpoints:
 *   GET  /leaderboard          — top 100 stacks, sorted by total_hr desc
 *   GET  /leaderboard/week     — this week's top submissions
 *   POST /submit               — submit or update a player's stack
 *   GET  /rank/:username       — single player entry + rank
 *
 * KV schema:
 *   player:{username}   → { username, display, stack[], total_hr, submitted_at, week_key }
 *   index:all           → [ { username, total_hr, submitted_at } ] (sorted array, max 1000)
 */

const ALLOWED_ORIGIN = 'https://gtavi.ai';
const MAX_INDEX_SIZE = 1000;
const RATE_LIMIT_TTL = 60;         // seconds between submissions per IP
const MAX_STACK_ITEMS = 20;        // max businesses in a submitted stack

// ── Moderation blocklist ──────────────────────────────────────────────────────
// Lowercase exact or substring matches. Extend as needed — no redeploy required
// once the list is in KV (see handleAdmin). For now hardcoded for simplicity.
const BLOCKED_NAMES = new Set([
  'admin', 'moderator', 'rockstar', 'gtavi.ai', 'gtaviai',
  'null', 'undefined', 'test', 'spam', 'bot',
]);

function isBlockedUsername(name) {
  const lower = name.toLowerCase().replace(/\s+/g, '');
  if (BLOCKED_NAMES.has(lower)) return true;
  // Block pure numbers or single chars
  if (/^\d+$/.test(lower)) return true;
  if (lower.length < 2) return true;
  return false;
}

/** ISO week key: "2026-W20" */
function weekKey(date = new Date()) {
  const d = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const week = Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
  return `${d.getUTCFullYear()}-W${String(week).padStart(2, '0')}`;
}

function cors(origin) {
  const allowed = origin === ALLOWED_ORIGIN || origin?.endsWith('.pages.dev');
  return {
    'Access-Control-Allow-Origin':  allowed ? origin : ALLOWED_ORIGIN,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age':       '86400',
  };
}

function json(data, status = 200, origin = '') {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...cors(origin) },
  });
}

/** Validate and sanitise a submitted stack entry */
function validateStack(stack) {
  if (!Array.isArray(stack) || stack.length === 0) return null;
  if (stack.length > MAX_STACK_ITEMS) return null;
  return stack.slice(0, MAX_STACK_ITEMS).map(item => ({
    id:        String(item.id   || '').slice(0, 60),
    name:      String(item.name || '').slice(0, 80),
    profit_hr: Math.max(0, Math.min(10_000_000, parseInt(item.profit_hr || item.profit || 0))),
  })).filter(s => s.id && s.profit_hr > 0);
}

/** Update the sorted leaderboard index in KV */
async function updateIndex(kv, username, total_hr, submitted_at) {
  const raw = await kv.get('index:all');
  let index = raw ? JSON.parse(raw) : [];

  // Remove existing entry for this player
  index = index.filter(e => e.username !== username);

  // Insert new entry
  index.push({ username, total_hr, submitted_at });

  // Sort descending by total_hr, keep top MAX_INDEX_SIZE
  index.sort((a, b) => b.total_hr - a.total_hr);
  if (index.length > MAX_INDEX_SIZE) index = index.slice(0, MAX_INDEX_SIZE);

  await kv.put('index:all', JSON.stringify(index), { expirationTtl: 86400 * 365 });
  return index;
}

/** GET /leaderboard — returns top 100 entries with rank */
async function handleLeaderboard(kv, url, origin) {
  const week   = url.searchParams.get('week') || null;
  const limit  = Math.min(100, parseInt(url.searchParams.get('limit') || '100'));
  const offset = Math.max(0, parseInt(url.searchParams.get('offset') || '0'));

  const raw = await kv.get('index:all');
  if (!raw) return json({ entries: [], total: 0 }, 200, origin);

  let index = JSON.parse(raw);

  // Optional week filter
  if (week) {
    index = index.filter(e => {
      const d = new Date(e.submitted_at);
      return weekKey(d) === week;
    });
  }

  const total = index.length;
  const page  = index.slice(offset, offset + limit);

  // Fetch full player data for the page slice
  const entries = await Promise.all(
    page.map(async (entry, i) => {
      const raw = await kv.get(`player:${entry.username}`);
      if (!raw) return null;
      const player = JSON.parse(raw);
      return {
        rank:         offset + i + 1,
        username:     player.username,
        display:      player.display || player.username,
        total_hr:     player.total_hr,
        stack:        player.stack,
        submitted_at: player.submitted_at,
        week_key:     player.week_key,
      };
    })
  );

  return json({
    entries:  entries.filter(Boolean),
    total,
    offset,
    limit,
    week_key: week || weekKey(),
  }, 200, origin);
}

/** POST /submit */
async function handleSubmit(kv, request, origin) {
  // Rate limiting by IP (best-effort)
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  const rateKey = `ratelimit:${ip}`;
  const recentSubmit = await kv.get(rateKey);
  if (recentSubmit) {
    return json({ error: 'Too many submissions. Wait 60 seconds.' }, 429, origin);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, 400, origin);
  }

  const username = String(body.username || '').trim().slice(0, 40);
  const display  = String(body.display  || username).trim().slice(0, 40);

  if (!username || username.length < 2) {
    return json({ error: 'username required (min 2 chars)' }, 400, origin);
  }
  if (isBlockedUsername(username) || isBlockedUsername(display)) {
    return json({ error: 'Username not allowed' }, 400, origin);
  }

  const stack = validateStack(body.stack);
  if (!stack || stack.length === 0) {
    return json({ error: 'stack must be a non-empty array of {id, name, profit_hr}' }, 400, origin);
  }

  const total_hr     = stack.reduce((s, item) => s + item.profit_hr, 0);
  const submitted_at = new Date().toISOString();
  const week         = weekKey();

  const player = { username, display, stack, total_hr, submitted_at, week_key: week };

  // Store player record and update index
  await kv.put(`player:${username}`, JSON.stringify(player), { expirationTtl: 86400 * 90 });
  await kv.put(rateKey, '1', { expirationTtl: RATE_LIMIT_TTL });
  const index = await updateIndex(kv, username, total_hr, submitted_at);

  const rank = index.findIndex(e => e.username === username) + 1;

  return json({
    ok:           true,
    username,
    display,
    total_hr,
    rank,
    week_key:     week,
    submitted_at,
    message:      `Rank #${rank} — $${Math.round(total_hr / 1000)}K/hr`,
  }, 200, origin);
}

/** GET /rank/:username */
async function handleRank(kv, username, origin) {
  const raw = await kv.get(`player:${username}`);
  if (!raw) return json({ error: 'Player not found' }, 404, origin);

  const player = JSON.parse(raw);
  const indexRaw = await kv.get('index:all');
  const index = indexRaw ? JSON.parse(indexRaw) : [];
  const rank = index.findIndex(e => e.username === username) + 1;

  return json({ ...player, rank: rank || null }, 200, origin);
}

/** Weekly cron: snapshot top 10 of the current week into KV */
async function handleWeeklyCron(kv) {
  const week   = weekKey();
  const raw    = await kv.get('index:all');
  if (!raw) return;

  const index = JSON.parse(raw);
  const thisWeek = index.filter(e => {
    const d = new Date(e.submitted_at);
    return weekKey(d) === week;
  });

  if (thisWeek.length === 0) {
    console.log(`[cron] No entries for week ${week} — skipping snapshot`);
    return;
  }

  // Fetch full player record for the winner to embed in the snapshot
  const winnerEntry = thisWeek[0];
  const winnerRaw   = await kv.get(`player:${winnerEntry.username}`);
  const winner      = winnerRaw ? JSON.parse(winnerRaw) : winnerEntry;

  const snapshot = {
    week_key:   week,
    snapped_at: new Date().toISOString(),
    top10:      thisWeek.slice(0, 10),
    winner: {
      username:     winner.username,
      display:      winner.display || winner.username,
      total_hr:     winner.total_hr,
      stack:        winner.stack || [],
      submitted_at: winner.submitted_at,
    },
  };

  await kv.put(`snapshot:${week}`, JSON.stringify(snapshot), { expirationTtl: 86400 * 60 });
  // Always keep a pointer to the latest completed snapshot for the winner banner
  await kv.put('snapshot:latest', JSON.stringify(snapshot), { expirationTtl: 86400 * 90 });
  console.log(`[cron] Snapped week ${week}: ${thisWeek.length} entries, winner: ${winner.display || winner.username}`);
}

export default {
  // ── Scheduled cron (every Monday 00:05 UTC — "0 5 * * 1" in wrangler.toml) ──
  async scheduled(event, env, ctx) {
    ctx.waitUntil(handleWeeklyCron(env.LEADERBOARD));
  },

  async fetch(request, env) {
    const url    = new URL(request.url);
    const origin = request.headers.get('Origin') || '';
    const kv     = env.LEADERBOARD;

    // CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: cors(origin) });
    }

    const path = url.pathname.replace(/\/$/, '');

    try {
      if (path === '/leaderboard' && request.method === 'GET') {
        return handleLeaderboard(kv, url, origin);
      }

      if (path === '/submit' && request.method === 'POST') {
        return handleSubmit(kv, request, origin);
      }

      if (path.startsWith('/rank/') && request.method === 'GET') {
        const username = decodeURIComponent(path.replace('/rank/', ''));
        return handleRank(kv, username, origin);
      }

      // Weekly snapshot — returns the snapped top-10 for a given week
      if (path === '/leaderboard/snapshot' && request.method === 'GET') {
        const w   = url.searchParams.get('week') || weekKey();
        const raw = await kv.get(`snapshot:${w}`);
        if (!raw) return json({ week_key: w, top10: [], message: 'No snapshot yet for this week' }, 200, origin);
        return json(JSON.parse(raw), 200, origin);
      }

      // Last week's winner — used by the leaderboard page winner banner
      if (path === '/leaderboard/winner' && request.method === 'GET') {
        const raw = await kv.get('snapshot:latest');
        if (!raw) return json({ winner: null, message: 'No winner yet — first snapshot runs Monday 00:05 UTC' }, 200, origin);
        return json(JSON.parse(raw), 200, origin);
      }

      // Health check
      if (path === '/health') {
        return json({ ok: true, ts: new Date().toISOString() }, 200, origin);
      }

      return json({ error: 'Not found', path }, 404, origin);

    } catch (err) {
      console.error('[leaderboard]', err);
      return json({ error: 'Internal server error' }, 500, origin);
    }
  },
};
