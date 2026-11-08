import dearpygui.dearpygui as dpg
import requests
import json
import os
import logging
import threading
from Util.login import load_credentials, login
from Util.common import set_status

logger = logging.getLogger("Util.gui")

_BASE      = os.path.dirname(__file__)
_OFFSETS   = os.path.join(_BASE, "../Offsets/offsets.json")
_REQUEST   = os.path.join(_BASE, "../Offsets/request.json")
_ITEMS_URL = "https://nebula.starbreeze.com/platform/public/namespaces/pd3/items/byCriteria"

_KEY_MAP = {
    "Weapon Patterns": "Weapon Pattern",
    "Weapon Stickers": "Weapon Sticker",
    "Spray Paints":    "Paint",
    "Weapon Packs":    "DLC Weapon Pack",
    "Tailor Packs":    "DLC Tailor Pack",
}

# Most-specific first so broad keywords don't steal items
_CATEGORIES = [
    ("Preplanning Assets", ["Preplanning", "asset", "Ammo Bag", "Armor Bag", "Medic Bag"]),
    ("Weapon Charms",      ["Weapon Charm", "Charm"]),
    ("Mask Mould",         ["Mask Mould"]),
    ("Weapon Patterns",    ["Weapon Pattern"]),
    ("Weapon Stickers",    ["Weapon Sticker"]),
    ("Mask Patterns",      ["Mask Pattern"]),
    ("Spray Paints",       ["Paint", "SprayCan"]),
    ("Tailor Packs",       ["Tailor Pack", "Tailor", "Trifecta Lootbag"]),
    ("Heist Pack",         ["Heist", "Data Center Steam"]),
    ("Compensation Bundle",["Compensation Bundle"]),
    ("Base Preset",        ["Base Preset", "Preset"]),
    ("Gloves Items",       ["Gloves"]),
    ("Characters",         ["Character"]),
    ("Twitch Items",       ["Twitch"]),
    ("Gadgets",            ["Sentry Gun", "Shock Grenade", "Smoke Grenade", "ThrowingKnife", "Vest"]),
    ("Attachments For Guns",["MOD"]),
    ("Masks",              ["Mask"]),
    ("Suit",               ["Suit"]),
    ("Weapon Packs",       ["Weapon Pack", "Weapon", "Pack"]),
    ("Gold Purchase",      ["Gold"]),
]

_PLATFORMS = ["Epic", "Steam"]
_GUNS      = ["Pistol", "Marksman", "LMG", "SMG", "Shotgun", "Rifle",
              "Revolver", "AssaultRifle", "Overkill"]


def _platform(title):
    tl = title.lower()
    for p in _PLATFORMS:
        if p.lower() in tl:
            return p
    return None


def _categorize(title):
    tl = title.lower()
    if "twitch drops" in tl:
        return "Twitch Items"

    plat  = _platform(title)
    is_gun = any(g.lower() in tl for g in _GUNS)

    if is_gun:
        return f"{plat} Guns" if plat else "Guns"

    for cat, keywords in _CATEGORIES:
        if any(kw.lower() in tl for kw in keywords):
            base = _KEY_MAP.get(cat, cat)
            return f"{plat} {base}" if plat else base

    return "Other"


def _run_update(status_tag):
    try:
        set_status(status_tag, "Loading stored credentials...")
        username, password = load_credentials()
        if not username or not password:
            set_status(status_tag,
                       "No saved credentials.\nLog in with 'Remember me' checked first.")
            return

        set_status(status_tag, "Authenticating...")
        _, token = login(username, password)
        if not token:
            set_status(status_tag, "Authentication failed. Check credentials.")
            return

        set_status(status_tag, "Fetching item catalogue from server...")
        resp = requests.get(_ITEMS_URL, headers={
            "Accept":                 "application/json",
            "Accept-Encoding":        "gzip, deflate",
            "Authorization":          f"Bearer {token}",
            "User-Agent":             "PAYDAY3/++UE4+Release-4.27-CL-0 WinGDK/6.2.9200.1.256.64bit",
            "x-flight-id":            "D95ABC824983E0DD92F8B7AE9D547206",
            "Namespace":              "pd3",
            "Game-Client-Version":    "1.0.0.0",
            "AccelByte-SDK-Version":  "24.7.2",
            "AccelByte-OSS-Version":  "0.12.1-2",
            "Host":                   "nebula.starbreeze.com",
        }, params={"limit": 2147483647, "includeSubCategoryItem": "false"}, timeout=60)

        if resp.status_code != 200:
            set_status(status_tag, f"Server returned {resp.status_code}. Try again later.")
            return

        raw_items = resp.json().get("data", [])
        if not isinstance(raw_items, list):
            set_status(status_tag, "Unexpected response format from server.")
            return

        set_status(status_tag, f"Categorizing {len(raw_items)} items...")
        result  = {}
        skipped = 0

        for item in raw_items:
            title  = item.get("title", "")
            region = item.get("regionData", [])
            if not title or not region:
                skipped += 1
                continue
            rd  = region[0]
            cat = _categorize(title)
            result.setdefault(cat, []).append({title: {
                "itemId":          item.get("itemId", ""),
                "price":           rd.get("price", 0),
                "discountedPrice": rd.get("discountedPrice", 0),
                "currency":        rd.get("currencyCode", "USD"),
            }})

        set_status(status_tag, "Saving offsets.json...")
        os.makedirs(os.path.dirname(_OFFSETS), exist_ok=True)
        with open(_OFFSETS, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

        n_items = sum(len(v) for v in result.values())
        set_status(status_tag,
                   f"Done!  {n_items} items in {len(result)} categories saved.\n"
                   f"({skipped} skipped — missing title or region data)")

    except requests.Timeout:
        set_status(status_tag, "Request timed out. Check your connection.")
    except requests.RequestException as e:
        logger.error(f"Network error updating offsets: {e}")
        set_status(status_tag, f"Network error: {e}")
    except Exception as e:
        logger.error(f"Error updating offsets: {e}")
        set_status(status_tag, f"Error: {e}")


def update_offsets_callback(sender=None, app_data=None, user_data=None):
    WIN  = "Update Offsets Window"
    STAT = "update_offsets_status"

    if dpg.does_item_exist(WIN):
        dpg.delete_item(WIN)

    with dpg.window(label="Update offsets.json", tag=WIN,
                    width=520, height=180, modal=True, no_resize=True):
        dpg.add_spacer(height=4)
        dpg.add_text("Starting update...", tag=STAT, wrap=490)
        dpg.add_spacer(height=10)
        dpg.add_separator()
        dpg.add_spacer(height=6)
        dpg.add_button(label="Close", width=-1,
                       callback=lambda: dpg.delete_item(WIN))

    threading.Thread(target=_run_update, args=(STAT,), daemon=True).start()
