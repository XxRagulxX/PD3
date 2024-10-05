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
def buy_inventory_callback():
    """Function to be triggered externally to open the Inventory purchase window."""
    slot_data = load_inventory('../Offsets/offsets.json')
    display_inventory_details(slot_data, "Inventory Slots")
            
def force_stop_purchase():
    """Stop the ongoing purchase process."""
    global purchase_running
    purchase_running = False

    # Log that the force stop was triggered
    logger.debug("Force stop triggered. Stopping the purchase.")
    
    # Ensure the item exists before setting its value
    if dpg.does_item_exist("purchase_status_text_Inventory_individual"):
        dpg.set_value("purchase_status_text_Inventory_individual", "Purchase process stopped by user.")
    
    if dpg.does_item_exist("purchase_status_text_Inventory_bulk"):
        dpg.set_value("purchase_status_text_Inventory_bulk", "Purchase process stopped by user.")
    
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

def load_inventory(file_path):
    """Load Inventory from the specified JSON file."""
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            Inventory = data.get("Inventory Slots", [])
            return Inventory
    except Exception as e:
        logger.error(f"Failed to load Inventory Slots: {e}")
        return []

def start_thread(target, *args):
    """Start a thread to run the target function."""
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()

def display_inventory_details(slot_data, Inventory_type):
    """Display the Inventory details in the GUI."""
    if dpg.does_item_exist("Buy Inventory Menu"):
        dpg.delete_item("Buy Inventory Menu")
    
    logger.debug(f"Loaded slot data: {slot_data}")

    with dpg.window(label="Buy Inventory", tag="Buy Inventory Menu", width=600, height=400, show=True):
        dpg.add_text(f"Items in {Inventory_type}:")
        
        total_Inventory = 0

        for slot in slot_data:
            for inventory_name, details in slot.items():
                logger.debug(f"Preparing button for {inventory_name} with details: {details}")

                if details and isinstance(details, dict):
                    total_Inventory += 1

                    def create_callback(inventory_name, item_id, price, currency):
                        return lambda: ask_how_many_inventory(inventory_name, item_id, price, currency)

                    dpg.add_button(label=inventory_name,
                                   callback=create_callback(inventory_name, details['itemId'], details['price'], details['currency']))
                else:
                    logger.warning(f"Slot details for {inventory_name} are invalid: {details}")

        dpg.add_button(label="Buy All Inventory", callback=lambda: ask_how_many_times_to_buy(total_Inventory))

        dpg.add_button(label="Back", callback=lambda: (dpg.hide_item("Buy Inventory Menu"), dpg.show_item("Main Menu")))
        

# Individual Purchase. 

def ask_how_many_inventory(inventory_name, item_id, price, currency):
    """Prompt the user for the number of Inventory to purchase."""
    if dpg.does_item_exist("Buy Inventory Window"):
        dpg.delete_item("Buy Inventory Window")
    
    with dpg.window(label=f"Buy {inventory_name}", tag="Buy Inventory Window", width=600, height=200, modal=True):
        dpg.add_text(f"How many {inventory_name} would you like to buy?")
        
        dpg.add_input_int(label="Number of Inventory", min_value=1, default_value=1, tag="slot_count_inventory_input")
        
        dpg.add_button(label="Confirm", callback=lambda: start_thread(confirm_slot_purchase, item_id, price, currency))
        dpg.add_button(label="Back", callback=lambda: (dpg.hide_item("Buy Inventory Window"), dpg.show_item("Buy Inventory Menu")))

def confirm_slot_purchase(item_id, price, currency):
    global purchase_running
    """Logic to handle the purchase confirmation and create a new window."""
    logger.debug(f"Attempting to purchase item: {item_id}")
    slot_count = dpg.get_value("slot_count_inventory_input")

    # Close the current window
    if dpg.does_item_exist("Buy Inventory Window"):
        dpg.delete_item("Buy Inventory Window")

    # Create a new window to display the purchase confirmation or further actions
    with dpg.window(label="Purchase Confirmation", tag="Purchase Confirmation Window", width=400, height=200):
        dpg.add_text("Your purchase is being processed...", tag="purchase_status_text_Inventory_individual")
        if not dpg.does_item_exist("force_stop_button_individuel"):
            dpg.add_button(label="Force Stop", tag="force_stop_button_individuel", callback=force_stop_purchase, parent="Purchase Confirmation Window")
        dpg.show_item("force_stop_button_individuel")

    # Start the purchase in a separate thread
    purchase_running = True
    threading.Thread(target=buy_individual_Inventory_slots, args=(slot_count, item_id, price, currency)).start()

def buy_individual_Inventory_slots(slot_count, item_id, price, currency):
    """Purchase a single Inventory item."""
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
    dpg.set_value("purchase_status_text_Inventory_individual", "Starting individual purchase...")

    for i in range(slot_count):
        if not purchase_running:
            logger.debug("Purchase process stopped by user.")
            break
        logger.debug(f"Purchasing slot {i + 1} out of {slot_count}.")

        try:
            response = requests.post(url, json=data, headers=headers)
            logger.debug(f"Response: {response.text}")

            if response.status_code == 201:
                logger.debug("Individual Inventory purchased successfully.")
                dpg.set_value("purchase_status_text_Inventory_individual", f"Purchased Inventory slot {i + 1} of {slot_count} successfully.")
            else:
                logger.error(f"Error purchasing individual Inventory: {response.text}")
                dpg.set_value("purchase_status_text_Inventory_individual", f"Error purchasing Inventory slot {i + 1}: {response.text}")
        except requests.RequestException as e:
            logger.error(f"Network error purchasing Inventory item {item_id}: {e}")
            dpg.set_value("purchase_status_text", f"Network error purchasing Inventory item {i + 1}: {e}")
        
        time.sleep(0.5)
    
    if dpg.does_item_exist("Purchase Confirmation Window"):
        dpg.delete_item("Purchase Confirmation Window")
    
    if dpg.does_item_exist("Buy Inventory Window"):
        dpg.delete_item("Buy Inventory Window")


#Bulk Purchase 

def ask_how_many_times_to_buy(total_Inventory):
    """Prompt the user for how many times to buy all Inventory."""
    if dpg.does_item_exist("Buy All Inventory Window"):
        dpg.delete_item("Buy All Inventory Window")

    with dpg.window(label="Buy All Inventory", tag="Buy All Inventory Window", width=600, height=200, modal=True):
        dpg.add_text(f"How many times would you like to buy {total_Inventory} Inventory?")
        
        dpg.add_input_int(label="Number of Times", min_value=1, default_value=1, tag="times_input")
        
        # Pass both total_Inventory and the value from times_input to confirm_buy_all
        dpg.add_button(label="Confirm", callback=lambda: start_thread(confirm_buy_all, total_Inventory, dpg.get_value("times_input")))
        dpg.add_button(label="Back", callback=lambda: dpg.hide_item("Buy All Inventory Window"))


def confirm_buy_all(total_Inventory, times_count):
    """Start the bulk purchase process in a new thread."""
    global purchase_running
    logger.debug("Attempting to purchase all Inventory.")


    if dpg.does_item_exist("Buy Inventory Window"):
        dpg.delete_item("Buy Inventory Window")


    with dpg.window(label="Purchase Confirmation", tag="Purchase Confirmation Window Bulk", width=400, height=200):
        dpg.add_text("Your purchase is being processed...", tag="purchase_status_text_Inventory_bulk")
        if not dpg.does_item_exist("force_stop_button_bulk"):
            dpg.add_button(label="Force Stop", tag="force_stop_button_bulk", callback=force_stop_purchase, parent="Purchase Confirmation Window Bulk")
        dpg.show_item("force_stop_button_bulk")

    purchase_running = True
    threading.Thread(target=execute_bulk_inventory_purchase, args=(total_Inventory, times_count)).start()

def buy_bulk_Inventory(item_id, price, currency, count, total_Inventory):
    """Purchase a Inventory item."""
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
            logger.debug(f"Inventory {item_id} purchased successfully.")
            dpg.set_value("purchase_status_text_Inventory_bulk", f"Purchased Inventory item {count + 1} of {total_Inventory}.")
        else:
            logger.error(f"Error purchasing Inventory item {item_id}: {response.text}")
            dpg.set_value("purchase_status_text_Inventory_bulk", f"Error purchasing Inventory item {count + 1}: {response.text}")
    except requests.RequestException as e:
        logger.error(f"Network error purchasing Inventory item {item_id}: {e}")
        dpg.set_value("purchase_status_text_Inventory_bulk", f"Network error purchasing Inventory item {count + 1}: {e}")

    time.sleep(0.5)  # Delay between purchases


def execute_bulk_inventory_purchase(total_Inventory, times_count):
    """Perform the bulk purchase in a separate thread."""
    global purchase_running
    slot_data = load_inventory('../Offsets/offsets.json')


    logger.debug(f"Total times to purchase: {times_count} of {total_Inventory}")

    count = 0

    for _ in range(times_count):
        for slot in slot_data:
            if not purchase_running:
                logger.debug("Purchase process stopped by user.")
                break

            for inventory_name, details in slot.items():
                item_id = details['itemId']
                price = details['price']
                currency = details['currency']

                logger.debug(f"Buying Inventory: {inventory_name} (Item ID: {item_id})")

                # Perform the purchase logic
                buy_bulk_Inventory(item_id, price, currency, count, total_Inventory)
                count += 1
                

    logger.debug(f"Purchased {count} of {total_Inventory} items.")
    dpg.set_value("purchase_status_text_Inventory_bulk", f"Purchased {count} of {total_Inventory} items.")


    if dpg.does_item_exist("Purchase Confirmation Window Bulk"):
        dpg.delete_item("Purchase Confirmation Window Bulk")

    if dpg.does_item_exist("force_stop_button_bulk"):
        dpg.delete_item("force_stop_button_bulk")

    if dpg.does_item_exist("Buy Inventory Window"):
        dpg.delete_item("Buy Inventory Window")