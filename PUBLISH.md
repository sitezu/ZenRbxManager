# Put ZenRbxManager on GitHub Pages

The website is ready in `site/index.html`, and the app is in `src/` and `web/`. GitHub currently has only the starter README; the new files are **not online yet**. The old and newly posted GitHub tokens were exposed in chat. Revoke both and do not use or paste them again.

## Option A: push the prepared local Git repository

If you are working in the original workspace where this project was built, it has already been merged with the existing `sitezu/ZenRbxManager` starter commit and `origin` points at the right URL. After signing in to GitHub on your own computer, run:

```bash
git -C ZenRbxManager push -u origin main
```

The CLI device-sign-in attempt from this sandbox failed due to a connection reset on GitHub's OAuth endpoint. No credentials are saved in the project.

## Option B: publish from the downloadable ZIP (Windows PowerShell)

1. Download `ZenRbxManager-repository.zip` and extract it somewhere, such as `Downloads\ZenRbxManager-repository\ZenRbxManager`.
2. Open PowerShell. Replace `$source` with the path to the **extracted inner** `ZenRbxManager` folder:

```powershell
$source = "$env:USERPROFILE\Downloads\ZenRbxManager-repository\ZenRbxManager"
git clone https://github.com/sitezu/ZenRbxManager.git
Get-ChildItem -LiteralPath $source -Force | Copy-Item -Destination .\ZenRbxManager -Recurse -Force
Set-Location .\ZenRbxManager
git add -A
git commit -m "Add ZenRbxManager app and website"
git push origin main
```

You will sign in through Git on your computer if prompted. Do not put a personal access token in a command or a remote URL. If `git` is not installed, install [Git for Windows](https://git-scm.com/download/win) first. You can also use GitHub Desktop to clone the existing repo, copy the extracted files into it, commit, and publish the commit.

## Turn on GitHub Pages

1. Open [the ZenRbxManager repository settings](https://github.com/sitezu/ZenRbxManager/settings/pages).
2. Under **Build and deployment**, choose **Source: GitHub Actions**.
3. Go to [Actions → Publish ZenRbxManager website](https://github.com/sitezu/ZenRbxManager/actions/workflows/pages.yml). If no run started after the push, click **Run workflow** on `main`.
4. Once deployment succeeds, visit **https://sitezu.github.io/ZenRbxManager/**. It will return 404 until the page is deployed.

The Windows app build is a separate GitHub Actions workflow. It tests the source and fails if a built executable is 100 MB or larger. Passing CI is not a substitute for testing a real Roblox login and launch on Windows. Do not publish an executable as a release until you have tested it.
