import dearpygui.dearpygui as dpg
import requests
import json
import os
import sys
import logging
import threading
from Util.login import load_credentials, login

logger = logging.getLogger("Util.gui")

_BASE_DIR    = os.path.dirname(__file__)
_ROOT        = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(_BASE_DIR)
_OFFSETS     = os.path.join(_ROOT, "Offsets", "offsets.json")
_REQUEST     = os.path.join(_ROOT, "Offsets", "request.json")

_stop_event  = threading.Event()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_request():
    try:
        with open(_REQUEST) as f:
            data = json.load(f)
        headers = data.get("headers", {})
        url     = data.get("url_buy_products", {}).get("url", "")
        return headers, url
    except Exception as e:
        logger.error(f"Failed to read request.json: {e}")
        return {}, ""


def _load_all_items():
    """Return flat list of (title, itemId, price, discountedPrice, currency)."""
    try:
        with open(_OFFSETS) as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read offsets.json: {e}")
        return []

    items = []
    for category, entries in data.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for title, details in entry.items():
                if not isinstance(details, dict):
                    continue
                items.append((
                    title,
                    details.get("itemId", ""),
                    details.get("price", 0),
                    details.get("discountedPrice", 0),
                    details.get("currency", "USD"),
                ))
    return items


def _set(tag, value):
    if dpg.does_item_exist(tag):
        dpg.set_value(tag, value)


def _refresh_token(headers):
    """Re-login and update Authorization in headers. Returns True on success."""
    username, password = load_credentials()
    if not username or not password:
        return False
    user_id, token = login(username, password)
    if token:
        headers["Authorization"] = f"Bearer {token}"
        return True
    return False


# ── Worker ────────────────────────────────────────────────────────────────────

def _run_buy_all(status_tag, bar_tag, counter_tag):
    _stop_event.clear()

    headers, url = _load_request()
    if not url or not headers:
        _set(status_tag, "Error: request.json missing or incomplete. Log in first.")
        return

    items = _load_all_items()
    if not items:
        _set(status_tag, "Error: offsets.json is empty or missing.")
        return

    total     = len(items)
    success   = 0
    failed    = 0
    skipped   = 0

    _set(status_tag, f"Starting — {total} items to purchase...")

    for idx, (title, item_id, price, disc_price, currency) in enumerate(items, 1):
        if _stop_event.is_set():
            _set(status_tag, f"Stopped by user.  Done {idx-1}/{total}  "
                             f"({success} ok, {failed} failed, {skipped} skipped)")
            break

        if not item_id:
            skipped += 1
            _set(counter_tag, f"{idx}/{total}")
            if dpg.does_item_exist(bar_tag):
                dpg.set_value(bar_tag, idx)
            continue

        payload = {
            "itemId":          item_id,
            "price":           price,
            "discountedPrice": disc_price,
            "currencyCode":    currency,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)

            if resp.status_code == 201:
                success += 1
                _set(status_tag, f"[{idx}/{total}] Bought: {title}")

            elif resp.status_code == 401:
                logger.warning("Token expired, re-logging in...")
                _set(status_tag, f"[{idx}/{total}] Token expired — re-authenticating...")
                if _refresh_token(headers):
                    resp2 = requests.post(url, json=payload, headers=headers, timeout=15)
                    if resp2.status_code == 201:
                        success += 1
                        _set(status_tag, f"[{idx}/{total}] Bought (after re-auth): {title}")
                    else:
                        failed += 1
                        logger.error(f"Failed after re-auth [{resp2.status_code}]: {title}")
                        _set(status_tag, f"[{idx}/{total}] Failed ({resp2.status_code}): {title}")
                else:
                    _set(status_tag, "Re-login failed. Stopping.")
                    break

            elif resp.status_code == 409:
                # Already owned — treat as success/skip
                skipped += 1
                _set(status_tag, f"[{idx}/{total}] Already owned: {title}")

            else:
                failed += 1
                logger.error(f"Error {resp.status_code} buying {title}: {resp.text[:120]}")
                _set(status_tag, f"[{idx}/{total}] Error {resp.status_code}: {title}")

        except requests.Timeout:
            failed += 1
            logger.error(f"Timeout buying {title}")
            _set(status_tag, f"[{idx}/{total}] Timeout: {title}")
        except requests.RequestException as e:
            failed += 1
            logger.error(f"Network error buying {title}: {e}")
            _set(status_tag, f"[{idx}/{total}] Network error: {e}")

        _set(counter_tag, f"{idx}/{total}  —  {success} bought  |  {failed} failed  |  {skipped} skipped")
        if dpg.does_item_exist(bar_tag):
            dpg.set_value(bar_tag, idx / total)

    else:
        # Completed the full loop without break
        _set(status_tag,
             f"All done!  {success} bought  |  {failed} failed  |  {skipped} skipped/owned")

    # Re-enable the buy button
    if dpg.does_item_exist("buy_all_start_btn"):
        dpg.configure_item("buy_all_start_btn", enabled=True, label="  Buy All Items")
    if dpg.does_item_exist("buy_all_stop_btn"):
        dpg.configure_item("buy_all_stop_btn", enabled=False)


# ── Callback ──────────────────────────────────────────────────────────────────

def buy_all_callback(sender=None, app_data=None, user_data=None):
    WIN     = "Buy All Window"
    STATUS  = "buy_all_status"
    BAR     = "buy_all_progress"
    COUNTER = "buy_all_counter"

    if dpg.does_item_exist(WIN):
        dpg.delete_item(WIN)

    items = _load_all_items()
    total = len(items)

    with dpg.window(label="Buy All Items", tag=WIN,
                    width=580, height=240, modal=False,
                    no_resize=True, no_collapse=True):

        dpg.add_text(f"This will purchase all {total} items from offsets.json once each.",
                     wrap=550)
        dpg.add_spacer(height=4)
        dpg.add_separator()
        dpg.add_spacer(height=6)

        dpg.add_text("Ready.", tag=STATUS, wrap=550)
        dpg.add_spacer(height=4)
        dpg.add_progress_bar(tag=BAR, default_value=0, width=-1, overlay="")
        dpg.add_spacer(height=2)
        dpg.add_text("", tag=COUNTER, color=(160, 160, 175, 255))
        dpg.add_spacer(height=8)
        dpg.add_separator()
        dpg.add_spacer(height=6)

        with dpg.group(horizontal=True):
            dpg.add_button(
                label="  Buy All Items", tag="buy_all_start_btn",
                width=270, height=36,
                callback=_on_start,
                user_data=(STATUS, BAR, COUNTER),
            )
            dpg.add_spacer(width=8)
            dpg.add_button(
                label="  Stop", tag="buy_all_stop_btn",
                width=120, height=36,
                enabled=False,
                callback=lambda: _stop_event.set(),
            )
            dpg.add_spacer(width=8)
            dpg.add_button(
                label="  Close", width=-1, height=36,
                callback=lambda: dpg.delete_item(WIN),
            )


def _on_start(sender, app_data, user_data):
    status_tag, bar_tag, counter_tag = user_data
    dpg.configure_item("buy_all_start_btn", enabled=False, label="  Running...")
    dpg.configure_item("buy_all_stop_btn",  enabled=True)
    _set(counter_tag, "")
    threading.Thread(
        target=_run_buy_all,
        args=(status_tag, bar_tag, counter_tag),
        daemon=True,
    ).start()
