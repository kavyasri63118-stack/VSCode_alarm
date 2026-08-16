# ═══════════════════════════════════════════════════════════════════════════
# Install Universal Background Hook into All PowerShell & VS Code Profiles
# ═══════════════════════════════════════════════════════════════════════════

$hookPath = "C:\Users\arumu\.gemini\antigravity\scratch\code-completion-alarm\vscode_integration\universal_terminal_hook.ps1"
$hookCode = Get-Content $hookPath -Raw

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

foreach ($p in $profilesToInstall) {
    $parent = Split-Path -Parent $p
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Set-Content -Path $p -Value $hookCode -Force
}

Write-Host "Universal background hook successfully active in all profile locations!" -ForegroundColor Green
