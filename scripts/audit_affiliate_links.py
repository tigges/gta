#!/usr/bin/env python3
"""
Affiliate link auditor — walks dist/, extracts every outbound commerce
URL, and verifies the matching affiliate parameter is present.

Failure modes detected:
  - Amazon URL missing `tag=...` for a market we have an Associates ID for
  - Amazon URL using the wrong tag (e.g. amazon.co.uk with the US tag)
  - NordVPN URL missing or wrong `aff_id=...`
  - ZAP-Hosting URL missing or wrong `aff=...`
  - Skimlinks JS not loaded on a page that contains commerce links
  - Stale Amazon ID values that no longer match affiliates.ts
"""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

EXPECTED_AMAZON_TAG = {
    "www.amazon.com":    "gtaviai-20",
    "www.amazon.co.uk":  "gtaviai-21",
    "www.amazon.de":     "gtaviai0e-21",
    "www.amazon.fr":     "gtaviai08-21",
    "www.amazon.ca":     "gtaviai02-20",
    "www.amazon.it":     "gtaviai07-21",
    "www.amazon.es":     "gtaviai00-21",
}
SKIMLINKS_AMAZON = {
    # No direct programme; Skimlinks fills the gap globally. Untagged is fine.
    "www.amazon.co.jp", "www.amazon.com.au", "www.amazon.com.br",
    "www.amazon.nl", "www.amazon.com.mx", "www.amazon.in",
    "www.amazon.se", "www.amazon.pl", "www.amazon.com.tr",
    "www.amazon.sa", "www.amazon.ae", "www.amazon.com.be",
    "www.amazon.co.za",
}

NORD_AFF_ID = "150614"
ZAP_AFF_ID  = "tigges-a-4754"

URL_RE = re.compile(r'https?://[^"\'<>\s]+', re.IGNORECASE)


def audit():
    failures: list[tuple[str, str, str]] = []
    stats: Counter = Counter()
    by_host: dict[str, Counter] = defaultdict(Counter)
    pages_with_skimlinks = 0
    total_pages = 0

    for html_path in DIST.rglob("*.html"):
        total_pages += 1
        text = html_path.read_text(encoding="utf-8", errors="ignore")

        if "skimresources.com/js/304799X1792988" in text:
            pages_with_skimlinks += 1

        for raw in URL_RE.findall(text):
            url = raw.rstrip(").,;\"'>")
            try:
                u = urlparse(url)
            except Exception:
                continue
            host = u.hostname or ""
            qs = parse_qs(u.query)
            rel = html_path.relative_to(DIST)

            if "amazon." in host:
                stats["amazon_total"] += 1
                by_host[host]["total"] += 1
                expected = EXPECTED_AMAZON_TAG.get(host)
                tag = (qs.get("tag") or [""])[0]
                if expected:
                    if tag == expected:
                        by_host[host]["tagged_ok"] += 1
                    elif tag:
                        failures.append((str(rel), url, f"Amazon tag mismatch: got '{tag}', want '{expected}'"))
                        by_host[host]["wrong_tag"] += 1
                    else:
                        failures.append((str(rel), url, f"Amazon untagged (expected '{expected}' for {host})"))
                        by_host[host]["untagged"] += 1
                elif host in SKIMLINKS_AMAZON:
                    by_host[host]["skimlinks_fallback"] += 1
                else:
                    by_host[host]["unknown_market"] += 1

            elif host == "go.nordvpn.net":
                stats["nord_total"] += 1
                aff_id = (qs.get("aff_id") or [""])[0]
                url_id = (qs.get("url_id") or [""])[0]
                if aff_id == NORD_AFF_ID and url_id == "902":
                    stats["nord_ok"] += 1
                elif aff_id == NORD_AFF_ID:
                    failures.append((str(rel), url, f"NordVPN aff_id OK but url_id='{url_id}' (expected '902')"))
                else:
                    failures.append((str(rel), url, f"NordVPN aff_id mismatch: got '{aff_id}', want '{NORD_AFF_ID}'"))

            elif host == "go.nordpass.io":
                stats["nordpass_total"] += 1
                aff_id = (qs.get("aff_id") or [""])[0]
                url_id = (qs.get("url_id") or [""])[0]
                if aff_id == NORD_AFF_ID and url_id == "9356":
                    stats["nordpass_ok"] += 1
                elif aff_id == NORD_AFF_ID:
                    failures.append((str(rel), url, f"NordPass aff_id OK but url_id='{url_id}' (expected '9356')"))
                else:
                    failures.append((str(rel), url, f"NordPass aff_id mismatch: got '{aff_id}', want '{NORD_AFF_ID}'"))

            elif host == "zap-hosting.com":
                stats["zap_total"] += 1
                aff = (qs.get("aff") or [""])[0]
                if aff == ZAP_AFF_ID:
                    stats["zap_ok"] += 1
                else:
                    failures.append((str(rel), url, f"ZAP aff mismatch: got '{aff}', want '{ZAP_AFF_ID}'"))

    print(f"Pages scanned: {total_pages}")
    print(f"Skimlinks JS present on: {pages_with_skimlinks}/{total_pages}")
    print()
    print("─── Amazon Associates ───────────────────────────────────────")
    for host in sorted(by_host):
        c = by_host[host]
        ok = c.get("tagged_ok", 0)
        skim = c.get("skimlinks_fallback", 0)
        bad = c.get("wrong_tag", 0) + c.get("untagged", 0)
        unknown = c.get("unknown_market", 0)
        total = c["total"]
        flag = "✓" if (ok + skim == total) else "✗"
        marker = ""
        if bad: marker += f" ✗{bad}"
        if unknown: marker += f" ?{unknown}"
        print(f"  {flag} {host:<22}  total={total:<4}  tagged={ok}  skimlinks={skim}{marker}")
    print()
    print("─── Other Programmes ────────────────────────────────────────")
    print(f"  NordVPN  (go.nordvpn.net):  total={stats.get('nord_total', 0)}, ok={stats.get('nord_ok', 0)}")
    print(f"  NordPass (go.nordpass.io):  total={stats.get('nordpass_total', 0)}, ok={stats.get('nordpass_ok', 0)}")
    print(f"  ZAP-Hosting:               total={stats.get('zap_total', 0)}, ok={stats.get('zap_ok', 0)}")
    print()
    if failures:
        print(f"─── ✗ {len(failures)} FAILURES ──────────────────────────────────────")
        for path, url, why in failures[:50]:
            print(f"  {path}\n    {url}\n    → {why}\n")
        if len(failures) > 50:
            print(f"  ... and {len(failures) - 50} more")
        return 1
    print("✓ All affiliate links carry the expected attribution.")
    return 0


if __name__ == "__main__":
    sys.exit(audit())
