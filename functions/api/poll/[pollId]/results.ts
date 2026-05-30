/**
 * GET /api/poll/:pollId/results
 *
 * Returns current vote counts for a poll without incrementing.
 * Used to show results to users who have already voted.
 *
 * Response: { votes: Record<string, number>, total: number }
 */

interface Env {
  POLL_VOTES: KVNamespace;
}

export const onRequestGet: PagesFunction<Env> = async ({ env, params }) => {
  const pollId = (params.pollId as string) || "";

  const voteKey = `poll:${pollId}:_options`;
  const stored  = await env.POLL_VOTES.get(voteKey);

  if (!stored) {
    return new Response(
      JSON.stringify({ votes: {}, total: 0 }),
      { headers: { "Content-Type": "application/json" } }
    );
  }

  const options: string[] = JSON.parse(stored);
  const votes: Record<string, number> = {};

  await Promise.all(
    options.map(async opt => {
      const key = `poll:${pollId}:${encodeURIComponent(opt)}`;
      const val = await env.POLL_VOTES.get(key);
      votes[opt] = val ? parseInt(val, 10) : 0;
    })
  );

  const total = Object.values(votes).reduce((s, v) => s + v, 0);

  return new Response(
    JSON.stringify({ votes, total }),
    {
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    }
  );
};
