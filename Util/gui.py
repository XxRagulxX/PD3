import dearpygui.dearpygui as dpg
import logging
import os
from functools import partial
from Util.login import login, manage_credentials, load_credentials
from Util.buy_Inventory import buy_inventory_callback
from Util.buy_paints import buy_paint_callback
from Util.buy_preplanning_assets import buy_preplanning_assets_callback
from Util.buy_weapon_pattern import buy_weapon_pattern_callback
from Util.buy_mask_pattern import buy_mask_pattern_callback
from Util.buy_weapon_sticker import buy_weapon_sticker_callback
from Util.buy_money import buy_money_farmer_callback
from Util.buy_cstacks import buy_cstacks_farmer_callback
from Util.buy_cred import buy_cred_farmer_callback
from Util.buy_custom import buy_custom_callback
from Util.buy_heist import buy_Heist_Pack_callback
from Util.buy_dlcweapon import buy_dlcweapon_Pack_callback
from Util.buy_dlctailor import buy_dlctailor_Pack_callback
from Util.buy_twitchdrop import buy_Twitch_Pack_callback
from Util.update_items import fetch_weapon_data
from Util.update_offsets import update_offsets_callback
from Util.buy_all import buy_all_callback
from Util.gun_stats import gun_stats_callback

logger = logging.getLogger("Util.gui")
logger.setLevel(logging.INFO)
_ch = logging.StreamHandler()
_ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(_ch)

user_id = None
access_token = None
debugger_mode_enabled = False

# ── Callbacks ────────────────────────────────────────────────────────────────

def toggle_debugger_mode(sender, app_data, user_data):
    global debugger_mode_enabled
    debugger_mode_enabled = dpg.get_value("debugger_mode_checkbox")
    logger.setLevel(logging.DEBUG if debugger_mode_enabled else logging.INFO)

def toggle_password_visibility(sender, app_data, user_data):
    show = dpg.get_value("show_password_checkbox")
    if show:
        dpg.configure_item("password_input", show=False)
        dpg.configure_item("password_input_temp", show=True)
        dpg.set_value("password_input_temp", dpg.get_value("password_input"))
    else:
        dpg.configure_item("password_input", show=True)
        dpg.configure_item("password_input_temp", show=False)
        dpg.set_value("password_input", dpg.get_value("password_input_temp"))

def login_callback(sender, app_data, user_data):
    global user_id, access_token
    if dpg.get_value("show_password_checkbox"):
        dpg.set_value("password_input", dpg.get_value("password_input_temp"))

    username = dpg.get_value("username_input")
    password = dpg.get_value("password_input")

    dpg.set_value("login_status", "")
    if not username or not password:
        dpg.set_value("login_status", "Please enter both username and password.")
        dpg.configure_item("login_status", color=[255, 180, 0, 255])
        return

    dpg.configure_item("login_button", label="  Logging in...")
    user_id, access_token = login(username, password)

    if user_id and access_token:
        if dpg.get_value("remember_me_checkbox"):
            manage_credentials(username, password, True)
        dpg.hide_item("login_window")
        dpg.show_item("Main Menu")
    else:
        dpg.configure_item("login_button", label="  LOGIN")
        dpg.set_value("login_status", "Login failed. Check your credentials.")
        dpg.configure_item("login_status", color=[255, 80, 80, 255])

def show_sub_menu(sender, app_data, user_data):
    dpg.hide_item("Main Menu")
    dpg.show_item(user_data)

def back_to_main(sender, app_data, user_data):
    dpg.hide_item(user_data)
    dpg.show_item("Main Menu")

def initialize_login():
    username, password = load_credentials()
    if username and password:
        dpg.set_value("username_input", username)
        dpg.set_value("password_input", password)
        dpg.set_value("password_input_temp", password)
    dpg.show_item("login_window")

# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_font():
    candidates = [
        "/usr/share/fonts/TTF/FiraSans-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/Library/Fonts/SF-Pro-Text-Regular.otf",
        "/Library/Fonts/Arial.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def _setup_theme():
    # Payday orange accent
    ORANGE      = (232, 104, 22, 255)
    ORANGE_HOV  = (255, 134, 42, 255)
    ORANGE_ACT  = (200, 78, 10, 255)
    BG_MAIN     = (18,  18,  22, 255)
    BG_WIN      = (24,  24,  30, 255)
    BG_CHILD    = (30,  30,  38, 255)
    BG_FRAME    = (38,  38,  48, 255)
    BG_FRAME_H  = (50,  50,  62, 255)
    BG_FRAME_A  = (60,  60,  74, 255)
    BORDER      = (52,  52,  65, 255)
    SCROLLBAR   = (55,  55,  68, 255)
    TEXT        = (238, 238, 242, 255)
    TEXT_DIM    = (130, 130, 145, 255)

    with dpg.theme() as t:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg,              BG_WIN)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg,               BG_CHILD)
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg,               BG_WIN)
            dpg.add_theme_color(dpg.mvThemeCol_Border,                BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_BorderShadow,          (0,0,0,0))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg,               BG_FRAME)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered,        BG_FRAME_H)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive,         BG_FRAME_A)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg,               BG_MAIN)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive,         (22, 22, 28, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed,      BG_MAIN)
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg,             BG_MAIN)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg,           BG_MAIN)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab,         SCROLLBAR)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered,  (75,75,90,255))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive,   (95,95,112,255))
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark,             ORANGE)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab,            ORANGE)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive,      ORANGE_HOV)
            dpg.add_theme_color(dpg.mvThemeCol_Button,                ORANGE)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,         ORANGE_HOV)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,          ORANGE_ACT)
            dpg.add_theme_color(dpg.mvThemeCol_Header,                (232,104,22,70))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered,         (232,104,22,120))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive,          (232,104,22,160))
            dpg.add_theme_color(dpg.mvThemeCol_Separator,             BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_SeparatorHovered,      ORANGE)
            dpg.add_theme_color(dpg.mvThemeCol_SeparatorActive,       ORANGE_HOV)
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGrip,            (232,104,22,40))
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGripHovered,     (232,104,22,100))
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGripActive,      (232,104,22,160))
            dpg.add_theme_color(dpg.mvThemeCol_Tab,                   BG_FRAME)
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered,            ORANGE_HOV)
            dpg.add_theme_color(dpg.mvThemeCol_TabActive,             ORANGE)
            dpg.add_theme_color(dpg.mvThemeCol_Text,                  TEXT)
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled,          TEXT_DIM)
            # Rounding & spacing
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding,        10)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding,         7)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding,         6)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding,         7)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding,     4)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding,          4)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding,           5)
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize,      1)
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize,       1)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize,       0)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding,         20, 16)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding,          12, 8)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing,           8,  8)
            dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing,      6,  5)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize,         10)
    return t

def _accent_button_theme():
    """Slightly larger/brighter variant — not used here but kept for future calls."""
    with dpg.theme() as t:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button,         (232, 104, 22, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,  (255, 140, 50, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,   (200, 78,  10, 255))
    return t

def _subtle_button_theme():
    """Muted grey button for Back / secondary actions."""
    with dpg.theme() as t:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button,         (48,  48,  60, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,  (62,  62,  76, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,   (38,  38,  50, 255))
    return t

# ── Main entry point ──────────────────────────────────────────────────────────

def run_gui():
    # Apply global theme
    dpg.bind_theme(_setup_theme())
    subtle = _subtle_button_theme()

    # Font setup
    font_path = _find_font()
    font_normal = None
    font_title  = None
    font_header = None
    if font_path:
        with dpg.font_registry():
            font_normal = dpg.add_font(font_path, 15)
            font_header = dpg.add_font(font_path, 18)
            font_title  = dpg.add_font(font_path, 26)
        dpg.bind_font(font_normal)

    VP_W, VP_H = 860, 620
    BTN_H = 42

    # ── LOGIN WINDOW ─────────────────────────────────────────────────────────
    LW, LH = 440, 350
    with dpg.window(tag="login_window", label="",
                    width=LW, height=LH, show=False,
                    no_title_bar=True, no_resize=True,
                    no_move=True, no_collapse=True,
                    pos=[(VP_W - LW) // 2, (VP_H - LH) // 2]):

        dpg.add_spacer(height=10)

        # Title
        with dpg.group(horizontal=False):
            dpg.add_text("PAYDAY BLACK MARKET", tag="_login_title",
                         color=(232, 104, 22, 255))
            if font_title:
                dpg.bind_item_font("_login_title", font_title)

            dpg.add_text("Revanced Edition", color=(140, 140, 155, 255))

        dpg.add_spacer(height=6)
        dpg.add_separator()
        dpg.add_spacer(height=10)

        # Username
        dpg.add_text("USERNAME", color=(160, 160, 175, 255))
        dpg.add_input_text(tag="username_input", width=-1,
                           hint="Enter your username")
        dpg.add_spacer(height=6)

        # Password
        dpg.add_text("PASSWORD", color=(160, 160, 175, 255))
        dpg.add_input_text(tag="password_input", width=-1,
                           password=True, hint="Enter your password", show=True)
        dpg.add_input_text(tag="password_input_temp", width=-1, show=False)
        dpg.add_spacer(height=6)

        # Option checkboxes
        with dpg.group(horizontal=True):
            dpg.add_checkbox(label="Show Password", tag="show_password_checkbox",
                             callback=toggle_password_visibility)
            dpg.add_spacer(width=14)
            dpg.add_checkbox(label="Remember me", tag="remember_me_checkbox")

        dpg.add_checkbox(label="Debugger Mode", tag="debugger_mode_checkbox",
                         callback=toggle_debugger_mode)
        dpg.add_spacer(height=12)

        # Login button
        dpg.add_button(label="  LOGIN", tag="login_button",
                       callback=login_callback, width=-1, height=BTN_H)

        dpg.add_spacer(height=6)
        dpg.add_text("", tag="login_status")

    # ── MAIN MENU ─────────────────────────────────────────────────────────────
    MW, MH = 820, 540
    with dpg.window(tag="Main Menu",
                    label="Payday Black Market  |  Revanced",
                    width=MW, height=MH, show=False,
                    no_collapse=True,
                    pos=[(VP_W - MW) // 2, (VP_H - MH) // 2]):

        # Header row
        dpg.add_text("MAIN MENU", tag="_mm_hdr", color=(232, 104, 22, 255))
        if font_header:
            dpg.bind_item_font("_mm_hdr", font_header)
        dpg.add_text("Choose an action below", color=(130, 130, 148, 255))
        dpg.add_separator()
        dpg.add_spacer(height=10)

        HALF = (MW - 20*2 - 12) // 2  # two columns with padding & gap

        def row(label_a, cb_a, ud_a, label_b, cb_b, ud_b):
            with dpg.group(horizontal=True):
                dpg.add_button(label=label_a, callback=cb_a, user_data=ud_a,
                               width=HALF, height=BTN_H)
                dpg.add_spacer(width=12)
                dpg.add_button(label=label_b, callback=cb_b, user_data=ud_b,
                               width=HALF, height=BTN_H)
            dpg.add_spacer(height=6)

        row("  Buy C-Stacks",          buy_cstacks_farmer_callback, None,
            "  Custom Buy",            buy_custom_callback,         None)

        row("  Buy Preplanning Assets", buy_preplanning_assets_callback, None,
            "  Buy Inventory",          buy_inventory_callback,          None)

        row("  Buy Paint",             buy_paint_callback,             None,
            "  Buy Weapon Pattern",    buy_weapon_pattern_callback,    None)

        row("  Buy Mask Pattern",      buy_mask_pattern_callback,      None,
            "  Buy Weapon Sticker",    buy_weapon_sticker_callback,    None)

        row("  Unlocker",              show_sub_menu, "Unlocker Menu",
            "  Treasure Top-Up",       show_sub_menu, "Treasure Top-Up Menu")

        dpg.add_spacer(height=4)
        with dpg.group(horizontal=True):
            dpg.add_button(label="  Buy All Items",
                           callback=buy_all_callback,
                           width=HALF, height=BTN_H)
            dpg.add_spacer(width=12)
            dpg.add_button(label="  Update Items (offsets.json)",
                           callback=update_offsets_callback,
                           width=HALF, height=BTN_H)

    # ── TREASURE TOP-UP MENU ──────────────────────────────────────────────────
    SW, SH = 500, 400
    with dpg.window(tag="Treasure Top-Up Menu", label="Treasure Top-Up",
                    width=SW, height=SH, show=False,
                    no_collapse=True,
                    pos=[(VP_W - SW) // 2, (VP_H - SH) // 2]):

        dpg.add_text("TREASURE TOP-UP", tag="_tu_hdr", color=(232, 104, 22, 255))
        if font_header:
            dpg.bind_item_font("_tu_hdr", font_header)
        dpg.add_separator()
        dpg.add_spacer(height=10)

        for lbl, cb in [
            ("  Money Farmer",    buy_money_farmer_callback),
            ("  C-Stacks Farmer", buy_cstacks_farmer_callback),
            ("  Cred Farmer",     buy_cred_farmer_callback),
            ("  Gun Max Level",   gun_stats_callback),
        ]:
            dpg.add_button(label=lbl, callback=cb, width=-1, height=BTN_H)
            dpg.add_spacer(height=5)

        dpg.add_spacer(height=10)
        dpg.add_separator()
        dpg.add_spacer(height=8)
        back = dpg.add_button(label="  Back to Main Menu", callback=back_to_main,
                              user_data="Treasure Top-Up Menu", width=-1, height=36)
        dpg.bind_item_theme(back, subtle)

    # ── UNLOCKER MENU ─────────────────────────────────────────────────────────
    with dpg.window(tag="Unlocker Menu", label="DLC Unlocker",
                    width=SW, height=SH, show=False,
                    no_collapse=True,
                    pos=[(VP_W - SW) // 2, (VP_H - SH) // 2]):

        dpg.add_text("DLC UNLOCKER", tag="_ul_hdr", color=(232, 104, 22, 255))
        if font_header:
            dpg.bind_item_font("_ul_hdr", font_header)
        dpg.add_separator()
        dpg.add_spacer(height=10)

        for lbl, cb in [
            ("  DLC Heist Unlocker",          buy_Heist_Pack_callback),
            ("  DLC Weapon Unlocker",          buy_dlcweapon_Pack_callback),
            ("  DLC Tailor Unlocker",          buy_dlctailor_Pack_callback),
            ("  Twitch Drop & Free Stuff",     buy_Twitch_Pack_callback),
        ]:
            dpg.add_button(label=lbl, callback=cb, width=-1, height=BTN_H)
            dpg.add_spacer(height=5)

        dpg.add_spacer(height=10)
        dpg.add_separator()
        dpg.add_spacer(height=8)
        back2 = dpg.add_button(label="  Back to Main Menu", callback=back_to_main,
                               user_data="Unlocker Menu", width=-1, height=36)
        dpg.bind_item_theme(back2, subtle)

    # ── Viewport & launch ─────────────────────────────────────────────────────
    dpg.create_viewport(title="Payday Black Market - Revanced",
                        width=VP_W, height=VP_H,
                        min_width=640, min_height=480)
    dpg.setup_dearpygui()
    dpg.set_viewport_clear_color([18, 18, 22, 255])
    initialize_login()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
