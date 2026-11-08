from Util.common import item_list_flow

def buy_paint_callback(sender=None, app_data=None, user_data=None):
    item_list_flow(category_key="Paint",             win_label="Buy Paint",
                   win_tag="Buy Paint Menu",          back_tag="Main Menu")

def buy_preplanning_assets_callback(sender=None, app_data=None, user_data=None):
    item_list_flow(category_key="Preplanning Assets", win_label="Buy Preplanning Assets",
                   win_tag="Buy Preplanning Assets Menu", back_tag="Main Menu")

def buy_weapon_pattern_callback(sender=None, app_data=None, user_data=None):
    item_list_flow(category_key="Weapon Pattern",    win_label="Buy Weapon Pattern",
                   win_tag="Buy Weapon Pattern Menu", back_tag="Main Menu")

def buy_mask_pattern_callback(sender=None, app_data=None, user_data=None):
    item_list_flow(category_key="Mask Patterns",     win_label="Buy Mask Pattern",
                   win_tag="Buy Mask Pattern Menu",   back_tag="Main Menu")

def buy_weapon_sticker_callback(sender=None, app_data=None, user_data=None):
    item_list_flow(category_key="Weapon Sticker",    win_label="Buy Weapon Sticker",
                   win_tag="Buy Weapon Sticker Menu", back_tag="Main Menu")
