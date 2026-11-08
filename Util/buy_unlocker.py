from Util.common import combo_purchase_flow

def buy_Heist_Pack_callback(sender=None, app_data=None, user_data=None):
    combo_purchase_flow(
        win_tag  = "Buy Heist Pack Menu",
        win_label= "DLC Heist Unlocker",
        back_tag = "Unlocker Menu",
        sections = [
            ("All Heist Maps",    "Heist Pack"),
            ("Epic Heist Packs",  "Epic Heist Pack"),
            ("Steam Heist Packs", "Steam Heist Pack"),
        ],
    )

def buy_dlcweapon_Pack_callback(sender=None, app_data=None, user_data=None):
    combo_purchase_flow(
        win_tag  = "Buy DLC Weapon Menu",
        win_label= "DLC Weapon Unlocker",
        back_tag = "Unlocker Menu",
        sections = [
            ("Base Weapon Packs",     "DLC Weapon Pack"),
            ("Epic DLC Weapon Packs", "Epic DLC Weapon Pack"),
            ("Steam DLC Weapon Packs","Steam DLC Weapon Pack"),
        ],
    )

def buy_dlctailor_Pack_callback(sender=None, app_data=None, user_data=None):
    combo_purchase_flow(
        win_tag  = "Buy DLC Tailor Menu",
        win_label= "DLC Tailor Unlocker",
        back_tag = "Unlocker Menu",
        sections = [
            ("Base Tailor Packs",      "DLC Tailor Pack"),
            ("Epic DLC Tailor Packs",  "Epic DLC Tailor Pack"),
            ("Steam DLC Tailor Packs", "Steam DLC Tailor Pack"),
        ],
    )

def buy_Twitch_Pack_callback(sender=None, app_data=None, user_data=None):
    combo_purchase_flow(
        win_tag  = "Buy Twitch Menu",
        win_label= "Twitch Drop & Free Stuff",
        back_tag = "Unlocker Menu",
        sections = [
            ("Twitch Drops & Free Items",  "Twitch Items"),
        ],
    )
