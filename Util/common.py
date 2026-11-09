import dearpygui.dearpygui as dpg
import requests
import json
import os
import sys
import time
import logging
import threading
from Util.login import load_credentials, login

logger   = logging.getLogger("Util.gui")
_BASE    = os.path.dirname(__file__)
_ROOT    = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(_BASE)
_REQUEST     = os.path.join(_ROOT, "Offsets", "request.json")
_OFFSETS     = os.path.join(_ROOT, "Offsets", "offsets.json")
_OWNED_CACHE = os.path.join(_ROOT, "Offsets", "owned.json")

# Set of itemIds the logged-in user already owns (populated after login).
_owned_ids: set = set()


def set_owned_ids(ids):
    global _owned_ids
    _owned_ids = set(ids)


def is_owned(item_id: str) -> bool:
    return item_id in _owned_ids


def load_owned_cache():
    """Return (cached_user_id, item_ids_set). Both None/empty on miss."""
    try:
        with open(_OWNED_CACHE) as f:
            d = json.load(f)
        return d.get("user_id"), set(d.get("item_ids", []))
    except Exception:
        return None, set()


def save_owned_cache(user_id: str, ids: set):
    os.makedirs(os.path.dirname(_OWNED_CACHE), exist_ok=True)
    with open(_OWNED_CACHE, "w") as f:
        json.dump({"user_id": user_id, "item_ids": sorted(ids)}, f, indent=2)

# Match the viewport size defined in gui.py
_VP_W, _VP_H = 860, 620

def _full_win(tag, label, show=True):
    """Return kwargs for a full-viewport, borderless, immovable window."""
    return dict(tag=tag, label=label, width=_VP_W, height=_VP_H,
                show=show, no_title_bar=True, no_resize=True,
                no_move=True, no_collapse=True,
                no_scrollbar=True, no_scroll_with_mouse=True,
                pos=[0, 0])


# ── I/O ──────────────────────────────────────────────────────────────────────

def load_token_headers():
    try:
        with open(_REQUEST) as f:
            d = json.load(f)
        return d.get("headers", {}), d.get("url_buy_products", {}).get("url", "")
    except Exception as e:
        logger.error(f"load_token_headers: {e}")
        return {}, ""


def load_farmer_config(url_key, payload_key):
    try:
        with open(_REQUEST) as f:
            d = json.load(f)
        return (
            d.get("headers", {}),
            d.get("url_buy", {}).get(url_key, ""),
            d.get(payload_key, {}),
        )
    except Exception as e:
        logger.error(f"load_farmer_config: {e}")
        return {}, "", {}


def load_category(key):
    try:
        with open(_OFFSETS) as f:
            return json.load(f).get(key, [])
    except Exception as e:
        logger.error(f"load_category({key!r}): {e}")
        return []


# ── Helpers ───────────────────────────────────────────────────────────────────

def set_status(tag, value):
    if dpg.does_item_exist(tag):
        dpg.set_value(tag, value)


def start_thread(fn, *args):
    t = threading.Thread(target=fn, args=args, daemon=True)
    t.start()
    return t


def refresh_token(headers):
    username, password = load_credentials()
    if not username or not password:
        return False
    _, token = login(username, password)
    if token:
        headers["Authorization"] = f"Bearer {token}"
        return True
    return False


# ── Purchase core ─────────────────────────────────────────────────────────────

def run_purchase_loop(count, item_id, price, disc_price, currency,
                      headers, url, status_tag, stop_flag=None,
                      bar_tag=None, counts_tag=None):
    """POST the purchase `count` times. Returns (success, failed)."""
    payload = {"itemId": item_id, "price": price,
               "discountedPrice": disc_price, "currencyCode": currency}
    success = failed = 0

    for i in range(count):
        if stop_flag and stop_flag.is_set():
            break
        set_status(status_tag, f"[{i+1}/{count}] Sending request...")
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            if resp.status_code == 201:
                success += 1
                set_status(status_tag, f"[{i+1}/{count}] Purchased.")
            elif resp.status_code == 401:
                set_status(status_tag, f"[{i+1}/{count}] Token expired — re-authenticating...")
                if refresh_token(headers):
                    resp2 = requests.post(url, json=payload, headers=headers, timeout=15)
                    if resp2.status_code == 201:
                        success += 1
                        set_status(status_tag, f"[{i+1}/{count}] Purchased (re-auth).")
                    else:
                        failed += 1
                        set_status(status_tag, f"[{i+1}/{count}] Error {resp2.status_code}.")
                else:
                    set_status(status_tag, "Re-login failed. Stopping.")
                    break
            else:
                failed += 1
                set_status(status_tag, f"[{i+1}/{count}] Error {resp.status_code}.")
        except requests.RequestException as e:
            failed += 1
            set_status(status_tag, f"[{i+1}/{count}] Network error: {e}")

        prog = (i + 1) / count
        if bar_tag and dpg.does_item_exist(bar_tag):
            dpg.set_value(bar_tag, prog)
        if counts_tag:
            rem = count - (i + 1)
            set_status(counts_tag,
                       f"Bought: {success}  |  Failed: {failed}  |  Remaining: {rem}")
        time.sleep(0.5)

    return success, failed


def run_farmer_loop(url, payload, headers, status_tag, stop_event, bar_tag=None):
    """PUT indefinitely every 10 s until stop_event is set."""
    slot = 1
    _WAIT = 10
    while not stop_event.is_set():
        if bar_tag and dpg.does_item_exist(bar_tag):
            dpg.set_value(bar_tag, 0.0)
        set_status(status_tag, f"Round {slot} — sending request...")
        try:
            resp = requests.put(url, json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                balance = resp.json().get("balance", "?")
                set_status(status_tag, f"Round {slot} done.  Balance: {balance:,}" if isinstance(balance, int) else f"Round {slot} done.  Balance: {balance}")
            elif resp.status_code == 401:
                set_status(status_tag, "Token expired — re-authenticating...")
                if not refresh_token(headers):
                    set_status(status_tag, "Re-login failed. Stopping.")
                    break
            else:
                set_status(status_tag, f"Round {slot} — Error {resp.status_code}: {resp.text[:80]}")
        except requests.RequestException as e:
            set_status(status_tag, f"Round {slot} — Network error: {e}")

        # Animate the bar as a countdown to the next round
        step = 0.1
        for tick in range(int(_WAIT / step)):
            if stop_event.is_set():
                break
            if bar_tag and dpg.does_item_exist(bar_tag):
                dpg.set_value(bar_tag, (tick + 1) * step / _WAIT)
            stop_event.wait(timeout=step)

        slot += 1
    set_status(status_tag, "Stopped.")
    if bar_tag and dpg.does_item_exist(bar_tag):
        dpg.set_value(bar_tag, 0.0)


# ── GUI windows ───────────────────────────────────────────────────────────────

def _confirm_win(win_tag, status_tag, stop_flag):
    if dpg.does_item_exist(win_tag):
        dpg.delete_item(win_tag)
    with dpg.window(label="Purchase", tag=win_tag,
                    width=460, height=140, no_resize=True):
        dpg.add_text("Processing...", tag=status_tag, wrap=430)
        dpg.add_spacer(height=8)
        dpg.add_separator()
        dpg.add_spacer(height=4)
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Force Stop", width=140, height=30,
                callback=lambda: (stop_flag.set(),
                                  set_status(status_tag, "Stopped by user.")))
            dpg.add_spacer(width=8)
            dpg.add_button(label="Close", width=-1, height=30,
                           callback=lambda: dpg.delete_item(win_tag))


def _quantity_win(win_tag, title, item_name, count_tag, on_confirm, back_win):
    if dpg.does_item_exist(win_tag):
        dpg.delete_item(win_tag)
    with dpg.window(label=title, tag=win_tag,
                    width=440, height=160, modal=True, no_resize=True):
        dpg.add_text(f"How many {item_name} to buy?", wrap=410)
        dpg.add_spacer(height=6)
        dpg.add_input_int(label="Count", tag=count_tag,
                          min_value=1, default_value=1, width=200)
        dpg.add_spacer(height=10)
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Confirm", width=160, height=30,
                callback=lambda: (dpg.delete_item(win_tag),
                                  on_confirm(dpg.get_value(count_tag))))
            dpg.add_spacer(width=8)
            dpg.add_button(
                label="Back", width=-1, height=30,
                callback=lambda: (dpg.hide_item(win_tag),
                                  dpg.show_item(back_win)))


# ── High-level flows ──────────────────────────────────────────────────────────

def item_list_flow(category_key, win_label, win_tag, back_tag,
                   count_tag=None, conf_tag=None, status_tag=None,
                   bulk_count_tag=None, bulk_conf_tag=None, bulk_status_tag=None):
    """
    Full item-list flow — all navigation is full-screen, no popups.
    - Item list page → click item → buy-item page (Back returns to list)
    - Buy All button → buy-all page (Back returns to list)
    """
    items = load_category(category_key)
    if dpg.does_item_exist(win_tag):
        dpg.delete_item(win_tag)

    total = sum(1 for e in items for k, v in e.items() if isinstance(v, dict))

    ITEM_WIN    = f"{win_tag}:item"
    BUYALL_WIN  = f"{win_tag}:buyall"

    # ── Individual item page ──────────────────────────────────────────────────
    def _open_item_page(name, det):
        for w in (ITEM_WIN, BUYALL_WIN):
            if dpg.does_item_exist(w):
                dpg.delete_item(w)
        dpg.hide_item(win_tag)

        stop       = threading.Event()
        s_tag      = f"{win_tag}:item_status"
        c_tag      = f"{win_tag}:item_count"
        btn_tag    = f"{win_tag}:item_buy"
        stop_tag   = f"{win_tag}:item_stop"
        bar_tag    = f"{win_tag}:item_bar"
        counts_tag = f"{win_tag}:item_counts"

        def _go_back(s=None, a=None, u=None):
            stop.set()
            if dpg.does_item_exist(ITEM_WIN):
                dpg.delete_item(ITEM_WIN)
            dpg.show_item(win_tag)

        def _buy(s=None, a=None, u=None):
            if not isinstance(det, dict):
                set_status(s_tag, "Error: item data missing.")
                return
            count      = dpg.get_value(c_tag)
            item_id    = det["itemId"]
            price      = det["price"]
            disc_price = det.get("discountedPrice", price)
            currency   = det["currency"]
            headers, url = load_token_headers()
            if not url or not headers:
                set_status(s_tag, "Not logged in. Please log in first.")
                return
            stop.clear()
            if dpg.does_item_exist(bar_tag):
                dpg.set_value(bar_tag, 0.0)
            set_status(counts_tag, f"Bought: 0  |  Failed: 0  |  Remaining: {count}")
            set_status(s_tag, "Starting...")
            dpg.configure_item(btn_tag, enabled=False, label="  Buying...")
            dpg.configure_item(stop_tag, enabled=True)
            def _work(_id=item_id, _p=price, _dp=disc_price, _c=currency,
                      _cnt=count, _h=headers, _u=url):
                bought, failed = run_purchase_loop(
                    _cnt, _id, _p, _dp, _c, _h, _u, s_tag, stop,
                    bar_tag=bar_tag, counts_tag=counts_tag)
                label = "Stopped." if stop.is_set() else f"Done — {bought} bought, {failed} failed."
                set_status(s_tag, label)
                set_status(counts_tag,
                           f"Bought: {bought}  |  Failed: {failed}  |  Remaining: 0")
                if dpg.does_item_exist(bar_tag):
                    dpg.set_value(bar_tag, 1.0 if bought else 0.0)
                if dpg.does_item_exist(btn_tag):
                    dpg.configure_item(btn_tag, enabled=True, label="  Buy")
                if dpg.does_item_exist(stop_tag):
                    dpg.configure_item(stop_tag, enabled=False)
            start_thread(_work)

        with dpg.window(**_full_win(ITEM_WIN, "")):
            dpg.add_spacer(height=10)
            dpg.add_button(label="  Back", width=-1, height=42, callback=_go_back)
            dpg.add_spacer(height=16)
            dpg.add_text(name, color=(185, 55, 185, 255))
            dpg.add_text(win_label, color=(130, 130, 148, 255))
            dpg.add_separator()
            dpg.add_spacer(height=16)
            dpg.add_text("How many to buy", color=(160, 160, 175, 255))
            dpg.add_input_int(label="", tag=c_tag,
                              min_value=1, default_value=1, width=-1)
            dpg.add_spacer(height=12)
            _HALF = (_VP_W - 40 - 12) // 2
            with dpg.group(horizontal=True):
                dpg.add_button(label="  Buy", tag=btn_tag,
                               width=_HALF, height=48, callback=_buy)
                dpg.add_spacer(width=12)
                dpg.add_button(label="  Stop", tag=stop_tag,
                               width=-1, height=48, enabled=False,
                               callback=lambda: stop.set())
            dpg.add_spacer(height=14)
            dpg.add_progress_bar(tag=bar_tag, default_value=0.0, width=-1, height=16)
            dpg.add_spacer(height=6)
            dpg.add_text("", tag=counts_tag,
                         color=(160, 160, 175, 255), wrap=_VP_W - 40)
            dpg.add_spacer(height=4)
            dpg.add_text("", tag=s_tag, wrap=_VP_W - 40)

    # ── Buy All page ──────────────────────────────────────────────────────────
    def _open_buyall_page():
        for w in (ITEM_WIN, BUYALL_WIN):
            if dpg.does_item_exist(w):
                dpg.delete_item(w)
        dpg.hide_item(win_tag)

        stop      = threading.Event()
        t_tag     = f"{win_tag}:ba_times"
        start_btn = f"{win_tag}:ba_start"
        stop_btn  = f"{win_tag}:ba_stop"
        bar_tag   = f"{win_tag}:ba_bar"
        item_tag  = f"{win_tag}:ba_item"
        count_tag = f"{win_tag}:ba_counts"
        err_tag   = f"{win_tag}:ba_errors"

        def _go_back():
            stop.set()
            if dpg.does_item_exist(BUYALL_WIN):
                dpg.delete_item(BUYALL_WIN)
            dpg.show_item(win_tag)

        def _start():
            times = dpg.get_value(t_tag)
            headers, url = load_token_headers()
            if not url or not headers:
                set_status(item_tag, "Not logged in. Please log in first.")
                return
            stop.clear()
            dpg.configure_item(start_btn, enabled=False, label="  Running...")
            dpg.configure_item(stop_btn,  enabled=True)
            if dpg.does_item_exist(bar_tag):
                dpg.set_value(bar_tag, 0.0)
            set_status(count_tag, "Bought: 0  |  Failed: 0  |  Skipped: 0")
            set_status(err_tag, "")

            def _work():
                bought = failed = skipped = done = 0
                total_ops = total * times
                errors = []

                for _ in range(times):
                    for entry in load_category(category_key):
                        if stop.is_set(): break
                        for n, d in entry.items():
                            if not isinstance(d, dict): continue
                            if stop.is_set(): break
                            done += 1
                            set_status(item_tag, f"[{done}/{total_ops}]  {n}")
                            if dpg.does_item_exist(bar_tag):
                                dpg.set_value(bar_tag, done / total_ops)

                            s, f = run_purchase_loop(
                                1, d["itemId"], d["price"],
                                d.get("discountedPrice", d["price"]),
                                d["currency"], headers, url, item_tag, stop)
                            bought  += s
                            failed  += f
                            if f:
                                errors.append(n)
                            set_status(count_tag,
                                f"Bought: {bought}  |  Failed: {failed}  |  Remaining: {total_ops - done}")

                if stop.is_set():
                    set_status(item_tag, f"Stopped at {done}/{total_ops}.")
                else:
                    dpg.set_value(bar_tag, 1.0)
                    set_status(item_tag, "All done!")

                set_status(count_tag,
                    f"Bought: {bought}  |  Failed: {failed}  |  Total processed: {done}")
                if errors:
                    set_status(err_tag, "Failed items:\n" + "\n".join(f"  • {e}" for e in errors[:20]))

                if dpg.does_item_exist(start_btn):
                    dpg.configure_item(start_btn, enabled=True, label="  Start")
                    dpg.configure_item(stop_btn,  enabled=False)
            start_thread(_work)

        _HALF = (_VP_W - 40 - 12) // 2
        with dpg.window(**_full_win(BUYALL_WIN, "")):
            dpg.add_spacer(height=10)
            dpg.add_button(label="  Back", width=-1, height=42, callback=_go_back)
            dpg.add_spacer(height=12)
            dpg.add_text(f"Buy All — {win_label}", color=(185, 55, 185, 255))
            dpg.add_text(f"{total} items will be purchased", color=(130, 130, 148, 255))
            dpg.add_separator()
            dpg.add_spacer(height=12)
            dpg.add_text("Repeat times", color=(160, 160, 175, 255))
            dpg.add_input_int(label="", tag=t_tag,
                              min_value=1, default_value=1, width=-1)
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                dpg.add_button(label="  Start", tag=start_btn,
                               width=_HALF, height=48, callback=_start)
                dpg.add_spacer(width=12)
                dpg.add_button(label="  Stop", tag=stop_btn,
                               width=-1, height=48, enabled=False,
                               callback=lambda: stop.set())
            dpg.add_spacer(height=12)
            dpg.add_separator()
            dpg.add_spacer(height=8)
            dpg.add_progress_bar(tag=bar_tag, default_value=0.0, width=-1, height=18)
            dpg.add_spacer(height=6)
            dpg.add_text("Ready.", tag=item_tag, color=(200, 200, 210, 255), wrap=_VP_W - 40)
            dpg.add_spacer(height=4)
            dpg.add_text("Bought: 0  |  Failed: 0  |  Remaining: 0",
                         tag=count_tag, color=(160, 160, 175, 255), wrap=_VP_W - 40)
            dpg.add_spacer(height=4)
            dpg.add_text("", tag=err_tag, color=(255, 100, 80, 255), wrap=_VP_W - 40)

    # ── Item list page ────────────────────────────────────────────────────────
    with dpg.window(**_full_win(win_tag, win_label)):
        dpg.add_spacer(height=10)
        dpg.add_text(win_label, color=(185, 55, 185, 255))
        dpg.add_spacer(height=4)
        with dpg.group(horizontal=True):
            dpg.add_button(label="  Back", width=140, height=36,
                           callback=lambda: (dpg.hide_item(win_tag), dpg.show_item(back_tag)))
            dpg.add_spacer(width=8)
            dpg.add_button(label="  Buy All", width=160, height=36,
                           callback=lambda: _open_buyall_page())
            dpg.add_spacer(width=12)
            dpg.add_text(f"{total} items available", color=(160, 160, 175, 255))
        dpg.add_separator()
        dpg.add_spacer(height=4)

        with dpg.child_window(height=_VP_H - 160, border=False):
            for entry in items:
                for name, det in entry.items():
                    if not isinstance(det, dict):
                        continue
                    owned  = is_owned(det.get("itemId", ""))
                    suffix = "  (owned)" if owned else ""
                    dpg.add_button(
                        label=f"  {name}{suffix}", width=-1, height=32,
                        user_data=(name, det),
                        callback=lambda s, a, u: _open_item_page(u[0], u[1]))
                    dpg.add_spacer(height=2)


def combo_purchase_flow(win_tag, win_label, back_tag, sections):
    """
    Combo-box based purchase window (for DLC/unlocker items).
    sections: list of (label_text, category_key) pairs
    """
    if dpg.does_item_exist(win_tag):
        dpg.delete_item(win_tag)

    status_tag = f"{win_tag}:status"
    bar_tag    = f"{win_tag}:bar"
    stop_tag   = f"{win_tag}:stop_btn"
    stop       = threading.Event()

    def _purchase(item_id, price, disc_price, currency):
        headers, url = load_token_headers()
        if not url or not headers:
            set_status(status_tag, "Not logged in. Please log in first.")
            return
        stop.clear()
        if dpg.does_item_exist(bar_tag):
            dpg.set_value(bar_tag, 0.0)
        set_status(status_tag, "Sending request...")
        if dpg.does_item_exist(stop_tag):
            dpg.configure_item(stop_tag, enabled=True)
        def _work(_id=item_id, _p=price, _dp=disc_price, _c=currency,
                  _h=headers, _u=url):
            s, f = run_purchase_loop(
                1, _id, _p, _dp, _c, _h, _u, status_tag, stop,
                bar_tag=bar_tag)
            if dpg.does_item_exist(bar_tag):
                dpg.set_value(bar_tag, 1.0 if s else 0.0)
            set_status(status_tag,
                       "Purchased successfully!" if s else "Purchase failed.")
            if dpg.does_item_exist(stop_tag):
                dpg.configure_item(stop_tag, enabled=False)
        start_thread(_work)

    with dpg.window(**_full_win(win_tag, win_label)):
        dpg.add_button(label="  Back", width=-1, height=30,
                       callback=lambda: (dpg.hide_item(win_tag), dpg.show_item(back_tag)))
        dpg.add_text(win_label, color=(185, 55, 185, 255))
        dpg.add_separator()

        for section_label, category_key in sections:
            items = load_category(category_key)
            options   = []
            callbacks = {}
            for entry in items:
                for name, det in entry.items():
                    if isinstance(det, dict):
                        display = f"{name} (owned)" if is_owned(det.get("itemId", "")) else name
                        options.append(display)
                        callbacks[display] = (det["itemId"], det["price"],
                                              det.get("discountedPrice", det["price"]),
                                              det["currency"])

            dpg.add_text(section_label, color=(160, 160, 175, 255))
            if options:
                dpg.add_combo(
                    options, label="",
                    user_data=callbacks,
                    callback=lambda s, a, u: _purchase(*u[a]),
                    width=-1)
            else:
                dpg.add_text("  (no items)", color=(120, 120, 130, 255))

        dpg.add_separator()
        dpg.add_progress_bar(tag=bar_tag, default_value=0.0, width=-1, height=14)
        dpg.add_text("Select an item above to purchase it.", tag=status_tag,
                     color=(200, 200, 210, 255), wrap=_VP_W - 40)
        dpg.add_button(
            label="  Stop", tag=stop_tag,
            width=-1, height=30, enabled=False,
            callback=lambda: stop.set())


def farmer_flow(win_tag, win_label, back_tag, url_key, payload_key):
    """Simple farmer window with Start / Stop / Back."""
    if dpg.does_item_exist(win_tag):
        dpg.delete_item(win_tag)

    stop_event = threading.Event()
    status_tag  = f"{win_tag}:status"
    bar_tag     = f"{win_tag}:bar"
    start_tag   = f"{win_tag}:start"
    stop_tag    = f"{win_tag}:stop"

    def _start():
        headers, url, payload = load_farmer_config(url_key, payload_key)
        if not url or not headers or not payload:
            set_status(status_tag, "Error: request.json missing/incomplete. Log in first.")
            return
        stop_event.clear()
        dpg.configure_item(start_tag, enabled=False, label="  Running...")
        dpg.configure_item(stop_tag,  enabled=True)
        start_thread(run_farmer_loop, url, payload, headers, status_tag, stop_event, bar_tag)

    def _stop():
        stop_event.set()
        dpg.configure_item(start_tag, enabled=True, label="  Start Farming")
        dpg.configure_item(stop_tag,  enabled=False)

    def _back():
        stop_event.set()
        dpg.hide_item(win_tag)
        dpg.show_item(back_tag)

    _HALF = (_VP_W - 40 - 12) // 2

    with dpg.window(**_full_win(win_tag, win_label)):
        dpg.add_button(label="  Back", width=-1, height=30, callback=_back)
        dpg.add_text(win_label, color=(185, 55, 185, 255))
        dpg.add_separator()
        dpg.add_text("Ready to farm. Press Start Farming to begin.",
                     tag=status_tag, wrap=_VP_W - 40, color=(200, 200, 210, 255))
        dpg.add_progress_bar(tag=bar_tag, default_value=0.0, width=-1, height=18)
        dpg.add_text("Progress bar counts down 10 s to the next round.",
                     color=(110, 110, 128, 255))
        dpg.add_separator()
        dpg.add_button(label="  Start Farming", tag=start_tag,
                       width=-1, height=52, callback=_start)
        dpg.add_button(label="  Stop", tag=stop_tag,
                       width=-1, height=40, enabled=False, callback=_stop)
