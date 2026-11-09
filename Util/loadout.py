import dearpygui.dearpygui as dpg
import zlib
import json
import os
import sys

from Util.common import _full_win, _VP_W, set_status

_BASE = os.path.dirname(__file__)
_ROOT = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(_BASE)
_OUT  = os.path.join(_ROOT, "Offsets", "loadout_decoded.json")


def loadout_decode_callback(sender=None, app_data=None, user_data=None):
    WIN        = "LoadOut Decoder"
    INPUT_TAG  = "loadout_hex_input"
    STATUS_TAG = "loadout_status"

    if dpg.does_item_exist(WIN):
        dpg.delete_item(WIN)

    def _decode(s=None, a=None, u=None):
        hex_str = dpg.get_value(INPUT_TAG).strip()
        if not hex_str:
            set_status(STATUS_TAG, "Please paste the Loadout hex data first.")
            return

        try:
            raw = bytes.fromhex(hex_str)
        except ValueError:
            set_status(STATUS_TAG, "Invalid hex — make sure you copied the full Loadout value.")
            return

        try:
            decompressed = zlib.decompress(raw)
        except zlib.error as e:
            set_status(STATUS_TAG, f"Decompression failed: {e}")
            return

        try:
            data = json.loads(decompressed.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            set_status(STATUS_TAG, f"JSON parse failed: {e}")
            return

        os.makedirs(os.path.dirname(_OUT), exist_ok=True)
        with open(_OUT, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        set_status(STATUS_TAG, f"Decoded & saved to:  {_OUT}")

    with dpg.window(**_full_win(WIN, "LoadOut Decoder")):
        dpg.add_button(label="  Back", width=-1, height=30,
                       callback=lambda: (dpg.hide_item(WIN), dpg.show_item("Main Menu")))

        dpg.add_text("LoadOut Decoder", color=(185, 55, 185, 255))
        dpg.add_separator()

        dpg.add_text(
            "Paste the Loadout hex value from the POST /records/PartyMemberData/public"
            " request body:",
            color=(160, 160, 175, 255), wrap=_VP_W - 40,
        )

        dpg.add_input_text(
            tag=INPUT_TAG, width=-1, height=390,
            multiline=True, hint="789CED9A...",
        )

        dpg.add_button(label="  Decode & Save", width=-1, height=46,
                       callback=_decode)

        dpg.add_text("", tag=STATUS_TAG, wrap=_VP_W - 40)

    dpg.hide_item("Main Menu")
    dpg.show_item(WIN)
