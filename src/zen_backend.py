"""Local-only API connecting the supplied Zen UI to Evanovar RAM's core.
No cloud service, no third-party account server, and no fake account rows.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests
from classes.account_manager import RobloxAccountManager
from classes.operation_result import OperationResult
from utils.app_paths import get_data_dir

THEMES = {'indigo', 'cyan', 'emerald', 'amber', 'rose', 'violet'}
DEFAULTS = {'theme': 'indigo', 'bloxstrap': False, 'startup': False, 'browser': 'edge', 'delay': 0.5, 'order': []}


class ZenBackend:
    def __init__(self, manager=None, data_dir=None):
        self.data_dir = Path(data_dir or get_data_dir())
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.manager = manager or RobloxAccountManager()
        # Existing files are loaded BEFORE enabling encryption; never overwrite a locked vault.
        if manager is None and not self.manager.encryption_config.is_setup_complete():
            self.manager.switch_encryption_method('hardware')
        self.lock = threading.RLock()
        self.config_file = self.data_dir / 'zen_settings.json'
        self.config = dict(DEFAULTS)
        if self.config_file.exists():
            try:
                loaded = json.loads(self.config_file.read_text(encoding='utf-8'))
                if isinstance(loaded, dict):
                    self.config.update({k: v for k, v in loaded.items() if k in DEFAULTS})
            except (ValueError, OSError):
                pass
        self.presences = {}
        self.presence_updated = 0.0
        self.refreshing = False

    def save_config(self):
        with self.lock:
            tmp = self.config_file.with_suffix('.tmp')
            tmp.write_text(json.dumps(self.config, indent=2), encoding='utf-8')
            os.replace(tmp, self.config_file)

    def status_refresh(self):
        if time.monotonic() - self.presence_updated < 90 or self.refreshing:
            return
        self.refreshing = True
        self.presence_updated = time.monotonic()
        threading.Thread(target=self._fetch_presence, daemon=True).start()

    def _fetch_presence(self):
        try:
            with self.lock:
                accounts = [(name, dict(info)) for name, info in self.manager.accounts.items()]
            for name, info in accounts:
                uid, cookie = info.get('user_id'), info.get('cookie')
                if not uid or not cookie:
                    continue
                try:
                    response = requests.post('https://presence.roblox.com/v1/presence/users',
                        json={'userIds': [int(uid)]}, cookies={'.ROBLOSECURITY': cookie}, timeout=6)
                    response.raise_for_status()
                    entries = response.json().get('userPresences') or []
                    if entries:
                        status = {0: 'offline', 1: 'online', 2: 'ingame', 3: 'online'}.get(entries[0].get('userPresenceType'), 'unknown')
                        with self.lock:
                            self.presences[name] = status
                except (requests.RequestException, ValueError, KeyError, TypeError):
                    with self.lock:
                        self.presences[name] = 'unknown'
        finally:
            self.refreshing = False

    def state(self):
        self.status_refresh()
        with self.lock:
            accounts = []
            for name, info in self.manager.accounts.items():
                if not isinstance(info, dict):
                    continue
                accounts.append({'username': name, 'alias': str(info.get('zen_alias') or ''),
                                 'note': str(info.get('note') or ''),
                                 'status': 'away' if info.get('zen_away') else self.presences.get(name, 'unknown')})
            rank = {name: i for i, name in enumerate(self.config.get('order', []))}
            accounts.sort(key=lambda a: rank.get(a['username'], len(rank)))
            return {'accounts': accounts, 'settings': dict(self.config)}

    def _require_account(self, name):
        if not isinstance(name, str) or name not in self.manager.accounts:
            raise ValueError('Select an existing account first.')
        return self.manager.accounts[name]

    def _result(self, result):
        if isinstance(result, OperationResult):
            if not result:
                raise ValueError(result.message or result.title or 'Operation failed.')
            return result.message or 'Done.'
        if result is False:
            raise ValueError('Operation failed.')
        return 'Done.'

    def action(self, kind, payload):
        if not isinstance(payload, dict):
            raise ValueError('Invalid request.')
        if kind == 'state':
            return self.state()
        if kind == 'cookie_import':
            cookie = str(payload.get('cookie') or '').strip()
            if len(cookie) > 8192:
                raise ValueError('Cookie is too long.')
            # The username is determined by Roblox, never trusted from the form.
            msg = self._result(self.manager.import_cookie_account_result(cookie))
            return {'message': msg, 'state': self.state()}
        if kind == 'browser_login':
            # UI runs this in a non-blocking background job on the HTTP server.
            browser = self.config.get('browser', 'edge')
            descriptor = {'key': browser, 'label': browser.title(), 'executable_path': '', 'driver_type': browser}
            return {'message': self._result(self.manager.add_account(amount=1, browser=descriptor)), 'state': self.state()}
        if kind == 'edit':
            name = payload.get('username')
            with self.lock:
                info = self._require_account(name)
                # Roblox username is immutable here: changing the dictionary key would
                # disconnect the stored cookie from its real identity.
                if str(payload.get('new_username') or '').strip() != name:
                    raise ValueError('Roblox usernames cannot be changed here. Reimport the account instead.')
                info['zen_alias'] = str(payload.get('alias') or '').strip()[:60]
                info['note'] = str(payload.get('note') or '')[:250]
                info['zen_away'] = bool(payload.get('away', False))
                self.manager.save_accounts()
            return {'message': 'Account saved.', 'state': self.state()}
        if kind == 'note':
            with self.lock:
                name = payload.get('username')
                self._require_account(name)
                self.manager.set_account_note(name, str(payload.get('note') or '')[:250])
            return {'message': 'Note saved.', 'state': self.state()}
        if kind == 'delete':
            with self.lock:
                name = payload.get('username')
                self._require_account(name)
                self.manager.delete_account(name)
                self.presences.pop(name, None)
                self.config['order'] = [x for x in self.config['order'] if x != name]
                self.save_config()
            return {'message': 'Account removed.', 'state': self.state()}
        if kind == 'order':
            names = payload.get('names')
            with self.lock:
                if not isinstance(names, list) or len(names) != len(set(map(str, names))) or set(names) != set(self.manager.accounts):
                    raise ValueError('Invalid account order.')
                self.config['order'] = names
                self.save_config()
            return {'message': 'Order saved.'}
        if kind == 'cookie_copy':
            # Avoid emitting the credential into any logs; explicit click only.
            with self.lock:
                return {'cookie': self._require_account(payload.get('username')).get('cookie', '')}
        if kind == 'launch':
            names = payload.get('names')
            if not isinstance(names, list) or not names or len(names) > 100 or len(names) != len(set(names)):
                raise ValueError('Select one or more accounts (maximum 100).')
            place = str(payload.get('place') or '').strip()
            job = str(payload.get('job') or '').strip()
            if place and not re.fullmatch(r'[1-9][0-9]{0,19}', place):
                raise ValueError('Place ID must be a positive number.')
            if job and (not place or not re.fullmatch(r'[0-9a-fA-F-]{36}', job)):
                raise ValueError('Enter a valid Place ID and server Job UUID.')
            with self.lock:
                for name in names:
                    self._require_account(name)
                launcher = 'bloxstrap' if self.config.get('bloxstrap') else 'default'
                delay = max(0, min(30, float(self.config.get('delay', 0.5))))
            results = []
            for i, name in enumerate(names):
                try:
                    result = self.manager.launch_roblox(name, game_id=place, job_id=job, launcher_preference=launcher)
                    results.append({'username': name, 'ok': bool(result), 'message': result.message if isinstance(result, OperationResult) else str(result)})
                except Exception as exc:
                    results.append({'username': name, 'ok': False, 'message': str(exc)})
                if i < len(names) - 1:
                    time.sleep(delay)
            return {'results': results, 'message': f"Launched {sum(r['ok'] for r in results)} of {len(results)} account(s)."}
        if kind == 'settings':
            key, value = payload.get('key'), payload.get('value')
            if key == 'theme' and value in THEMES:
                pass
            elif key == 'bloxstrap' and type(value) is bool:
                pass
            elif key == 'browser' and value in ('edge', 'chrome', 'firefox'):
                pass
            elif key == 'delay' and isinstance(value, (int, float)) and 0 <= value <= 30:
                pass
            elif key == 'startup' and type(value) is bool:
                self.set_startup(value)
            else:
                raise ValueError('Invalid setting.')
            with self.lock:
                self.config[key] = value
                self.save_config()
            return {'message': 'Preference saved.', 'state': self.state()}
        if kind == 'export':
            # No security cookies or credentials in exported configuration.
            with self.lock:
                return {'filename': 'ZenRbxManager-config.json', 'config': {k: self.config[k] for k in DEFAULTS if k != 'startup'}}
        if kind == 'import':
            config = payload.get('config')
            if not isinstance(config, dict):
                raise ValueError('Expected a configuration JSON object.')
            validated = {}
            for k in ('theme', 'bloxstrap', 'browser', 'delay'):
                if k in config:
                    value = config[k]
                    if ((k == 'theme' and value in THEMES) or (k == 'bloxstrap' and type(value) is bool)
                        or (k == 'browser' and value in ('edge', 'chrome', 'firefox'))
                        or (k == 'delay' and isinstance(value, (int, float)) and 0 <= value <= 30)):
                        validated[k] = value
                    else:
                        raise ValueError(f'Invalid setting: {k}')
            with self.lock:
                self.config.update(validated)
                self.save_config()
            return {'message': 'Configuration imported (no credentials).', 'state': self.state()}
        if kind == 'window':
            if sys.platform != 'win32':
                raise ValueError('Window controls require Windows.')
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                raise ValueError('Window is not active.')
            if payload.get('action') == 'minimize':
                user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
            elif payload.get('action') == 'close':
                user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
            else:
                raise ValueError('Invalid window action.')
            return {'message': 'Done.'}
        if kind == 'clear_cache':
            # Only delete temporary profiles created by the app; NEVER stored account cookies.
            count = 0
            temp = Path(tempfile.gettempdir())
            for folder in temp.glob('roblox_login_*'):
                if folder.is_dir() and folder.stat().st_mtime < time.time() - 3600:
                    shutil.rmtree(folder, ignore_errors=True)
                    count += 1
            return {'message': f'Cleared {count} old temporary login profile(s). Saved accounts were not deleted.'}
        raise ValueError('Unknown action.')

    def set_startup(self, enabled):
        if sys.platform != 'win32':
            raise ValueError('Windows Startup is only available on Windows.')
        root = os.environ.get('APPDATA')
        if not root:
            raise ValueError('Windows APPDATA is not available.')
        startup = Path(root) / 'Microsoft/Windows/Start Menu/Programs/Startup'
        shortcut = startup / 'ZenRbxManager.cmd'
        if enabled:
            startup.mkdir(parents=True, exist_ok=True)
            if getattr(sys, 'frozen', False):
                command = f'"{sys.executable}"'
            else:
                command = f'"{sys.executable}" "{Path(__file__).resolve().parent / "main.py"}"'
            shortcut.write_text('@echo off\nstart "" ' + command + '\n', encoding='utf-8')
        else:
            shortcut.unlink(missing_ok=True)
