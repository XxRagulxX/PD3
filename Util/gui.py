import dearpygui.dearpygui as dpg
import logging
from functools import partial
from Util.login import login, manage_credentials, load_credentials
from Util.buy_Inventory import buy_inventory_callback
from Util.buy_paints import buy_paint_callback
from Util.buy_preplanning_assets import buy_preplanning_assets_callback
from Util.buy_weapon_pattern import buy_weapon_pattern_callback

# Setting up logging for debugger mode
logger = logging.getLogger("Util.gui")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Global variables
user_id = None
access_token = None
debugger_mode_enabled = False  # Global flag to track debugger mode

def toggle_debugger_mode(sender, app_data, user_data):
    global debugger_mode_enabled
    debugger_mode_enabled = dpg.get_value("debugger_mode_checkbox")
    if debugger_mode_enabled:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debugger mode enabled. Opening terminal and showing detailed logs.")
    else:
        logger.setLevel(logging.INFO)
        logger.debug("Debugger mode disabled.")

def toggle_password_visibility(sender, app_data, user_data):
    show_password = dpg.get_value("show_password_checkbox")
    if show_password:
        dpg.configure_item("password_input", show=False)
        dpg.configure_item("password_input_temp", show=True)
        dpg.set_value("password_input_temp", dpg.get_value("password_input"))
    else:
        dpg.configure_item("password_input", show=True)
        dpg.configure_item("password_input_temp", show=False)
        dpg.set_value("password_input", dpg.get_value("password_input_temp"))

def login_callback(sender, app_data, user_data):
    global user_id, access_token, debugger_mode_enabled

    if dpg.get_value("show_password_checkbox"):
        dpg.set_value("password_input", dpg.get_value("password_input_temp"))

    username = dpg.get_value("username_input")
    password = dpg.get_value("password_input")

    if debugger_mode_enabled:
        logger.debug(f"Attempting login with username: {username}")

    if username and password:
        user_id, access_token = login(username, password)
        if user_id and access_token:
            if debugger_mode_enabled:
                logger.debug(f"Login successful! User ID: {user_id}, Access Token: {access_token}")
            if dpg.get_value("remember_me_checkbox"):
                manage_credentials(username, password, dpg.get_value("remember_me_checkbox"))
            dpg.hide_item("login_window")
            dpg.show_item("Main Menu")
        else:
            if debugger_mode_enabled:
                logger.debug("Login failed. Invalid credentials.")
            dpg.add_text("Login failed. Please check your credentials.", parent="login_window", color=[255, 0, 0])
    else:
        if debugger_mode_enabled:
            logger.debug("Login failed. Missing username or password.")
        dpg.add_text("Please enter both username and password.", parent="login_window", color=[255, 0, 0])

def menu_callback(sender, app_data, user_data):
    if debugger_mode_enabled:
        logger.debug(f"Selected menu: {user_data}")

def show_sub_menu(sender, app_data, user_data):
    if debugger_mode_enabled:
        logger.debug(f"Showing sub-menu: {user_data}")
    dpg.hide_item("Main Menu")
    dpg.show_item(user_data)

def back_to_main(sender, app_data, user_data):
    if debugger_mode_enabled:
        logger.debug(f"Going back to Main Menu from: {user_data}")
    dpg.hide_item(user_data)
    dpg.show_item("Main Menu")

def initialize_login():
    username, password = load_credentials()
    if username and password:
        dpg.set_value("username_input", username)
        dpg.set_value("password_input", password)
        dpg.set_value("password_input_temp", password)
        dpg.show_item("login_window")
    else:
        dpg.show_item("login_window")

# Main menu options
main_menu_options = {
    1: "Buy C-Stacks",
    2: "Custom Buy",
    3: "Buy Preplanning Assets",
    4: "Buy Inventory",
    5: "Buy Paint",
    6: "Buy Weapon Pattern",
    7: "Buy Mask Pattern",
    8: "Buy Weapon Sticker",
    9: "Unlocker",
    10: "Treasure Top-Up"
}

# DLC Unlocker options
dlc_menu_options = {
    0: "DLC Map Unlocker",
    1: "DLC Weapon Unlocker",
    2: "DLC Tailor Unlocker",
    3: "Twitch Drop, Preorder Bonus & Other Free Stuff Unlock"
}

# Farm menu options
farm_menu_options = {
    0: "Money Farmer",
    1: "Gold Farmer",
    2: "Cred Farmer",
    3: "Gun Max Level",
    4: "Max Level & Renown"
}

dpg.create_context()

# Login window
with dpg.window(label="Login Window", tag="login_window", width=400, height=200):
    dpg.add_input_text(label="Username", tag="username_input")
    dpg.add_input_text(label="Password", tag="password_input", password=True, show=True)
    dpg.add_input_text(label="Password Temp", tag="password_input_temp", show=False)
    dpg.add_checkbox(label="Show Password", tag="show_password_checkbox", callback=toggle_password_visibility)
    dpg.add_checkbox(label="Remember my login", tag="remember_me_checkbox")
    dpg.add_checkbox(label="Enable Debugger Mode", tag="debugger_mode_checkbox", callback=toggle_debugger_mode)
    dpg.add_button(label="Login", callback=login_callback)

with dpg.window(label="Main Menu", tag="Main Menu", width=600, height=400, show=False):
    for key, label in main_menu_options.items():
        if label == "Buy Inventory":
            dpg.add_button(label=label, callback=buy_inventory_callback)
        elif label == "Buy Preplanning Assets":
            dpg.add_button(label=label, callback=buy_preplanning_assets_callback)
        elif label == "Buy Paint":
            dpg.add_button(label=label, callback=buy_paint_callback)
        elif label == "Buy Weapon Pattern":
            dpg.add_button(label=label, callback=buy_weapon_pattern_callback)
        elif label == "Treasure Top-Up":
            dpg.add_button(label=label, callback=show_sub_menu, user_data="Treasure Top-Up Menu")
        elif label == "Unlocker":
            dpg.add_button(label=label, callback=show_sub_menu, user_data="Unlocker Menu")
        else:
            dpg.add_button(label=label, callback=show_sub_menu, user_data=f"Sub Menu {key}")

with dpg.window(label="Treasure Top-Up Menu", tag="Treasure Top-Up Menu", width=600, height=400, show=False):
    for key, label in farm_menu_options.items():
        dpg.add_button(label=label, callback=menu_callback, user_data=label)
    dpg.add_button(label="Back", callback=back_to_main, user_data="Treasure Top-Up Menu")  # Back button

# Unlocker Menu window
with dpg.window(label="Unlocker Menu", tag="Unlocker Menu", width=600, height=400, show=False):
    for key, label in dlc_menu_options.items():
        dpg.add_button(label=label, callback=menu_callback, user_data=label)
    dpg.add_button(label="Back", callback=back_to_main, user_data="Unlocker Menu")  # Back button

dpg.create_viewport(title="Payday Black Market- Revanced", width=800, height=600)
dpg.setup_dearpygui()
initialize_login()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
