# ═══════════════════════════════════════════════════════════════════════════
# Code-Alarm Ultimate Clean Terminal Aliases (Zero Prompt Interference)
# ═══════════════════════════════════════════════════════════════════════════

$aliasesCode = @"

# Code-Alarm Universal Command Runners
function notify { python -m code_alarm.cli run @args }
function alarm  { python -m code_alarm.cli run @args }
function n      { python -m code_alarm.cli run @args }
"@

$profilesToUpdate = @(
    "C:\Users\arumu\OneDrive\Documents\WindowsPowerShell\Microsoft.VSCode_profile.ps1",
    "C:\Users\arumu\OneDrive\Documents\WindowsPowerShell\profile.ps1",
    "C:\Users\arumu\OneDrive\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1",
    "C:\Users\arumu\Documents\WindowsPowerShell\Microsoft.VSCode_profile.ps1",
    "C:\Users\arumu\Documents\WindowsPowerShell\profile.ps1",
    "C:\Users\arumu\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1"
)

foreach ($p in $profilesToUpdate) {
    $parent = Split-Path -Parent $p
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }

    $existing = if (Test-Path $p) { Get-Content $p -Raw } else { "" }
    # Clean up old definitions
    $cleaned = ($existing -split "`r?`n" | Where-Object { 
        $_ -notmatch "function notify" -and $_ -notmatch "function alarm" -and $_ -notmatch "function n\s" -and $_ -notmatch "Param\(" -and $_ -notmatch "CommandArgs"
    }) -join "`r`n"
    
    Set-Content -Path $p -Value ($cleaned.Trim() + "`n" + $aliasesCode) -Force
}

Write-Host "Aliases 'notify', 'alarm', and 'n' successfully installed into all profile locations." -ForegroundColor Green
