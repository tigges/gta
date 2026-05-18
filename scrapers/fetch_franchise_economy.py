"""
fetch_franchise_economy.py — Cross-title GTA franchise economic history.

Scrapes the GTA Fandom Wiki for mission payouts and property/asset prices
across all mainline GTA titles (III → GTA VI), then computes normalised
economic metrics for cross-title comparison.

Key metric: "Hours to aspirational purchase" (Big Mac Index for GTA)
  = price of the most aspirational item in each title
  ÷ maximum efficient hourly earnings

This exposes the evolution of GTA's economic design across 25 years:
from simple mission payments (III) to live-service empire (Online).

Sources:
  GTA Fandom Wiki — mission payout tables, asset/property pages
  Curated seed — economic metadata, complexity scores, aspirational items

Output:
  data/franchise/economic-history.json

Usage:
  python3 scrapers/fetch_franchise_economy.py
"""

import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from utils import write_json, has_changed, now_iso

WIKI_API = "https://gta.fandom.com/api.php"
HEADERS  = {"User-Agent": "gtavi.ai-bot/1.0 (+https://gtavi.ai; franchise-economy-research)"}
DELAY    = 0.5
OUT_PATH = "franchise/economic-history.json"


# ── Per-title configuration ───────────────────────────────────────────────────
# Each entry defines: what to scrape + curated economic metadata
# scraped data supplements the curated seed

TITLES: list[dict] = [
    {
        "id":            "gta-1",
        "short":         "GTA 1",
        "release_year":  1997,
        "platform":      "PC/PS1",
        "wiki_missions": None,   # No structured payout table on wiki
        "economic_features": ["missions"],
        "passive_income":    False,
        "investment_mechanics": False,
        "real_money_purchases": False,
        "property_market":   False,
        # Curated data
        "avg_mission_payout":   5000,
        "top_mission_payout":   50000,
        "best_gta_per_hr":      30000,
        "aspirational_item":    "Gang territory control",
        "aspirational_price":   None,
        "hours_to_aspirational": None,
        "top_earner":           "Completing missions / collecting hidden packages",
        "currency_note":        "GTA$ as abstract reward. No significant purchases.",
        "complexity_score":     1,
        "complexity_breakdown": {
            "mission_income": True, "passive_income": False, "property_market": False,
            "businesses": False, "investment": False, "multiplayer_economy": False,
            "microtransactions": False,
        },
        "notes": "Top-down 2D. Economy was rudimentary — missions paid fixed amounts, few meaningful purchases.",
    },
    {
        "id":            "gta-2",
        "short":         "GTA 2",
        "release_year":  1999,
        "platform":      "PC/PS1/DC",
        "wiki_missions": None,
        "economic_features": ["missions", "score_multiplier"],
        "passive_income":    False,
        "investment_mechanics": False,
        "real_money_purchases": False,
        "property_market":   False,
        "avg_mission_payout":   10000,
        "top_mission_payout":   100000,
        "best_gta_per_hr":      60000,
        "aspirational_item":    "Gang allegiance / high score",
        "aspirational_price":   None,
        "hours_to_aspirational": None,
        "top_earner":           "Mission chains with score multipliers",
        "currency_note":        "Score + GTA$ hybrid. Church save cost $50,000.",
        "complexity_score":     2,
        "complexity_breakdown": {
            "mission_income": True, "passive_income": False, "property_market": False,
            "businesses": False, "investment": False, "multiplayer_economy": False,
            "microtransactions": False,
        },
        "notes": "Introduced score multipliers — moral economy (gang reputation). Save mechanic had a cost.",
    },
    {
        "id":            "gta-3",
        "short":         "GTA III",
        "release_year":  2001,
        "platform":      "PS2/PC/Xbox",
        "wiki_missions": "Missions in GTA III",
        "economic_features": ["missions", "safehouse"],
        "passive_income":    False,
        "investment_mechanics": False,
        "real_money_purchases": False,
        "property_market":   False,
        "avg_mission_payout":   10000,
        "top_mission_payout":   100000,
        "best_gta_per_hr":      60000,
        "aspirational_item":    "Banshee sports car (steal; no buy price in shops)",
        "aspirational_price":   None,
        "hours_to_aspirational": None,
        "top_earner":           "Late-game story missions ($20k-$100k)",
        "currency_note":        "First 3D GTA economy. Portland Safehouse $1,500. Hidden package rewards.",
        "complexity_score":     2,
        "complexity_breakdown": {
            "mission_income": True, "passive_income": False, "property_market": False,
            "businesses": False, "investment": False, "multiplayer_economy": False,
            "microtransactions": False,
        },
        "notes": "Pure mission economy. Vehicles cannot be bought — only stolen. Economy serves narrative.",
    },
    {
        "id":            "gta-vc",
        "short":         "GTA Vice City",
        "release_year":  2002,
        "platform":      "PS2/PC/Xbox",
        "wiki_missions": "Missions in GTA Vice City",
        "wiki_assets":   "Assets in GTA Vice City",
        "economic_features": ["missions", "property_purchase", "passive_income", "vehicle_purchase"],
        "passive_income":    True,
        "investment_mechanics": False,
        "real_money_purchases": False,
        "property_market":   True,
        "avg_mission_payout":   8000,
        "top_mission_payout":   50000,
        "best_gta_per_hr":      120000,
        "aspirational_item":    "Malibu Club",
        "aspirational_price":   120000,
        "hours_to_aspirational": 1.0,
        "top_earner":           "Pole Position Club (full assets: $12k + passive income)",
        "currency_note":        "First purchasable businesses/assets in 3D GTA. Vercetti Estate $250,000.",
        "complexity_score":     5,
        "complexity_breakdown": {
            "mission_income": True, "passive_income": True, "property_market": True,
            "businesses": True, "investment": False, "multiplayer_economy": False,
            "microtransactions": False,
        },
        "notes": "Landmark: first 3D GTA with purchasable businesses generating passive income. The template for GTA Online.",
    },
    {
        "id":            "gta-sa",
        "short":         "GTA San Andreas",
        "release_year":  2004,
        "platform":      "PS2/PC/Xbox",
        "wiki_missions": "Missions in GTA San Andreas",
        "wiki_assets":   "Businesses in GTA San Andreas",
        "economic_features": ["missions", "property_purchase", "passive_income",
                              "vehicle_purchase", "gang_territory", "gambling", "stocks_prototype"],
        "passive_income":    True,
        "investment_mechanics": True,
        "real_money_purchases": False,
        "property_market":   True,
        "avg_mission_payout":   10000,
        "top_mission_payout":   100000,
        "best_gta_per_hr":      200000,
        "aspirational_item":    "Four Dragons Casino ($500,000) or Verdant Meadows airstrip",
        "aspirational_price":   500000,
        "hours_to_aspirational": 2.5,
        "top_earner":           "Robbery missions + territory income (up to $10k/territory held)",
        "currency_note":        "Most complex pre-Online economy. 3 cities, gang territories, betting, import/export. Houses across map.",
        "complexity_score":     7,
        "complexity_breakdown": {
            "mission_income": True, "passive_income": True, "property_market": True,
            "businesses": True, "investment": True, "multiplayer_economy": False,
            "microtransactions": False,
        },
        "notes": "Peak single-player GTA economy. Gang territory generates periodic income. Casino gambling. Vehicle import/export. The blueprint for complexity.",
    },
    {
        "id":            "gta-4",
        "short":         "GTA IV",
        "release_year":  2008,
        "platform":      "PS3/X360/PC",
        "wiki_missions": "Missions in GTA IV",
        "economic_features": ["missions"],
        "passive_income":    False,
        "investment_mechanics": False,
        "real_money_purchases": False,
        "property_market":   False,
        "avg_mission_payout":   5000,
        "top_mission_payout":   250000,
        "best_gta_per_hr":      80000,
        "aspirational_item":    "Infernus supercar",
        "aspirational_price":   95000,
        "hours_to_aspirational": 1.2,
        "top_earner":           "Three Leaf Clover bank job ($250,000 one-time) or late missions",
        "currency_note":        "Deliberate economic regression. Rockstar stripped property/business systems for realism. No vehicle shops.",
        "complexity_score":     2,
        "complexity_breakdown": {
            "mission_income": True, "passive_income": False, "property_market": False,
            "businesses": False, "investment": False, "multiplayer_economy": False,
            "microtransactions": False,
        },
        "notes": "Economic regression by design. Niko is a criminal, not a businessman. Liberty City feels more grounded with no empire to build.",
    },
    {
        "id":            "gta-4-tlad",
        "short":         "TLaD (GTA IV)",
        "release_year":  2009,
        "platform":      "PS3/X360/PC",
        "wiki_missions": None,
        "economic_features": ["missions", "gang_business"],
        "passive_income":    False,
        "investment_mechanics": False,
        "real_money_purchases": False,
        "property_market":   False,
        "avg_mission_payout":   8000,
        "top_mission_payout":   150000,
        "best_gta_per_hr":      90000,
        "aspirational_item":    "Club income (The Lost MC)",
        "aspirational_price":   None,
        "hours_to_aspirational": None,
        "top_earner":           "Lost MC clubhouse business income (~minor passive)",
        "complexity_score":     3,
        "complexity_breakdown": {
            "mission_income": True, "passive_income": True, "property_market": False,
            "businesses": True, "investment": False, "multiplayer_economy": False,
            "microtransactions": False,
        },
        "notes": "Added minor passive income via club operations — a half-step back toward VC/SA mechanics.",
    },
    {
        "id":            "gta-5",
        "short":         "GTA V (Story)",
        "release_year":  2013,
        "platform":      "PS3/X360/PS4/XB1/PC/PS5/XBS",
        "wiki_missions": "Missions in GTA V",
        "economic_features": ["missions", "heists", "property_purchase",
                              "passive_income", "stock_market", "vehicle_purchase"],
        "passive_income":    True,
        "investment_mechanics": True,
        "real_money_purchases": False,
        "property_market":   True,
        "avg_mission_payout":   15000,
        "top_mission_payout":   41600000,
        "best_gta_per_hr":      2000000,
        "aspirational_item":    "Adder supercar",
        "aspirational_price":   1000000,
        "hours_to_aspirational": 0.5,
        "top_earner":           "The Big Score + assassination stock plays ($2B+ theoretical)",
        "currency_note":        "Stock market (LCN + BAWSAQ) first proper investment system. Assassination plays multiply wealth by 10-20× if done last.",
        "complexity_score":     7,
        "complexity_breakdown": {
            "mission_income": True, "passive_income": True, "property_market": True,
            "businesses": True, "investment": True, "multiplayer_economy": False,
            "microtransactions": False,
        },
        "notes": "The Big Score is the economic climax. Stock market assassination plays are the most sophisticated single-player economy mechanic in the franchise.",
    },
    {
        "id":            "gta-online",
        "short":         "GTA Online",
        "release_year":  2013,
        "platform":      "PS3/X360/PS4/XB1/PC/PS5/XBS",
        "wiki_missions": "Missions in GTA Online",
        "economic_features": ["missions", "heists", "property_purchase", "passive_income",
                              "business_empire", "vehicle_purchase", "microtransactions",
                              "weekly_events", "stock_market"],
        "passive_income":    True,
        "investment_mechanics": True,
        "real_money_purchases": True,
        "property_market":   True,
        "avg_mission_payout":   20000,
        "top_mission_payout":   1200000,
        "best_gta_per_hr":      1700000,
        "aspirational_item":    "Full meta stack (Kosatka + Oppressor Mk2 + Nightclub + Bunker + Acid Lab)",
        "aspirational_price":   35000000,
        "hours_to_aspirational": 21.0,
        "top_earner":           "Cayo Perico Heist solo ($1.2M/hr, $340k net per run)",
        "currency_note":        "Shark Cards: $18.75 USD for endgame in 2013, $437.50 USD in 2026. 23.3× inflation.",
        "complexity_score":     10,
        "complexity_breakdown": {
            "mission_income": True, "passive_income": True, "property_market": True,
            "businesses": True, "investment": True, "multiplayer_economy": True,
            "microtransactions": True,
        },
        "notes": "Live service economy. The most complex virtual economy in mainstream gaming. Weekly Rockstar manipulation via bonus events.",
    },
    {
        "id":            "gta-6",
        "short":         "GTA VI",
        "release_year":  2026,
        "platform":      "PS5/XBS",
        "wiki_missions": None,
        "economic_features": ["missions", "TBD"],
        "passive_income":    None,
        "investment_mechanics": None,
        "real_money_purchases": True,
        "property_market":   None,
        "avg_mission_payout":   None,
        "top_mission_payout":   None,
        "best_gta_per_hr":      None,
        "aspirational_item":    "TBD — Day-1 ready, populate at launch",
        "aspirational_price":   None,
        "hours_to_aspirational": None,
        "top_earner":           "TBD",
        "currency_note":        "GTA VI economy details not confirmed pre-launch.",
        "complexity_score":     None,
        "complexity_breakdown": None,
        "notes": "Schema ready. Auto-populates from GTA VI wiki at launch via fetch_gta_wiki.py.",
    },
]


# ── Wiki scrapers ─────────────────────────────────────────────────────────────

def parse_money(text: str) -> int | None:
    t = text.replace(",", "").replace("$", "").replace("GTA", "").strip()
    # Handle ranges — take higher value
    if "–" in t or "-" in t:
        parts = re.split(r"[–\-]", t)
        vals = [parse_money(p) for p in parts]
        valid = [v for v in vals if v]
        return max(valid) if valid else None
    try:
        v = float(re.sub(r"[^0-9.]", "", t))
        return int(v) if v > 0 else None
    except (ValueError, TypeError):
        return None


def fetch_mission_payouts(session: requests.Session, page: str) -> list[dict]:
    """Extract mission payouts from a 'Missions in GTA X' wiki page."""
    try:
        r = session.get(WIKI_API, params={
            "action": "parse", "page": page,
            "prop":   "wikitext", "format": "json",
        }, headers=HEADERS, timeout=20)
        r.raise_for_status()
        wt = r.json().get("parse", {}).get("wikitext", {}).get("*", "")
    except Exception as e:
        print(f"  warn: could not fetch {page}: {e}")
        return []

    missions: list[dict] = []

    # Extract current section heading (mission giver)
    current_giver = ""
    current_section = ""

    for line in wt.split("\n"):
        # Section headers
        hdr_m = re.match(r"={2,4}\s*(.+?)\s*={2,4}", line)
        if hdr_m:
            raw = hdr_m.group(1)
            # Clean wiki links
            clean = re.sub(r"\[\[(?:[^\|\]]+\|)?([^\]]+)\]\]", r"\1", raw)
            clean = re.sub(r"'{2,}", "", clean).strip()
            # Skip file/icon patterns
            if "File:" not in raw and "Image:" not in raw and len(clean) < 60:
                current_giver = clean
            continue

        # Mission rows: lines starting with | that contain [[Mission Name]]
        if not line.startswith("|"):
            continue
        link_m = re.search(r"\[\[([^\]\|#]+)(?:\|([^\]]+))?\]\]", line)
        if not link_m:
            continue
        title = (link_m.group(2) or link_m.group(1)).strip()
        if not title or len(title) < 3:
            continue

        # Extract payout — look for $NUMBER pattern on this line
        payout_m = re.search(r"\$([\d,]+)", line)
        payout = parse_money(payout_m.group(0)) if payout_m else None

        if title and (payout or True):  # include even without payout for completeness
            missions.append({
                "title":   title,
                "giver":   current_giver,
                "payout":  payout,
            })

    return missions


def fetch_assets(session: requests.Session, page: str) -> list[dict]:
    """Extract asset/business purchase prices from a VC/SA assets page."""
    try:
        r = session.get(WIKI_API, params={
            "action": "parse", "page": page,
            "prop":   "wikitext", "format": "json",
        }, headers=HEADERS, timeout=20)
        r.raise_for_status()
        wt = r.json().get("parse", {}).get("wikitext", {}).get("*", "")
    except Exception as e:
        print(f"  warn: could not fetch {page}: {e}")
        return []

    assets: list[dict] = []

    # Parse wikitable rows: |Name || $Purchase_Price || $Daily_Income
    rows = re.findall(
        r"\|\s*\[\[([^\]]+)\]\][^\n]*\n"
        r"\|\s*\$?([\d,]+)[^\n]*\n"
        r"\|\s*\$?([\d,]+)",
        wt
    )
    for name_raw, price_raw, income_raw in rows:
        name   = re.sub(r"\|.*", "", name_raw).strip()
        price  = parse_money(price_raw)
        income = parse_money(income_raw)
        if name and price:
            assets.append({"name": name, "purchase_price": price, "daily_income": income})

    # Also try simpler pattern: |$X on its own line
    if not assets:
        current_name = ""
        current_price = None
        for line in wt.split("\n"):
            link_m = re.search(r"\[\[([^\]\|#]+)(?:\|([^\]]+))?\]\]", line)
            if link_m:
                current_name = (link_m.group(2) or link_m.group(1)).strip()
            if current_name and line.strip().startswith("|"):
                pm = re.search(r"\$([\d,]+)", line)
                if pm:
                    val = parse_money(pm.group(0))
                    if val and val > 1000:
                        if current_price is None:
                            current_price = val
                        else:
                            assets.append({
                                "name": current_name,
                                "purchase_price": current_price,
                                "daily_income": val,
                            })
                            current_name = ""
                            current_price = None

    return assets


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("[fetch_franchise_economy] Building cross-title economic history…")

    session = requests.Session()
    output_titles: list[dict] = []

    for title in TITLES:
        print(f"\n  [{title['release_year']}] {title['short']}")

        entry: dict = {**title}  # start with curated metadata

        # Fetch missions if wiki page configured
        if title.get("wiki_missions"):
            time.sleep(DELAY)
            missions = fetch_mission_payouts(session, title["wiki_missions"])
            missions_with_payout = [m for m in missions if m.get("payout")]
            payouts = [m["payout"] for m in missions_with_payout]

            if payouts:
                wiki_top = max(payouts)
                wiki_avg = sum(payouts) // len(payouts)
                # Only override curated if wiki gives more data
                if wiki_top > (title.get("top_mission_payout") or 0):
                    entry["top_mission_payout"] = wiki_top
                entry["mission_count"] = len(missions)
                entry["missions_with_payout"] = len(missions_with_payout)
                print(f"    missions: {len(missions)} scraped, {len(missions_with_payout)} with payout, top=${wiki_top:,}")
            else:
                entry["mission_count"] = len(missions)
                print(f"    missions: {len(missions)} scraped, no payouts extracted")

            # Store top-10 by payout for the data file
            top_missions = sorted(missions_with_payout, key=lambda m: m["payout"], reverse=True)[:10]
            entry["top_missions"] = top_missions

        # Fetch assets for VC/SA
        if title.get("wiki_assets"):
            time.sleep(DELAY)
            assets = fetch_assets(session, title["wiki_assets"])
            if assets:
                entry["assets"] = assets
                print(f"    assets: {len(assets)} scraped")
            else:
                print(f"    assets: none extracted")

        # Compute normalised effort cost (if we have the data)
        hrly = entry.get("best_gta_per_hr")
        asp  = entry.get("aspirational_price")
        if hrly and asp:
            entry["hours_to_aspirational"] = round(asp / hrly, 1)

        output_titles.append(entry)

    # ── Compute economic complexity ranking ───────────────────────────────────
    scores = [(t["id"], t["complexity_score"] or 0) for t in output_titles if t["complexity_score"] is not None]
    scores.sort(key=lambda x: x[1], reverse=True)

    print(f"\n  Economic complexity ranking:")
    for rank, (gid, score) in enumerate(scores, 1):
        t = next(t for t in output_titles if t["id"] == gid)
        print(f"    #{rank}  {t['short']:20} {score}/10  {t['top_earner'][:40]}")

    # ── Normalised effort chart data ──────────────────────────────────────────
    effort_data = [
        {
            "id":    t["id"],
            "short": t["short"],
            "year":  t["release_year"],
            "aspirational_item":    t.get("aspirational_item"),
            "aspirational_price":   t.get("aspirational_price"),
            "best_gta_per_hr":      t.get("best_gta_per_hr"),
            "hours_to_aspirational":t.get("hours_to_aspirational"),
            "complexity_score":     t.get("complexity_score"),
        }
        for t in output_titles
        if t.get("hours_to_aspirational") is not None and t.get("complexity_score") is not None
    ]

    output = {
        "last_updated":    now_iso(),
        "source":          "GTA Fandom Wiki + curated research (GTAForums, community archives)",
        "schema_version":  "1.0",
        "note": (
            "Cross-title GTA franchise economic history. "
            "hours_to_aspirational = aspirational_price / best_gta_per_hr — the 'Big Mac Index' for GTA. "
            "complexity_score = 1-10 based on number of active economic mechanics. "
            "GTA VI entry is a pre-launch stub."
        ),
        "title_count":     len(output_titles),
        "effort_chart_data": effort_data,
        "titles":          output_titles,
    }

    if has_changed(output, OUT_PATH):
        write_json(OUT_PATH, output)
        print(f"\n[fetch_franchise_economy] ✓ Saved {len(output_titles)} titles")
    else:
        print("\n[fetch_franchise_economy] No changes")

    print("[fetch_franchise_economy] Done.")


if __name__ == "__main__":
    main()
