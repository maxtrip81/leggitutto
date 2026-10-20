; Installazione per Windows (Inno Setup 6). Compila prima con build_windows.bat.
#ifndef AppVersion
  #define AppVersion "1.1.0"
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

ShowLanguageDialog=yes
LanguageDetectionMethod=none

[Languages]
; La prima lingua è quella predefinita: italiano.
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
it.DesktopIcon=Crea un'icona sul desktop
en.DesktopIcon=Create a desktop icon
it.SendTo=Aggiungi LeggiTutto al menu "Invia a" (clic destro su un file)
en.SendTo=Add LeggiTutto to the "Send to" menu (right-click on a file)
it.SendToName=LeggiTutto (converti in testo)
en.SendToName=LeggiTutto (convert to text)
it.Uninstall=Disinstalla LeggiTutto
en.Uninstall=Uninstall LeggiTutto
it.Launch=Avvia LeggiTutto
en.Launch=Start LeggiTutto

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; Flags: unchecked
Name: "sendto"; Description: "{cm:SendTo}"

[Files]
Source: "..\dist\LeggiTutto\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\LeggiTutto"; Filename: "{app}\LeggiTutto.exe"
Name: "{group}\{cm:Uninstall}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\LeggiTutto"; Filename: "{app}\LeggiTutto.exe"; Tasks: desktopicon
Name: "{usersendto}\{cm:SendToName}"; Filename: "{app}\LeggiTutto.exe"; Tasks: sendto

[Run]
Filename: "{app}\LeggiTutto.exe"; Description: "{cm:Launch}"; Flags: nowait postinstall skipifsilent
