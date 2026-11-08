import sys
import os
import dearpygui.dearpygui as dpg
import Util.gui as gui

def _ensure_data_dir():
    if not getattr(sys, 'frozen', False):
        return
    dst = os.path.join(os.path.dirname(sys.executable), "Offsets")
    if not os.path.exists(dst):
        import shutil
        shutil.copytree(os.path.join(sys._MEIPASS, "Offsets"), dst)

if __name__ == "__main__":
    _ensure_data_dir()
    dpg.create_context()
    gui.run_gui()
