import json
import threading
from http.client import HTTPConnection

import pytest

from zen_backend import ZenBackend
from main import make_server


class FakeManager:
    def __init__(self):
        self.accounts = {'Alpha': {'cookie': 'secret-one', 'user_id': 0, 'note': 'First'},
                         'Beta': {'cookie': 'secret-two', 'user_id': 0, 'note': 'Second'}}
        self.saved = 0
        self.launched = []

    def save_accounts(self):
        self.saved += 1

    def set_account_note(self, name, note):
        self.accounts[name]['note'] = note
        self.save_accounts()
        return True

    def delete_account(self, name):
        del self.accounts[name]
        self.save_accounts()
        return True

    def launch_roblox(self, name, game_id='', job_id='', launcher_preference='default'):
        self.launched.append((name, game_id, job_id, launcher_preference))
        return True

    def import_cookie_account_result(self, cookie):
        if cookie != 'valid-test-cookie':
            raise ValueError('Cookie rejected.')
        self.accounts['Imported'] = {'cookie': cookie, 'user_id': 0, 'note': ''}
        self.save_accounts()
        return True

    def add_account(self, amount=1, browser=None):
        assert amount == 1 and browser['key'] == 'edge'
        self.accounts['WebLogin'] = {'cookie': 'private-web-cookie', 'user_id': 0, 'note': ''}
        self.save_accounts()
        return True


@pytest.fixture
def backend(tmp_path):
    service = ZenBackend(FakeManager(), tmp_path)
    service.presence_updated = float('inf')  # no live Roblox network in tests
    return service


def test_state_no_credentials_and_crud(backend):
    state = backend.action('state', {})
    assert state['accounts'][0]['username'] == 'Alpha'
    assert 'secret-one' not in json.dumps(state)
    backend.action('edit', {'username': 'Alpha', 'new_username': 'Alpha', 'alias': 'Main', 'note': 'Hi', 'away': True})
    assert backend.action('state', {})['accounts'][0]['status'] == 'away'
    assert backend.manager.saved == 1
    with pytest.raises(ValueError, match='cannot be changed'):
        backend.action('edit', {'username': 'Alpha', 'new_username': 'Stolen'})
    backend.action('note', {'username': 'Alpha', 'note': 'A' * 300})
    assert len(backend.manager.accounts['Alpha']['note']) == 250
    backend.action('order', {'names': ['Beta', 'Alpha']})
    assert backend.action('state', {})['accounts'][0]['username'] == 'Beta'
    with pytest.raises(ValueError):
        backend.action('order', {'names': ['Beta', 'Beta']})
    backend.action('delete', {'username': 'Beta'})
    assert [a['username'] for a in backend.action('state', {})['accounts']] == ['Alpha']


def test_launch_and_preferences(backend):
    backend.action('settings', {'key': 'bloxstrap', 'value': True})
    backend.action('settings', {'key': 'delay', 'value': 0})
    result = backend.action('launch', {'names': ['Alpha', 'Beta'], 'place': '12345', 'job': ''})
    assert len(result['results']) == 2
    assert backend.manager.launched == [('Alpha', '12345', '', 'bloxstrap'), ('Beta', '12345', '', 'bloxstrap')]
    for invalid in [{'names': ['NoSuch']}, {'names': ['Alpha'], 'place': 'abc'},
                    {'names': ['Alpha'], 'job': 'not-a-uuid'}, {'names': ['Alpha', 'Alpha']}]:
        with pytest.raises(ValueError):
            backend.action('launch', invalid)


def test_import_and_browser_login_are_real_backend_calls(backend):
    with pytest.raises(ValueError, match='rejected'):
        backend.action('cookie_import', {'cookie': 'invalid'})
    response = backend.action('cookie_import', {'cookie': 'valid-test-cookie'})
    assert any(a['username'] == 'Imported' for a in response['state']['accounts'])
    assert 'valid-test-cookie' not in json.dumps(response)
    response = backend.action('browser_login', {})
    assert any(a['username'] == 'WebLogin' for a in response['state']['accounts'])
    assert 'private-web-cookie' not in json.dumps(response)


def test_config_export_import_and_copy(backend):
    assert backend.action('cookie_copy', {'username': 'Alpha'})['cookie'] == 'secret-one'
    exported = backend.action('export', {})
    assert 'secret-one' not in json.dumps(exported)
    backend.action('import', {'config': {'theme': 'rose', 'browser': 'chrome'}})
    assert backend.action('state', {})['settings']['theme'] == 'rose'
    with pytest.raises(ValueError):
        backend.action('import', {'config': {'theme': 'hacked'}})
    with pytest.raises(ValueError):
        backend.action('settings', {'key': 'startup', 'value': 'yes'})


def test_package_self_test_loads_ui_and_loopback_api():
    from main import run_self_test
    assert run_self_test() == 0


def test_server_security_and_static(backend):
    server = make_server(backend)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    conn = HTTPConnection('127.0.0.1', server.server_port)
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        conn.request('GET', '/', headers={'Host': f'127.0.0.1:{server.server_port}'})
        response = conn.getresponse(); html = response.read().decode()
        assert response.status == 200 and 'ZenRbxManager' in html
        import re
        token = json.loads(re.search(r'const ZEN_TOKEN = (.*?);', html).group(1))
        headers = {'Host': f'127.0.0.1:{server.server_port}', 'Origin': base,
                   'Content-Type': 'application/json', 'X-Zen-Token': token}
        conn.request('POST', '/api/state', '{}', {**headers, 'Origin': 'https://evil.example'})
        assert conn.getresponse().status == 403
        conn.close(); conn = HTTPConnection('127.0.0.1', server.server_port)
        conn.request('POST', '/api/state', '{}', headers)
        response=conn.getresponse(); data=json.loads(response.read())
        assert response.status == 200 and len(data['accounts']) == 2
        conn.request('GET', '/assets/style.css', headers={'Host': f'127.0.0.1:{server.server_port}'})
        response=conn.getresponse(); assert response.status == 200 and b'account-grid' not in response.read()  # custom layout is in HTML
        conn.request('GET', '/assets/../src/main.py', headers={'Host': f'127.0.0.1:{server.server_port}'})
        assert conn.getresponse().status == 404
    finally:
        conn.close(); server.shutdown(); server.server_close(); worker.join(timeout=3)


def test_desktop_host_forces_embedded_webview2():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / 'src/main.py').read_text()
    assert "webview.start(gui='edgechromium'" in source
    assert "webview.start(inspect, gui='edgechromium'" in source
    assert 'subprocess.Popen' not in source
    assert '--app=' not in source
    assert 'frameless=True, transparent=True' in source
    assert "DRAG_REGION_DIRECT_TARGET_ONLY'] = True" in source
    assert 'class DesktopWindowControls:' in source
    assert "server = make_server(backend)" in source


def test_native_window_controls_call_actual_host_methods():
    from main import DesktopWindowControls

    class FakeWindow:
        def __init__(self):
            self.calls = []

        def minimize(self): self.calls.append('minimize')
        def destroy(self): self.calls.append('close')
        def resize(self, width, height): self.calls.append(('resize', width, height))

    bridge = DesktopWindowControls()
    bridge.window = FakeWindow()
    bridge.minimize()
    bridge.resize(100, 5000)
    bridge.close()
    assert bridge.window.calls == ['minimize', ('resize', 900, 2160), 'close']
