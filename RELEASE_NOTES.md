## ZenRbxManager for Windows — preview build

A small first release for people who switch between Roblox accounts and want one place to keep them organized. You can label accounts, leave notes, and launch a selected account into Roblox Home or a specific Place ID. The interface borrows its dark-grid, indigo-and-violet style from ZenTask.

### Before you download

- **Preview, not a fully verified release.** Automated Python and browser-UI tests pass, and the Windows build is checked to be under 100 MB. A real Roblox sign-in and game launch have **not** been tested on a Windows PC by the project maintainers yet.
- You need Windows 10 or 11, Edge or Chrome for the app window, and Roblox installed for launching. Browser-based sign-in may download a matching WebDriver. These programs are **not** inside the executable.
- The executable is unsigned. Windows may show a SmartScreen warning; review the source code and confirm the file's SHA-256 using `SHA256SUMS.txt` before deciding whether to run it.
- Keep a backup of `AccountManagerData` before switching from another account manager or moving computers. Never share a `.ROBLOSECURITY` cookie.

### Files

- `ZenRbxManager-<version>.exe` — portable Windows build (put it in a folder where it can save data).
- `SHA256SUMS.txt` — checksum for verifying the download.
- `LICENSE` — GPL-3.0 terms inherited from the upstream backend.

See the [README](https://github.com/sitezu/ZenRbxManager#readme) for setup, limitations, and source instructions. If something fails, please [open an issue](https://github.com/sitezu/ZenRbxManager/issues) with the steps to reproduce. **Do not include account cookies, passwords, or auth tickets in an issue.**
