<div align="center">
  <img src="site/og.svg" alt="ZenRbxManager — your Roblox accounts, in one place" width="100%">

  **A calmer account workspace for Windows.**  
  Organize accounts, launch into Roblox, and keep local notes without the clutter.

  [🌐 Website](https://sitezu.github.io/ZenRbxManager/) · [🛠 Run from source](#run-from-source) · [📦 Windows builds](#building-and-size-limit)
</div>

# ZenRbxManager

> **Release status:** A downloadable Windows release has not been published or verified yet. See the instructions below; the CI workflow will enforce the under-100-MB executable size limit.

Windows 10/11 Roblox account manager using the supplied ZenRbxManager HTML design and the account storage/Roblox launch/browser-login backend from [evanovar/RobloxAccountManager](https://github.com/evanovar/RobloxAccountManager). The upstream project is GPL-3.0; this derivative includes its original LICENSE and must remain GPL-compatible when redistributed. Not affiliated with Roblox.

## Features

- Add a real account through a Selenium-driven browser login or import a Roblox security cookie. The username is validated with Roblox; the username field on the mockup is informational, not trusted.
- Encrypted local account storage on first run; reads/migrates the upstream `AccountManagerData` format. Existing vaults that require a password are **not** silently replaced: use your original application to migrate them to hardware encryption first. **Back up `AccountManagerData` before switching apps.**
- Search, filter by live Roblox presence (when available), select, reorder, edit alias/notes, manually mark away, delete, and copy cookies after confirmation. Unknown status is shown as Unknown rather than claiming an account is offline. Away is a manual designation.
- Launch the selected account(s) into Roblox Home or a Place ID, optionally a Job ID. Bloxstrap option uses the upstream Bloxstrap launcher; it requires Bloxstrap to already be installed. Launch failures are shown per account.
- Change accent theme, login browser, launch delay, Windows Startup behavior; export/import non-sensitive preferences as JSON; clear old temporary login profiles without deleting saved account cookies.

## Prerequisites

- Windows 10/11; Microsoft Edge or Google Chrome installed (the app does not bundle a browser). Roblox installed for launching accounts.
- For website login: selected browser (Edge, Chrome, or Firefox) and a working Selenium WebDriver; Selenium Manager may download a matching driver on first use. Cookie import does not require WebDriver.
- Internet access to Roblox for cookie validation, live presence and launching. The UI assets work offline; no Tailwind/Font Awesome CDN.

## Run from source

```powershell
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -e '.[test]'
python src/main.py
python -m pytest -q
```

Run in a folder containing the old `AccountManagerData` to reuse the existing data. The saved data folder, installed Edge/Chrome, Roblox, and Selenium's optional downloaded driver are **not** included in the 100 MB portable-exe size target. If you need a fully self-contained installer including a browser and Roblox, that cannot fit under 100 MB.

## Building and size limit

A Windows GitHub Actions workflow runs the tests, builds a PyInstaller one-file executable, and fails if the executable is 100,000,000 bytes or larger. The binary is attached as a workflow artifact. Build locally with the same command from `.github/workflows/windows-build.yml`. A Windows binary cannot be built or end-to-end tested in a Linux environment; the Windows CI result is the authoritative size check.

## Security

The HTTP server binds only to `127.0.0.1` on a random port; it validates Host, Origin, a random session token and JSON Content-Type on all API requests. It is not a remotely hosted web app. Never paste or commit a GitHub token or Roblox session cookie into the repository. Export Config does not export account cookies. The built-in copy action reveals the cookie to the system clipboard only after confirmation; clear your clipboard afterward. As with upstream, hardware encryption is tied to machine identifiers; keep backups before changing computers.

## Differences from the mockup

The two demonstration accounts and alert-only actions have been removed. Roblox usernames are immutable in the edit dialog (changing text would not change the identity authenticated by the saved cookie). The mockup's Auto-Reconnect and Tray toggles were replaced with working browser and launch-delay preferences, since the lightweight browser shell cannot honestly implement reliable reconnect/tray behavior without a resident process supervisor. The cleanup control clears old temporary login profiles, not saved account credentials.

## Website and GitHub Pages

`site/index.html` is the product website, inspired by [sitezu/Zentask](https://github.com/sitezu/Zentask). It is a static, dependency-free page with no ZenTask app claims or assets. The desktop UI in `web/index.html` uses the same dark-grid/indigo-violet styling. See [ATTRIBUTION.md](ATTRIBUTION.md) for upstream credits.

When this project is pushed to `sitezu/ZenRbxManager`, enable **Settings → Pages → Build and deployment → Source: GitHub Actions**. The `.github/workflows/pages.yml` workflow then publishes only `site/` to `https://sitezu.github.io/ZenRbxManager/`. Before publication the GitHub and website links are placeholders for the intended repository, not live download links.

## Publish to your GitHub account

Do **not** use an exposed token. Revoke the previously posted token, then create an empty repository named `ZenRbxManager` under `sitezu` using GitHub's website or an authenticated `gh` CLI on your own computer. From this project directory:

```bash
git remote add origin https://github.com/sitezu/ZenRbxManager.git
git branch -M main
git push -u origin main
```

The workspace copy is initialized as a local Git repository. If you downloaded the ZIP instead, run `git init -b main`, `git add .`, and `git commit -m "Initial ZenRbxManager app and site"` before adding the remote. Creating a remote repository in your GitHub account requires a safe authenticated session. Never put credentials in the remote URL or commit history.
