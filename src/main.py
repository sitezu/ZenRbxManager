"""Windows desktop entry point. Uses installed Edge/Chrome instead of bundling Chromium."""
from __future__ import annotations

import json
import mimetypes
import os
import secrets
import shutil
import subprocess
import sys
import threading
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from utils.app_paths import get_resource_path, get_data_dir
from zen_backend import ZenBackend

WEB = Path(get_resource_path('web')).resolve()


def make_server(backend, port=0):
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        server_version = 'ZenRbxManager'

        def log_message(self, fmt, *args):
            # Do not log requests: account credentials may be contained in POST bodies.
            pass

        def _send(self, status, body, mime='application/json; charset=utf-8'):
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; font-src 'self' data:; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def _host_ok(self):
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

        def do_GET(self):
            if not self._host_ok():
                return self._send(403, b'Forbidden', 'text/plain')
            uri = urlsplit(self.path).path
            if uri == '/':
                html = (WEB / 'index.html').read_text(encoding='utf-8')
                html = html.replace('"__ZEN_TOKEN__"', json.dumps(token))
                return self._send(200, html.encode(), 'text/html; charset=utf-8')
            if not uri.startswith('/assets/'):
                return self._send(404, b'Not found', 'text/plain')
            item = (WEB / uri.lstrip('/')).resolve()
            if not item.is_relative_to(WEB / 'assets') or not item.is_file():
                return self._send(404, b'Not found', 'text/plain')
            return self._send(200, item.read_bytes(), mimetypes.guess_type(item.name)[0] or 'application/octet-stream')

        def do_POST(self):
            # Per-process secret + same-origin checks prevent other websites from
            # making blind requests to the privileged loopback backend.
            origin = self.headers.get('Origin')
            base = f'http://127.0.0.1:{self.server.server_port}'
            if (not self._host_ok() or origin != base or
                self.headers.get('X-Zen-Token') != token or
                self.headers.get('Content-Type', '').split(';')[0] != 'application/json'):
                return self._send(403, b'{"error":"Forbidden"}')
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if length < 1 or length > 32_768:
                    raise ValueError('Request is too large or empty.')
                payload = json.loads(self.rfile.read(length))
                path = urlsplit(self.path).path
                if not path.startswith('/api/'):
                    return self._send(404, b'{"error":"Not found"}')
                result = backend.action(path[5:], payload)
                self._send(200, json.dumps(result).encode())
            except (ValueError, TypeError, KeyError) as exc:
                self._send(400, json.dumps({'error': str(exc)}).encode())
            except Exception as exc:
                # Never return stack traces or credentials to the browser.
                self._send(500, json.dumps({'error': f'Operation failed: {type(exc).__name__}'}).encode())

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def run_self_test():
    """Exercise bundled UI + local API without Roblox, browser or saved accounts.

    Used by Windows CI after installing the setup package. This is not an
    end-to-end Roblox authentication or launch test.
    """
    import re
    import urllib.request

    class EmptyManager:
        accounts = {}

    with tempfile.TemporaryDirectory(prefix='zenrbx_test_') as data_dir:
        backend = ZenBackend(manager=EmptyManager(), data_dir=data_dir)
        backend.presence_updated = float('inf')  # never contact Roblox
        server = make_server(backend)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            with urllib.request.urlopen(base + '/', timeout=8) as response:
                html = response.read().decode('utf-8')
            match = re.search(r'const ZEN_TOKEN = ("[^"]+");', html)
            if not match or 'ZenRbxManager' not in html:
                raise RuntimeError('Bundled desktop HTML did not load.')
            session_token = json.loads(match.group(1))
            with urllib.request.urlopen(base + '/assets/app.js', timeout=8) as response:
                if b'updateState' not in response.read():
                    raise RuntimeError('Bundled UI JavaScript did not load.')
            request = urllib.request.Request(base + '/api/state', data=b'{}', method='POST', headers={
                'Content-Type': 'application/json', 'Origin': base, 'X-Zen-Token': session_token,
            })
            with urllib.request.urlopen(request, timeout=8) as response:
                data = json.load(response)
            if data.get('accounts') != [] or data.get('settings', {}).get('theme') != 'indigo':
                raise RuntimeError('Local account API returned unexpected data.')
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)
    print('ZenRbxManager package self-test passed (UI and local API; no Roblox account used).')
    return 0


def installed_browser():
    local = os.environ.get('LOCALAPPDATA', '')
    pf86 = os.environ.get('ProgramFiles(x86)', '')
    pf = os.environ.get('ProgramFiles', '')
    candidates = [
        Path(p) / r'Microsoft/Edge/Application/msedge.exe' for p in [pf86, pf, local] if p
    ] + [Path(p) / r'Google/Chrome/Application/chrome.exe' for p in [pf, pf86, local] if p]
    for path in candidates:
        if path.is_file():
            return str(path)
    return shutil.which('msedge') or shutil.which('chrome') or shutil.which('chromium')


def main():
    if '--self-test' in sys.argv:
        try:
            return run_self_test()
        except Exception as exc:
            print(f'Package self-test failed: {exc}', file=sys.stderr)
            return 1
    if sys.platform != 'win32':
        print('ZenRbxManager requires Windows 10/11 to launch Roblox. Tests can run on other systems.')
        return 1
    try:
        backend = ZenBackend()
    except Exception as exc:
        # Do not create a fresh vault if an existing encrypted vault cannot open.
        print(f'Could not open account data: {exc}', file=sys.stderr)
        return 1
    server = make_server(backend)
    url = f'http://127.0.0.1:{server.server_port}/'
    browser = installed_browser()
    if not browser:
        server.server_close()
        print('Install Microsoft Edge or Google Chrome to run the Zen UI.', file=sys.stderr)
        return 1
    try:
        # Temporary isolated shell profile: do not grow the portable data directory.
        with tempfile.TemporaryDirectory(prefix='zenrbx_shell_', ignore_cleanup_errors=True) as profile:
            window = subprocess.Popen([browser, f'--app={url}', '--window-size=1000,630',
                                        f'--user-data-dir={profile}', '--no-first-run'])
            print('ZenRbxManager window started.')
            threading.Thread(target=lambda: (window.wait(), server.shutdown()), daemon=True).start()
            server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
