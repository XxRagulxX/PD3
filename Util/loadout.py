import dearpygui.dearpygui as dpg
import zlib
import json
import os
import sys

from Util.common import _full_win, _VP_W, set_status

_BASE    = os.path.dirname(__file__)
_ROOT    = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(_BASE)
_OUT_DEC = os.path.join(_ROOT, "Offsets", "loadout_decoded.json")
_OUT_ENC = os.path.join(_ROOT, "Offsets", "loadout_encoded.json")


def _encode(decoded_data):
    """Return (hex_str, cs, ds) from a dict."""
    json_bytes = json.dumps(decoded_data, indent=4, ensure_ascii=False).encode("utf-8")
    compressed = zlib.compress(json_bytes)
    return compressed.hex().upper(), len(compressed), len(json_bytes)


def loadout_decode_callback(sender=None, app_data=None, user_data=None):
    WIN        = "LoadOut Decoder"
    INPUT_TAG  = "lo_hex_input"
    STATUS_TAG = "lo_status"
    if dpg.does_item_exist(WIN):
        dpg.delete_item(WIN)

    # ── Decode ────────────────────────────────────────────────────────────────
    def _do_decode(s=None, a=None, u=None):
        hex_str = dpg.get_value(INPUT_TAG).strip()
        if not hex_str:
            set_status(STATUS_TAG, "Paste the Loadout hex data first.")
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

        os.makedirs(os.path.dirname(_OUT_DEC), exist_ok=True)
        with open(_OUT_DEC, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        set_status(STATUS_TAG, f"Decoded — saved to {_OUT_DEC}")

    # ── Encode & Save ─────────────────────────────────────────────────────────
    def _do_encode(s=None, a=None, u=None):
        if not os.path.exists(_OUT_DEC):
            set_status(STATUS_TAG, "No loadout_decoded.json found — decode first.")
            return
        try:
            with open(_OUT_DEC, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            set_status(STATUS_TAG, f"Failed to read loadout_decoded.json: {e}")
            return

        hex_str, cs, ds = _encode(data)
        payload = {"Loadout": hex_str, "CS": cs, "DS": ds}
        os.makedirs(os.path.dirname(_OUT_ENC), exist_ok=True)
        with open(_OUT_ENC, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4)
        set_status(STATUS_TAG, f"Encoded — saved to {_OUT_ENC}  (CS={cs}, DS={ds})")

    # ── UI ────────────────────────────────────────────────────────────────────
    with dpg.window(**_full_win(WIN, "LoadOut Decoder")):
        dpg.add_button(label="  Back", width=-1, height=30,
                       callback=lambda: (dpg.hide_item(WIN), dpg.show_item("Main Menu")))

        dpg.add_text("LoadOut Decoder", color=(185, 55, 185, 255))
        dpg.add_separator()

        # ── Decode section ────────────────────────────────────────────────────
        dpg.add_text("DECODE", color=(130, 130, 148, 255))
        dpg.add_text("Paste the Loadout hex value from the POST /records/PartyMemberData/public body:",
                     color=(160, 160, 175, 255), wrap=_VP_W - 40)

        dpg.add_input_text(tag=INPUT_TAG, width=-1, height=120,
                           multiline=True, hint="789CED9A...")

        dpg.add_button(label="  Decode & Save", width=-1, height=42, callback=_do_decode)

        dpg.add_separator()

        # ── Encode + Send section ─────────────────────────────────────────────
        dpg.add_text("ENCODE", color=(130, 130, 148, 255))
        dpg.add_text(f"Edit  {_OUT_DEC}  then:",
                     color=(160, 160, 175, 255), wrap=_VP_W - 40)

        dpg.add_button(label="  Encode & Save to File", width=-1, height=42,
                       callback=_do_encode)

        dpg.add_separator()
        dpg.add_text("", tag=STATUS_TAG, wrap=_VP_W - 40)

    dpg.hide_item("Main Menu")
    dpg.show_item(WIN)
