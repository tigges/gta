/**
 * POST /api/poll/:pollId/vote
 *
 * Records a single vote for a poll option.
 * Uses Cloudflare KV (POLL_VOTES binding) to store cumulative counts.
 * Cookie-based deduplication prevents duplicate votes from the same client.
 *
 * Request body: { option: string }
 * Response: { votes: Record<string, number>, total: number }
 *
 * Setup (Cloudflare Pages dashboard):
 *   1. Create a KV namespace named "POLL_VOTES"
 *   2. Bind it to this Pages project under Settings → Functions → KV Namespace Bindings
 *      Variable name: POLL_VOTES
 */

interface Env {
  POLL_VOTES: KVNamespace;
}

const COOKIE_MAX_AGE = 60 * 60 * 24 * 365; // 1 year

function getCookieName(pollId: string): string {
  return `voted_${pollId.replace(/[^a-z0-9_]/gi, "_")}`;
}

async function getVotes(kv: KVNamespace, pollId: string, options: string[]): Promise<Record<string, number>> {
  const votes: Record<string, number> = {};
  await Promise.all(
    options.map(async opt => {
      const key = `poll:${pollId}:${encodeURIComponent(opt)}`;
      const val = await kv.get(key);
      votes[opt] = val ? parseInt(val, 10) : 0;
    })
  );
  return votes;
}

export const onRequestPost: PagesFunction<Env> = async ({ request, env, params }) => {
  const pollId = (params.pollId as string) || "";

  // Parse request body
  let option: string;
  try {
    const body = await request.json() as { option?: string };
    option = body.option?.trim() || "";
  } catch {
    return new Response(JSON.stringify({ error: "invalid_body" }), { status: 400 });
  }

  if (!option) {
    return new Response(JSON.stringify({ error: "missing_option" }), { status: 400 });
  }

  // Deduplication: check cookie
  const cookieName = getCookieName(pollId);
  const cookies    = request.headers.get("Cookie") || "";
  const alreadyVoted = cookies.split(";").some(c => c.trim().startsWith(`${cookieName}=`));

  if (alreadyVoted) {
    // Return current results without incrementing
    const voteKey = `poll:${pollId}:_options`;
    const storedOptions = await env.POLL_VOTES.get(voteKey);
    const options = storedOptions ? JSON.parse(storedOptions) : [option];
    const votes = await getVotes(env.POLL_VOTES, pollId, options);
    return new Response(
      JSON.stringify({ votes, total: Object.values(votes).reduce((s, v) => s + v, 0), already_voted: true }),
      { status: 409, headers: { "Content-Type": "application/json" } }
    );
  }

  // Store the option list so results endpoint can retrieve all options
  const voteKey    = `poll:${pollId}:_options`;
  const existing   = await env.POLL_VOTES.get(voteKey);
  const allOptions: string[] = existing ? JSON.parse(existing) : [];
  if (!allOptions.includes(option)) allOptions.push(option);
  await env.POLL_VOTES.put(voteKey, JSON.stringify(allOptions));

  // Increment the vote counter
  const key     = `poll:${pollId}:${encodeURIComponent(option)}`;
  const current = parseInt((await env.POLL_VOTES.get(key)) || "0", 10);
  await env.POLL_VOTES.put(key, String(current + 1));

  // Return updated results
  const votes = await getVotes(env.POLL_VOTES, pollId, allOptions);
  const total = Object.values(votes).reduce((s, v) => s + v, 0);

  return new Response(
    JSON.stringify({ votes, total }),
    {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Set-Cookie": `${cookieName}=1; Path=/; Max-Age=${COOKIE_MAX_AGE}; SameSite=Lax; Secure`,
      },
    }
  );
};
