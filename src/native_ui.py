"""Real Windows/Tk desktop UI. No browser, WebView, HTML renderer, or HTTP server.

The supplied HTML is retained as a visual reference only. All account operations
use the existing ZenBackend directly; only Roblox's sign-in flow may open a browser.
"""
from __future__ import annotations

import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from zen_backend import THEMES

BG = '#090a0f'
PANEL = '#141522'
FIELD = '#0b0c15'
EDGE = '#29283d'
TEXT = '#f5f4ff'
MUTED = '#a2a9bf'
DIM = '#737e99'
PALETTE = {
    'indigo': '#6366f1', 'cyan': '#06b6d4', 'emerald': '#10b981',
    'amber': '#f59e0b', 'rose': '#f43f5e', 'violet': '#818cf8',
}
FONT = 'Segoe UI'


def label(parent, text, size=10, color=TEXT, weight='normal', **kw):
    return tk.Label(parent, text=text, bg=parent.cget('bg'), fg=color,
                    font=(FONT, size, weight), **kw)


def button(parent, text, command, accent=None, width=None):
    bg = accent or FIELD
    btn = tk.Button(parent, text=text, command=command, bg=bg, fg=TEXT,
                    activebackground=accent or '#242439', activeforeground='white',
                    relief='flat', bd=0, cursor='hand2', padx=14, pady=9,
                    font=(FONT, 10, 'bold'), highlightthickness=0, width=width)
    return btn


def entry(parent, textvariable=None, show=None):
    return tk.Entry(parent, textvariable=textvariable, show=show, bg=FIELD, fg=TEXT,
                    insertbackground=TEXT, selectbackground='#5754b3', relief='flat',
                    bd=0, font=(FONT, 10), highlightthickness=1,
                    highlightbackground=EDGE, highlightcolor='#8b89ff')


def editor(parent, height=5):
    return tk.Text(parent, width=1, height=height, wrap='word', bg=FIELD, fg=TEXT,
                   insertbackground=TEXT, selectbackground='#5754b3', relief='flat',
                   bd=0, padx=12, pady=10, font=(FONT, 10), highlightthickness=1,
                   highlightbackground=EDGE, highlightcolor='#8b89ff', undo=True)


class NativeApp:
    def __init__(self, root: tk.Tk, backend, maximize=True):
        self.root, self.backend = root, backend
        self.root.title('ZenRbxManager')
        self.root.configure(bg=BG)
        self.root.minsize(900, 600)
        self.root.geometry('1120x720')
        if maximize and self.root.tk.call('tk', 'windowingsystem') == 'win32':
            self.root.state('zoomed')  # real Windows maximize; no fake titlebar
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.closed = False
        self.busy = False
        self.filter = 'all'
        self.hide_names = False
        self.accounts = []
        self.selected_name = None
        self.note_account = None
        self.note_timer = None
        self.accent = PALETTE['indigo']
        self.search = tk.StringVar()
        self.status_text = tk.StringVar(value='Ready · local desktop application')
        self._configure_tree_style()
        self._build()
        self.refresh(keep_selection=False)
        self.root.after(45_000, self.periodic_refresh)

    def _configure_tree_style(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('Zen.Treeview', background=FIELD, fieldbackground=FIELD,
                        foreground=TEXT, rowheight=34, borderwidth=0,
                        font=(FONT, 10))
        style.map('Zen.Treeview', background=[('selected', '#39366d')],
                  foreground=[('selected', '#ffffff')])
        style.configure('Zen.Treeview.Heading', background='#161625', foreground=MUTED,
                        relief='flat', borderwidth=0, font=(FONT, 9, 'bold'), padding=(9, 12))
        style.map('Zen.Treeview.Heading', background=[('active', '#202039')])
        style.configure('Zen.Vertical.TScrollbar', background='#24243b', troughcolor=FIELD,
                        borderwidth=0, arrowsize=12)
        style.configure('Zen.TNotebook', background=PANEL, borderwidth=0)
        style.configure('Zen.TNotebook.Tab', background=FIELD, foreground=MUTED,
                        padding=(17, 9), font=(FONT, 10))
        style.map('Zen.TNotebook.Tab', background=[('selected', '#33305d')],
                  foreground=[('selected', TEXT)])
        style.configure('Zen.TCombobox', fieldbackground=FIELD, background=FIELD,
                        foreground=TEXT, arrowcolor=MUTED, borderwidth=0,
                        padding=6, font=(FONT, 10))
        style.map('Zen.TCombobox', fieldbackground=[('readonly', FIELD)],
                  foreground=[('readonly', TEXT)])

    def _build(self):
        # These frames are layout regions of the native window, not a fake OS window.
        header = tk.Frame(self.root, bg='#19192b', height=62)
        header.pack(side='top', fill='x')
        header.pack_propagate(False)
        logo = tk.Label(header, text='Z', bg=self.accent, fg='white',
                        font=(FONT, 19, 'bold'), width=2)
        logo.pack(side='left', padx=(20, 14), pady=11)
        self.logo = logo
        label(header, 'ZENRBXMANAGER', 13, TEXT, 'bold').pack(side='left')
        label(header, '  ●', 11, '#20c997').pack(side='left')
        label(header, 'ACCOUNT WORKSPACE', 9, MUTED, 'bold').pack(side='right', padx=22)

        workspace = tk.Frame(self.root, bg=PANEL)
        workspace.pack(fill='both', expand=True)
        workspace.grid_columnconfigure(0, weight=4, minsize=430)
        workspace.grid_columnconfigure(1, weight=1, minsize=300)
        workspace.grid_rowconfigure(0, weight=1)
        left = tk.Frame(workspace, bg=PANEL)
        left.grid(row=0, column=0, sticky='nsew', padx=(17, 8), pady=16)
        right = tk.Frame(workspace, bg=PANEL)
        right.grid(row=0, column=1, sticky='nsew', padx=(8, 17), pady=16)
        self.workspace, self.left, self.right = workspace, left, right
        self._build_accounts(left)
        self._build_execution(right)
        status = tk.Label(self.root, textvariable=self.status_text, bg=BG, fg=DIM,
                          font=(FONT, 9), anchor='w', padx=18, pady=6)
        status.pack(side='bottom', fill='x')
        self.status_label = status

    def _build_accounts(self, panel):
        search_bar = tk.Frame(panel, bg=PANEL)
        search_bar.pack(fill='x', pady=(0, 12))
        label(search_bar, 'SEARCH', 9, DIM, 'bold').pack(side='left', padx=(0, 10))
        self.search_input = entry(search_bar, self.search)
        self.search_input.pack(side='left', fill='x', expand=True, ipady=8)
        self.search_input.insert(0, '')
        self.search.trace_add('write', lambda *_: self.render_rows())
        filters = tk.Frame(panel, bg=PANEL)
        filters.pack(fill='x', pady=(0, 12))
        self.filter_buttons = {}
        for name, text in [('all', 'All Accs'), ('online', 'Online'), ('ingame', 'In-Game'),
                           ('away', 'Away'), ('offline', 'Offline')]:
            item = button(filters, text, lambda n=name: self.set_filter(n))
            item.pack(side='left', padx=(0, 6))
            self.filter_buttons[name] = item
        self._paint_filters()

        table = tk.Frame(panel, bg=FIELD, highlightthickness=1, highlightbackground=EDGE)
        table.pack(fill='both', expand=True)
        self.table = table
        cols = ('username', 'status', 'alias', 'note')
        self.tree = ttk.Treeview(table, columns=cols, show='headings', selectmode='extended',
                                 style='Zen.Treeview')
        for name, title, size, stretch in [('username', 'USERNAME', 180, True),
                                           ('status', 'STATUS', 86, False),
                                           ('alias', 'TAG', 110, True),
                                           ('note', 'NOTES', 200, True)]:
            self.tree.heading(name, text=title)
            self.tree.column(name, width=size, minwidth=65, anchor='w', stretch=stretch)
        self.tree.pack(side='left', fill='both', expand=True)
        scroll = ttk.Scrollbar(table, orient='vertical', command=self.tree.yview,
                               style='Zen.Vertical.TScrollbar')
        scroll.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scroll.set)
        self.empty_label = tk.Label(table, text='Your space is ready.\nAdd your first account to get started.',
                                    bg=FIELD, fg=MUTED, justify='center',
                                    font=(FONT, 12, 'bold'))
        self.tree.tag_configure('online', foreground='#34d399')
        self.tree.tag_configure('ingame', foreground='#b4abff')
        self.tree.tag_configure('away', foreground='#fbbf24')
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.tree.bind('<Double-1>', lambda _e: self.edit_account())
        self.tree.bind('<Delete>', lambda _e: self.delete_account())

        actions = tk.Frame(panel, bg=PANEL)
        actions.pack(fill='x', pady=(10, 0))
        secondary = tk.Frame(actions, bg=PANEL)
        secondary.pack(fill='x', pady=(0, 7))
        button(secondary, 'Edit', self.edit_account).pack(side='left', padx=(0, 6))
        button(secondary, 'Delete', self.delete_account).pack(side='left', padx=(0, 6))
        button(secondary, 'Privacy', self.toggle_privacy).pack(side='left', padx=(0, 6))
        button(secondary, '↑', lambda: self.move_account(-1)).pack(side='left', padx=(0, 4))
        button(secondary, '↓', lambda: self.move_account(1)).pack(side='left')
        primary = tk.Frame(actions, bg=PANEL)
        primary.pack(fill='x')
        button(primary, '+ Add New Account', self.add_account).pack(side='left')
        button(primary, 'Launch Selected', lambda: self.launch(), accent=self.accent).pack(side='right')
        self.actions = primary
        # Additional credential action is deliberately not a default toolbar button.
        actions.bind('<Button-3>', lambda _e: self.copy_cookie())
        self.tree.bind('<Button-3>', self.account_menu)

    def _build_execution(self, panel):
        title = tk.Frame(panel, bg=FIELD, padx=12, pady=10)
        title.pack(fill='x', pady=(0, 12))
        label(title, 'EXECUTION CENTER', 10, TEXT, 'bold').pack(side='left')
        button(title, '⚙  Settings', self.settings).pack(side='right')
        button(panel, '▶   Join Specific Place', self.place_dialog, accent=self.accent).pack(fill='x', pady=(0, 8))
        button(panel, '↗   Launch Main Client', lambda: self.launch()).pack(fill='x', pady=(0, 18))
        label(panel, 'NOTES & CONFIG', 9, MUTED, 'bold').pack(anchor='w')
        note_tools = tk.Frame(panel, bg=PANEL)
        note_tools.pack(fill='x', pady=(8, 9))
        button(note_tools, '+ AFK Note', lambda: self.insert_note('AFK Grind Session')).pack(side='left', padx=(0, 5))
        button(note_tools, '+ VIP Note', lambda: self.insert_note('Main VIP Account')).pack(side='left', padx=(0, 5))
        button(note_tools, 'Clear', lambda: self.insert_note('')).pack(side='left')
        self.counter = label(panel, '0 / 250', 9, DIM)
        self.counter.pack(anchor='e', pady=(0, 5))
        self.notes = editor(panel, height=9)
        self.notes.pack(fill='both', expand=True)
        self.notes.bind('<KeyRelease>', self.on_note_changed)
        self.notes.bind('<FocusOut>', lambda _e: self.save_note())
        self.notes.configure(state='disabled')

    def status(self, text):
        self.status_text.set(text)

    def error(self, exc):
        self.status('Operation failed. See the dialog for details.')
        messagebox.showerror('ZenRbxManager', str(exc), parent=self.root)

    def action(self, kind, payload=None, done=None):
        """Fast, local operations; state comes back directly from the backend."""
        try:
            result = self.backend.action(kind, payload or {})
            if result.get('state'):
                self.refresh(state=result['state'])
            if result.get('message'):
                self.status(result['message'])
            if done:
                done(result)
            return result
        except Exception as exc:
            self.error(exc)
            return None

    def async_action(self, kind, payload=None, done=None):
        """Roblox/network operations never block the native UI event loop."""
        if self.busy:
            self.status('Please wait for the current operation.')
            return
        self.busy = True
        self.status('Working…')
        def worker():
            try:
                result, err = self.backend.action(kind, payload or {}), None
            except Exception as exc:
                result, err = None, exc
            def finish():
                if self.closed:
                    return
                self.busy = False
                if err:
                    self.error(err)
                    return
                if result.get('state'):
                    self.refresh(state=result['state'])
                if result.get('message'):
                    self.status(result['message'])
                if done:
                    done(result)
            if not self.closed:
                self.root.after(0, finish)
        threading.Thread(target=worker, daemon=True).start()

    def refresh(self, state=None, keep_selection=True):
        if state is None:
            try:
                state = self.backend.action('state', {})
            except Exception as exc:
                self.error(exc)
                return
        self.accounts = state['accounts']
        self.config = state['settings']
        self._set_theme(self.config.get('theme', 'indigo'))
        old = self.selected_name if keep_selection else None
        self.render_rows()
        if old and old in self.tree.get_children():
            self.tree.selection_set(old)
            self.tree.focus(old)
        elif self.selected_name not in {item['username'] for item in self.accounts}:
            self.selected_name = None
            self._set_note(None)

    def render_rows(self):
        if not hasattr(self, 'tree'):
            return
        selected = set(self.tree.selection())
        self.tree.delete(*self.tree.get_children())
        needle = self.search.get().strip().casefold()
        for item in self.accounts:
            if needle not in (item['username'] + ' ' + item['alias']).casefold():
                continue
            if self.filter != 'all' and item['status'] != self.filter:
                continue
            username = item['username']
            name = '••••••••' if self.hide_names else username
            status = item['status'].replace('ingame', 'In-Game').title()
            note = item['note'].replace('\n', ' ')[:72]
            self.tree.insert('', 'end', iid=username,
                             values=(name, status, item['alias'] or '—', note),
                             tags=(item['status'],))
        still = [name for name in selected if self.tree.exists(name)]
        if self.tree.get_children():
            self.empty_label.place_forget()
        else:
            self.empty_label.place(relx=.5, rely=.53, anchor='center')
        if still:
            self.tree.selection_set(still)
        elif not self.accounts:
            self.status('Your space is ready. Add your first account to get started.')

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        current = selected[0]
        if current != self.selected_name:
            self.save_note()
            self.selected_name = current
            item = next((x for x in self.accounts if x['username'] == current), None)
            self._set_note(item)

    def _set_note(self, item):
        self.notes.configure(state='normal')
        self.notes.delete('1.0', 'end')
        self.notes.insert('1.0', item['note'] if item else '')
        self.notes.configure(state='normal' if item else 'disabled')
        self.note_account = item['username'] if item else None
        self.counter.configure(text=f"{len(item['note']) if item else 0} / 250")

    def on_note_changed(self, _event=None):
        if not self.note_account:
            return
        text = self.notes.get('1.0', 'end-1c')
        if len(text) > 250:
            self.notes.delete('1.0+250c', 'end')
            text = text[:250]
        self.counter.configure(text=f'{len(text)} / 250')
        if self.note_timer:
            self.root.after_cancel(self.note_timer)
        self.note_timer = self.root.after(700, self.save_note)

    def save_note(self):
        if self.note_timer:
            self.root.after_cancel(self.note_timer)
            self.note_timer = None
        name = self.note_account
        if not name:
            return
        text = self.notes.get('1.0', 'end-1c')[:250]
        previous = next((x['note'] for x in self.accounts if x['username'] == name), None)
        if previous != text:
            self.action('note', {'username': name, 'note': text})

    def insert_note(self, text):
        if not self.note_account:
            self.status('Select an account before editing its note.')
            return
        self.notes.delete('1.0', 'end')
        self.notes.insert('1.0', text)
        self.on_note_changed()

    def selected(self):
        result = list(self.tree.selection())
        return result or ([self.selected_name] if self.selected_name else [])

    def set_filter(self, name):
        self.filter = name
        self._paint_filters()
        self.render_rows()

    def _paint_filters(self):
        for name, item in self.filter_buttons.items():
            item.configure(bg=self.accent if name == self.filter else FIELD)

    def _set_theme(self, name):
        self.accent = PALETTE.get(name, PALETTE['indigo'])
        self.logo.configure(bg=self.accent)
        self._paint_filters()
        for parent in (self.actions, self.right):
            for child in parent.winfo_children():
                if isinstance(child, tk.Button) and child.cget('bg') in PALETTE.values():
                    child.configure(bg=self.accent, activebackground=self.accent)

    def toggle_privacy(self):
        self.hide_names = not self.hide_names
        self.render_rows()

    def move_account(self, direction):
        selected = self.selected()
        if len(selected) != 1:
            self.status('Select one account to reorder.')
            return
        names = [a['username'] for a in self.accounts]
        position = names.index(selected[0])
        next_pos = position + direction
        if 0 <= next_pos < len(names):
            names[position], names[next_pos] = names[next_pos], names[position]
            self.action('order', {'names': names})
            self.refresh()

    def account_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
        menu = tk.Menu(self.root, tearoff=0, bg=PANEL, fg=TEXT,
                       activebackground=self.accent, activeforeground='white')
        menu.add_command(label='Edit account', command=self.edit_account)
        menu.add_command(label='Copy cookie (sensitive)', command=self.copy_cookie)
        menu.add_command(label='Delete account', command=self.delete_account)
        menu.tk_popup(event.x_root, event.y_root)
        menu.grab_release()

    def copy_cookie(self):
        selected = self.selected()
        if len(selected) != 1:
            self.status('Select one account before copying a cookie.')
            return
        if not messagebox.askyesno('Sensitive account credential',
                                  'Copy this account cookie? Anyone who has it can access your account.\n'
                                  'Never paste it into an issue or share it.', parent=self.root):
            return
        result = self.action('cookie_copy', {'username': selected[0]})
        if result:
            self.root.clipboard_clear()
            self.root.clipboard_append(result['cookie'])
            self.status('Cookie copied. Keep it private and clear the clipboard when finished.')

    def _dialog(self, title, width=460, height=420):
        dialog = tk.Toplevel(self.root, bg=PANEL)
        dialog.title(title)
        self.root.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - width) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - height) // 2
        dialog.geometry(f'{width}x{height}+{max(0, x)}+{max(0, y)}')
        dialog.minsize(width, height)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.focus_set()
        dialog.columnconfigure(0, weight=1)
        return dialog

    def add_account(self):
        dialog = self._dialog('Add New Account', 500, 420)
        label(dialog, 'ADD NEW ACCOUNT', 14, TEXT, 'bold').pack(anchor='w', padx=24, pady=(24, 12))
        tabs = ttk.Notebook(dialog, style='Zen.TNotebook')
        tabs.pack(fill='both', expand=True, padx=20, pady=10)
        website = tk.Frame(tabs, bg=PANEL)
        cookie = tk.Frame(tabs, bg=PANEL)
        tabs.add(website, text='Website Login')
        tabs.add(cookie, text='Roblox Cookie')
        label(website, 'Sign in using the browser selected in Settings.\n'
              'Only the Roblox login flow opens a browser; the app itself stays native.',
              10, MUTED, justify='left').pack(anchor='w', padx=12, pady=20)
        def login():
            dialog.destroy()
            self.async_action('browser_login')
        button(website, 'Open Roblox Sign-In', login, accent=self.accent).pack(fill='x', padx=12)
        label(cookie, 'Paste a cookie from an account you own. Keep it private.',
              10, MUTED).pack(anchor='w', padx=12, pady=(16, 8))
        value = editor(cookie, height=4)
        value.pack(fill='x', padx=12, pady=(0, 14))
        def submit():
            raw = value.get('1.0', 'end-1c').strip()
            if not raw:
                messagebox.showerror('ZenRbxManager', 'Enter a Roblox cookie.', parent=dialog)
                return
            value.delete('1.0', 'end')
            dialog.destroy()
            self.async_action('cookie_import', {'cookie': raw})
        button(cookie, 'Import My Account', submit, accent=self.accent).pack(fill='x', padx=12)

    def place_dialog(self):
        dialog = self._dialog('Target Specific Place', 440, 280)
        label(dialog, 'TARGET SPECIFIC PLACE', 13, TEXT, 'bold').pack(anchor='w', padx=24, pady=(22, 15))
        label(dialog, 'PLACE ID', 9, MUTED, 'bold').pack(anchor='w', padx=24)
        place = entry(dialog)
        place.pack(fill='x', padx=24, pady=(5, 13), ipady=7)
        label(dialog, 'SERVER JOB ID  ·  OPTIONAL', 9, MUTED, 'bold').pack(anchor='w', padx=24)
        job = entry(dialog)
        job.pack(fill='x', padx=24, pady=(5, 16), ipady=7)
        def submit():
            if not place.get().strip():
                messagebox.showerror('ZenRbxManager', 'Place ID is required.', parent=dialog)
                return
            target, server = place.get().strip(), job.get().strip()
            dialog.destroy()
            self.launch(target, server)
        button(dialog, 'Launch Into Session', submit, accent=self.accent).pack(fill='x', padx=24)

    def launch(self, place='', job=''):
        names = self.selected()
        if not names:
            self.status('Select one or more accounts before launching.')
            return
        self.save_note()
        self.async_action('launch', {'names': names, 'place': place, 'job': job},
                          done=self._show_launch_failures)

    def _show_launch_failures(self, result):
        failed = [f"{x['username']}: {x['message']}" for x in result.get('results', []) if not x['ok']]
        if failed:
            messagebox.showwarning('Roblox launch', '\n'.join(failed), parent=self.root)

    def edit_account(self):
        selected = self.selected()
        if len(selected) != 1:
            self.status('Select one account to edit.')
            return
        current = next((x for x in self.accounts if x['username'] == selected[0]), None)
        if not current:
            return
        self.save_note()
        dialog = self._dialog('Edit Account', 460, 410)
        label(dialog, 'EDIT ACCOUNT', 13, TEXT, 'bold').pack(anchor='w', padx=24, pady=(20, 10))
        label(dialog, 'ROBLOX USERNAME  ·  READ ONLY', 9, MUTED, 'bold').pack(anchor='w', padx=24)
        label(dialog, current['username'], 10, TEXT).pack(anchor='w', padx=24, pady=(4, 12))
        label(dialog, 'ALIAS / TAG', 9, MUTED, 'bold').pack(anchor='w', padx=24)
        alias = entry(dialog)
        alias.insert(0, current['alias'])
        alias.pack(fill='x', padx=24, pady=(4, 12), ipady=7)
        label(dialog, 'NOTES', 9, MUTED, 'bold').pack(anchor='w', padx=24)
        note = editor(dialog, height=4)
        note.insert('1.0', current['note'])
        note.pack(fill='both', expand=True, padx=24, pady=(4, 9))
        away = tk.BooleanVar(value=current['status'] == 'away')
        tk.Checkbutton(dialog, text='Mark as Away', variable=away, bg=PANEL, fg=TEXT,
                       selectcolor=FIELD, activebackground=PANEL, activeforeground=TEXT,
                       font=(FONT, 10)).pack(anchor='w', padx=24)
        def submit():
            payload = {'username': current['username'], 'new_username': current['username'],
                       'alias': alias.get(), 'note': note.get('1.0', 'end-1c'), 'away': away.get()}
            if self.action('edit', payload):
                dialog.destroy()
                self._set_note(next((x for x in self.accounts if x['username'] == selected[0]), None))
        button(dialog, 'Save Account', submit, accent=self.accent).pack(fill='x', padx=24, pady=(10, 20))

    def delete_account(self):
        selected = self.selected()
        if len(selected) != 1:
            self.status('Select one account to delete.')
            return
        name = selected[0]
        if messagebox.askyesno('Delete Account', f'Remove {name} from this computer? This cannot be undone.',
                               parent=self.root):
            self.action('delete', {'username': name})

    def settings(self):
        dialog = self._dialog('Settings & Preferences', 500, 610)
        label(dialog, 'SETTINGS & PREFERENCES', 13, TEXT, 'bold').pack(anchor='w', padx=23, pady=(19, 14))
        label(dialog, 'ACCENT THEME', 9, MUTED, 'bold').pack(anchor='w', padx=23)
        palette = tk.Frame(dialog, bg=PANEL)
        palette.pack(fill='x', padx=23, pady=(8, 17))
        for name in ['indigo', 'cyan', 'emerald', 'amber', 'rose', 'violet']:
            tk.Button(palette, bg=PALETTE[name], activebackground=PALETTE[name],
                      relief='flat', bd=0, width=4, height=2, cursor='hand2',
                      command=lambda key=name: self.action('settings', {'key': 'theme', 'value': key})).pack(side='left', padx=(0, 10))
        label(dialog, 'AUTOMATION & SYSTEM PREFERENCES', 9, MUTED, 'bold').pack(anchor='w', padx=23)
        bloxstrap = tk.BooleanVar(value=bool(self.config.get('bloxstrap')))
        startup = tk.BooleanVar(value=bool(self.config.get('startup')))
        def toggle(key, variable):
            if not self.action('settings', {'key': key, 'value': variable.get()}):
                variable.set(not variable.get())
        for text, key, var in [('Use Bloxstrap (requires installation)', 'bloxstrap', bloxstrap),
                               ('Launch with Windows Startup', 'startup', startup)]:
            tk.Checkbutton(dialog, text=text, variable=var, command=lambda k=key, v=var: toggle(k, v),
                           bg=PANEL, fg=TEXT, activebackground=PANEL, activeforeground=TEXT,
                           selectcolor=FIELD, font=(FONT, 10), anchor='w').pack(fill='x', padx=23, pady=8)
        row = tk.Frame(dialog, bg=PANEL)
        row.pack(fill='x', padx=23, pady=(8, 10))
        label(row, 'Login browser', 10, MUTED).pack(side='left')
        browser = tk.StringVar(value=self.config.get('browser', 'edge'))
        chooser = ttk.Combobox(row, textvariable=browser, values=['edge', 'chrome', 'firefox'],
                               width=12, state='readonly', style='Zen.TCombobox')
        chooser.pack(side='right')
        chooser.bind('<<ComboboxSelected>>', lambda _e: self.action('settings', {'key': 'browser', 'value': browser.get()}))
        row = tk.Frame(dialog, bg=PANEL)
        row.pack(fill='x', padx=23, pady=(0, 15))
        label(row, 'Delay between launches (seconds)', 10, MUTED).pack(side='left')
        delay = tk.StringVar(value=str(self.config.get('delay', .5)))
        field = entry(row, delay)
        field.configure(width=7)
        field.pack(side='right', ipady=6)
        def save_delay(_event=None):
            try:
                value = float(delay.get())
            except ValueError:
                value = -1
            if not self.action('settings', {'key': 'delay', 'value': value}):
                delay.set(str(self.config.get('delay', .5)))
        field.bind('<FocusOut>', save_delay)
        field.bind('<Return>', save_delay)
        label(dialog, 'MANAGER UTILITIES', 9, MUTED, 'bold').pack(anchor='w', padx=23, pady=(4, 10))
        tools = tk.Frame(dialog, bg=PANEL)
        tools.pack(fill='x', padx=23)
        button(tools, 'Export Config', self.export_config).pack(side='left', fill='x', expand=True, padx=(0, 4))
        button(tools, 'Import Config', self.import_config).pack(side='left', fill='x', expand=True, padx=(4, 0))
        button(dialog, 'Clear Old Login Profiles', lambda: self.action('clear_cache')).pack(fill='x', padx=23, pady=10)
        label(dialog, 'Saved cookies are never included in config exports.', 9, DIM).pack(anchor='w', padx=23, pady=7)
        button(dialog, 'Close Settings', dialog.destroy, accent=self.accent).pack(fill='x', padx=23, pady=(13, 17))

    def export_config(self):
        result = self.action('export')
        if not result:
            return
        path = filedialog.asksaveasfilename(parent=self.root, initialfile=result['filename'],
                                            defaultextension='.json', filetypes=[('JSON', '*.json')])
        if path:
            try:
                Path(path).write_text(json.dumps(result['config'], indent=2), encoding='utf-8')
                self.status('Configuration saved without cookies.')
            except OSError as exc:
                self.error(exc)

    def import_config(self):
        path = filedialog.askopenfilename(parent=self.root, filetypes=[('JSON', '*.json')])
        if not path:
            return
        try:
            file = Path(path)
            if file.stat().st_size > 32768:
                raise ValueError('Config file is too large.')
            config = json.loads(file.read_text(encoding='utf-8'))
            self.action('import', {'config': config})
        except (ValueError, OSError) as exc:
            self.error(exc)

    def periodic_refresh(self):
        if self.closed:
            return
        if not self.busy:
            self.refresh()
        self.root.after(45_000, self.periodic_refresh)

    def close(self):
        self.closed = True
        if self.note_timer:
            self.root.after_cancel(self.note_timer)
        self.save_note()
        self.root.destroy()


def run_gui_self_test():
    """Native window/layout smoke test without a Roblox account or saved data."""
    import tempfile
    from zen_backend import ZenBackend

    class EmptyManager:
        accounts = {}

    with tempfile.TemporaryDirectory(prefix='zenrbx_native_test_') as data_dir:
        backend = ZenBackend(manager=EmptyManager(), data_dir=data_dir)
        backend.presence_updated = float('inf')
        root = tk.Tk()
        try:
            app = NativeApp(root, backend, maximize=False)
            root.update_idletasks()
            root.update()
            assert app.root.winfo_exists() and app.workspace.winfo_width() >= 800
            assert app.root.winfo_width() == app.workspace.winfo_width()
            assert app.left.winfo_width() > app.right.winfo_width()
            assert app.tree.get_children() == ()
            app.set_filter('online')
            app.toggle_privacy()
            assert not app.tree.get_children()
        finally:
            root.destroy()
    print('Native Tk window self-test passed (no WebView, browser, or Roblox account).')
    return 0
