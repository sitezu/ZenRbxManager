"""ZenRbxManager Windows entry point: real native Tk window, no WebView.

The HTML mock is kept as a visual reference but is NOT loaded at runtime. The
native desktop app invokes ZenBackend directly, without starting a web server.
"""
from __future__ import annotations

import os
import sys

from zen_backend import ZenBackend
from native_ui import NativeApp, run_gui_self_test


def run_self_test():
    """Smoke-test native UI without saved accounts or Roblox network traffic."""
    import tkinter
    if tkinter.TkVersion < 8.6:
        raise RuntimeError('Tk 8.6 or newer is required.')
    # Linux unit tests may run without a display; Windows CI always opens a
    # real native test window, checking the installed executable after setup.
    if sys.platform == 'win32' or os.environ.get('DISPLAY'):
        return run_gui_self_test()
    print('Native Tk module import passed; GUI display not available on this test machine.')
    return 0


def main():
    if '--self-test' in sys.argv:
        try:
            return run_self_test()
        except Exception as exc:
            print(f'Native window self-test failed: {exc}', file=sys.stderr)
            return 1
    if sys.platform != 'win32':
        print('ZenRbxManager requires Windows 10/11 to launch Roblox. Tests can run elsewhere.')
        return 1
    try:
        import tkinter as tk
        from tkinter import messagebox
        backend = ZenBackend()
        root = tk.Tk()
        NativeApp(root, backend)
        root.mainloop()
    except Exception as exc:
        print(f'Could not start the native application: {exc}', file=sys.stderr)
        try:
            messagebox.showerror('ZenRbxManager', f'Could not start the native application: {exc}')
        except Exception:
            pass
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
