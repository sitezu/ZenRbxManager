## ZenRbxManager — original-UI desktop candidate (not released)

The current `main` branch replaces the earlier Edge/Chrome app-mode shell with a **desktop window with the original HTML/CSS UI embedded in Microsoft WebView2**. It preserves the dark two-column account layout, filters, notes, launches, themes, and settings, with the Python backend behind a token-protected local API. The app no longer opens a separate Edge/Chrome `--app` window. Roblox browser sign-in is a separate, optional flow. The original custom header now replaces the OS title bar: its minimize/close controls operate the native window, and the original thin rounded border surrounds the edge-to-edge workspace. A corner grip allows resizing.

### Before any new release

- **Do not publish a new setup release until an owner has signed in to Roblox and launched a game on Windows.** Automated tests can check the packaged UI/backend, packaging, size, installation, and uninstall, but they cannot verify live Roblox workflows.
- The already published `v0.1.0-preview` portable EXE is an **older browser-shell build**. Do not download it to evaluate the new WebView2 desktop window. The newest successful Windows Actions run for the WebView2 desktop commit provides a setup candidate for testing.
- The Windows candidate is unsigned. Review the code, verify its `SETUP-SHA256SUMS.txt`, and back up `AccountManagerData` first. Never share your `.ROBLOSECURITY` cookie, password, or auth ticket.
- Windows 10/11 and Roblox are needed for real launching. Microsoft WebView2 Runtime is required for the manager window; a separate browser and matching WebDriver may be required for optional Roblox website sign-in.

See the [README](README.md) for source setup, [Windows test checklist](TEST_ON_WINDOWS.md) for live testing, and [PUBLISH.md](PUBLISH.md) for release gates. ZenRbxManager is independent and not affiliated with Roblox.
