"""
post_weekly_digest_resend.py
────────────────────────────
Auto-generates and sends a branded weekly GTA VI.AI intel digest via Resend.

Content assembled from live JSON:
  data/feeds/newswire.json      → top 5 news items
  data/gta-6/predictions.json   → top 3 predictions by confidence
  data/franchise/ttwo-stock.json → data point of the week
  data/gta-6/trailer-velocity.json → trailer view counts

Requires:
  RESEND_API_KEY      — resend.com API key
  RESEND_AUDIENCE_ID  — audience UUID from resend.com → Audiences

Called by .github/workflows/weekly-digest.yml every Tuesday 10:00 UTC.
"""

import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests

API_KEY     = os.environ.get("RESEND_API_KEY", "")
AUDIENCE_ID = os.environ.get("RESEND_AUDIENCE_ID", "")
DATA        = Path(__file__).parent.parent / "data"
SITE_URL    = "https://gtavi.ai"
FROM_EMAIL  = "GTA VI.AI <digest@gtavi.ai>"   # must be a verified Resend domain
LAUNCH_DATE = date(2026, 11, 19)


# ── Helpers ───────────────────────────────────────────────────────────────────

def load(path: str) -> dict:
    p = DATA / path
    if not p.exists():
        return {}
    with open(p) as f:
        return json.load(f)


def countdown_days() -> int:
    return (LAUNCH_DATE - date.today()).days


def tier_label(tier: str) -> str:
    return {"confirmed": "CONFIRMED", "reported": "REPORTED"}.get(tier, "PREDICTED")


def tier_hex(tier: str) -> str:
    return {"confirmed": "#0d9488", "reported": "#f59e0b"}.get(tier, "#9898b8")


def confidence_bar(pct: int, width: int = 20) -> str:
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


# ── Email HTML ────────────────────────────────────────────────────────────────

def build_html(news_items: list, predictions: list, stock_note: str, trailer_note: str) -> str:
    today_str   = datetime.now(timezone.utc).strftime("%B %d, %Y")
    days_left   = countdown_days()

    # ── News items ────────────────────────────────────────────────────────────
    news_rows = ""
    for i, item in enumerate(news_items[:5]):
        source = item.get("source", "")
        title  = item.get("title", "")[:90]
        url    = item.get("url", SITE_URL + "/news")
        border = "border-top:1px solid #1e1e23;" if i > 0 else ""
        news_rows += f"""
        <tr>
          <td style="padding:10px 0;{border}">
            <div style="color:#6b6b7e;font-size:9px;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:3px">{source}</div>
            <a href="{url}" style="color:#d4d4d8;font-size:13px;text-decoration:none;line-height:1.4">{title}</a>
          </td>
        </tr>"""

    # ── Prediction cards ──────────────────────────────────────────────────────
    pred_cards = ""
    for pred in predictions[:3]:
        tier    = pred.get("confidence_tier", "predicted")
        conf    = pred.get("confidence", 0)
        title   = pred.get("title", "")
        value   = pred.get("value", "—")
        unit    = pred.get("unit") or ""
        basis   = (pred.get("basis") or "")[:120]
        color   = tier_hex(tier)
        label   = tier_label(tier)
        bar     = confidence_bar(conf, 18)
        pred_id = pred.get("id", "")
        url     = f"{SITE_URL}/gta-vi/intel#{pred_id}"

        pred_cards += f"""
        <tr>
          <td style="padding:12px 0">
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="border:1px solid #1e1e23;border-left:3px solid {color};background:#131316">
              <tr>
                <td style="padding:14px 16px">
                  <div style="margin-bottom:6px">
                    <span style="color:{color};font-size:9px;text-transform:uppercase;
                                 letter-spacing:0.15em;border:1px solid {color}44;
                                 padding:2px 6px;margin-right:8px">{label}</span>
                    <span style="color:{color};font-size:13px;font-weight:700">{conf}%</span>
                  </div>
                  <div style="color:#ebebef;font-size:13px;font-weight:700;margin-bottom:4px">{title}</div>
                  <div style="color:#f59e0b;font-size:20px;font-weight:700;margin-bottom:6px">
                    {value}{(" " + unit) if unit else ""}
                  </div>
                  <div style="color:{color};font-size:10px;letter-spacing:0.05em;margin-bottom:8px">{bar} {conf}%</div>
                  <div style="color:#6b6b7e;font-size:11px;line-height:1.5">{basis}</div>
                  <div style="margin-top:10px">
                    <a href="{url}" style="color:{color};font-size:10px;text-transform:uppercase;
                                           letter-spacing:0.12em;text-decoration:none">Full analysis →</a>
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>"""

    # ── Data point row ────────────────────────────────────────────────────────
    data_rows = ""
    if stock_note:
        data_rows += f"""
        <tr>
          <td style="padding:6px 0;border-bottom:1px solid #1e1e23">
            <span style="color:#6b6b7e;font-size:9px;text-transform:uppercase;letter-spacing:0.12em">TTWO Stock  </span>
            <span style="color:#d4d4d8;font-size:12px">{stock_note}</span>
          </td>
        </tr>"""
    data_rows += f"""
        <tr>
          <td style="padding:6px 0;border-bottom:1px solid #1e1e23">
            <span style="color:#6b6b7e;font-size:9px;text-transform:uppercase;letter-spacing:0.12em">Countdown  </span>
            <span style="color:#f59e0b;font-size:12px">{days_left} days to Nov 19 launch</span>
          </td>
        </tr>"""
    if trailer_note:
        data_rows += f"""
        <tr>
          <td style="padding:6px 0">
            <span style="color:#6b6b7e;font-size:9px;text-transform:uppercase;letter-spacing:0.12em">Trailer Views  </span>
            <span style="color:#d4d4d8;font-size:12px">{trailer_note}</span>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>GTA VI.AI — Weekly Intel Digest</title>
</head>
<body style="margin:0;padding:0;background:#0e0e11;-webkit-text-size-adjust:100%">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0e0e11">
  <tr>
    <td align="center" style="padding:24px 16px">
      <table width="600" cellpadding="0" cellspacing="0"
             style="max-width:600px;width:100%;font-family:Courier New,Consolas,Monaco,monospace">

        <!-- ── HEADER ── -->
        <tr>
          <td style="padding:24px 28px;border:1px solid #1e1e23;border-bottom:none;background:#0a0a0d">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <span style="color:#71717a;font-size:16px;font-weight:700">GTA</span><span style="color:#f59e0b;font-size:16px;font-weight:700">VI</span><span style="color:#52525b;font-size:10px;margin-left:2px">.AI</span>
                </td>
                <td align="right">
                  <span style="color:#6b6b7e;font-size:9px;text-transform:uppercase;letter-spacing:0.15em">{days_left}d to launch · Nov 19 2026</span>
                </td>
              </tr>
            </table>
            <div style="color:#3f3f46;font-size:9px;text-transform:uppercase;letter-spacing:0.2em;margin-top:10px;padding-top:10px;border-top:1px solid #1e1e23">
              Weekly Intel Digest · {today_str}
            </div>
          </td>
        </tr>

        <!-- ── ACCENT LINE ── -->
        <tr>
          <td style="height:2px;background:linear-gradient(90deg,#f59e0b,transparent);border-left:1px solid #1e1e23;border-right:1px solid #1e1e23"></td>
        </tr>

        <!-- ── NEWS ── -->
        <tr>
          <td style="padding:24px 28px;border-left:1px solid #1e1e23;border-right:1px solid #1e1e23;border-bottom:1px solid #1e1e23">
            <div style="color:#9898b8;font-size:9px;text-transform:uppercase;letter-spacing:0.2em;margin-bottom:16px">// Intelligence this week</div>
            <table width="100%" cellpadding="0" cellspacing="0">
              {news_rows}
            </table>
            <div style="margin-top:14px">
              <a href="{SITE_URL}/news" style="color:#f59e0b;font-size:10px;text-transform:uppercase;letter-spacing:0.12em;text-decoration:none">Full newswire →</a>
            </div>
          </td>
        </tr>

        <!-- ── PREDICTIONS ── -->
        <tr>
          <td style="padding:24px 28px;border-left:1px solid #1e1e23;border-right:1px solid #1e1e23;border-bottom:1px solid #1e1e23">
            <div style="color:#9898b8;font-size:9px;text-transform:uppercase;letter-spacing:0.2em;margin-bottom:4px">// Signal spotlight</div>
            <div style="color:#3f3f46;font-size:9px;margin-bottom:16px">Top confidence-scored GTA VI predictions this week</div>
            <table width="100%" cellpadding="0" cellspacing="0">
              {pred_cards}
            </table>
            <div style="margin-top:8px">
              <a href="{SITE_URL}/gta-vi/intel" style="color:#f59e0b;font-size:10px;text-transform:uppercase;letter-spacing:0.12em;text-decoration:none">All {"{"}len_all_preds{"}"} predictions →</a>
            </div>
          </td>
        </tr>

        <!-- ── DATA POINT ── -->
        <tr>
          <td style="padding:20px 28px;border-left:1px solid #1e1e23;border-right:1px solid #1e1e23;border-bottom:1px solid #1e1e23">
            <div style="color:#9898b8;font-size:9px;text-transform:uppercase;letter-spacing:0.2em;margin-bottom:14px">// Data point of the week</div>
            <table width="100%" cellpadding="0" cellspacing="0">
              {data_rows}
            </table>
          </td>
        </tr>

        <!-- ── CTA ── -->
        <tr>
          <td style="padding:20px 28px;border-left:1px solid #1e1e23;border-right:1px solid #1e1e23;border-bottom:1px solid #1e1e23;text-align:center">
            <a href="{SITE_URL}" style="display:inline-block;background:#f59e0b;color:#000;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.15em;padding:10px 24px;text-decoration:none">
              Open full intelligence →
            </a>
          </td>
        </tr>

        <!-- ── FOOTER ── -->
        <tr>
          <td style="padding:16px 28px;border:1px solid #1e1e23;border-top:none;background:#0a0a0d;text-align:center">
            <div style="color:#3f3f46;font-size:9px;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:8px">
              gtavi.ai · Data-driven GTA intelligence
            </div>
            <div style="color:#27272a;font-size:9px">
              You're receiving this because you subscribed at gtavi.ai.
              <a href="{{{{unsubscribe}}}}" style="color:#3f3f46;text-decoration:underline">Unsubscribe</a>
            </div>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
</body>
</html>"""


# ── Data assembly ──────────────────────────────────────────────────────────────

def get_news() -> list:
    d = load("feeds/newswire.json")
    items = d.get("items", [])
    return sorted(items, key=lambda x: x.get("published_at", ""), reverse=True)[:5]


def get_predictions() -> tuple[list, int]:
    d = load("gta-6/predictions.json")
    preds = d.get("predictions", [])
    top = sorted(
        [p for p in preds if not p.get("outcome_verified")],
        key=lambda x: x.get("confidence", 0),
        reverse=True,
    )[:3]
    return top, len(preds)


def get_stock_note() -> str:
    d = load("franchise/ttwo-stock.json")
    series = d.get("series", [])
    if len(series) < 2:
        return ""
    latest = series[-1]
    prev   = series[-2]
    price  = latest.get("close", 0)
    change = ((price - prev.get("close", price)) / prev.get("close", price)) * 100
    sign   = "+" if change >= 0 else ""
    return f"${price:.2f}  {sign}{change:.1f}% this week"


def get_trailer_note() -> str:
    d = load("gta-6/trailer-velocity.json")
    trailers = d.get("trailers", [])
    total = 0
    for t in trailers:
        snaps = t.get("snapshots", [])
        if snaps:
            total += snaps[-1].get("views", 0)
    if total < 1_000_000:
        return ""
    if total >= 1_000_000_000:
        return f"{total/1_000_000_000:.2f}B combined views (T1 + T2)"
    return f"{total/1_000_000:.0f}M combined views (T1 + T2)"


# ── Resend API ────────────────────────────────────────────────────────────────

def get_contacts() -> list[str]:
    """Return all unsubscribed=False email addresses from the Resend Audience."""
    url  = f"https://api.resend.com/audiences/{AUDIENCE_ID}/contacts"
    resp = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=30)
    if not resp.ok:
        print(f"[digest] Failed to fetch contacts: {resp.status_code} {resp.text}", file=sys.stderr)
        return []
    data = resp.json()
    contacts = data.get("data", [])
    return [c["email"] for c in contacts if not c.get("unsubscribed", False)]


def send_email(to_email: str, subject: str, html: str) -> bool:
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={"from": FROM_EMAIL, "to": [to_email], "subject": subject, "html": html},
        timeout=30,
    )
    return resp.ok


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if not API_KEY:
        print("[digest] RESEND_API_KEY not set — skipping", file=sys.stderr)
        sys.exit(0)
    if not AUDIENCE_ID:
        print("[digest] RESEND_AUDIENCE_ID not set — skipping", file=sys.stderr)
        sys.exit(0)

    print("[digest] Assembling content…")
    news             = get_news()
    predictions, total_preds = get_predictions()
    stock_note       = get_stock_note()
    trailer_note     = get_trailer_note()

    html = build_html(news, predictions, stock_note, trailer_note)
    # Inject real prediction count into the "all N predictions →" link
    html = html.replace("{len_all_preds}", str(total_preds))

    today   = datetime.now(timezone.utc).strftime("%b %d")
    subject = f"GTA VI.AI Intel — {today} · {countdown_days()}d to launch"

    print("[digest] Fetching subscriber list…")
    contacts = get_contacts()
    print(f"[digest] Sending to {len(contacts)} subscriber(s)…")

    sent = failed = 0
    for email in contacts:
        if send_email(email, subject, html):
            sent += 1
        else:
            failed += 1
            print(f"[digest] Failed: {email}", file=sys.stderr)

    print(f"[digest] Done — {sent} sent, {failed} failed")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
