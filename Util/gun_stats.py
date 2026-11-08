import dearpygui.dearpygui as dpg
import json
import os
import sys
import logging
import requests
import threading

logger = logging.getLogger("Util.gui")

_BASE        = os.path.dirname(__file__)
_ROOT        = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(_BASE)
_WEAPONS     = os.path.join(_ROOT, "Offsets", "weapons.json")
_REQUEST     = os.path.join(_ROOT, "Offsets", "request.json")
MAX_LEVEL    = 28


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_weapons():
    try:
        with open(_WEAPONS) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load weapons.json: {e}")
        return []


def _load_headers_and_url():
    try:
        with open(_REQUEST) as f:
            d = json.load(f)
        return d.get("headers", {}), d.get("url_buy_products", {}).get("url_upgrade", "")
    except Exception as e:
        logger.error(f"Failed to load request.json: {e}")
        return {}, ""


def _set_status(msg, color=(200, 200, 210, 255)):
    if dpg.does_item_exist("gun_status"):
        dpg.set_value("gun_status", msg)
        dpg.configure_item("gun_status", color=color)


# ── Core ──────────────────────────────────────────────────────────────────────

def _apply_level(stat_code, current_level, target_level):
    increment = target_level - current_level
    if increment <= 0:
        _set_status(
            f"Target {target_level} is not higher than current level {current_level}.",
            color=(255, 100, 80, 255))
        return

    headers, url = _load_headers_and_url()
    if not url or not headers:
        _set_status("Not logged in — please log in first.", color=(255, 100, 80, 255))
        return

    _set_status(f"Sending increment of {increment} to reach level {target_level}...")

    def _work():
        payload = [{"inc": increment, "statCode": stat_code}]
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            if resp.status_code == 200:
                _set_status(
                    f"Done! {stat_code} levelled to {target_level}.",
                    color=(80, 220, 120, 255))
            else:
                _set_status(
                    f"Server returned {resp.status_code}: {resp.text[:120]}",
                    color=(255, 100, 80, 255))
        except requests.RequestException as e:
            _set_status(f"Network error: {e}", color=(255, 100, 80, 255))

    threading.Thread(target=_work, daemon=True).start()


def _on_gun_selected(gun_stats, gun_name):
    """Populate level controls when a gun is chosen from the combo."""
    entry = next((g for g in gun_stats if gun_name in g), None)
    if not entry:
        return

    current_level = int(entry[gun_name]["value"])
    stat_code     = entry[gun_name]["statCode"]

    if dpg.does_item_exist("gun_current_level"):
        dpg.set_value("gun_current_level",
                      f"Current level: {current_level} / {MAX_LEVEL}")

    if dpg.does_item_exist("gun_target_input"):
        dpg.configure_item("gun_target_input",
                           min_value=current_level + 1,
                           max_value=MAX_LEVEL,
                           default_value=min(current_level + 1, MAX_LEVEL))
        dpg.show_item("gun_target_input")
        dpg.show_item("gun_apply_btn")

    # Store current selection in button user_data
    if dpg.does_item_exist("gun_apply_btn"):
        dpg.set_item_user_data("gun_apply_btn", (stat_code, current_level))

    _set_status("")


# ── Entry point ───────────────────────────────────────────────────────────────

def gun_stats_callback(sender=None, app_data=None, user_data=None):
    WIN = "Gun Stats Menu"
    if dpg.does_item_exist(WIN):
        dpg.delete_item(WIN)

    gun_stats = _load_weapons()
    gun_names = [list(g.keys())[0] for g in gun_stats if isinstance(g, dict)]

    with dpg.window(label="Gun Stats", tag=WIN,
                    width=560, height=320, show=True, no_collapse=True):

        dpg.add_text("Select a weapon:", color=(160, 160, 175, 255))
        dpg.add_combo(
            gun_names, label="", width=-1,
            callback=lambda s, a: _on_gun_selected(gun_stats, a))

        dpg.add_spacer(height=10)
        dpg.add_text("", tag="gun_current_level", color=(200, 200, 210, 255))
        dpg.add_spacer(height=6)

        dpg.add_input_int(
            label="Target level", tag="gun_target_input",
            min_value=1, max_value=MAX_LEVEL, default_value=1,
            width=200, show=False)

        dpg.add_spacer(height=8)

        dpg.add_button(
            label="  Apply Level", tag="gun_apply_btn",
            width=200, height=34, show=False,
            callback=lambda s, a, ud: _apply_level(ud[0], ud[1],
                                                    dpg.get_value("gun_target_input")),
        )

        dpg.add_spacer(height=8)
        dpg.add_separator()
        dpg.add_spacer(height=4)
        dpg.add_text("", tag="gun_status", wrap=530)
        dpg.add_spacer(height=4)
        dpg.add_button(
            label="  Back", width=-1, height=32,
            callback=lambda: (dpg.hide_item(WIN), dpg.show_item("Unlocker Menu")))
