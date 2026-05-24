"""
GTA VI pre-order retailer listing monitor.

Watches official product listing pages at major retailers for GTA VI.
When a listing goes live (price, editions, availability), this is
typically the first public confirmation before any official announcement.

Sources:
  - PlayStation Store (US) — ps.store/search
  - Xbox Store (US) — xbox.com/search
  - Amazon US — amazon.com/s?k=grand+theft+auto+6
  - Best Buy US — bestbuy.com/site/searchpage.jsp
  - GameStop US — gamestop.com/search

Output: data/feeds/preorder-listings.json
  status: "not_live" | "wishlist" | "pre_order" | "available"
  Each retailer tracked independently with its current state.

No API key required — HTML scrape only.
"""

import re
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from utils import has_changed, now_iso, write_json

import requests
from bs4 import BeautifulSoup

OUT_PATH = "feeds/preorder-listings.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

GTA_PATTERNS = [
    r"grand theft auto.{0,10}(vi|6)",
    r"gta.{0,4}(vi|6)",
    r"gta6",
    r"gta vi",
]


def contains_gta6(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in GTA_PATTERNS)


def check_amazon() -> dict:
    try:
        resp = requests.get(
            "https://www.amazon.com/s?k=grand+theft+auto+6+ps5",
            headers=HEADERS, timeout=20,
        )
        soup = BeautifulSoup(resp.text, "lxml")
        results = soup.find_all("div", {"data-component-type": "s-search-result"})
        for r in results:
            title_el = r.find("h2")
            if title_el and contains_gta6(title_el.get_text()):
                price_el = r.find("span", class_="a-price-whole")
                status = "pre_order" if price_el else "wishlist"
                return {
                    "retailer": "Amazon US",
                    "status": status,
                    "url": "https://www.amazon.com/s?k=grand+theft+auto+6+ps5",
                    "found_title": title_el.get_text(strip=True)[:80],
                    "price": f"${price_el.get_text(strip=True)}" if price_el else None,
                }
        return {"retailer": "Amazon US", "status": "not_live", "url": "https://www.amazon.com/s?k=grand+theft+auto+6+ps5"}
    except Exception as e:
        return {"retailer": "Amazon US", "status": "error", "error": str(e)[:100]}


def check_bestbuy() -> dict:
    """Best Buy scraper — returns 'unknown' on timeout (bot detection) rather than 'error'."""
    bb_url = "https://www.bestbuy.com/site/searchpage.jsp?st=grand+theft+auto+6"
    # Best Buy applies aggressive bot detection that causes connection hangs on server IPs.
    # Use a session with realistic browser headers and a tight 12 s timeout.
    session = requests.Session()
    bb_headers = {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }
    try:
        resp = session.get(bb_url, headers=bb_headers, timeout=12, allow_redirects=True)
        if not resp.ok:
            return {"retailer": "Best Buy US", "status": "unknown",
                    "note": f"HTTP {resp.status_code} — bot-gated or geo-blocked", "url": bb_url}

        soup = BeautifulSoup(resp.text, "lxml")
        items = soup.find_all(class_=re.compile(r"sku-title|product-title"))
        for item in items:
            if contains_gta6(item.get_text()):
                card = item.find_parent(class_=re.compile(r"sku-item|list-item"))
                pre_order_btn = card.find(string=re.compile(r"pre.order|add to cart", re.I)) if card else None
                status = "pre_order" if pre_order_btn else "wishlist"
                return {
                    "retailer": "Best Buy US",
                    "status": status,
                    "url": bb_url,
                    "found_title": item.get_text(strip=True)[:80],
                }
        return {"retailer": "Best Buy US", "status": "not_live", "url": bb_url}

    except requests.exceptions.Timeout:
        # Timeout = bot-detection hang (not a real error — data is simply unavailable)
        return {"retailer": "Best Buy US", "status": "unknown",
                "note": "unreachable from server IP (timeout — bot detection)", "url": bb_url}
    except Exception as e:
        return {"retailer": "Best Buy US", "status": "error", "error": str(e)[:120], "url": bb_url}


def check_gamestop() -> dict:
    try:
        resp = requests.get(
            "https://www.gamestop.com/search#q=grand+theft+auto+6&t=products",
            headers=HEADERS, timeout=20,
        )
        text = resp.text.lower()
        if contains_gta6(text):
            status = "pre_order" if "pre-order" in text or "preorder" in text else "wishlist"
            return {
                "retailer": "GameStop US",
                "status": status,
                "url": "https://www.gamestop.com/search#q=grand+theft+auto+6",
            }
        return {"retailer": "GameStop US", "status": "not_live", "url": "https://www.gamestop.com/search#q=grand+theft+auto+6"}
    except Exception as e:
        return {"retailer": "GameStop US", "status": "error", "error": str(e)[:100]}


def check_psstore() -> dict:
    """PlayStation Store US search API."""
    try:
        resp = requests.get(
            "https://store.playstation.com/en-us/search/grand%20theft%20auto%206",
            headers=HEADERS, timeout=20,
        )
        text = resp.text.lower()
        if contains_gta6(text):
            status = "pre_order" if "pre-order" in text or "add to cart" in text else "wishlist"
            return {
                "retailer": "PlayStation Store",
                "status": status,
                "url": "https://store.playstation.com/en-us/search/grand%20theft%20auto%206",
            }
        return {"retailer": "PlayStation Store", "status": "not_live", "url": "https://store.playstation.com/en-us/search/grand%20theft%20auto%206"}
    except Exception as e:
        return {"retailer": "PlayStation Store", "status": "error", "error": str(e)[:100]}


def main() -> None:
    print("Checking GTA VI retailer listings...")

    listings = []
    for check_fn in [check_amazon, check_bestbuy, check_gamestop, check_psstore]:
        result = check_fn()
        status = result.get("status", "unknown")
        icon = "🟢" if status == "pre_order" else "🟡" if status == "wishlist" else "⚪" if status == "not_live" else "🔴"
        print(f"  {icon} {result['retailer']}: {status}")
        result["checked_at"] = now_iso()
        listings.append(result)

    live_count = sum(1 for l in listings if l["status"] in ("pre_order", "wishlist"))

    payload = {
        "last_updated": now_iso(),
        "summary": f"{live_count}/{len(listings)} retailers have GTA VI listed",
        "pre_orders_live": any(l["status"] == "pre_order" for l in listings),
        "wishlists_live":  any(l["status"] == "wishlist" for l in listings),
        "listings": listings,
    }

    if has_changed(payload, OUT_PATH):
        write_json(OUT_PATH, payload)
        if payload["pre_orders_live"]:
            print("🚨 GTA VI PRE-ORDERS ARE LIVE at one or more retailers!")
        elif payload["wishlists_live"]:
            print("📋 GTA VI wishlist/coming-soon listings found — pre-orders expected soon.")
        else:
            print("Pre-order listings: not yet live at any monitored retailer.")
    else:
        print("No changes detected.")


if __name__ == "__main__":
    main()
