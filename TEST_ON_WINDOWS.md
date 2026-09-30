# Real-Windows test before a setup release

The setup candidate from [Windows app / size check](https://github.com/sitezu/ZenRbxManager/actions/workflows/windows-build.yml) has automated checks for compilation, UI/backend startup, silent installation and uninstall. **Those checks do not sign in to Roblox or launch a Roblox game.** Only test live account flows with an account you own. Never send the project your account cookie, password, or auth ticket.

## Prepare

1. Download the `ZenRbxManager-Setup-Candidate` artifact from the newest successful Windows build run. Extract `ZenRbxManager-Setup-candidate.exe` and `SETUP-SHA256SUMS.txt`.
2. In PowerShell, run `(Get-FileHash .\ZenRbxManager-Setup-candidate.exe -Algorithm SHA256).Hash.ToLower()` and compare the result with `SETUP-SHA256SUMS.txt`.
3. Back up any existing `AccountManagerData` folder. Install on a Windows 10 or 11 machine with Roblox and Edge or Chrome installed. The build is unsigned, so Windows may warn you.

## Run through the app

- [ ] Install using the wizard without requiring administrator permissions. Confirm the Start Menu shortcut opens the app.
- [ ] Confirm an empty account list appears on a new installation, with no sample accounts.
- [ ] Add an account you own through the browser sign-in flow. If it fails, note the error **without including any cookie or password**. If you choose to test cookie import, use your own cookie and keep it private.
- [ ] Restart the app. Confirm the account still appears, and that search, status filtering, name privacy and selecting work.
- [ ] Edit its alias and note. Restart again and verify they persisted. Test theme changes and settings persistence.
- [ ] With Roblox installed, launch that account into Roblox Home. Verify the correct account opens.
- [ ] Launch into a valid Place ID; if you have permission, test a specific server Job ID too.
- [ ] If you have multiple accounts you own, try selecting both and launching them. Check any error message rather than assuming success.
- [ ] Close the app. Run the uninstaller from Windows Settings. Confirm the app shortcut/EXE are removed, but your saved accounts have **not** been silently deleted. Keep your backup.

## Report results

Tell me which boxes passed and which failed, your Windows version, and the exact non-sensitive error text. **Do not paste a Roblox cookie, GitHub token, password, or account data file.** I will fix any failures before tagging a setup release. Only after the live checks pass should the setup installer be published as a release.
