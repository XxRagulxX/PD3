import dearpygui.dearpygui as dpg
import threading
from Util.common import (_full_win, _VP_W, farmer_flow, load_token_headers,
                         set_status, start_thread, run_purchase_loop)

def buy_money_farmer_callback(sender=None, app_data=None, user_data=None):
    farmer_flow(
        win_tag     = "Money Farmer",
        win_label   = "Money Farmer",
        back_tag    = "Treasure Top-Up Menu",
        url_key     = "url_money",
        payload_key = "payload_money",
    )

def buy_cstacks_farmer_callback(sender=None, app_data=None, user_data=None):
    farmer_flow(
        win_tag     = "CStacks Farmer",
        win_label   = "C-Stacks Farmer",
        back_tag    = "Treasure Top-Up Menu",
        url_key     = "url_cstacks",
        payload_key = "payload_cstacks",
    )

def buy_cred_farmer_callback(sender=None, app_data=None, user_data=None):
    farmer_flow(
        win_tag     = "Cred Farmer",
        win_label   = "Cred Farmer",
        back_tag    = "Treasure Top-Up Menu",
        url_key     = "url_usd",
        payload_key = "payload_cred",
    )


def buy_custom_callback(sender=None, app_data=None, user_data=None):
    WIN        = "Buy Custom"
    BAR_TAG    = "cust_bar"
    COUNTS_TAG = "cust_counts"
    STATUS_TAG = "cust_status"
    STOP_TAG   = "cust_stop"
    BUY_TAG    = "cust_buy_btn"

    if dpg.does_item_exist(WIN):
        dpg.delete_item(WIN)

    stop = threading.Event()

    def _do_buy(s=None, a=None, u=None):
        currency  = u  # passed via user_data on each button
        item_id   = dpg.get_value("cust_item_id").strip()
        price_str = dpg.get_value("cust_price").strip()
        count     = dpg.get_value("cust_count")

        if not item_id or not price_str:
            set_status(STATUS_TAG, "Please fill in Item ID and Price.")
            return
        try:
            price = int(price_str)
        except ValueError:
            set_status(STATUS_TAG, "Price must be a number.")
            return

        headers, url = load_token_headers()
        if not url or not headers:
            set_status(STATUS_TAG, "Not logged in. Please log in first.")
            return

        stop.clear()
        if dpg.does_item_exist(BAR_TAG):
            dpg.set_value(BAR_TAG, 0.0)
        set_status(COUNTS_TAG, f"Bought: 0  |  Failed: 0  |  Remaining: {count}")
        set_status(STATUS_TAG, "Starting...")
        if dpg.does_item_exist(STOP_TAG):
            dpg.configure_item(STOP_TAG, enabled=True)

        def _work(_id=item_id, _p=price, _c=currency, _cnt=count,
                  _h=headers, _u=url):
            bought, failed = run_purchase_loop(
                _cnt, _id, _p, _p, _c, _h, _u, STATUS_TAG, stop,
                bar_tag=BAR_TAG, counts_tag=COUNTS_TAG)
            set_status(STATUS_TAG, f"Done — {bought} bought, {failed} failed.")
            if dpg.does_item_exist(BAR_TAG):
                dpg.set_value(BAR_TAG, 1.0 if bought else 0.0)
            if dpg.does_item_exist(STOP_TAG):
                dpg.configure_item(STOP_TAG, enabled=False)

        start_thread(_work)

    _HALF = (_VP_W - 40 - 12) // 2

    with dpg.window(**_full_win(WIN, "Custom Buy")):
        # Keep spacers only where ItemSpacing alone isn't enough.
        # ItemSpacing=8 is already added automatically between every pair of items.
        dpg.add_button(label="  Back", width=-1, height=30,
                       callback=lambda: (stop.set(),
                                         dpg.hide_item(WIN),
                                         dpg.show_item("Main Menu")))
        dpg.add_text("Custom Buy", color=(185, 55, 185, 255))
        dpg.add_separator()

        dpg.add_text("Item ID", color=(160, 160, 175, 255))
        dpg.add_input_text(label="", tag="cust_item_id", width=-1,
                           hint="Paste the item ID here")

        dpg.add_text("Price", color=(160, 160, 175, 255))
        dpg.add_input_text(label="", tag="cust_price", width=-1,
                           hint="e.g. 200000")

        dpg.add_text("How many to buy", color=(160, 160, 175, 255))
        dpg.add_input_int(label="", tag="cust_count",
                          min_value=1, default_value=1, width=-1)

        dpg.add_text("Payment type  —  click to buy", color=(160, 160, 175, 255))
        with dpg.group(horizontal=True):
            for cur in ("CASH", "GOLD", "USD"):
                dpg.add_button(label=f"  {cur}  ", height=36,
                               user_data=cur, callback=_do_buy)
                dpg.add_spacer(width=8)
            dpg.add_button(label="  Stop", tag=STOP_TAG,
                           height=36, enabled=False,
                           callback=lambda: stop.set())

        dpg.add_progress_bar(tag=BAR_TAG, default_value=0.0, width=-1, height=14)
        dpg.add_text("", tag=COUNTS_TAG, color=(160, 160, 175, 255), wrap=_VP_W - 40)
        dpg.add_text("", tag=STATUS_TAG, wrap=_VP_W - 40)

    dpg.hide_item("Main Menu")
    dpg.show_item(WIN)
