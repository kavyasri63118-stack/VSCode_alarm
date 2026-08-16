# ═══════════════════════════════════════════════════════════════════════════
# Comprehensive PowerShell & VS Code Profile Auto-Alarm Installer
# ═══════════════════════════════════════════════════════════════════════════

$hookPath = "C:\Users\arumu\.gemini\antigravity\scratch\code-completion-alarm\vscode_integration\terminal_autohook.ps1"
$marker = "`n# == CODE-ALARM HOOK ==`nif (Test-Path `"$hookPath`") { . `"$hookPath`" }`n"

$profilesToInstall = @(
    "C:\Users\arumu\OneDrive\Documents\WindowsPowerShell\Microsoft.VSCode_profile.ps1",
    "C:\Users\arumu\OneDrive\Documents\WindowsPowerShell\profile.ps1",
    "C:\Users\arumu\OneDrive\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1",
    "C:\Users\arumu\Documents\WindowsPowerShell\Microsoft.VSCode_profile.ps1",
    "C:\Users\arumu\Documents\WindowsPowerShell\profile.ps1",
    "C:\Users\arumu\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1",
    "C:\Users\arumu\OneDrive\Documents\PowerShell\Microsoft.VSCode_profile.ps1",
    "C:\Users\arumu\OneDrive\Documents\PowerShell\profile.ps1",
    "C:\Users\arumu\Documents\PowerShell\Microsoft.VSCode_profile.ps1",
    "C:\Users\arumu\Documents\PowerShell\profile.ps1"
)

$count = 0
foreach ($p in $profilesToInstall) {
    $parent = Split-Path -Parent $p
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    $existing = if (Test-Path $p) { Get-Content $p -Raw } else { "" }
    if ($existing -notmatch "CODE-ALARM HOOK") {
        Add-Content -Path $p -Value $marker
        $count++
    }
}

Write-Host "Code-Alarm hook successfully written to $count profile configurations." -ForegroundColor Green
