"""Windows desktop entry point. The original HTML runs inside a native WebView2 window."""
from __future__ import annotations

import json
import mimetypes
import secrets
import sys
import threading
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from utils.app_paths import get_resource_path
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
            if ('<!-- BEGIN EMBEDDED APP SCRIPT -->' not in html or
                    'function updateState(state)' not in html or
                    '<script src=' in html):
                raise RuntimeError('Self-contained desktop UI JavaScript did not load.')
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


def run_ui_smoke_test():
    """Windows CI: render original HTML in a real WebView2 window with no account.

    This checks the desktop host and local UI/API integration, not Roblox login.
    """
    import webview

    class EmptyManager:
        accounts = {}

    with tempfile.TemporaryDirectory(prefix='zenrbx_webview_test_') as data_dir:
        backend = ZenBackend(manager=EmptyManager(), data_dir=data_dir)
        backend.presence_updated = float('inf')
        server = make_server(backend)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        window = webview.create_window('ZenRbxManager UI check',
                                       url=f'http://127.0.0.1:{server.server_port}/',
                                       width=1000, height=650, background_color='#090a0f',
                                       easy_drag=False)
        checks = []

        def inspect():
            try:
                if not window.events.loaded.wait(25):
                    raise RuntimeError('WebView2 did not load the desktop UI.')
                import time
                for _ in range(50):
                    state = window.evaluate_js("""(() => ({
                      title: document.querySelector('h1')?.textContent,
                      empty: !!document.getElementById('emptyStateNotice'),
                      root: !!document.getElementById('widget'),
                      fakeControls: !!document.querySelector('.window-controls')
                    }))()""")
                    if state and state.get('empty'):
                        assert state['title'] == 'ZENRBXMANAGER' and state['root']
                        assert not state['fakeControls']
                        checks.append(True)
                        return
                    time.sleep(.25)
                raise RuntimeError('Original account UI did not initialize.')
            except Exception as exc:
                checks.append(exc)
            finally:
                window.destroy()

        try:
            # No fallback to MSHTML or an external browser.
            webview.start(inspect, gui='edgechromium', private_mode=True)
            if checks != [True]:
                raise RuntimeError(f'WebView2 GUI smoke test failed: {checks!r}')
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)
    print('WebView2 desktop UI smoke test passed (no Roblox account used).')
    return 0


def main():
    if '--self-test' in sys.argv or '--ui-smoke-test' in sys.argv:
        try:
            import webview
            if not callable(webview.create_window):
                raise RuntimeError('Embedded desktop renderer is unavailable.')
            if '--ui-smoke-test' in sys.argv:
                return run_ui_smoke_test()
            return run_self_test()
        except Exception as exc:
            print(f'Package self-test failed: {exc}', file=sys.stderr)
            return 1
    if sys.platform != 'win32':
        print('ZenRbxManager requires Windows 10/11 to launch Roblox. Tests can run elsewhere.')
        return 1
    try:
        import webview
        backend = ZenBackend()
        server = make_server(backend)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            url = f'http://127.0.0.1:{server.server_port}/'
            webview.create_window('ZenRbxManager', url=url, width=1180, height=760,
                                  min_size=(900, 600), maximized=True, easy_drag=False,
                                  background_color='#090a0f')
            # No external browser shell. Fail rather than fall back to MSHTML/IE.
            webview.start(gui='edgechromium', private_mode=True)
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)
    except Exception as exc:
        print(f'Could not start WebView2. Install Microsoft WebView2 Runtime: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
