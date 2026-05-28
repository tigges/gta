/**
 * Cloudflare Pages Function — POST /api/subscribe
 *
 * Accepts { email } from the NewsletterSignup form,
 * adds the contact to the Resend Audience, and returns JSON.
 *
 * Environment variables required (Cloudflare Pages → Settings → Env Vars):
 *   RESEND_API_KEY      — from resend.com dashboard
 *   RESEND_AUDIENCE_ID  — audience UUID from resend.com → Audiences
 */

interface Env {
  RESEND_API_KEY: string;
  RESEND_AUDIENCE_ID: string;
}

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...CORS },
  });
}

export async function onRequestOptions() {
  return new Response(null, { status: 204, headers: CORS });
}

export async function onRequestPost({ request, env }: { request: Request; env: Env }) {
  const apiKey    = env.RESEND_API_KEY;
  const audienceId = env.RESEND_AUDIENCE_ID;

  if (!apiKey || !audienceId) {
    return json({ error: "Server not configured" }, 503);
  }

  let email: string;
  try {
    const body = await request.json() as { email?: string };
    email = (body.email ?? "").trim().toLowerCase();
  } catch {
    return json({ error: "Invalid request body" }, 400);
  }

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return json({ error: "Invalid email address" }, 400);
  }

  const res = await fetch(
    `https://api.resend.com/audiences/${audienceId}/contacts`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, unsubscribed: false }),
    }
  );

  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { name?: string };
    // "audience_contact_already_exists" is not an error from the user's perspective
    if ((err as any).name === "audience_contact_already_exists") {
      return json({ ok: true, message: "Already subscribed" });
    }
    return json({ error: "Subscription failed — please try again" }, 502);
  }

  return json({ ok: true, message: "Subscribed" });
}
