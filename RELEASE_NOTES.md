## ZenRbxManager — native desktop candidate (not released)

The current `main` branch replaces the earlier Edge/Chrome app-mode shell with a **native Tk desktop window**. It preserves the account manager's dark two-column layout, search and filters, notes, launch controls, themes, and settings, while calling the Python backend directly. It does not start a local HTTP server, use a WebView, or open a browser for the manager window. Only Roblox's optional browser sign-in may open a browser.

### Before any new release

- **Do not publish a native setup release until an owner has signed in to Roblox and launched a game on Windows.** Automated tests can check the native widget layout, packaging, size, installation, and uninstall, but they cannot verify live Roblox workflows.
- The already published `v0.1.0-preview` portable EXE is an **older browser-shell build**. Do not download it to evaluate the native UI. The newest successful Windows Actions run for a native-UI commit provides a setup candidate for testing.
- The Windows candidate is unsigned. Review the code, verify its `SETUP-SHA256SUMS.txt`, and back up `AccountManagerData` first. Never share your `.ROBLOSECURITY` cookie, password, or auth ticket.
- Windows 10/11 and Roblox are needed for real launching. A browser and a matching WebDriver may be required **only for the optional Roblox website sign-in flow**.

See the [README](README.md) for source setup, [Windows test checklist](TEST_ON_WINDOWS.md) for live testing, and [PUBLISH.md](PUBLISH.md) for release gates. ZenRbxManager is independent and not affiliated with Roblox.
