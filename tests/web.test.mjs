import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { JSDOM } from 'jsdom';

const html = readFileSync(new URL('../web/index.html', import.meta.url), 'utf8');
const script = readFileSync(new URL('../web/assets/app.js', import.meta.url), 'utf8');
const originalAccounts = [
  { username: 'Alpha', alias: 'Main', note: 'My account', status: 'online' },
  { username: 'Beta', alias: 'Alt', note: '', status: 'offline' },
];

function createApp() {
  const calls = [];
  const state = {
    accounts: structuredClone(originalAccounts),
    settings: { theme: 'rose', bloxstrap: false, browser: 'edge', startup: false, delay: 0.5, order: [] },
  };
  const injected = html.replace('const ZEN_TOKEN = "__ZEN_TOKEN__";', 'const ZEN_TOKEN = "test-token";');
  const dom = new JSDOM(injected, {
    url: 'http://127.0.0.1:8800/', runScripts: 'dangerously', pretendToBeVisual: true,
    beforeParse(window) {
      window.alert = () => {};
      window.confirm = () => true;
      window.fetch = async (url, options) => {
        const action = url.replace('/api/', '');
        const payload = JSON.parse(options.body);
        calls.push({ action, payload });
        if (options.headers['X-Zen-Token'] !== 'test-token') throw Error('Missing session token');
        if (action === 'settings') state.settings[payload.key] = payload.value;
        if (action === 'note') {
          const account = state.accounts.find(x => x.username === payload.username);
          if (account) account.note = payload.note;
        }
        return { ok: true, json: async () => action === 'state' ? structuredClone(state) : { message: 'Saved', state: structuredClone(state) } };
      };
    },
  });
  return { dom, window: dom.window, state, calls };
}

const settle = () => new Promise(resolve => setTimeout(resolve, 30));

test('initial load shows real accounts and persisted preferences', async () => {
  const { dom, window, calls } = createApp();
  try {
    await settle();
    assert.equal(window.document.querySelectorAll('.account-row').length, 2);
    assert.equal(window.document.querySelector('.account-name').textContent, 'Alpha');
    assert.equal(window.document.getElementById('emptyStateNotice'), null);
    assert.equal(window.document.getElementById('prefBloxstrap').checked, false);
    assert.equal(window.document.getElementById('prefBrowser').value, 'edge');
    assert.equal(window.document.documentElement.style.getPropertyValue('--th-500'), '244 63 94');
    assert.equal(calls[0].action, 'state');
  } finally { dom.window.close(); }
});

test('account search, selection, settings and notes use actual UI state', async () => {
  const { dom, window, calls } = createApp();
  try {
    await settle();
    window.document.getElementById('accountSearchInput').value = 'beTa';
    window.filterAccounts();
    const rows = [...window.document.querySelectorAll('.account-row')];
    assert.equal(rows[0].style.display, 'none');
    assert.equal(rows[1].style.display, 'grid');
    window.selectAccount('Alpha');
    assert.equal(window.document.getElementById('descInput').value, 'My account');
    window.document.getElementById('descInput').value = 'Updated note';
    window.queueNoteSave();
    await new Promise(resolve => setTimeout(resolve, 750));
    assert.ok(calls.some(c => c.action === 'note' && c.payload.username === 'Alpha' && c.payload.note === 'Updated note'));
    window.openSettingsModal();
    assert.ok(!window.document.getElementById('settingsModal').classList.contains('hidden'));
    window.setTheme('indigo');
    await settle();
    assert.ok(calls.some(c => c.action === 'settings' && c.payload.value === 'indigo'));
  } finally { dom.window.close(); }
});

test('account names from state render as text rather than HTML', async () => {
  const { dom, window, state } = createApp();
  try {
    await settle();
    state.accounts = [{ username: '<img src=x onerror=alert(1)>', alias: '', note: '', status: 'unknown' }];
    window.updateState(state);
    assert.equal(window.document.querySelectorAll('#accountList img').length, 0);
    assert.equal(window.document.querySelector('.account-name').textContent, '<img src=x onerror=alert(1)>');
  } finally { dom.window.close(); }
});


test('workspace occupies the window without fake chrome or a grid desktop', async () => {
  const { dom, window } = createApp();
  try {
    await settle();
    const doc = window.document;
    assert.equal(doc.querySelector('h1').textContent, 'ZENRBXMANAGER');
    assert.ok(doc.querySelector('main.workspace > section.account-panel'));
    assert.ok(doc.querySelector('main.workspace > aside.execution-panel'));
    assert.equal(doc.querySelector('.window-controls'), null);
    assert.equal(doc.querySelector('[onclick^="windowAction"]'), null);
    assert.equal(doc.querySelector('#widget').classList.contains('rounded-2xl'), false);
    assert.ok(html.includes('#widget {width:100%;height:100%;'), 'the app fills the viewport');
    assert.match(html, /background-image:none !important/);
  } finally { dom.window.close(); }
});


test('single-file HTML embeds the canonical app logic and font without remote assets', () => {
  const embedded = html.match(/<!-- BEGIN EMBEDDED APP SCRIPT -->\s*<script>\s*([\s\S]*?)\s*<\/script>\s*<!-- END EMBEDDED APP SCRIPT -->/);
  assert.ok(embedded, 'embedded application logic exists');
  assert.equal(embedded[1].trim(), script.trim(), 'embedded JS is in sync with source');
  assert.ok(html.includes('data:font/woff2;base64,'), 'icon font is inline');
  assert.ok(!/<script\s+src=|<link\s+[^>]*href=/.test(html), 'no external script or stylesheet');
});


test('all account and destination dialogs still open with inlined handlers', async () => {
  const { dom, window } = createApp();
  try {
    await settle();
    const visible = id => !window.document.getElementById(id).classList.contains('hidden');
    window.openAddAccountModal(); assert.ok(visible('addAccountModal'));
    window.switchAddTab('cookie');
    assert.ok(!window.document.getElementById('addCookieSection').classList.contains('hidden'));
    window.closeAddAccountModal(); assert.ok(!visible('addAccountModal'));
    window.openPlaceModal(); assert.ok(visible('placeModal'));
    window.closePlaceModal(); assert.ok(!visible('placeModal'));
    window.openEditModal('Alpha'); assert.ok(visible('editModal'));
    assert.equal(window.document.getElementById('editAlias').value, 'Main');
    window.closeEditModal(); assert.ok(!visible('editModal'));
    window.openSettingsModal(); assert.ok(visible('settingsModal'));
    window.closeSettingsModal(); assert.ok(!visible('settingsModal'));
    window.setStatusFilter('online');
    assert.equal(window.document.querySelectorAll('.account-row[style*="display: none"]').length, 1);
  } finally { dom.window.close(); }
});
