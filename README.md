<div align="center">

<img src="site/og.png" alt="ZenRbxManager — Your accounts. One place. Full-viewport application preview" width="100%">

# ZENRBXMANAGER

### Your accounts. One place. Back to the game.

An independent Windows account workspace for the Roblox accounts **you own**. Keep the details straight, choose where you're going, and launch with confidence.

[![Windows build](https://github.com/sitezu/ZenRbxManager/actions/workflows/windows-build.yml/badge.svg)](https://github.com/sitezu/ZenRbxManager/actions/workflows/windows-build.yml)
[![Website](https://img.shields.io/badge/website-explore-6366f1)](https://sitezu.github.io/ZenRbxManager/)
[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-a855f7)](LICENSE)

**[Download portable preview](https://github.com/sitezu/ZenRbxManager/releases/tag/v0.1.0-preview)** &nbsp;·&nbsp; **[Explore the website](https://sitezu.github.io/ZenRbxManager/)** &nbsp;·&nbsp; **[Try the setup candidate](#prefer-a-setup-wizard)**

<sub>WINDOWS 10 / 11 &nbsp; • &nbsp; OPEN SOURCE &nbsp; • &nbsp; LOCAL ACCOUNT STORAGE &nbsp; • &nbsp; UNDER 100 MB PER EXECUTABLE</sub>

</div>

> [!IMPORTANT]
> **Preview, not a verified Roblox release.** The portable EXE is published and its download checksum was verified. The newer setup installer is an **Actions test artifact, not a release**. Automated tests cover the interface, backend, packaged startup, size limit, installation and uninstall; **live Roblox sign-in and game launch still need testing on Windows**. The screenshots below show the supplied HTML UI inside a new **embedded WebView2 desktop window** on `main`. The published v0.1.0-preview is an **older external-browser-shell build**.

---

## A better place for the accounts you actually use

One account for one game, another for a different group, and a third you haven't touched in months. ZenRbxManager gives those accounts a home: a clean list, useful context, and launch controls in a **real frameless Windows desktop window with the original HTML/CSS UI filling it edge to edge**. The supplied header and rounded border are part of that window, not a floating web card. No separate Edge/Chrome app-mode window.

<img src="site/readme-features.png" alt="Six ZenRbxManager features: account list, launching, notes, settings, local storage and honest presence" width="100%">

### See the workspace

These are **real captures of the original HTML UI**, which the Windows desktop window renders through WebView2. They are not a populated demo account. The original header replaces the OS title bar, with working minimize/close buttons in the desktop app. No credentials or account cookies appear in them.

<img src="site/app-preview.webp" alt="The full-viewport ZenRbxManager workspace with account list, filters and launch controls" width="100%">

<details>
<summary><b>See settings and themes ↗</b></summary>
<br>
<img src="site/settings-preview.webp" alt="ZenRbxManager settings dialog over the full-viewport workspace" width="100%">
</details>

## From first launch to the right game

| | What to do | What happens |
|:--:|:--|:--|
| **01** | **Add an account you own** | Sign in in a supported browser, or import your own `.ROBLOSECURITY` cookie. Roblox validates the account; don't give your cookie to anyone else. |
| **02** | **Make it recognizable** | Give it an alias and note. Search, filter, reorder, select, or hide displayed usernames when you need some privacy. |
| **03** | **Choose your destination** | Launch Roblox Home or enter a Place ID. An optional Job ID can target a specific server. Multiple selected accounts can be launched with a configurable delay. |

Presence can show Online or In-Game when Roblox supplies it. If a reliable result isn't available, the app shows **Unknown** instead of guessing.

## Get it for Windows

### Portable preview · published

1. Download **[`ZenRbxManager-v0.1.0-preview.exe`](https://github.com/sitezu/ZenRbxManager/releases/download/v0.1.0-preview/ZenRbxManager-v0.1.0-preview.exe)** from the [v0.1.0-preview release](https://github.com/sitezu/ZenRbxManager/releases/tag/v0.1.0-preview). Compare its SHA-256 hash with the release's `SHA256SUMS.txt`.
2. Keep the EXE in a folder where it can create `AccountManagerData`. This **older portable preview** uses Edge or Chrome for its app window; install Roblox before trying to launch a game. To test the embedded original UI, use the newer setup candidate below.
3. Choose **Add New Account**. Browser sign-in can download a matching WebDriver on first use. Only use accounts you own.

**Important:** This published portable preview predates the embedded WebView2 rewrite; it **still opens an external browser app window**. Do not download it to evaluate the new desktop window. It is unsigned, so Windows SmartScreen may display a warning. Inspect the source before trusting an account-management app.

### Prefer a setup wizard?

The [latest successful Windows build](https://github.com/sitezu/ZenRbxManager/actions/workflows/windows-build.yml) **for the WebView2 desktop commit** provides a **`ZenRbxManager-Setup-Candidate`** artifact. Older Actions artifacts may use the external browser shell or Tk prototype; check the run’s commit. Sign in to GitHub, open the successful run, download the artifact ZIP, extract `ZenRbxManager-Setup-candidate.exe`, and verify it using the included `SETUP-SHA256SUMS.txt`.

This **per-user Inno Setup candidate** adds a Start Menu shortcut, offers an optional desktop shortcut, and includes an uninstaller that leaves saved accounts alone. CI checks the under-100 MB limit, starts the packaged backend and UI bundle without a Roblox account, silently installs the app, self-tests the installed bundle, and uninstalls it. You must confirm that WebView2 actually renders the window on your PC. **None of that verifies a real Roblox login or game launch.** Please use the [real-Windows test checklist](TEST_ON_WINDOWS.md), report non-sensitive failures, and **do not expect a setup release until the live tests pass**.

> [!CAUTION]
> Back up `AccountManagerData` before upgrades, reinstalls or migrations. Hardware-encrypted vaults can be tied to the original computer; an upstream password-encrypted vault may need migration in the original app. **Never paste a password, `.ROBLOSECURITY` cookie, auth ticket or account data file into an issue.**

## The original UI, inside a desktop window

The current candidate uses your **original HTML/CSS interface** in an embedded **Microsoft Edge WebView2** control hosted by a Windows desktop window. It is a web renderer **inside** the app, not a separate browser tab or an `--app` Edge/Chrome window. The interface fills a frameless window; its original header, working minimize/close buttons and rounded border replace the OS title bar. A subtle corner grip allows resizing. A token-protected loopback API connects it to the existing Python backend. **WebView2 Runtime must be installed** (separate from the Edge browser); if missing, install Microsoft's Evergreen WebView2 Runtime. Roblox's optional website sign-in may open a separate browser. The runtime, Roblox, optional WebDriver and saved data are outside the executable size limit. The published `v0.1.0-preview` still uses the older external-browser-shell launcher.

| What matters | How it works |
|:--|:--|
| **Local account vault** | Saved account data stays in `AccountManagerData` on your PC; a new vault uses hardware-based encryption. |
| **Settings export** | Exports preferences without login cookies. |
| **Your controls** | Accent theme, sign-in browser, launch delay, optional Bloxstrap integration and Windows Startup. |
| **Transparent limitations** | No Auto-Rejoin and no minimize-to-tray. This preview has not completed live Roblox verification. |

## Run from source

On Windows, with Python 3.13 and Git:

```powershell
git clone https://github.com/sitezu/ZenRbxManager.git
cd ZenRbxManager
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -e '.[test]'
python src/main.py
python -m pytest -q
```

The launcher is [`src/main.py`](src/main.py); it hosts the original [`web/index.html`](web/index.html) in WebView2. The HTML's styles, icon font and working JavaScript are bundled locally. If you change [`web/assets/app.js`](web/assets/app.js), run `python scripts/embed_app_js.py` to refresh the embedded copy; UI tests check they match. To regenerate empty-state images with Playwright Chromium and Pillow: `python scripts/capture_ui.py`, `python scripts/make_banner.py`, `python scripts/make_readme_visuals.py`. Screenshot generation mocks an **empty local state**; it never uses a real account.

<details>
<summary><b>How are releases tested?</b></summary>
<br>
The <a href=".github/workflows/windows-build.yml">Windows workflow</a> tests Python and JavaScript, builds a portable EXE and a setup candidate, enforces <code>&lt; 100,000,000 bytes</code> for each, and self-tests the packaged and installed app plus the install/uninstall flow. The <a href=".github/workflows/release.yml">release workflow</a> is ready for a <em>future</em> tag. Automated checks cannot replace an owner's Roblox sign-in and launch test on Windows. No new setup tag will be created before that test passes.
</details>

<details>
<summary><b>Can I copy a cookie or report an issue?</b></summary>
<br>
Copying a saved account cookie requires confirmation. A cookie grants account access: clear your clipboard afterward, and never share the cookie, password, token or account data with anyone. For bugs, share only Windows version, steps and non-sensitive error text via <a href="https://github.com/sitezu/ZenRbxManager/issues">GitHub Issues</a>.
</details>

<details>
<summary><b>Does it work on macOS or Linux?</b></summary>
<br>
No. Roblox client launching is Windows-specific. Some tests run on Linux, but the desktop app is intended for Windows 10/11.
</details>

---

### Made in the open

The account backend adapts [evanovar/RobloxAccountManager](https://github.com/evanovar/RobloxAccountManager) under **GPL-3.0**. The project site's visual foundation draws from [sitezu/Zentask](https://github.com/sitezu/Zentask) under **MIT**. Read [ATTRIBUTION.md](ATTRIBUTION.md) and the included licenses. ZenRbxManager is an independent community project, **not affiliated with or endorsed by Roblox**.

<div align="center"><sub>Made with care by <a href="https://github.com/sitezu">sitezu</a> · <a href="https://sitezu.github.io/ZenRbxManager/">Website</a> · <a href="https://github.com/sitezu/ZenRbxManager/issues">Issues</a> · <a href="TEST_ON_WINDOWS.md">Test checklist</a></sub></div>
