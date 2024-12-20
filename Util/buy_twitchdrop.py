import dearpygui.dearpygui as dpg
import os
import time
import logging
import requests
import json
import threading

# Configure logging
logger = logging.getLogger("Util.gui")
# logger.setLevel(logging.debug)
logger.setLevel(logging.DEBUG if __debug__ else logging.WARNING)


request_file = "../Offsets/request.json"

# Starting Code..
def buy_Twitch_Pack_callback():
    """Function to be triggered externally to open the Twitch_Pack purchase window."""
    Twitch_data = load_twitch_Packs('../Offsets/offsets.json')
    display_Twitch_Pack_details(Twitch_data, "Twitch Items")
            
def force_stop_purchase():
    """Stop the ongoing purchase process."""
    global purchase_running
    purchase_running = False

    # Log that the force stop was triggered
    logger.debug("Force stop triggered. Stopping the purchase.")
    
    # Ensure the item exists before setting its value
    if dpg.does_item_exist("purchase_status_text_individual_twitch"):
        dpg.set_value("purchase_status_text_individual_twitch", "Purchase process stopped by user.")
    
    if dpg.does_item_exist("purchase_status_text_bulk"):
        dpg.set_value("purchase_status_text_bulk", "Purchase process stopped by user.")
    
    # Ensure the Purchase Confirmation Window exists before deleting it
    if dpg.does_item_exist("Purchase Confirmation Window"):
        dpg.hide_item("Purchase Confirmation Window")  
    if dpg.does_item_exist("Purchase Confirmation Window Bulk"):
        dpg.hide_item("Purchase Confirmation Window Bulk") 
        

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
            return {}, ""
    return {}, ""

def load_twitch_Packs(file_path):
    """Load Twitch_Pack from the specified JSON file."""
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            Twitch_Packs = data.get("Twitch Items", [])
            return Twitch_Packs
    except Exception as e:
        logger.error(f"Failed to load Twitch Pack: {e}")
        return []
    
def start_thread(target, *args):
    """Start a thread to run the target function."""
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()

def display_Twitch_Pack_details(Twitch_data, Twitch_Pack_type):
    """Display both Twitch Pack and Epic Pack details in dropdown lists."""
    if dpg.does_item_exist("Buy Twitch Pack Menu"):
        dpg.delete_item("Buy Twitch Pack Menu")
    
    logger.debug(f"Loaded slot data: {Twitch_data}")

    with dpg.window(label="Buy Twitch Pack", tag="Buy Twitch Pack Menu", width=600, height=400, show=True):
        # Add dropdown for regular Twitch Packs
        dpg.add_text(f"Select an item from {Twitch_Pack_type}:")

        twitch_pack_options = []  # List to hold the names of Twitch Packs
        twitch_pack_callbacks = {}  # Dictionary to map the pack name to its purchase callback

        for slot in Twitch_data:
            for Twitch_Pack_name, details in slot.items():
                logger.debug(f"Preparing option for {Twitch_Pack_name} with details: {details}")

                if details and isinstance(details, dict):
                    twitch_pack_options.append(Twitch_Pack_name)
                    
                    # Store the callback for this Twitch Pack
                    def create_callback(item_id, price, currency):
                        return lambda: confirm_twitch_purchase(item_id, price, currency)

                    twitch_pack_callbacks[Twitch_Pack_name] = create_callback(details['itemId'], details['price'], details['currency'])
                else:
                    logger.warning(f"Slot details for {Twitch_Pack_name} are invalid: {details}")

        # Add dropdown (combo box) to select a regular Twitch Pack
        dpg.add_combo(
            twitch_pack_options,
            label="Twitch Pack",
            callback=lambda sender, app_data: twitch_pack_callbacks[app_data](),
        )

        # Add a Back button to return to the previous menu
        dpg.add_spacer()
        dpg.add_button(label="Back",callback=lambda: (dpg.hide_item("Buy Twitch Pack Menu"), dpg.show_item("Unlocker Menu"))
)


def confirm_twitch_purchase(item_id, price, currency):
    global purchase_running
    """Logic to handle the purchase confirmation and create a new window."""
    logger.debug(f"Attempting to purchase item: {item_id}")
    slot_count = dpg.get_value("slot_count_Twitch_Pack_input")

    # Close the current window
    if dpg.does_item_exist("Buy Twitch Pack Window"):
        dpg.delete_item("Buy Twitch Pack Window")

    # Create a new window to display the purchase confirmation or further actions
    with dpg.window(label="Purchase Confirmation", tag="Purchase Confirmation Window", width=400, height=200):
        dpg.add_text("Your purchase is being processed...", tag="purchase_status_text_individual_twitch")
        if not dpg.does_item_exist("force_stop_button_individuel"):
            dpg.add_button(label="Force Stop", tag="force_stop_button_individuel", callback=force_stop_purchase, parent="Purchase Confirmation Window")
        dpg.show_item("force_stop_button_individuel")

    # Start the purchase in a separate thread
    purchase_running = True
    threading.Thread(target=buy_individual_twitch_Pack, args=(slot_count, item_id, price, currency)).start()

def buy_individual_twitch_Pack(slot_count, item_id, price, currency):
    """Purchase a single Twitch Pack item."""
    headers, url = load_token_headers()

    if not url or not headers:
        logger.error("Failed to load URL or headers from request.json.")
        return

    logger.debug(f"URL: {url}")
    logger.debug(f"Headers: {headers}")

    data = {
        "itemId": item_id,
        "price": price,
        "discountedPrice": price,
        "currencyCode": currency
    }

    # Send initial status
    dpg.set_value("purchase_status_text_individual_twitch", "Starting purchase...")

    if not purchase_running:
        logger.debug("Purchase process stopped by user.")
        return

    logger.debug(f"Purchasing slot 1 out of 1.")

    try:
        response = requests.post(url, json=data, headers=headers)
        print(response.text)
        logger.debug(f"Response: {response.text}")

        if response.status_code == 201:
            logger.debug("Twitch Pack purchased successfully.")
            dpg.set_value("purchase_status_text_individual_twitch", f"Purchased slot 1 successfully.")
        else:
            logger.error(f"Error purchasing individual Twitch Pack: {response.text}")
            dpg.set_value("purchase_status_text_individual_twitch", f"Error purchasing slot 1: {response.text}")
    except requests.RequestException as e:
        logger.error(f"Network error purchasing item {item_id}: {e}")
        dpg.set_value("purchase_status_text", f"Network error purchasing item: {e}")

    # Clean up windows
    if dpg.does_item_exist("Purchase Confirmation Window"):
        dpg.delete_item("Purchase Confirmation Window")
    
    if dpg.does_item_exist("Buy Twitch Pack Window"):
        dpg.delete_item("Buy Twitch Pack Window")
