# ═══════════════════════════════════════════════════════════════════════════
# Clean Notify Function for All PowerShell and VS Code Profiles
# ═══════════════════════════════════════════════════════════════════════════

$cleanNotify = @"

# Code-Alarm Notify Shortcut
function notify {
    param([Parameter(ValueFromRemainingArguments=`$true)][string[]]`$CommandArgs)
    if (-not `$CommandArgs -or `$CommandArgs.Count -eq 0) {
        python -m code_alarm.cli --help
    } else {
        python -m code_alarm.cli run `$CommandArgs
    }
}
"@

$profiles = @(
    "C:\Users\arumu\OneDrive\Documents\WindowsPowerShell\Microsoft.VSCode_profile.ps1",
    "C:\Users\arumu\OneDrive\Documents\WindowsPowerShell\profile.ps1",
    "C:\Users\arumu\OneDrive\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1",
    "C:\Users\arumu\Documents\WindowsPowerShell\Microsoft.VSCode_profile.ps1",
    "C:\Users\arumu\Documents\WindowsPowerShell\profile.ps1",
    "C:\Users\arumu\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1"
)

foreach ($p in $profiles) {
    $parent = Split-Path -Parent $p
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    
    $existing = if (Test-Path $p) { Get-Content $p -Raw } else { "" }
    if ($existing -notmatch "function notify") {
        Add-Content -Path $p -Value $cleanNotify
    }
}

Write-Host "Notify function installed into all profile targets." -ForegroundColor Green
