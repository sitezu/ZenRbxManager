"""Native widget tests use no browser, HTTP server, saved credentials, or Roblox API."""
import os
import sys
import tkinter as tk

import pytest

from native_ui import NativeApp
from zen_backend import ZenBackend


class DummyManager:
    def __init__(self):
        self.accounts = {
            'Alpha': {'note': 'Original', 'zen_alias': 'Main', 'cookie': 'private-one'},
            'Beta': {'note': '', 'zen_alias': 'Alt', 'cookie': 'private-two'},
        }

    def set_account_note(self, name, note):
        self.accounts[name]['note'] = note
        return True

    def save_accounts(self):
        pass

    def delete_account(self, name):
        del self.accounts[name]
        return True


@pytest.mark.skipif(sys.platform != 'win32' and not os.environ.get('DISPLAY'),
                    reason='Native widget tests require a desktop display')
def test_native_window_layout_and_original_ui_controls(tmp_path):
    backend = ZenBackend(manager=DummyManager(), data_dir=tmp_path)
    backend.presence_updated = float('inf')
    root = tk.Tk()
    try:
        app = NativeApp(root, backend, maximize=False)
        root.update()
        assert root.winfo_width() == app.workspace.winfo_width()
        assert app.left.winfo_width() > app.right.winfo_width()
        assert app.tree.get_children() == ('Alpha', 'Beta')
        app.search.set('alt')
        assert app.tree.get_children() == ('Beta',)
        app.search.set('')
        app.set_filter('online')
        assert not app.tree.get_children()  # no fake presence result
        app.set_filter('all')
        app.tree.selection_set('Alpha')
        app.on_select()
        app.insert_note('New note')
        app.save_note()
        assert backend.manager.accounts['Alpha']['note'] == 'New note'
        app.toggle_privacy()
        assert app.tree.item('Alpha', 'values')[0] == '••••••••'
        app.action('settings', {'key': 'theme', 'value': 'cyan'})
        assert app.logo.cget('bg') == '#06b6d4'
        app.move_account(1)
        assert app.tree.get_children() == ('Beta', 'Alpha')
        for open_dialog in (app.add_account, app.place_dialog, app.edit_account, app.settings):
            app.tree.selection_set('Alpha')
            app.on_select()
            open_dialog()
            dialogs = [child for child in root.winfo_children() if isinstance(child, tk.Toplevel)]
            assert len(dialogs) == 1
            dialogs[0].destroy()
    finally:
        root.destroy()
