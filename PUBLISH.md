# Website and preview releases

The site is published at **https://sitezu.github.io/ZenRbxManager/** from the `site/` directory by [the Pages workflow](.github/workflows/pages.yml). Changes to `site/` on `main` deploy automatically. The current downloadable app is a **portable Windows preview**. The published portable preview still uses the older browser shell; an original-UI WebView2 setup installer candidate is built in CI, but must not be tagged for release until someone tests real Roblox login and launch on Windows.

## How to publish another preview

**Do not create a new tag while real Roblox login and game-launch testing is still pending. The steps below apply only after the owner confirms the live Windows checks.**

1. Make and test changes on `main`. Run `python -m pytest -q` and `npm ci && npm test`, plus `python src/main.py --self-test` to exercise the bundled HTML/local API without a Roblox account. The Windows desktop WebView2 window itself still needs a live PC test. The [Windows build workflow](.github/workflows/windows-build.yml) must pass too.
2. Update `RELEASE_NOTES.md`, the versioned download link in `site/index.html`, and the release link in `README.md` to the tag you are about to create. Keep the preview warning if live account flows remain unverified.
3. Commit and push. Tag that exact tested commit, e.g. `git tag v0.1.1-preview && git push origin v0.1.1-preview`.
4. [The release workflow](.github/workflows/release.yml) builds a Windows EXE, runs Python and frontend tests, fails if the EXE is **100,000,000 bytes or larger**, writes a SHA-256 checksum, and uploads the EXE, checksum, and GPL license to a prerelease.
5. Check the [release page](https://github.com/sitezu/ZenRbxManager/releases), download the asset, verify its checksum, and test it on Windows with accounts you own before calling it stable.

## How the website is published

The Pages workflow uploads **only `site/`**, not your desktop app data or source dependencies. To redeploy, push a site change to `main` or run the workflow manually under GitHub Actions. GitHub Pages must be configured in the repository's **Settings → Pages → Build and deployment → GitHub Actions**.

## Security

Do not include authentication cookies, account exports, GitHub tokens, or temporary account data in a commit or issue. Previously posted GitHub tokens were exposed in chat and should be revoked. To authorize GitHub changes, use GitHub's device flow or your own machine's credential manager; don't paste tokens into chats or remote URLs.
