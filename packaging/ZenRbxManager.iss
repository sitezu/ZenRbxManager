; ZenRbxManager per-user Windows setup. Build with Inno Setup 6 (ISCC.exe).
; Never ship account data, cookies or Selenium browser profiles in this installer.
#ifndef MyAppVersion
  #define MyAppVersion "candidate"
#endif
#define MyAppName "ZenRbxManager"
#define MyAppExeName "ZenRbxManager.exe"

[Setup]
AppId={{B5737D03-BDA0-4765-9E35-771ED4DAF622}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=sitezu
AppPublisherURL=https://github.com/sitezu/ZenRbxManager
AppSupportURL=https://github.com/sitezu/ZenRbxManager/issues
AppUpdatesURL=https://github.com/sitezu/ZenRbxManager/releases
DefaultDirName={localappdata}\Programs\ZenRbxManager
DefaultGroupName=ZenRbxManager
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=ZenRbxManager-Setup-{#MyAppVersion}
SetupIconFile=..\assets-icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
LicenseFile=..\LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
VersionInfoVersion=0.1.1.0

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\ZenRbxManager"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\ZenRbxManager"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Open ZenRbxManager"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Startup shortcut created by ZenRbxManager's own preference, if enabled.
Type: files; Name: "{userstartup}\ZenRbxManager.cmd"
; Deliberately keep {app}\AccountManagerData so uninstalling does not delete saved accounts.
