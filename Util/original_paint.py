import dearpygui.dearpygui as dpg
import os
import time
import logging
import requests
import json
import threading

# Configure logging
logger = logging.getLogger("Util.gui")
logger.setLevel(logging.INFO)

total_purchases = 0
total_count = 0
progress_updated = False


request_file = "../Offsets/request.json"

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

def load_paints(file_path):
    """Load Paint Paint from the specified JSON file."""
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            paints = data.get("Paint", [])
            return paints
    except Exception as e:
        logger.error(f"Failed to load Paint Paint: {e}")
        return []

def ask_how_many_paints(paint_name, item_id, price, currency):
    """Prompt the user for the number of Paint to purchase."""
    if dpg.does_item_exist("Buy Paint Window"):
        dpg.delete_item("Buy Paint Window")
    
    with dpg.window(label=f"Buy {paint_name}", tag="Buy Paint Window", width=600, height=200, modal=True):
        dpg.add_text(f"How many {paint_name} would you like to buy?")
        
        dpg.add_input_int(label="Number of Paints", min_value=1, default_value=1, tag="slot_count_input")
        
        dpg.add_button(label="Confirm", callback=lambda: start_thread(confirm_slot_purchase, item_id, price, currency))
        dpg.add_button(label="Back", callback=lambda: (dpg.hide_item("Buy Paint Window"), dpg.show_item("Buy Paint")))

def start_thread(target, *args):
    """Start a thread to run the target function."""
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()

def buy_individual_paint(slot_count, item_id, price, currency):
    """Purchase a single paint item."""
    headers, url = load_token_headers()

    if not url or not headers:
        logger.error("Failed to load URL or headers from request.json.")
        return

    logger.info(f"URL: {url}")
    logger.info(f"Headers: {headers}")

    data = {
        "itemId": item_id,
        "price": price,
        "discountedPrice": price,
        "currencyCode": currency
    }

    dpg.set_value("purchase_status_text_individual", "Starting individual purchase...")

    for i in range(slot_count):
        logger.info(f"Purchasing slot {i + 1} out of {slot_count}.")

        try:
            response = requests.post(url, json=data, headers=headers)

            if response.status_code == 201:
                logger.info("Individual paint purchased successfully.")
                dpg.set_value("purchase_status_text_individual", f"Purchased slot {i + 1} of {slot_count} successfully.")
            else:
                logger.error(f"Error purchasing individual paint: {response.text}")
                dpg.set_value("purchase_status_text_individual", f"Error purchasing slot {i + 1}: {response.text}")
        except requests.RequestException as e:
            logger.error(f"Network error during purchase: {e}")
            dpg.set_value("purchase_status_text_individual", f"Network error: {e}")
        time.sleep(0.5)

def buy_bulk_paints(item_id, price, currency, count, total_paints):
    """Purchase a paint item."""
    headers, url = load_token_headers()

    if not url or not headers:
        logger.error("Failed to load URL or headers from request.json.")
        return

    data = {
        "itemId": item_id,
        "price": price,
        "discountedPrice": price,
        "currencyCode": currency
    }

    try:
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 201:
            logger.info(f"Paint {item_id} purchased successfully.")
            dpg.set_value("purchase_status_text", f"Purchased item {count + 1} of {total_paints}.")
        else:
            logger.error(f"Error purchasing item {item_id}: {response.text}")
            dpg.set_value("purchase_status_text", f"Error purchasing item {count + 1}: {response.text}")
    except requests.RequestException as e:
        logger.error(f"Network error purchasing item {item_id}: {e}")
        dpg.set_value("purchase_status_text", f"Network error purchasing item {count + 1}: {e}")

    time.sleep(0.5)  # Delay between purchases

def confirm_slot_purchase(item_id, price, currency):
    """Confirm the slot purchase based on user input."""
    logger.info(f"Attempting to purchase item: {item_id}")
    slot_count = dpg.get_value("slot_count_input")

    if not dpg.does_item_exist("purchase_status_text_individual"):
        dpg.add_text(label="Purchase Status", tag="purchase_status_text_individual", default_value="Starting purchase.", parent="Buy Paint Window")

    # Call to purchase the paint
    buy_individual_paint(slot_count, item_id, price, currency)

    # After purchase, close the current window and show the Paint menu
    if dpg.does_item_exist("Buy Paint Window"):
         dpg.hide_item("Buy Paint Window")
    if dpg.does_item_exist("Buy Paint Menu"):
        dpg.show_item("Buy Paint Menu")


def display_Paint_details(slot_data, Paint_type):
    """Display the Paint details in the GUI."""
    if dpg.does_item_exist("Buy Paint Menu"):
        dpg.delete_item("Buy Paint Menu")
    
    logger.info(f"Loaded slot data: {slot_data}")

    with dpg.window(label="Buy Paint", tag="Buy Paint Menu", width=600, height=400, show=True):
        dpg.add_text(f"Items in {Paint_type}:")
        
        total_paints = 0

        for slot in slot_data:
            for paint_name, details in slot.items():
                logger.info(f"Preparing button for {paint_name} with details: {details}")

                if details and isinstance(details, dict):
                    total_paints += 1

                    def create_callback(paint_name, item_id, price, currency):
                        return lambda: ask_how_many_paints(paint_name, item_id, price, currency)

                    dpg.add_button(label=paint_name,
                                   callback=create_callback(paint_name, details['itemId'], details['price'], details['currency']))
                else:
                    logger.warning(f"Slot details for {paint_name} are invalid: {details}")

        dpg.add_button(label="Buy All Paints", callback=lambda: ask_how_many_times_to_buy(total_paints))

        dpg.add_button(label="Back", callback=lambda: (dpg.hide_item("Buy Paint Menu"), dpg.show_item("Main Menu")))

def ask_how_many_times_to_buy(total_paints):
    """Prompt the user for how many times to buy all paints."""
    if dpg.does_item_exist("Buy All Paints Window"):
        dpg.delete_item("Buy All Paints Window")

    with dpg.window(label="Buy All Paints", tag="Buy All Paints Window", width=600, height=200, modal=True):
        dpg.add_text(f"How many times would you like to buy {total_paints} paints?")
        
        dpg.add_input_int(label="Number of Times", min_value=1, default_value=1, tag="times_input")
        
        # Pass both total_paints and the value from times_input to confirm_buy_all
        dpg.add_button(label="Confirm", callback=lambda: start_thread(confirm_buy_all, total_paints, dpg.get_value("times_input")))
        dpg.add_button(label="Back", callback=lambda: dpg.hide_item("Buy All Paints Window"))

def confirm_buy_all(total_paints, times_count):
    """Start the bulk purchase process in a new thread."""
    
    logger.info("Attempting to purchase all paints.")

    if not dpg.does_item_exist("purchase_status_text"):
        dpg.add_text(label="Purchase Status", tag="purchase_status_text", default_value="Starting purchase.", parent="Buy All Paints Window")

    dpg.set_value("purchase_status_text", "")

    # Start a new thread for the bulk purchase
    purchase_thread = threading.Thread(target=execute_bulk_purchase, args=(total_paints, times_count))
    purchase_thread.start()

    # Add a frame callback to periodically update the progress in the GUI
    dpg.set_frame_callback(1, update_bulk_purchase_progress)

def update_bulk_purchase_progress():
    """Check for progress updates and update the GUI."""
    global total_purchases, total_count, bulk_purchase_progress_updated
    if bulk_purchase_progress_updated:
        dpg.set_value("purchase_status_text", f"Bulk Purchase Progress: {total_purchases} of {total_count} items.")
        bulk_purchase_progress_updated = False  # Reset after updating

def execute_bulk_purchase(total_paints, times_count):
    """Perform the bulk purchase in a separate thread."""
    global total_purchases, total_count, bulk_purchase_progress_updated
    slot_data = load_paints('../Offsets/offsets.json')


    if times_count <= 0:
        logger.warning("Invalid times_count value, exiting the purchase.")
        return

    total_purchases = 0
    total_count = total_paints * times_count

    logger.info(f"Total times to purchase: {times_count} of {total_paints}")

    count = 0

    for _ in range(times_count):
        for slot in slot_data:
            for paint_name, details in slot.items():
                item_id = details['itemId']
                price = details['price']
                currency = details['currency']

                logger.info(f"Buying paint: {paint_name} (Item ID: {item_id})")

                # Perform the purchase logic
                buy_bulk_paints(item_id, price, currency, count, total_paints)
                count += 1
                
                total_purchases += 1

                # Mark that the progress has been updated
                bulk_purchase_progress_updated = True

                time.sleep(0.5)  # Delay between each bulk purchase (if needed)

    logger.info(f"Purchased {total_purchases} of {total_paints} items.")
    dpg.set_value("purchase_status_text", f"Purchased {total_purchases} of {total_paints} items.")

    # After bulk purchase completes, return to "Buy Paint Menu"
    if dpg.does_item_exist("Buy All Paints Window"):
        dpg.hide_item("Buy All Paints Window")
    if dpg.does_item_exist("Buy Paint Menu"):
        dpg.show_item("Buy Paint Menu")

def update_purchase_progress():
    """Check for progress updates and update the GUI."""
    global total_purchases, total_count, progress_updated
    if progress_updated:
        dpg.set_value("purchase_status_text", f"Purchased {total_purchases} of {total_count} items.")
        progress_updated = False  # Reset after updating

def buy_paint_callback():
    """Function to be triggered externally to open the Paint purchase window."""
    slot_data = load_paints('../Offsets/offsets.json')
    display_Paint_details(slot_data, "Paint")