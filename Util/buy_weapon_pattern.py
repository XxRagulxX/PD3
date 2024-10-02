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
def buy_weapon_pattern_callback():
    """Function to be triggered externally to open the Weapon Pattern purchase window."""
    slot_data = load_weapon_pattern('../Offsets/offsets.json')
    display_weapon_pattern_details(slot_data, "Weapon Pattern")
            
def force_stop_purchase():
    """Stop the ongoing purchase process."""
    global purchase_running
    purchase_running = False

    # Log that the force stop was triggered
    logger.debug("Force stop triggered. Stopping the purchase.")
    
    # Ensure the item exists before setting its value
    if dpg.does_item_exist("purchase_status_text_individual"):
        dpg.set_value("purchase_status_text_individual", "Purchase process stopped by user.")
    
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

def load_weapon_pattern(file_path):
    """Load Weapon Pattern from the specified JSON file."""
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            paints = data.get("Weapon Pattern", [])
            return paints
    except Exception as e:
        logger.error(f"Failed to load Weapon Pattern: {e}")
        return []

def start_thread(target, *args):
    """Start a thread to run the target function."""
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()

def display_weapon_pattern_details(slot_data, Paint_type):
    """Display the weapon pattern details in the GUI."""
    if dpg.does_item_exist("Buy Weapon Pattern Menu"):
        dpg.delete_item("Buy Weapon Pattern Menu")
    
    logger.debug(f"Loaded slot data: {slot_data}")

    with dpg.window(label="Buy Weapon Pattern", tag="Buy Weapon Pattern Menu", width=600, height=400, show=True):
        dpg.add_text(f"Items in {Paint_type}:")
        
        total_paints = 0

        for slot in slot_data:
            for weapon_pattern_name, details in slot.items():
                logger.debug(f"Preparing button for {weapon_pattern_name} with details: {details}")

                if details and isinstance(details, dict):
                    total_paints += 1

                    def create_callback(weapon_pattern_name, item_id, price, currency):
                        return lambda: ask_how_manay_weapon_pattern(weapon_pattern_name, item_id, price, currency)

                    dpg.add_button(label=weapon_pattern_name,
                                   callback=create_callback(weapon_pattern_name, details['itemId'], details['price'], details['currency']))
                else:
                    logger.warning(f"Slot details for {weapon_pattern_name} are invalid: {details}")

        dpg.add_button(label="Buy All Weapon Pattern", callback=lambda: ask_how_many_times_to_buy(total_paints))

        dpg.add_button(label="Back", callback=lambda: (dpg.hide_item("Buy Weapon Pattern Menu"), dpg.show_item("Main Menu")))

# Individual Purchase. 

def ask_how_manay_weapon_pattern(weapon_pattern_name, item_id, price, currency):
    """Prompt the user for the number of Weapon Pattern to purchase."""
    if dpg.does_item_exist("Buy Weapon Pattern Window"):
        dpg.delete_item("Buy Weapon Pattern Window")
    
    with dpg.window(label=f"Buy {weapon_pattern_name}", tag="Buy Weapon Pattern Window", width=600, height=200, modal=True):
        dpg.add_text(f"How many {weapon_pattern_name} would you like to buy?")
        
        dpg.add_input_int(label="Number of Weapon Pattern", min_value=1, default_value=1, tag="slot_count_input")
        
        dpg.add_button(label="Confirm", callback=lambda: start_thread(confirm_weapon_pattern_purchase, item_id, price, currency))
        dpg.add_button(label="Back", callback=lambda: (dpg.hide_item("Buy Weapon Pattern Window"), dpg.show_item("Buy Weapon Pattern Menu")))

def confirm_weapon_pattern_purchase(item_id, price, currency):
    global purchase_running
    """Logic to handle the purchase confirmation and create a new window."""
    logger.debug(f"Attempting to purchase item: {item_id}")
    slot_count = dpg.get_value("slot_count_input")

    # Close the current window
    if dpg.does_item_exist("Buy Weapon Pattern Window"):
        dpg.delete_item("Buy Weapon Pattern Window")

    # Create a new window to display the purchase confirmation or further actions
    with dpg.window(label="Purchase Confirmation", tag="Purchase Confirmation Window", width=400, height=200):
        dpg.add_text("Your purchase is being processed...", tag="purchase_status_text_individual")
        if not dpg.does_item_exist("force_stop_button_individuel"):
            dpg.add_button(label="Force Stop", tag="force_stop_button_individuel", callback=force_stop_purchase, parent="Purchase Confirmation Window")
        dpg.show_item("force_stop_button_individuel")

    # Start the purchase in a separate thread
    purchase_running = True
    threading.Thread(target=buy_individual_weapon_pattern, args=(slot_count, item_id, price, currency)).start()

def buy_individual_weapon_pattern(slot_count, item_id, price, currency):
    """Purchase a single weapon pattern item."""
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
    dpg.set_value("purchase_status_text_individual", "Starting individual purchase...")

    for i in range(slot_count):
        if not purchase_running:
            logger.debug("Purchase process stopped by user.")
            break
        logger.debug(f"Purchasing slot {i + 1} out of {slot_count}.")

        try:
            response = requests.post(url, json=data, headers=headers)
            logger.debug(f"Response: {response.text}")

            if response.status_code == 201:
                logger.debug("Individual Weapon Pattern purchased successfully.")
                dpg.set_value("purchase_status_text_individual", f"Purchased slot {i + 1} of {slot_count} successfully.")
            else:
                logger.error(f"Error purchasing individual Weapon Pattern: {response.text}")
                dpg.set_value("purchase_status_text_individual", f"Error purchasing slot {i + 1}: {response.text}")
        except requests.RequestException as e:
            logger.error(f"Network error purchasing item {item_id}: {e}")
            dpg.set_value("purchase_status_text", f"Network error purchasing item {i + 1}: {e}")
        
        time.sleep(0.5)
    
    if dpg.does_item_exist("Purchase Confirmation Window"):
        dpg.delete_item("Purchase Confirmation Window")


#Bulk Purchase 

def ask_how_many_times_to_buy(total_paints):
    """Prompt the user for how many times to Buy All Weapon Pattern."""
    if dpg.does_item_exist("Buy All Weapon Pattern Window"):
        dpg.delete_item("Buy All Weapon Pattern Window")

    with dpg.window(label="Buy All Weapon Pattern", tag="Buy All Weapon Pattern Window", width=600, height=200, modal=True):
        dpg.add_text(f"How many times would you like to buy {total_paints} paints?")
        
        dpg.add_input_int(label="Number of Times", min_value=1, default_value=1, tag="times_input")
        
        # Pass both total_paints and the value from times_input to confirm_buy_all
        dpg.add_button(label="Confirm", callback=lambda: start_thread(confirm_buy_all, total_paints, dpg.get_value("times_input")))
        dpg.add_button(label="Back", callback=lambda: dpg.hide_item("Buy All Weapon Pattern Window"))


def confirm_buy_all(total_paints, times_count):
    """Start the bulk purchase process in a new thread."""
    global purchase_running
    logger.debug("Attempting to purchase All Weapon Pattern")


    if dpg.does_item_exist("Buy Weapon Pattern Window"):
        dpg.delete_item("Buy Weapon Pattern Window")


    with dpg.window(label="Purchase Confirmation", tag="Purchase Confirmation Window Bulk", width=400, height=200):
        dpg.add_text("Your purchase is being processed...", tag="purchase_status_text_bulk")
        if not dpg.does_item_exist("force_stop_button_bulk"):
            dpg.add_button(label="Force Stop", tag="force_stop_button_bulk", callback=force_stop_purchase, parent="Purchase Confirmation Window Bulk")
        dpg.show_item("force_stop_button_bulk")

    purchase_running = True
    threading.Thread(target=execute_bulk_purchase, args=(total_paints, times_count)).start()

def buy_bulk_paints(item_id, price, currency, count, total_paints):
    """Purchase a paint item."""
    headers, url = load_token_headers()

    data = {
        "itemId": item_id,
        "price": price,
        "discountedPrice": price,
        "currencyCode": currency
    }

    try:
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 201:
            logger.debug(f"Weapon Pattern {item_id} purchased successfully.")
            dpg.set_value("purchase_status_text_bulk", f"Purchased item {count + 1} of {total_paints}.")
        else:
            logger.error(f"Error purchasing item {item_id}: {response.text}")
            dpg.set_value("purchase_status_text_bulk", f"Error purchasing item {count + 1}: {response.text}")
    except requests.RequestException as e:
        logger.error(f"Network error purchasing item {item_id}: {e}")
        dpg.set_value("purchase_status_text_bulk", f"Network error purchasing item {count + 1}: {e}")

    time.sleep(0.5)  # Delay between purchases


def execute_bulk_purchase(total_paints, times_count):
    """Perform the bulk purchase in a separate thread."""
    global purchase_running
    slot_data = load_weapon_pattern('../Offsets/offsets.json')


    logger.debug(f"Total times to purchase: {times_count} of {total_paints}")

    count = 0

    for _ in range(times_count):
        for slot in slot_data:
            if not purchase_running:
                logger.debug("Purchase process stopped by user.")
                break

            for weapon_pattern_name, details in slot.items():
                item_id = details['itemId']
                price = details['price']
                currency = details['currency']

                logger.debug(f"Buying paint: {weapon_pattern_name} (Item ID: {item_id})")

                # Perform the purchase logic
                buy_bulk_paints(item_id, price, currency, count, total_paints)
                count += 1
                

    logger.debug(f"Purchased {count} of {total_paints} items.")
    dpg.set_value("purchase_status_text_bulk", f"Purchased {count} of {total_paints} items.")


    if dpg.does_item_exist("Purchase Confirmation Window Bulk"):
        dpg.delete_item("Purchase Confirmation Window Bulk")

    if dpg.does_item_exist("force_stop_button_bulk"):
        dpg.delete_item("force_stop_button_bulk")


