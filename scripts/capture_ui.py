"""Capture the original HTML interface used inside the desktop WebView2 host.

Requires Playwright Chromium. Mocks only the account API: no user data, cookies,
Roblox traffic or external resources are used.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT / 'web')))
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1200, 'height': 760}, device_scale_factor=1)
        page.route('**/api/**', lambda route: route.fulfill(json={
            'accounts': [], 'settings': {'theme': 'indigo', 'browser': 'edge',
            'bloxstrap': False, 'startup': False, 'delay': 0.5, 'order': []}}))
        page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='networkidle')
        box = page.locator('#widget').bounding_box()
        assert box == {'x': 0, 'y': 0, 'width': 1200, 'height': 760}, box
        assert page.locator('h1').inner_text() == 'ZENRBXMANAGER'
        assert page.locator('.window-controls button').count() == 2
        assert page.evaluate("getComputedStyle(document.body).backgroundColor") == 'rgb(9, 10, 15)'
        assert page.locator('#widget').evaluate('(el) => getComputedStyle(el).borderTopLeftRadius') == '16px'
        assert page.locator('#widget').evaluate('(el) => getComputedStyle(el).borderTopColor') == 'rgb(29, 35, 49)'
        header = page.locator('#widget > header').bounding_box()
        workspace = page.locator('#widget > main').bounding_box()
        assert header['x'] == 1 and header['y'] == 1 and header['width'] == 1198
        assert workspace['y'] == header['y'] + header['height']
        assert workspace['height'] + header['height'] + 2 == 760
        assert page.locator('.account-panel').is_visible() and page.locator('.execution-panel').is_visible()
        page.screenshot(path=str(ROOT / 'site/app-preview.webp'), type='webp', quality=88)
        page.locator('button[onclick="openSettingsModal()"]:visible').click()
        page.locator('#settingsModal').wait_for(state='visible')
        page.wait_for_timeout(350)  # allow opening transition to finish
        page.screenshot(path=str(ROOT / 'site/settings-preview.webp'), type='webp', quality=86)
        for width, height in [(900, 640), (600, 800), (380, 720)]:
            page.set_viewport_size({'width': width, 'height': height})
            box = page.locator('#widget').bounding_box()
            assert box == {'x': 0, 'y': 0, 'width': width, 'height': height}, box
        print('Full-viewport layout verified at 1200x760, 900x640, 600x800, 380x720.')
        browser.close()
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)
