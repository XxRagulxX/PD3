import dearpygui.dearpygui as dpg
import os
import time
import logging
import requests
import json
import threading
from Util.login import load_credentials, login

# Configure logging
logger = logging.getLogger("Util.gui")
logger.setLevel(logging.DEBUG if __debug__ else logging.WARNING)

request_file = "../Offsets/request.json"
purchase_stop_event = threading.Event()  # Event for stopping the purchase process

# Function to load headers, payload, and URL from JSON
def load_token_headers():
    """Load token headers and URL from the request JSON file."""
    json_file_path = os.path.join(os.path.dirname(__file__), request_file)
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, "r") as f:
                data = json.load(f)
                return data.get("headers", {}), data.get("url_buy_products", {}).get("url", "")
        except json.JSONDecodeError:
            logger.error("Error: Invalid JSON in request file.")
            return {}, {}, ""
    return {}, {}, ""

# Thread-safe method to update Dear PyGui elements
def update_gui_element(tag, value):
    if dpg.does_item_exist(tag):
        dpg.set_value(tag, value)

# Function to start a new thread
def start_thread(target, *args):
    """Start a thread to run the target function."""
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()

# Callback function for the Money Farmer button
def buy_custom_callback():
    """Function to be triggered externally to open the purchase window."""
    display_preplanning_details("Preplanning Assets")

# Force stop the purchase process
def force_stop_purchase():
    """Sets the event to stop the purchase process immediately."""
    purchase_stop_event.set()
    logger.debug("Force stop triggered. Stopping the purchase.")
    update_gui_element("purchase_status_cstacks_buy", "Purchase process stopped by user.")
    if dpg.does_item_exist("Purchase Confirmation Window"):
        dpg.delete_item("Purchase Confirmation Window")

# Display the Preplanning Assets purchase UI
def display_preplanning_details(assets_type):
    if dpg.does_item_exist("Buy Custom"):
        dpg.delete_item("Buy Custom")

    with dpg.window(label="Buy Custom", tag="Buy Custom", width=600, height=400, show=True):
        dpg.add_text(f"Items in {assets_type}:")

        # Text boxes for user input
        dpg.add_input_text(label="Enter Item ID", tag="item_id_input", width=300)
        dpg.add_input_text(label="Enter Price", tag="price_input", width=300)

        dpg.add_input_int(label="Number of Purchases", min_value=1, default_value=1, tag="purchase_count_input")

        # Payment type buttons
        dpg.add_text("Select Payment Type:")
        with dpg.group(horizontal=True):
            dpg.add_button(label="CASH", callback=lambda: start_thread(confirm_assets_purchase, dpg.get_value("item_id_input"), dpg.get_value("price_input"), dpg.get_value("purchase_count_input") , "CASH"))
            dpg.add_button(label="GOLD", callback=lambda: start_thread(confirm_assets_purchase, dpg.get_value("item_id_input"), dpg.get_value("price_input"), dpg.get_value("purchase_count_input") ,"GOLD"))
            dpg.add_button(label="USD", callback=lambda: start_thread(confirm_assets_purchase, dpg.get_value("item_id_input"), dpg.get_value("price_input"), dpg.get_value("purchase_count_input") ,"USD"))
        
        dpg.add_spacer()
        # Action buttons
        dpg.add_button(label="Back", callback=lambda: (dpg.hide_item("Buy Custom"), dpg.show_item("Main Menu")))

# Confirm the purchase and start a new thread
def confirm_assets_purchase(item_id, price, purchase_count, currency):
    """Starts the purchase confirmation process."""
#    purchase_stop_event.clear()  # Reset the stop event
    logger.debug("Starting individual purchase confirmation.")
    
    if dpg.does_item_exist("Buy Custom"):
        dpg.delete_item("Buy Custom")

    with dpg.window(label="Purchase Confirmation", tag="Purchase Confirmation Window", width=400, height=200):
        dpg.add_text("Your purchase is being processed...", tag="purchase_status_cstacks_buy")
        dpg.add_button(label="Force Stop", tag="force_stop_button_individual", callback=force_stop_purchase)

    start_thread(buy_preplanning_assets(item_id, price, purchase_count, currency))
    # buy_preplanning_assets

# Function to handle the purchase process
def buy_preplanning_assets(item_id, price, num_purchases, currency, ):
    payload_cstacks = {
        "itemId": item_id,
        "price": price,
        "discountedPrice": price,
        "currencyCode": currency
    }
    headers, url = load_token_headers()

    if not url or not headers:
        logger.error("Failed to load URL or headers from request.json.")
        update_gui_element("purchase_status_cstacks_buy", "Failed to load request details.")
        return

    update_gui_element("purchase_status_cstacks_buy", f"Starting purchase for {num_purchases} times...")
    
    for purchase_slot in range(1, num_purchases + 1):
        logger.debug(f"Purchasing slot {purchase_slot}.")

        try:
            response = requests.post(url, json=payload_cstacks, headers=headers)
            logger.debug(f"Response: {response.text}")

            if response.status_code == 201:
                logger.debug("Purchase successful.")
                update_gui_element("purchase_status_cstacks_buy", f"Purchase {purchase_slot} successful. Total balance: {num_purchases}")
            elif response.status_code == 401:  # Token expired (unauthorized)
                logger.warning("Token expired, attempting re-login.")
                username, password = load_credentials()
                if username and password:
                    user_id, access_token = login(username, password)
                    if access_token:
                        headers["Authorization"] = f"Bearer {access_token}"
                        logger.info("Retrying purchase after re-login.")
                        response = requests.post(url, json=payload_cstacks, headers=headers)
                        if response.status_code == 201:
                            logger.debug("Purchase successful after re-login.")
                            update_gui_element("purchase_status_cstacks_buy", f"Purchase {purchase_slot} successful. Total balance: {num_purchases}")
                        else:
                            logger.error(f"Error after re-login: {response.text}")
                            update_gui_element("purchase_status_cstacks_buy", f"Error after re-login: {response.text}")
                    else:
                        logger.error("Re-login failed. Cannot continue purchase.")
                        update_gui_element("purchase_status_cstacks_buy", "Re-login failed.")
                else:
                    logger.error("No stored credentials found for re-login.")
                    update_gui_element("purchase_status_cstacks_buy", "No credentials found for re-login.")
            else:
                logger.error(f"Error purchasing item: {response.text}")
                update_gui_element("purchase_status_cstacks_buy", f"Error: {response.text}")
        except requests.RequestException as e:
            logger.error(f"Network error: {e}")
            update_gui_element("purchase_status_cstacks_buy", f"Network error: {e}")

    logger.debug("Purchase process completed.")
    update_gui_element("purchase_status_cstacks_buy", "Purchase process completed.")
    if dpg.does_item_exist("Purchase Confirmation Window"):
        dpg.delete_item("Purchase Confirmation Window")
