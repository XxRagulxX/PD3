import dearpygui.dearpygui as dpg
import requests
import json
import os
import logging

logger = logging.getLogger("Util.gui")
logger.setLevel(logging.DEBUG if __debug__ else logging.WARNING)

request_file = "../Offsets/request.json"
output_file = "./Offsets/weapons.json"  # Save inside the current directory's "Offsets" folder

def load_token_headers():
    """Load token headers and URL from the request JSON file."""
    json_file_path = os.path.join(os.path.dirname(__file__), request_file)
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, "r") as f:
                data = json.load(f)
                return data.get("headers", {}), data.get("url_buy_products", {}).get("url_upgrade", "")
        except json.JSONDecodeError:
            logger.error("Error: Invalid JSON in request file.")
            return {}, ""
    return {}, ""

def fetch_weapon_data():
    """Fetch weapon data and save the results to a JSON file."""
    headers, url = load_token_headers()
    if not url:
        raise ValueError("URL for weapon data is not provided.")
    
    # Show window to inform the user the script is being updated
    with dpg.window(label="Weapon Data", tag="Weapon Data", width=500, height=100, show=True):
        dpg.add_text("Updating the script...")

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            # Parse the JSON response
            data = response.json()

            # Ensure "data" exists and is a list
            if not isinstance(data.get("data"), list):
                raise ValueError("The JSON does not contain a 'data' key with a list value.")

            # List to store results
            results = []

            # Iterate over the data list
            for item in data["data"]:
                if isinstance(item, dict):
                    # Check if "statCode" contains "weapon-level"
                    if "weapon-level" in item.get("statCode", ""):
                        # Extract weapon name by formatting the "statCode"
                        weapon_name = item.get("statCode", "").split("-weapon-level")[0].replace("-", " ").title()

                        # Append the formatted dictionary to results
                        results.append({
                            weapon_name: {
                                "statCode": item.get("statCode", "Unknown Code"),
                                "value": item.get("value", 0.0)  # Default to 0.0 if "value" is missing
                            }
                        })

            # Save results to the output JSON file
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w") as file:
                json.dump(results, file, indent=4)

            logger.debug("Weapon data update completed successfully.")
            dpg.add_text("Update completed successfully.", parent="Weapon Data")
            dpg.add_button(label="Close", callback=lambda: dpg.delete_item("Weapon Data"), parent="Weapon Data")
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON response.")
            dpg.add_text("Failed to decode JSON response.", parent="Weapon Data", color=[255, 0, 0])
            dpg.add_button(label="Close", callback=lambda: dpg.delete_item("Weapon Data"), parent="Weapon Data")
        except Exception as e:
            logger.error(f"Error during script update: {e}")
            dpg.add_text(f"Error during script update: {e}", parent="Weapon Data", color=[255, 0, 0])
            dpg.add_button(label="Close", callback=lambda: dpg.delete_item("Weapon Data"), parent="Weapon Data")
    else:
        logger.error(f"Failed to retrieve data. Status code: {response.status_code}")
        dpg.add_text(f"Connection error: {response.status_code}", parent="Weapon Data", color=[255, 0, 0])
        dpg.add_button(label="Close", callback=lambda: dpg.delete_item("Weapon Data"), parent="Weapon Data")
