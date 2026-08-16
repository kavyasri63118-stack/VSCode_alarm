; ═══════════════════════════════════════════════════════════════════════════
; Code Alarm V2 — Official Inno Setup Windows Installer Script
; Generates: CodeAlarm-Setup.exe
; Per-user installation: {localappdata}\Programs\CodeAlarm (No admin rights required)
; ═══════════════════════════════════════════════════════════════════════════

#define MyAppName "Code Alarm"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Code Alarm Open Source"
#define MyAppURL "https://github.com/code-alarm"
#define MyAppExeName "CodeAlarm.exe"
#define MyCliExeName "code-alarm.exe"

[Setup]
; Basic Application Info
AppId={{D68F1247-92B1-4A59-8EF9-A51239B217D2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Destination Directories
DefaultDirName={localappdata}\Programs\CodeAlarm
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output Configuration
OutputDir=..\dist_installer
OutputBaseFilename=CodeAlarm-Setup
SetupIconFile=..\assets\code_alarm.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Privileges: User-level (No UAC / No Administrator prompts required)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline

; Visual Styling
UninstallDisplayIcon={app}\{#MyAppExeName}
ChangesEnvironment=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Start Code Alarm automatically when Windows starts (quiet background mode)"; GroupDescription: "Windows Startup Options:"; Flags: unchecked

[Files]
; Standalone PyInstaller Application Files
Source: "..\dist\CodeAlarm\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "n.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\code_alarm.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\assets\code_alarm.png"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
; Start Menu Shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\code_alarm.ico"; Comment: "Code Alarm V2 — Intelligent Developer Execution & Alert System"
Name: "{group}\Code Alarm Dashboard (Web)"; Filename: "http://127.0.0.1:8088"; IconFilename: "{app}\assets\code_alarm.ico"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Optional Desktop Shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\code_alarm.ico"; Tasks: desktopicon

; Optional Windows Startup Shortcut
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--background"; IconFilename: "{app}\assets\code_alarm.ico"; Tasks: autostart

[Registry]
; Add application directory to user PATH so `code-alarm` and `n` work globally in terminal
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Check: NeedsAddPath(ExpandConstant('{app}'))

[Run]
; Run application upon installation completion
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Helper function to prevent duplicate PATH entries
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  // Look for the path with leading and trailing semicolons
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;
