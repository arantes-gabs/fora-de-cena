#ifndef AppVersion
  #define AppVersion "0.5.0-beta.2"
#endif
#ifndef AppNumericVersion
  #define AppNumericVersion "0.5.0.2"
#endif
#ifndef PayloadDir
  #error PayloadDir deve apontar para o pacote validado
#endif
#ifndef OutputDir
  #error OutputDir deve apontar para a pasta de artefatos
#endif

[Setup]
AppId={{DC9A750F-9098-4E03-8184-C1DB480A63D8}
AppName=Fora de Cena
AppVersion={#AppVersion}
VersionInfoVersion={#AppNumericVersion}
VersionInfoTextVersion={#AppVersion}
VersionInfoProductVersion={#AppNumericVersion}
AppPublisher=Fora de Cena contributors
DefaultDirName={localappdata}\Programs\ForaDeCena
DefaultGroupName=Fora de Cena
PrivilegesRequired=lowest
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
MinVersion=10.0.19041
OutputDir={#OutputDir}
OutputBaseFilename=ForaDeCena-{#AppVersion}-Setup
SetupIconFile=..\assets\brand\app-icon.ico
UninstallDisplayIcon={app}\ForaDeCena.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
DisableWelcomePage=no
CloseApplications=yes
RestartApplications=no
InfoBeforeFile=TESTE_LOCAL.txt
UninstallDisplayName=Fora de Cena

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; Flags: unchecked

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Fora de Cena"; Filename: "{app}\ForaDeCena.exe"; AppUserModelID: "ForaDeCena.Desktop"
Name: "{group}\Guia rápido"; Filename: "{app}\_internal\GUIA_RAPIDO.html"
Name: "{autodesktop}\Fora de Cena"; Filename: "{app}\ForaDeCena.exe"; Tasks: desktopicon; AppUserModelID: "ForaDeCena.Desktop"

; No driver registration, browser extension installation, auto-run or downloads.
; Per-user settings remain after uninstall; never delete them recursively.
