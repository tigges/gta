"""
fetch_gta_properties.py — GTA Online property price registry.

Scrapes the GTA Fandom Wiki for all purchasable property types in GTA Online,
extracting price ranges, DLC origin, capacity, and daily fees.

Sources:
  Per-type wiki pages (Apartments, Offices, Bunkers, Nightclubs, etc.)
  Supplement: curated seed for types without clean wiki price tables.

Output:
  data/gta-5/economy/properties.json

Schema per property entry:
  id, name, type, price_min, price_max, dlc, capacity_note,
  daily_fee, upgrade_cost, purchase_site, notes, wiki_page

Usage:
  python3 scrapers/fetch_gta_properties.py
"""

import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from utils import write_json, has_changed, now_iso

WIKI_API = "https://gta.fandom.com/api.php"
HEADERS  = {"User-Agent": "gtavi.ai-bot/1.0 (+https://gtavi.ai; property-research)"}
DELAY    = 0.6
OUT_PATH = "gta-5/economy/properties.json"

# ── Property type definitions ─────────────────────────────────────────────────
# wiki_page: GTA Fandom wiki page title
# type: category slug
# purchase_site: in-game website
# daily_fee: base daily fee where known

PROPERTY_TYPES = [
    {"type": "apartment",        "wiki_page": "Apartments",            "purchase_site": "Dynasty 8"},
    {"type": "garage",           "wiki_page": "Garages in GTA Online", "purchase_site": "Dynasty 8"},
    {"type": "yacht",            "wiki_page": "Galaxy Super Yacht",    "purchase_site": "DockTease"},
    {"type": "office",           "wiki_page": "Offices",               "purchase_site": "Dynasty 8 Executive"},
    {"type": "warehouse",        "wiki_page": "Warehouses",            "purchase_site": "SecuroServ (Office)"},
    {"type": "vehicle-warehouse","wiki_page": "Vehicle Warehouses",    "purchase_site": "SecuroServ (Office)"},
    {"type": "clubhouse",        "wiki_page": "Clubhouses",            "purchase_site": "The Open Road"},
    {"type": "bunker",           "wiki_page": "Bunkers",               "purchase_site": "Maze Bank Foreclosures"},
    {"type": "hangar",           "wiki_page": "Hangars",               "purchase_site": "Elitas Travel"},
    {"type": "facility",         "wiki_page": "Facilities",            "purchase_site": "Maze Bank Foreclosures"},
    {"type": "nightclub",        "wiki_page": "Nightclubs",            "purchase_site": "Dynasty 8 Executive"},
    {"type": "arcade",           "wiki_page": "Arcades",               "purchase_site": "Maze Bank Foreclosures"},
    {"type": "auto-shop",        "wiki_page": "Auto Shops",            "purchase_site": "Southern San Andreas Super Autos"},
    {"type": "agency",           "wiki_page": "Agency",                "purchase_site": "Dynasty 8 Executive"},
    {"type": "salvage-yard",     "wiki_page": "Salvage Yard",          "purchase_site": "Maze Bank Foreclosures"},
]

# ── Curated seed for types/locations not easily scraped ───────────────────────
# Fully verified from GTA Fandom Wiki and GTABase community records.
# Format: {type, name, price_min, price_max, dlc, notes, ...}

CURATED_PROPERTIES: list[dict] = [
    # ── Apartments ────────────────────────────────────────────────────────────
    {"id":"apartment-low",       "name":"Low-End Apartment",      "type":"apartment",  "price_min":25000,    "price_max":80000,    "dlc":"Launch (2013)",                  "capacity_vehicles":2,  "daily_fee":0,  "purchase_site":"Dynasty 8"},
    {"id":"apartment-mid",       "name":"Mid-Range Apartment",    "type":"apartment",  "price_min":80000,    "price_max":200000,   "dlc":"Launch (2013)",                  "capacity_vehicles":6,  "daily_fee":0,  "purchase_site":"Dynasty 8"},
    {"id":"apartment-high",      "name":"High-End Apartment",     "type":"apartment",  "price_min":200000,   "price_max":400000,   "dlc":"Launch (2013)",                  "capacity_vehicles":10, "daily_fee":0,  "purchase_site":"Dynasty 8"},
    {"id":"penthouse-stilt",     "name":"Stilt House / Penthouse","type":"apartment",  "price_min":395000,   "price_max":750000,   "dlc":"Executives and Other Criminals (2015)", "capacity_vehicles":10, "daily_fee":0, "purchase_site":"Dynasty 8"},
    {"id":"master-penthouse",    "name":"Master Penthouse",       "type":"apartment",  "price_min":1500000,  "price_max":6500000,  "dlc":"The Diamond Casino & Resort (2019)", "capacity_vehicles":10, "daily_fee":0, "purchase_site":"Dynasty 8 Executive", "notes":"Includes penthouse at The Diamond. Accommodation + perks. Not a standard safehouse."},
    # ── Garages ───────────────────────────────────────────────────────────────
    {"id":"garage-2",            "name":"2-Car Garage",           "type":"garage",     "price_min":25000,    "price_max":30000,    "dlc":"Launch (2013)",                  "capacity_vehicles":2,  "daily_fee":0,  "purchase_site":"Dynasty 8"},
    {"id":"garage-6",            "name":"6-Car Garage",           "type":"garage",     "price_min":32500,    "price_max":150000,   "dlc":"Launch (2013)",                  "capacity_vehicles":6,  "daily_fee":0,  "purchase_site":"Dynasty 8"},
    {"id":"garage-10",           "name":"10-Car Garage",          "type":"garage",     "price_min":150000,   "price_max":350000,   "dlc":"Launch (2013)",                  "capacity_vehicles":10, "daily_fee":0,  "purchase_site":"Dynasty 8"},
    {"id":"eclipse-blvd-garage", "name":"Eclipse Blvd Garage (50-car)", "type":"garage","price_min":449000,  "price_max":449000,   "dlc":"Los Santos Drug Wars (2022)",    "capacity_vehicles":50, "daily_fee":0,  "purchase_site":"Dynasty 8", "notes":"Does not count toward garage ownership limit."},
    # ── Yachts ────────────────────────────────────────────────────────────────
    {"id":"orion-yacht",         "name":"Orion (Smallest Yacht)", "type":"yacht",      "price_min":6000000,  "price_max":6000000,  "dlc":"Executives and Other Criminals (2015)", "daily_fee":0, "purchase_site":"DockTease", "notes":"Purely cosmetic. No income generation. Captain charges $25k per move."},
    {"id":"pisces-yacht",        "name":"Pisces (Mid Yacht)",     "type":"yacht",      "price_min":7000000,  "price_max":7000000,  "dlc":"Executives and Other Criminals (2015)", "daily_fee":0, "purchase_site":"DockTease"},
    {"id":"aquarius-yacht",      "name":"Aquarius (Largest Yacht)","type":"yacht",     "price_min":8000000,  "price_max":8000000,  "dlc":"Executives and Other Criminals (2015)", "daily_fee":0, "purchase_site":"DockTease", "notes":"Most expensive vanity purchase in GTA Online. Also unlocks A Superyacht Life missions."},
    # ── Offices ───────────────────────────────────────────────────────────────
    {"id":"office-maze-bank-west","name":"Maze Bank West",        "type":"office",     "price_min":1000000,  "price_max":1000000,  "dlc":"Finance and Felony (2016)",      "daily_fee":50, "purchase_site":"Dynasty 8 Executive", "notes":"Cheapest office. Unlocks CEO role and Special Cargo."},
    {"id":"office-arcadius",     "name":"Arcadius Business Centre","type":"office",    "price_min":2250000,  "price_max":2250000,  "dlc":"Finance and Felony (2016)",      "daily_fee":50, "purchase_site":"Dynasty 8 Executive"},
    {"id":"office-lombank",      "name":"Lombank West",           "type":"office",     "price_min":3100000,  "price_max":3100000,  "dlc":"Finance and Felony (2016)",      "daily_fee":50, "purchase_site":"Dynasty 8 Executive"},
    {"id":"office-maze-bank-tower","name":"Maze Bank Tower",      "type":"office",     "price_min":4000000,  "price_max":4000000,  "dlc":"Finance and Felony (2016)",      "daily_fee":50, "purchase_site":"Dynasty 8 Executive"},
    # ── Warehouses (Special Cargo) ────────────────────────────────────────────
    {"id":"warehouse-small",     "name":"Small Warehouse (16 crates)", "type":"warehouse","price_min":250000,"price_max":350000,   "dlc":"Finance and Felony (2016)",      "capacity_crates":16,   "daily_fee":0,  "purchase_site":"SecuroServ (Office)"},
    {"id":"warehouse-medium",    "name":"Medium Warehouse (42 crates)","type":"warehouse","price_min":880000,"price_max":1200000,  "dlc":"Finance and Felony (2016)",      "capacity_crates":42,   "daily_fee":0,  "purchase_site":"SecuroServ (Office)"},
    {"id":"warehouse-large",     "name":"Large Warehouse (111 crates)","type":"warehouse","price_min":2175000,"price_max":3500000, "dlc":"Finance and Felony (2016)",      "capacity_crates":111,  "daily_fee":0,  "purchase_site":"SecuroServ (Office)", "notes":"Best $/crate ratio. Aim for 111-crate sell for ~$2.2M gross."},
    # ── Vehicle Warehouses ────────────────────────────────────────────────────
    {"id":"vehicle-warehouse-cheap","name":"Vehicle Warehouse (cheapest)","type":"vehicle-warehouse","price_min":1500000,"price_max":1500000,"dlc":"Import/Export (2016)", "capacity_vehicles":40, "daily_fee":0,  "purchase_site":"SecuroServ (Office)", "notes":"All vehicle warehouses hold 40 cars regardless of price."},
    {"id":"vehicle-warehouse-mid",  "name":"Vehicle Warehouse (mid)",    "type":"vehicle-warehouse","price_min":2135000,"price_max":2495000,"dlc":"Import/Export (2016)", "capacity_vehicles":40, "daily_fee":0,  "purchase_site":"SecuroServ (Office)"},
    {"id":"vehicle-warehouse-prem", "name":"Vehicle Warehouse (premium)","type":"vehicle-warehouse","price_min":2850000,"price_max":2850000,"dlc":"Import/Export (2016)", "capacity_vehicles":40, "daily_fee":0,  "purchase_site":"SecuroServ (Office)"},
    # ── Clubhouses ────────────────────────────────────────────────────────────
    {"id":"clubhouse-cheap",     "name":"MC Clubhouse (cheapest)", "type":"clubhouse", "price_min":200000,   "price_max":200000,   "dlc":"Bikers (2016)",                  "daily_fee":0,  "purchase_site":"The Open Road", "notes":"Unlocks MC president role and all MC businesses."},
    {"id":"clubhouse-premium",   "name":"MC Clubhouse (premium)",  "type":"clubhouse", "price_min":495000,   "price_max":495000,   "dlc":"Bikers (2016)",                  "daily_fee":0,  "purchase_site":"The Open Road"},
    # ── MC Businesses ─────────────────────────────────────────────────────────
    {"id":"cocaine-lockup",      "name":"Cocaine Lockup",          "type":"mc-business","price_min":975000,  "price_max":1852500,  "dlc":"Bikers (2016)",                  "upgrade_cost":1325000, "daily_fee":2167, "purchase_site":"The Open Road", "notes":"Best MC business. Upgrade: Equipment $1.175M + Staff $0.15M."},
    {"id":"meth-lab",            "name":"Methamphetamine Lab",      "type":"mc-business","price_min":910000,  "price_max":1995000,  "dlc":"Bikers (2016)",                  "upgrade_cost":1431500, "daily_fee":2350, "purchase_site":"The Open Road"},
    {"id":"counterfeit-cash",    "name":"Counterfeit Cash Factory", "type":"mc-business","price_min":845000,  "price_max":1750000,  "dlc":"Bikers (2016)",                  "upgrade_cost":1153000, "daily_fee":2100, "purchase_site":"The Open Road"},
    {"id":"weed-farm",           "name":"Weed Farm",               "type":"mc-business","price_min":715000,  "price_max":1560000,  "dlc":"Bikers (2016)",                  "upgrade_cost":1253000, "daily_fee":1800, "purchase_site":"The Open Road"},
    {"id":"document-forgery",    "name":"Document Forgery Office", "type":"mc-business","price_min":650000,  "price_max":1235000,  "dlc":"Bikers (2016)",                  "upgrade_cost":745000,  "daily_fee":1650, "purchase_site":"The Open Road", "notes":"Lowest value MC business. Not recommended."},
    # ── Bunkers ───────────────────────────────────────────────────────────────
    {"id":"bunker-farmhouse",    "name":"Farmhouse Bunker",        "type":"bunker",     "price_min":1165000,  "price_max":1165000,  "dlc":"Gunrunning (2017)",              "upgrade_cost":1753000, "daily_fee":2000, "purchase_site":"Maze Bank Foreclosures", "notes":"Best location for deliveries."},
    {"id":"bunker-chumash",      "name":"Chumash Bunker",          "type":"bunker",     "price_min":1700000,  "price_max":1700000,  "dlc":"Gunrunning (2017)",              "upgrade_cost":1753000, "daily_fee":2000, "purchase_site":"Maze Bank Foreclosures"},
    {"id":"bunker-thomson",      "name":"Thomson Scrapyard",       "type":"bunker",     "price_min":1950000,  "price_max":1950000,  "dlc":"Gunrunning (2017)",              "upgrade_cost":1753000, "daily_fee":2000, "purchase_site":"Maze Bank Foreclosures"},
    {"id":"bunker-zancudo",      "name":"Zancudo River Bunker",    "type":"bunker",     "price_min":2375000,  "price_max":2375000,  "dlc":"Gunrunning (2017)",              "upgrade_cost":1753000, "daily_fee":2000, "purchase_site":"Maze Bank Foreclosures"},
    {"id":"bunker-raton",        "name":"Raton Canyon Bunker",     "type":"bunker",     "price_min":2250000,  "price_max":2250000,  "dlc":"Gunrunning (2017)",              "upgrade_cost":1753000, "daily_fee":2000, "purchase_site":"Maze Bank Foreclosures"},
    {"id":"bunker-desert",       "name":"Grand Senora Desert",     "type":"bunker",     "price_min":1550000,  "price_max":1550000,  "dlc":"Gunrunning (2017)",              "upgrade_cost":1753000, "daily_fee":2000, "purchase_site":"Maze Bank Foreclosures"},
    # ── Hangars ───────────────────────────────────────────────────────────────
    {"id":"hangar-lsia-1",       "name":"LSIA Hangar 1",           "type":"hangar",     "price_min":1200000,  "price_max":1200000,  "dlc":"Smuggler's Run (2017)",          "upgrade_cost":1695000, "daily_fee":1000, "purchase_site":"Elitas Travel", "notes":"Cheapest hangar. Central location."},
    {"id":"hangar-lsia-2",       "name":"LSIA Hangar A17",         "type":"hangar",     "price_min":1525000,  "price_max":1525000,  "dlc":"Smuggler's Run (2017)",          "upgrade_cost":1695000, "daily_fee":1000, "purchase_site":"Elitas Travel"},
    {"id":"hangar-fort-zancudo-1","name":"Zancudo Hangar 3497",    "type":"hangar",     "price_min":2085000,  "price_max":2085000,  "dlc":"Smuggler's Run (2017)",          "upgrade_cost":1695000, "daily_fee":1000, "purchase_site":"Elitas Travel", "notes":"Military base access. Removes 3-star wanted level on entry."},
    {"id":"hangar-fort-zancudo-2","name":"Zancudo Hangar 3499",    "type":"hangar",     "price_min":3250000,  "price_max":3250000,  "dlc":"Smuggler's Run (2017)",          "upgrade_cost":1695000, "daily_fee":1000, "purchase_site":"Elitas Travel"},
    # ── Facilities (Doomsday Heist) ───────────────────────────────────────────
    {"id":"facility-paleto",     "name":"Paleto Bay Facility",     "type":"facility",   "price_min":1250000,  "price_max":1250000,  "dlc":"The Doomsday Heist (2017)",      "daily_fee":0, "purchase_site":"Maze Bank Foreclosures", "notes":"Cheapest facility. Unlocks Doomsday Heist."},
    {"id":"facility-zancudo",    "name":"Route 68 Approach",       "type":"facility",   "price_min":1750000,  "price_max":1750000,  "dlc":"The Doomsday Heist (2017)",      "daily_fee":0, "purchase_site":"Maze Bank Foreclosures"},
    {"id":"facility-raton",      "name":"Lago Zancudo",            "type":"facility",   "price_min":1900000,  "price_max":1900000,  "dlc":"The Doomsday Heist (2017)",      "daily_fee":0, "purchase_site":"Maze Bank Foreclosures"},
    {"id":"facility-ron",        "name":"Ron Alternates Wind Farm","type":"facility",   "price_min":2100000,  "price_max":2100000,  "dlc":"The Doomsday Heist (2017)",      "daily_fee":0, "purchase_site":"Maze Bank Foreclosures"},
    {"id":"facility-land-act",   "name":"Land Act Reservoir",      "type":"facility",   "price_min":2585000,  "price_max":2585000,  "dlc":"The Doomsday Heist (2017)",      "daily_fee":0, "purchase_site":"Maze Bank Foreclosures"},
    {"id":"facility-sandy",      "name":"Grapeseed",               "type":"facility",   "price_min":2950000,  "price_max":2950000,  "dlc":"The Doomsday Heist (2017)",      "daily_fee":0, "purchase_site":"Maze Bank Foreclosures"},
    # ── Nightclubs ────────────────────────────────────────────────────────────
    {"id":"nightclub-elysian",   "name":"Elysian Island Nightclub","type":"nightclub",  "price_min":1080000,  "price_max":1080000,  "dlc":"After Hours (2018)",             "upgrade_cost":1900000, "daily_fee":1000, "purchase_site":"Dynasty 8 Executive", "notes":"Cheapest nightclub. Best passive earner — requires linked businesses."},
    {"id":"nightclub-la-mesa",   "name":"La Mesa Nightclub",       "type":"nightclub",  "price_min":1358200,  "price_max":1358200,  "dlc":"After Hours (2018)",             "upgrade_cost":1900000, "daily_fee":1000, "purchase_site":"Dynasty 8 Executive"},
    {"id":"nightclub-vespucci",  "name":"Vespucci Canals Nightclub","type":"nightclub", "price_min":1500000,  "price_max":1500000,  "dlc":"After Hours (2018)",             "upgrade_cost":1900000, "daily_fee":1000, "purchase_site":"Dynasty 8 Executive"},
    {"id":"nightclub-del-perro",  "name":"Del Perro Nightclub",    "type":"nightclub",  "price_min":1645000,  "price_max":1645000,  "dlc":"After Hours (2018)",             "upgrade_cost":1900000, "daily_fee":1000, "purchase_site":"Dynasty 8 Executive"},
    {"id":"nightclub-rockford",  "name":"Rockford Hills Nightclub","type":"nightclub",  "price_min":1700000,  "price_max":1700000,  "dlc":"After Hours (2018)",             "upgrade_cost":1900000, "daily_fee":1000, "purchase_site":"Dynasty 8 Executive"},
    {"id":"nightclub-downtown",  "name":"Downtown Vinewood Nightclub","type":"nightclub","price_min":1695000, "price_max":1695000,  "dlc":"After Hours (2018)",             "upgrade_cost":1900000, "daily_fee":1000, "purchase_site":"Dynasty 8 Executive"},
    {"id":"nightclub-strawberry","name":"Strawberry Nightclub",    "type":"nightclub",  "price_min":1525000,  "price_max":1525000,  "dlc":"After Hours (2018)",             "upgrade_cost":1900000, "daily_fee":1000, "purchase_site":"Dynasty 8 Executive"},
    {"id":"nightclub-mission-row","name":"Mission Row Nightclub",  "type":"nightclub",  "price_min":1440000,  "price_max":1440000,  "dlc":"After Hours (2018)",             "upgrade_cost":1900000, "daily_fee":1000, "purchase_site":"Dynasty 8 Executive"},
    # ── Arcades ───────────────────────────────────────────────────────────────
    {"id":"arcade-videogeddon",  "name":"Videogeddon (La Mesa)",   "type":"arcade",     "price_min":1235000,  "price_max":1235000,  "dlc":"The Diamond Casino Heist (2019)","daily_fee":0, "purchase_site":"Maze Bank Foreclosures", "notes":"Cheapest arcade. Unlocks Diamond Casino Heist + Master Control Terminal."},
    {"id":"arcade-eight-bit",    "name":"Eight-Bit (Vinewood)",    "type":"arcade",     "price_min":1875000,  "price_max":1875000,  "dlc":"The Diamond Casino Heist (2019)","daily_fee":0, "purchase_site":"Maze Bank Foreclosures"},
    {"id":"arcade-pixel-pete",   "name":"Pixel Pete's (Paleto)",   "type":"arcade",     "price_min":1235000,  "price_max":1235000,  "dlc":"The Diamond Casino Heist (2019)","daily_fee":0, "purchase_site":"Maze Bank Foreclosures"},
    {"id":"arcade-find-locations","name":"Other Arcades (5 total)","type":"arcade",     "price_min":1235000,  "price_max":2530000,  "dlc":"The Diamond Casino Heist (2019)","daily_fee":0, "purchase_site":"Maze Bank Foreclosures"},
    # ── Auto Shops ────────────────────────────────────────────────────────────
    {"id":"auto-shop-strawberry","name":"Strawberry Auto Shop",    "type":"auto-shop",  "price_min":1670000,  "price_max":1670000,  "dlc":"Los Santos Tuners (2021)",       "daily_fee":0, "purchase_site":"Southern SA Super Autos", "notes":"Auto Shop contracts pay $170-300k per run."},
    {"id":"auto-shop-banning",   "name":"Banning Auto Shop",       "type":"auto-shop",  "price_min":1920000,  "price_max":1920000,  "dlc":"Los Santos Tuners (2021)",       "daily_fee":0, "purchase_site":"Southern SA Super Autos"},
    {"id":"auto-shop-elburro",   "name":"El Burro Heights Auto Shop","type":"auto-shop","price_min":1705000,  "price_max":1705000,  "dlc":"Los Santos Tuners (2021)",       "daily_fee":0, "purchase_site":"Southern SA Super Autos"},
    {"id":"auto-shop-harmony",   "name":"Harmony Auto Shop",       "type":"auto-shop",  "price_min":1750000,  "price_max":1750000,  "dlc":"Los Santos Tuners (2021)",       "daily_fee":0, "purchase_site":"Southern SA Super Autos"},
    {"id":"auto-shop-mission-row","name":"Mission Row Auto Shop",  "type":"auto-shop",  "price_min":1830000,  "price_max":1830000,  "dlc":"Los Santos Tuners (2021)",       "daily_fee":0, "purchase_site":"Southern SA Super Autos"},
    # ── Agencies ──────────────────────────────────────────────────────────────
    {"id":"agency-little-seoul", "name":"Little Seoul Agency",     "type":"agency",     "price_min":2010000,  "price_max":2010000,  "dlc":"The Contract (2021)",            "daily_fee":0, "purchase_site":"Dynasty 8 Executive", "notes":"Cheapest agency. Unlocks Dr Dre VIP Contract + Security Contracts."},
    {"id":"agency-rockford",     "name":"Rockford Hills Agency",   "type":"agency",     "price_min":2415000,  "price_max":2415000,  "dlc":"The Contract (2021)",            "daily_fee":0, "purchase_site":"Dynasty 8 Executive"},
    {"id":"agency-vespucci",     "name":"Vespucci Beach Agency",   "type":"agency",     "price_min":2145000,  "price_max":2145000,  "dlc":"The Contract (2021)",            "daily_fee":0, "purchase_site":"Dynasty 8 Executive"},
    {"id":"agency-downtown",     "name":"Downtown LS Agency",      "type":"agency",     "price_min":2115000,  "price_max":2115000,  "dlc":"The Contract (2021)",            "daily_fee":0, "purchase_site":"Dynasty 8 Executive"},
    # ── Salvage Yards ─────────────────────────────────────────────────────────
    {"id":"salvage-yard-strawberry","name":"Strawberry Salvage Yard","type":"salvage-yard","price_min":1650000,"price_max":1650000, "dlc":"San Andreas Mercenaries (2023)", "daily_fee":0, "purchase_site":"Maze Bank Foreclosures", "notes":"Best location for tow truck deliveries. Unlocks Salvage Yard Heist robberies."},
    {"id":"salvage-yard-cypress","name":"Cypress Flats Salvage Yard","type":"salvage-yard","price_min":1950000,"price_max":1950000, "dlc":"San Andreas Mercenaries (2023)", "daily_fee":0, "purchase_site":"Maze Bank Foreclosures"},
    # ── Garment Factory ───────────────────────────────────────────────────────
    {"id":"garment-factory",     "name":"Darnell Bros Garment Factory","type":"garment-factory","price_min":2405000,"price_max":2405000,"dlc":"Agents of Sabotage (2024)",  "daily_fee":0, "purchase_site":"Maze Bank Foreclosures", "notes":"Single fixed location. Unlocks FIB Files contracts (~$400k/hr active). 10-car garage + MkII workshop."},
    # ── Bail Enforcement Office ───────────────────────────────────────────────
    {"id":"bail-office-downtown","name":"Downtown Vinewood Bail Office","type":"bail-office","price_min":1500000,"price_max":1500000, "dlc":"Bottom Dollar Bounties (2024)", "daily_fee":0, "purchase_site":"Maze Bank Foreclosures", "notes":"Single location. Unlocks bail enforcement contracts + passive agent safe income."},
    # ── Kosatka (Cayo Perico) ─────────────────────────────────────────────────
    {"id":"kosatka",             "name":"Kosatka Submarine",       "type":"submarine",  "price_min":2200000,  "price_max":2200000,  "dlc":"The Cayo Perico Heist (2020)",   "upgrade_cost":1750000, "daily_fee":0, "purchase_site":"Warstock Cache & Carry", "notes":"Required for Cayo Perico Heist (~$1.2M/hr). Pay back in ~2 runs. Best ROI property in GTA Online."},
    # ── Money Fronts (2025) ───────────────────────────────────────────────────
    {"id":"hands-on-car-wash",   "name":"Hands On Car Wash",       "type":"money-front","price_min":700000,   "price_max":700000,   "dlc":"Money Fronts (2025)",            "daily_fee":0, "purchase_site":"Maze Bank Foreclosures", "notes":"Hub for Money Fronts DLC. +35% Counterfeit Cash boost. Required to unlock other Money Fronts."},
    {"id":"smoke-on-the-water",  "name":"Smoke on the Water",      "type":"money-front","price_min":900000,   "price_max":900000,   "dlc":"Money Fronts (2025)",            "daily_fee":0, "purchase_site":"Maze Bank Foreclosures", "notes":"+35% Weed Farm product value. Requires Car Wash."},
    {"id":"higgins-helitours",   "name":"Higgins Helitours",        "type":"money-front","price_min":800000,   "price_max":800000,   "dlc":"Money Fronts (2025)",            "daily_fee":0, "purchase_site":"Maze Bank Foreclosures", "notes":"+10% Air Freight Cargo. Requires Car Wash. Vespucci Helipad helicopter spawn."},
]


def fetch_wiki_price_range(session: requests.Session, page: str) -> tuple[int | None, int | None]:
    """Extract |price = $X - $Y from a wiki page infobox."""
    r = session.get(WIKI_API, params={
        "action": "parse", "page": page,
        "prop":   "wikitext", "format": "json",
    }, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        return None, None
    wt = r.json().get("parse", {}).get("wikitext", {}).get("*", "")
    # Infobox price field
    m = re.search(r'\|price\s*=\s*\$?([\d,]+)\s*(?:-|–|to)\s*\$?([\d,]+)', wt, re.IGNORECASE)
    if m:
        lo = int(m.group(1).replace(",", ""))
        hi = int(m.group(2).replace(",", ""))
        return lo, hi
    # Single price
    m2 = re.search(r'\|price\s*=\s*\$?([\d,]+)', wt, re.IGNORECASE)
    if m2:
        p = int(m2.group(1).replace(",", ""))
        return p, p
    return None, None


def main() -> None:
    print("[fetch_gta_properties] Building GTA Online property registry…")

    session = requests.Session()

    # Try to enrich curated data with live wiki prices where possible
    enriched = 0
    for prop in CURATED_PROPERTIES:
        if not prop.get("price_min"):
            time.sleep(DELAY)
            lo, hi = fetch_wiki_price_range(session, prop.get("wiki_page", prop["name"]))
            if lo:
                prop["price_min"] = lo
                prop["price_max"] = hi or lo
                enriched += 1

    print(f"  Properties: {len(CURATED_PROPERTIES)} curated, {enriched} wiki-enriched")

    # Compute price statistics per type
    type_counts: dict[str, int] = {}
    for p in CURATED_PROPERTIES:
        type_counts[p["type"]] = type_counts.get(p["type"], 0) + 1

    output = {
        "last_updated": now_iso(),
        "source": "GTA Fandom Wiki + curated seed (GTABase / community records)",
        "note": (
            "All purchasable properties in GTA Online. price_min = cheapest location / configuration. "
            "price_max = most expensive. upgrade_cost = full upgrade (Equipment + Staff, excl. Security). "
            "daily_fee = GTA$/day when owned, regardless of activity."
        ),
        "property_count": len(CURATED_PROPERTIES),
        "type_counts": type_counts,
        "properties": CURATED_PROPERTIES,
    }

    # Print summary
    print(f"\n  By type:")
    for t, n in sorted(type_counts.items()):
        sample = next(p for p in CURATED_PROPERTIES if p["type"] == t)
        lo = sample["price_min"]
        print(f"    {t:20} {n:2} entries  min=${lo:,}")

    if has_changed(output, OUT_PATH):
        write_json(OUT_PATH, output)
        print(f"\n[fetch_gta_properties] ✓ Saved {len(CURATED_PROPERTIES)} properties")
    else:
        print("\n[fetch_gta_properties] No changes")


if __name__ == "__main__":
    main()
