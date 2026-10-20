; Installazione per Windows (Inno Setup 6). Compila prima con build_windows.bat.
#ifndef AppVersion
  #define AppVersion "1.0.1"
#endif

[Setup]
AppId={{6E0B7C1A-4F43-4C1E-9C4B-1E7A2D5B9F10}
AppName=LeggiTutto
AppVersion={#AppVersion}
AppPublisher=Massimiliano Mascioli Trippa
AppContact=max@maxtrip.it
AppSupportURL=mailto:max@maxtrip.it
AppCopyright=© 2026 Massimiliano Mascioli Trippa
VersionInfoCompany=Massimiliano Mascioli Trippa
VersionInfoCopyright=© 2026 Massimiliano Mascioli Trippa
VersionInfoDescription=Installazione di LeggiTutto
VersionInfoVersion={#AppVersion}
DefaultDirName={autopf}\LeggiTutto
DefaultGroupName=LeggiTutto
OutputDir=..\dist
OutputBaseFilename=LeggiTutto-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern

[Languages]
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "Crea un'icona sul desktop"; Flags: unchecked
Name: "sendto"; Description: "Aggiungi LeggiTutto al menu ""Invia a"" (clic destro su un file)"

[Files]
Source: "..\dist\LeggiTutto\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\LeggiTutto"; Filename: "{app}\LeggiTutto.exe"
Name: "{group}\Disinstalla LeggiTutto"; Filename: "{uninstallexe}"
Name: "{autodesktop}\LeggiTutto"; Filename: "{app}\LeggiTutto.exe"; Tasks: desktopicon
Name: "{usersendto}\LeggiTutto (converti in testo)"; Filename: "{app}\LeggiTutto.exe"; Tasks: sendto

[Run]
Filename: "{app}\LeggiTutto.exe"; Description: "Avvia LeggiTutto"; Flags: nowait postinstall skipifsilent
