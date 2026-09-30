"""Capture the real native desktop UI under a local display (no account data).

On Linux: xvfb-run -a python scripts/capture_native.py
Requires Pillow. This is a Tk window screenshot, never a web mockup.
"""
from pathlib import Path
import tempfile
import tkinter as tk
from PIL import ImageGrab
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from native_ui import NativeApp
from zen_backend import ZenBackend

class EmptyManager:
    accounts = {}

with tempfile.TemporaryDirectory(prefix='zenrbx_native_capture_') as data_dir:
    backend = ZenBackend(manager=EmptyManager(), data_dir=data_dir)
    backend.presence_updated = float('inf')
    root = tk.Tk()
    root.geometry('1200x760+25+25')
    app = NativeApp(root, backend, maximize=False)
    root.geometry('1200x760+25+25')
    root.update()
    bbox = (root.winfo_rootx(), root.winfo_rooty(),
            root.winfo_rootx() + root.winfo_width(),
            root.winfo_rooty() + root.winfo_height())
    shot = ImageGrab.grab(bbox=bbox)
    shot.save(ROOT / 'site/app-preview.webp', 'WEBP', quality=88)
    app.settings()
    root.update()
    ImageGrab.grab(bbox=bbox).save(ROOT / 'site/settings-preview.webp', 'WEBP', quality=88)
    root.destroy()
    print('Captured native window and settings:', bbox)
