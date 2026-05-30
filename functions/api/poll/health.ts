/**
 * GET /api/poll/health
 *
 * Diagnostic endpoint — confirms the POLL_VOTES KV namespace binding
 * is correctly attached to this Cloudflare Pages project.
 *
 * Responses:
 *   200  { ok: true,  kv: "bound",   test: "write+read passed" }
 *   500  { ok: false, kv: "missing", error: "POLL_VOTES binding not found" }
 *   500  { ok: false, kv: "bound",   error: "<kv error message>" }
 *
 * Setup check:
 *   Cloudflare Pages → Settings → Functions → KV Namespace Bindings
 *   Variable name must be exactly: POLL_VOTES
 */

interface Env {
  POLL_VOTES: KVNamespace;
}

export const onRequestOptions: PagesFunction = async () =>
  new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin":  "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
    },
  });

export const onRequestGet: PagesFunction<Env> = async ({ env }) => {
  const headers = {
    "Content-Type": "application/json",
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
  };

  if (!env.POLL_VOTES) {
    return new Response(
      JSON.stringify({
        ok: false,
        kv: "missing",
        error: "POLL_VOTES binding not found — add it in Cloudflare Pages → Settings → Functions → KV Namespace Bindings",
        fix: "Variable name must be exactly: POLL_VOTES",
      }),
      { status: 500, headers }
    );
  }

  // Write a test key and read it back to confirm KV is functional
  const testKey = "__health_check__";
  const testVal = `ok-${Date.now()}`;

  try {
    await env.POLL_VOTES.put(testKey, testVal, { expirationTtl: 60 });
    const readBack = await env.POLL_VOTES.get(testKey);

    if (readBack !== testVal) {
      return new Response(
        JSON.stringify({
          ok: false,
          kv: "bound",
          error: "KV write succeeded but read returned wrong value",
          written: testVal,
          read: readBack,
        }),
        { status: 500, headers }
      );
    }

    return new Response(
      JSON.stringify({
        ok: true,
        kv: "bound",
        test: "write+read passed",
        note: "POLL_VOTES is correctly bound and functional. Votes will persist.",
      }),
      { status: 200, headers }
    );
  } catch (err: any) {
    return new Response(
      JSON.stringify({
        ok: false,
        kv: "bound",
        error: err?.message ?? String(err),
        note: "KV binding exists but threw on read/write. Check namespace permissions.",
      }),
      { status: 500, headers }
    );
  }
};
