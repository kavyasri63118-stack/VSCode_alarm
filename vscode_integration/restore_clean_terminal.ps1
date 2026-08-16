# ═══════════════════════════════════════════════════════════════════════════
# Clean up all PowerShell & VS Code profiles to restore original terminal
# ═══════════════════════════════════════════════════════════════════════════

$profilesToClean = @(
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

foreach ($p in $profilesToClean) {
    if (Test-Path $p) {
        $content = Get-Content $p -Raw
        if ($content -match "CODE-ALARM") {
            # Remove Code-Alarm hook lines completely
            $cleaned = ($content -split "`r?`n" | Where-Object { 
                $_ -notmatch "CODE-ALARM" -and $_ -notmatch "terminal_autohook.ps1"
            }) -join "`r`n"
            
            if ($cleaned.Trim() -eq "") {
                Remove-Item $p -Force -ErrorAction SilentlyContinue
            } else {
                Set-Content -Path $p -Value $cleaned.Trim() -Force
            }
        }
    }
}

# Add only a lightweight, clean function 'notify' that doesn't modify prompt or PSReadLine
$cleanNotifyCode = @"

# Code-Alarm Clean Runner (No Prompt Modification)
function notify {
    param([Parameter(ValueFromRemainingArguments=`$true)][string[]]`$CommandArgs)
    if (-not `$CommandArgs -or `$CommandArgs.Count -eq 0) {
        python -m code_alarm.cli --help
        return
    }
    
    `$cmdLine = `$CommandArgs -join " "
    `$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    # Execute command naturally
    & `$CommandArgs[0] `$CommandArgs[1..(`$CommandArgs.Count - 1)]
    `$exitCode = `$LASTEXITCODE
    `$isSuccess = `$?
    if (`$exitCode -ne `$null -and `$exitCode -ne 0) { `$isSuccess = `$false }
    
    `$stopwatch.Stop()
    `$elapsed = `$stopwatch.Elapsed.TotalSeconds
    `$durStr = if (`$elapsed -ge 60) { "{0}m {1}s" -f [int](`$elapsed/60), [int](`$elapsed%60) } else { "{0:N1}s" -f `$elapsed }

    # Instant background chime & toast
    [System.Threading.ThreadPool]::QueueUserWorkItem({
        param(`$state)
        `$ok = `$state[0]
        `$cmd = `$state[1]
        `$dur = `$state[2]
        
        try {
            if (`$ok) {
                [System.Console]::Beep(523, 100)
                [System.Threading.Thread]::Sleep(30)
                [System.Console]::Beep(659, 100)
                [System.Threading.Thread]::Sleep(30)
                [System.Console]::Beep(784, 250)
            } else {
                [System.Console]::Beep(700, 150)
                [System.Threading.Thread]::Sleep(50)
                [System.Console]::Beep(450, 200)
            }
        } catch {}

        try {
            [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
            `$notify = New-Object System.Windows.Forms.NotifyIcon
            `$notify.Icon = [System.Drawing.SystemIcons]::Information
            `$notify.BalloonTipIcon = if (`$ok) { [System.Windows.Forms.ToolTipIcon]::Info } else { [System.Windows.Forms.ToolTipIcon]::Error }
            `$notify.BalloonTipTitle = if (`$ok) { "Command Completed" } else { "Command Failed" }
            `$notify.BalloonTipText = "`$cmd (in `$dur)"
            `$notify.Visible = `$True
            `$notify.ShowBalloonTip(3000)
            [System.Threading.Thread]::Sleep(3500)
            `$notify.Dispose()
        } catch {}
    }, @(`$isSuccess, `$cmdLine, `$durStr)) | Out-Null
}
"@

# Put this clean helper into the main profile without touching prompt/Enter keys
$mainProfile = "C:\Users\arumu\OneDrive\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1"
$parent = Split-Path -Parent $mainProfile
if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
Add-Content -Path $mainProfile -Value $cleanNotifyCode

Write-Host "Terminal profiles restored to clean state! Zero interference with prompt or keys." -ForegroundColor Green
