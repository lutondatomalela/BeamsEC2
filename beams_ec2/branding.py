"""Application icon shared by source and frozen Windows builds."""
from pathlib import Path
import sys


def asset_path(name):
    root=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))
    return root/'assets'/name


def apply_icon(window):
    import tkinter as tk
    image=tk.PhotoImage(file=str(asset_path('beamsec2.png')))
    window.iconphoto(True,image)
    window._program_icon=image
    if sys.platform=='win32':
        window.iconbitmap(str(asset_path('beamsec2.ico')))
