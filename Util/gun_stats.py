import dearpygui.dearpygui as dpg
import json
import os
import logging
import requests

logger = logging.getLogger("Util.gui")
logger.setLevel(logging.DEBUG if __debug__ else logging.WARNING)

weapon_file = "../Offsets/weapons.json"
request_file = "../Offsets/request.json"
max_level = 28

def gun_stats_callback():
    """Function to be triggered externally to open the Gun Stats window."""
    gun_stats = load_gun_stats()
    display_gun_stats_details(gun_stats)

def load_gun_stats():
    """Load gun stats from the JSON file."""
    json_file_path = os.path.join(os.path.dirname(__file__), weapon_file)
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("Error: Invalid JSON in request file.")
            return []
    return []

def display_gun_stats_details(gun_stats):
    """Display gun stats details in a dropdown list."""
    if dpg.does_item_exist("Gun Stats Menu"):
        dpg.delete_item("Gun Stats Menu")

    logger.debug(f"Loaded gun stats data: {gun_stats}")

    with dpg.window(label="Gun Stats", tag="Gun Stats Menu", width=600, height=400, show=True):
        dpg.add_text("Select an item from Guns Stats:")
        gun_names = [list(gun.keys())[0] for gun in gun_stats]
        dpg.add_combo(gun_names, label="Guns", callback=lambda sender, app_data: show_gun_level(gun_stats, app_data))

        # Add a Back button to return to the previous menu
        dpg.add_spacer()
        dpg.add_button(label="Back", callback=lambda: (dpg.hide_item("Gun Stats Menu"), dpg.show_item("Unlocker Menu")))

def show_gun_level(gun_stats, selected_gun):
    """Show the current level of the selected gun and allow the user to enter the level up value."""
    for gun in gun_stats:
        if selected_gun in gun:
            current_level = gun[selected_gun]["value"]
            stat_code = gun[selected_gun]["statCode"]
            break

    if dpg.does_item_exist("Gun Level Info"):
        dpg.delete_item("Gun Level Info")

    with dpg.window(label="Gun Level Info", tag="Gun Level Info", width=400, height=200, show=True):
        dpg.add_text(f"Current level of {selected_gun}: {current_level}")
        dpg.add_input_int(label="Enter level up value", min_value=0, max_value=max_level - current_level, tag="level_up_value")
        dpg.add_button(label="Level Up", callback=lambda: validate_level_up_value(dpg.get_value("level_up_value"), current_level, stat_code))

def validate_level_up_value(level_up_value, current_level, stat_code):
    """Validate the level up value and prepare the payload."""
    if current_level + level_up_value > max_level:
        dpg.add_text("Error: Level up value exceeds the maximum level.", color=[255, 0, 0], parent="Gun Level Info")
    else:
        payload_value = level_up_value
        # dpg.add_text(f"Payload value to send: {payload_value}", parent="Gun Level Info")
        # dpg.add_text(f"Stat code: {stat_code}", parent="Gun Level Info")
        send_payload(payload_value, stat_code)

def send_payload(value, stat_code):
    """Send the payload to the specified URL."""

    headers, url = load_token_headers()
    # url = "https://szel3hys1l.execute-api.us-east-1.amazonaws.com//social/v1/public/statitems/value/bulk"
    # headers = {
    #     "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    #     "Content-Type": "application/json",
    #     "Accept": "*/*",
    #     "User-Agent": "PAYDAY3/++UE4+Release-4.27-CL-0 Windows/10.0.26100.1.256.64bit"
    # }
    payload = [{
        "inc": value,
        "statCode": stat_code
    }]
    print(payload)
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        print(data)
        dpg.add_text("Payload sent successfully.", color=[0, 255, 0], parent="Gun Level Info")
    else:
        dpg.add_text(f"Failed to send payload. Status code: {response.status_code}", color=[255, 0, 0], parent="Gun Level Info")

def force_stop_purchase():
    """Stop the ongoing purchase process."""
    global purchase_running
    purchase_running = False

    # Log that the force stop was triggered
    logger.debug("Force stop triggered. Stopping the purchase.")
    
    # Ensure the item exists before setting its value
    if dpg.does_item_exist("purchase_status_text_individual_dlcweapon"):
        dpg.set_value("purchase_status_text_individual_dlcweapon", "Purchase process stopped by user.")
    
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