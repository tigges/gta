"""
GTA VI pre-order retailer listing monitor.

Watches official product listing pages at major retailers for GTA VI.
When a listing goes live (price, editions, availability), this is
typically the first public confirmation before any official announcement.

Sources:
  - PlayStation Store (US) — store.playstation.com
  - Xbox Store (US) — Microsoft Catalog API (bigId: 9nl3wwnzlzzn)
  - Amazon US — amazon.com/s?k=grand+theft+auto+6
  - Best Buy US — bestbuy.com/site/searchpage.jsp
  - GameStop US — gamestop.com/search

Output: data/feeds/preorder-listings.json
  status: "not_live" | "wishlist" | "pre_order" | "available"
  Each retailer tracked independently with its current state.

No API key required. Xbox uses the public Microsoft Catalog API.
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


# ── Xbox Store ─────────────────────────────────────────────────────────────

# Confirmed Xbox Store product ID for Grand Theft Auto VI.
# Source: xbox.com/en-US/games/store/grand-theft-auto-vi/9nl3wwnzlzzn
XBOX_GTA6_PRODUCT_ID = "9nl3wwnzlzzn"
XBOX_CATALOG_URL = (
    f"https://displaycatalog.mp.microsoft.com/v7.0/products"
    f"?bigIds={XBOX_GTA6_PRODUCT_ID}&market=US&languages=en-us"
    f"&MS-CV=DGU1mcuYo0WMMp+F.1"
)
XBOX_STORE_URL = f"https://www.xbox.com/en-US/games/store/grand-theft-auto-vi/{XBOX_GTA6_PRODUCT_ID}"


def check_xbox_store() -> dict:
    """
    Xbox Store via Microsoft Catalog API.

    Uses the public displaycatalog endpoint — no auth required.
    Status logic:
      pre_order  — product has a Fulfill action AND a non-zero list price
      wishlist   — product exists in catalog, Fulfill available, price = 0
      not_live   — product not found or catalog error
    """
    try:
        resp = requests.get(XBOX_CATALOG_URL, timeout=15)
        if not resp.ok:
            return {
                "retailer": "Xbox Store",
                "status": "unknown",
                "note": f"Catalog API HTTP {resp.status_code}",
                "url": XBOX_STORE_URL,
            }

        products = resp.json().get("Products", [])
        if not products:
            return {"retailer": "Xbox Store", "status": "not_live", "url": XBOX_STORE_URL}

        prod = products[0]
        title_props = (prod.get("LocalizedProperties") or [{}])[0]
        found_title = title_props.get("ProductTitle", "")

        can_fulfill = False
        has_price   = False
        price_str   = None

        for sku_avail in prod.get("DisplaySkuAvailabilities", []):
            for avail in sku_avail.get("Availabilities", []):
                actions = avail.get("Actions", [])
                if "Fulfill" in actions:
                    can_fulfill = True
                    price = (
                        avail.get("OrderManagementData", {})
                        .get("Price", {})
                    )
                    list_price = price.get("ListPrice") or 0.0
                    if list_price and list_price > 0:
                        has_price = True
                        price_str = f"${list_price:.2f}"

        if can_fulfill and has_price:
            result = {"retailer": "Xbox Store", "status": "pre_order", "url": XBOX_STORE_URL}
            if found_title:
                result["found_title"] = found_title[:80]
            if price_str:
                result["price"] = price_str
            return result

        if can_fulfill or found_title:
            return {
                "retailer": "Xbox Store",
                "status": "wishlist",
                "url": XBOX_STORE_URL,
                "found_title": found_title[:80] if found_title else None,
                "note": "Listed in catalog — price not yet set",
            }

        return {"retailer": "Xbox Store", "status": "not_live", "url": XBOX_STORE_URL}

    except Exception as e:
        return {"retailer": "Xbox Store", "status": "error", "error": str(e)[:120], "url": XBOX_STORE_URL}


def main() -> None:
    print("Checking GTA VI retailer listings...")

    listings = []
    for check_fn in [check_psstore, check_xbox_store, check_amazon, check_bestbuy, check_gamestop]:
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
