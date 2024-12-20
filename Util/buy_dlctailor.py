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
def buy_dlctailor_Pack_callback():
    """Function to be triggered externally to open the Heist_Pack purchase window."""
    dlctailor_data = load_dlctailor_Packs('../Offsets/offsets.json')
    display_dlctailor_Pack_details(dlctailor_data, "Tailor Packs")
            
def force_stop_purchase():
    """Stop the ongoing purchase process."""
    global purchase_running
    purchase_running = False

    # Log that the force stop was triggered
    logger.debug("Force stop triggered. Stopping the purchase.")
    
    # Ensure the item exists before setting its value
    if dpg.does_item_exist("purchase_status_text_dlctailor_individual"):
        dpg.set_value("purchase_status_text_dlctailor_individual", "Purchase process stopped by user.")
    
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

def load_dlctailor_Packs(file_path):
    """Load Heist_Pack from the specified JSON file."""
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            dlctailor_Packs = data.get("Tailor Packs", [])
            return dlctailor_Packs
    except Exception as e:
        logger.error(f"Failed to load dlctailor Pack: {e}")
        return []
    
def load_dlctailor_Packs_Epic(file_path):
    """Load Heist_Pack from the specified JSON file."""
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            dlctailor_Packs = data.get("Epic Tailor Packs", [])
            return dlctailor_Packs
    except Exception as e:
        logger.error(f"Failed to load dlctailor Pack: {e}")
        return []
    
def load_dlctailor_Packs_Steam(file_path):
    """Load Heist_Pack from the specified JSON file."""
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            dlctailor_Packs = data.get("Steam Tailor Packs", [])
            return dlctailor_Packs
    except Exception as e:
        logger.error(f"Failed to load dlctailor Pack: {e}")
        return []

def start_thread(target, *args):
    """Start a thread to run the target function."""
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()

def display_dlctailor_Pack_details(dlctailor_data, dlctailor_Pack_type):
    """Display both dlctailor Pack and Epic Pack details in dropdown lists."""
    if dpg.does_item_exist("Buy DLC Tailor Pack Menu"):
        dpg.delete_item("Buy DLC Tailor Pack Menu")
    
    logger.debug(f"Loaded slot data: {dlctailor_data}")

    with dpg.window(label="Buy DLC Tailor Pack", tag="Buy DLC Tailor Pack Menu", width=600, height=400, show=True):
        # Add dropdown for regular dlc tailor Packs
        dpg.add_text(f"Select an item from {dlctailor_Pack_type}:")

        dlctailor_pack_options = []  # List to hold the names of dlctailor Packs
        dlctailor_pack_callbacks = {}  # Dictionary to map the pack name to its purchase callback

        for slot in dlctailor_data:
            for dlctailor_Pack_name, details in slot.items():
                logger.debug(f"Preparing option for {dlctailor_Pack_name} with details: {details}")

                if details and isinstance(details, dict):
                    dlctailor_pack_options.append(dlctailor_Pack_name)
                    
                    # Store the callback for this dlc tailor Pack
                    def create_callback(item_id, price, currency):
                        return lambda: confirm_slot_purchase(item_id, price, currency)

                    dlctailor_pack_callbacks[dlctailor_Pack_name] = create_callback(details['itemId'], details['price'], details['currency'])
                else:
                    logger.warning(f"Slot details for {dlctailor_Pack_name} are invalid: {details}")

        # Add dropdown (combo box) to select a regular dlc tailor Pack
        dpg.add_combo(
            dlctailor_pack_options,
            label="Tailor Packs",
            callback=lambda sender, app_data: dlctailor_pack_callbacks[app_data](),
        )

        # Add dropdown for Epic dlc tailor Packs
        dlctailor_data_epic = load_dlctailor_Packs_Epic('../Offsets/offsets.json')
        dpg.add_text("Select an item from Epic DLC Tailor Packs:")
        epic_dlctailor_pack_options = []
        epic_dlctailor_pack_callbacks = {}

        for slot in dlctailor_data_epic:
            for dlctailor_Pack_name, details in slot.items():
                logger.debug(f"Preparing option for {dlctailor_Pack_name} with details: {details}")

                if details and isinstance(details, dict):
                    epic_dlctailor_pack_options.append(dlctailor_Pack_name)

                    # Store the callback for this Epic dlc tailor Pack
                    def create_callback(item_id, price, currency):
                        return lambda: confirm_slot_purchase(item_id, price, currency)

                    epic_dlctailor_pack_callbacks[dlctailor_Pack_name] = create_callback(details['itemId'], details['price'], details['currency'])
                else:
                    logger.warning(f"Slot details for {dlctailor_Pack_name} are invalid: {details}")

        # Add dropdown (combo box) to select an Epic dlc tailor Pack
        dpg.add_combo(
            epic_dlctailor_pack_options,
            label="Epic DLC Tailor Packs",
            callback=lambda sender, app_data: epic_dlctailor_pack_callbacks[app_data](),
        )

                # Add dropdown for Steam dlctailor Packs
        dlctailor_data_steam = load_dlctailor_Packs_Steam('../Offsets/offsets.json')
        dpg.add_text("Select an item from Steam DLC Tailor Packs:")
        steam_dlctailor_pack_options = []
        steam_dlctailor_pack_callbacks = {}

        for slot in dlctailor_data_steam:
            for dlctailor_Pack_name, details in slot.items():
                logger.debug(f"Preparing option for {dlctailor_Pack_name} with details: {details}")

                if details and isinstance(details, dict):
                    steam_dlctailor_pack_options.append(dlctailor_Pack_name)

                    # Store the callback for this Steam dlc tailor Pack
                    def create_callback(item_id, price, currency):
                        return lambda: confirm_slot_purchase(item_id, price, currency)

                    steam_dlctailor_pack_callbacks[dlctailor_Pack_name] = create_callback(details['itemId'], details['price'], details['currency'])
                else:
                    logger.warning(f"Slot details for {dlctailor_Pack_name} are invalid: {details}")

        # Add dropdown (combo box) to select an Steam dlc tailor Pack
        dpg.add_combo(
            steam_dlctailor_pack_options,
            label="Steam DLC Tailor Packs",
            callback=lambda sender, app_data: steam_dlctailor_pack_callbacks[app_data](),
        )

        # Add a Back button to return to the previous menu
        dpg.add_spacer()
        dpg.add_button(label="Back",callback=lambda: (dpg.hide_item("Buy DLC Tailor Pack Menu"), dpg.show_item("Unlocker Menu"))
)


def confirm_slot_purchase(item_id, price, currency):
    global purchase_running
    """Logic to handle the purchase confirmation and create a new window."""
    logger.debug(f"Attempting to purchase item: {item_id}")
    slot_count = dpg.get_value("slot_count_dlctailor_Pack_input")

    # Close the current window
    if dpg.does_item_exist("Buy DLC Tailor Pack Window"):
        dpg.delete_item("Buy DLC Tailor Pack Window")

    # Create a new window to display the purchase confirmation or further actions
    with dpg.window(label="Purchase Confirmation", tag="Purchase Confirmation Window", width=400, height=200):
        dpg.add_text("Your purchase is being processed...", tag="purchase_status_text_dlctailor_individual")
        if not dpg.does_item_exist("force_stop_button_individuel"):
            dpg.add_button(label="Force Stop", tag="force_stop_button_individuel", callback=force_stop_purchase, parent="Purchase Confirmation Window")
        dpg.show_item("force_stop_button_individuel")

    # Start the purchase in a separate thread
    purchase_running = True
    threading.Thread(target=buy_dlctailor_individual_Pack, args=(slot_count, item_id, price, currency)).start()

def buy_dlctailor_individual_Pack(slot_count, item_id, price, currency):
    """Purchase a single Dlc tailor Pack item."""
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
    dpg.set_value("purchase_status_text_dlctailor_individual", "Starting purchase...")

    if not purchase_running:
        logger.debug("Purchase process stopped by user.")
        return

    logger.debug(f"Purchasing slot 1 out of 1.")

    try:
        response = requests.post(url, json=data, headers=headers)
        print(response.text)
        logger.debug(f"Response: {response.text}")

        if response.status_code == 201:
            logger.debug("dlctailor Pack purchased successfully.")
            dpg.set_value("purchase_status_text_dlctailor_individual", f"Purchased slot 1 successfully.")
        else:
            logger.error(f"Error purchasing individual dlctailor Pack: {response.text}")
            dpg.set_value("purchase_status_text_dlctailor_individual", f"Error purchasing slot 1: {response.text}")
    except requests.RequestException as e:
        logger.error(f"Network error purchasing item {item_id}: {e}")
        dpg.set_value("purchase_status_text", f"Network error purchasing item: {e}")

    # Clean up windows
    if dpg.does_item_exist("Purchase Confirmation Window"):
        dpg.delete_item("Purchase Confirmation Window")
    
    if dpg.does_item_exist("Buy DLC Tailor Pack Window"):
        dpg.delete_item("Buy DLC Tailor Pack Window")
