; LitigationOS Installer — MBP LLC
; Requires Inno Setup 6.x

[Setup]
AppId={{LITIGATION-OS-MBP-LLC}
AppName=LitigationOS
AppVersion=1.0.0
AppVerName=LitigationOS 1.0.0
AppPublisher=MBP LLC
AppPublisherURL=https://litigationos.com
AppSupportURL=https://litigationos.com/support
DefaultDirName={autopf}\LitigationOS
DefaultGroupName=LitigationOS
AllowNoIcons=yes
LicenseFile=..\..\LICENSE
OutputDir=.\output
OutputBaseFilename=LitigationOS-Setup-1.0.0
SetupIconFile=..\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\icon.ico
WizardImageFile=..\assets\wizard_banner.bmp
WizardSmallImageFile=..\assets\wizard_small.bmp

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\litigationos\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\LitigationOS"; Filename: "{app}\litigationos.exe"; IconFilename: "{app}\icon.ico"
Name: "{group}\{cm:UninstallProgram,LitigationOS}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\LitigationOS"; Filename: "{app}\litigationos.exe"; Tasks: desktopicon; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\litigationos.exe"; Description: "{cm:LaunchProgram,LitigationOS}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\MBP LLC\LitigationOS"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\MBP LLC\LitigationOS"; ValueType: string; ValueName: "Version"; ValueData: "1.0.0"
