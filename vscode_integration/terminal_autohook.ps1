# ═══════════════════════════════════════════════════════════════════════════
# CODE-ALARM: Universal Automatic Terminal Hook for PowerShell & VS Code
# Detects EVERY command (Flutter, Dart, Python, C, C++, Rust, Node, Git, etc.)
# ═══════════════════════════════════════════════════════════════════════════

# Native WinForms assembly for instant desktop toast notifications
try {
    [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
} catch {}

# Global Trigger Function
function global:__TriggerCodeAlarm($cmdText, $elapsedSec, $isSuccess) {
    [System.Threading.ThreadPool]::QueueUserWorkItem({
        param($state)
        $ok = $state[0]
        $cmd = $state[1]
        $dur = $state[2]

        try {
            if ($ok) {
                # Uplifting 3-note harmonic chime (C5 -> E5 -> G5)
                [System.Console]::Beep(523, 100)
                [System.Threading.Thread]::Sleep(30)
                [System.Console]::Beep(659, 100)
                [System.Threading.Thread]::Sleep(30)
                [System.Console]::Beep(784, 250)
            } else {
                # Warning descending chord
                [System.Console]::Beep(700, 150)
                [System.Threading.Thread]::Sleep(50)
                [System.Console]::Beep(450, 200)
            }
        } catch {}

        try {
            $notify = New-Object System.Windows.Forms.NotifyIcon
            $notify.Icon = [System.Drawing.SystemIcons]::Information
            $notify.BalloonTipIcon = if ($ok) { [System.Windows.Forms.ToolTipIcon]::Info } else { [System.Windows.Forms.ToolTipIcon]::Error }
            $notify.BalloonTipTitle = if ($ok) { "✅ Command Finished" } else { "❌ Command Failed" }
            $notify.BalloonTipText = "$cmd (Completed in $dur)"
            $notify.Visible = $True
            $notify.ShowBalloonTip(3000)
            [System.Threading.Thread]::Sleep(3500)
            $notify.Dispose()
        } catch {}
    }, @($isSuccess, $cmdText, ("{0:N1}s" -f $elapsedSec))) | Out-Null
}

$global:__codeAlarmLastHistId = -1
$global:__codeAlarmTimer = [System.Diagnostics.Stopwatch]::StartNew()

# Hook Enter key if PSReadLine is available
try {
    if (Get-Command Set-PSReadLineKeyHandler -ErrorAction SilentlyContinue) {
        Set-PSReadLineKeyHandler -Key Enter -ScriptBlock {
            $global:__codeAlarmTimer.Restart()
            [Microsoft.PowerShell.PSConsoleReadLine]::AcceptLine()
        }
    }
} catch {}

# Extend the prompt function
if (Test-Path Function:\prompt) {
    $global:__codeAlarmOrigPrompt = $Function:prompt
}

function prompt {
    $lastExitOk = $?
    $lastCode = $LASTEXITCODE

    $lastHistory = Get-History -Count 1 -ErrorAction SilentlyContinue
    if ($lastHistory -and $lastHistory.Id -ne $global:__codeAlarmLastHistId) {
        $global:__codeAlarmLastHistId = $lastHistory.Id
        $cmdText = $lastHistory.CommandLine
        $elapsed = $global:__codeAlarmTimer.Elapsed.TotalSeconds
        
        if ($cmdText -and $cmdText -ne "prompt" -and $cmdText -ne "cls" -and $cmdText -ne "clear") {
            $isSuccess = $lastExitOk
            if ($lastCode -ne $null -and $lastCode -ne 0) {
                $isSuccess = $false
            }
            global:__TriggerCodeAlarm $cmdText $elapsed $isSuccess
        }
    }

    $global:__codeAlarmTimer.Restart()

    if ($global:__codeAlarmOrigPrompt) {
        & $global:__codeAlarmOrigPrompt
    } else {
        "PS $($executionContext.SessionState.Path.CurrentLocation)$('>' * ($nestedPromptLevel + 1)) "
    }
}
