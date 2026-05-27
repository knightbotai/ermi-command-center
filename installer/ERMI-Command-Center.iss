#define AppName "ERMI Command Center"
#ifndef AppVersion
#define AppVersion "0.1.0-mvp"
#endif
#ifndef AppFileVersion
#define AppFileVersion "0.1.0.0"
#endif
#define AppPublisher "KnightBot / DeeTorch"
#define AppExeName "START-HERE.cmd"

[Setup]
AppId={{A8973B11-1F4D-4F57-A6E7-4B5769EE6A42}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\ERMI Command Center
DefaultGroupName=ERMI Command Center
DisableProgramGroupPage=no
AllowNoIcons=yes
OutputDir=output
OutputBaseFilename=ERMI-Command-Center-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\generated\ermi.ico
WizardImageFile=assets\generated\wizard-side.bmp
WizardSmallImageFile=assets\generated\wizard-banner.bmp
UninstallDisplayIcon={app}\assets\generated\ermi.ico
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoVersion={#AppFileVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=ERMI Command Center local MVP installer
VersionInfoProductName={#AppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce
Name: "launchafter"; Description: "Launch ERMI Command Center after setup"; GroupDescription: "First run:"; Flags: checkedonce

[Files]
Source: "..\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: ".git\*,archive\*,node_modules\*,dist\*,build\*,artifacts\*,.pytest_cache\*,.venv\*,__pycache__\*,*.egg-info\*,*.pyc,*.pyo,*.sqlite3,*.db,*.log,installer\output\*"

[Icons]
Name: "{group}\ERMI Command Center"; Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\install\Launch-ERMI.ps1"""; WorkingDir: "{app}"; IconFilename: "{app}\installer\assets\generated\ermi.ico"
Name: "{group}\Update ERMI Command Center"; Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\install\Update-ERMI.ps1"""; WorkingDir: "{app}"; IconFilename: "{app}\installer\assets\generated\ermi.ico"
Name: "{autodesktop}\ERMI Command Center"; Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\install\Launch-ERMI.ps1"""; WorkingDir: "{app}"; IconFilename: "{app}\installer\assets\generated\ermi.ico"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\install\Install-ERMI.ps1"" -SkipShortcuts"; WorkingDir: "{app}"; Description: "Install ERMI dependencies and run diagnostics"; Flags: runascurrentuser waituntilterminated
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\install\Launch-ERMI.ps1"""; WorkingDir: "{app}"; Description: "Launch ERMI Command Center"; Flags: nowait postinstall skipifsilent; Tasks: launchafter

[UninstallDelete]
Type: filesandordirs; Name: "{app}\node_modules"
Type: filesandordirs; Name: "{app}\dist"
