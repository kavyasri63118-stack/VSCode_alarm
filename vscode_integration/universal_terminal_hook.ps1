# ═══════════════════════════════════════════════════════════════════════════
# UNIVERSAL CODE-ALARM: 100% Invisible Background Hook for All Commands
# Works for Flutter, Dart, Python, C, C++, Java, Node, Rust, Code Runner, etc.
# ═══════════════════════════════════════════════════════════════════════════

try {
    [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
} catch {}

$global:__codeAlarmLastHistId = -1

# Preserve the original prompt appearance
if (Test-Path Function:\prompt) {
    $global:__codeAlarmOrigPrompt = $Function:prompt
}

function prompt {
    $isOk = $?
    $lastCode = $LASTEXITCODE

    $lastHist = Get-History -Count 1 -ErrorAction SilentlyContinue
    if ($lastHist -and $lastHist.Id -ne $global:__codeAlarmLastHistId) {
        $global:__codeAlarmLastHistId = $lastHist.Id
        $cmd = $lastHist.CommandLine

        # Ignore internal commands and clear screen
        if ($cmd -and $cmd -ne "cls" -and $cmd -ne "clear" -and $cmd -ne "exit") {
            if ($lastCode -ne $null -and $lastCode -ne 0) {
                $isOk = $false
            }

            # Asynchronous background chime & notification (0ms terminal impact)
            [System.Threading.ThreadPool]::QueueUserWorkItem({
                param($state)
                $ok = $state[0]
                $c = $state[1]

                try {
                    if ($ok) {
                        # Uplifting 3-note harmonic chime (C5 -> E5 -> G5)
                        [System.Console]::Beep(523, 90)
                        [System.Threading.Thread]::Sleep(20)
                        [System.Console]::Beep(659, 90)
                        [System.Threading.Thread]::Sleep(20)
                        [System.Console]::Beep(784, 200)
                    } else {
                        # Warning chord
                        [System.Console]::Beep(700, 130)
                        [System.Threading.Thread]::Sleep(30)
                        [System.Console]::Beep(450, 180)
                    }
                } catch {}

                try {
                    $notify = New-Object System.Windows.Forms.NotifyIcon
                    $notify.Icon = [System.Drawing.SystemIcons]::Information
                    $notify.BalloonTipIcon = if ($ok) { [System.Windows.Forms.ToolTipIcon]::Info } else { [System.Windows.Forms.ToolTipIcon]::Error }
                    $notify.BalloonTipTitle = if ($ok) { "✅ Command Finished" } else { "❌ Command Failed" }
                    $notify.BalloonTipText = "$c"
                    $notify.Visible = $True
                    $notify.ShowBalloonTip(2500)
                    [System.Threading.Thread]::Sleep(3000)
                    $notify.Dispose()
                } catch {}
            }, @($isOk, $cmd)) | Out-Null
        }
    }

    # Render original prompt exactly as before
    if ($global:__codeAlarmOrigPrompt) {
        & $global:__codeAlarmOrigPrompt
    } else {
        "PS $($executionContext.SessionState.Path.CurrentLocation)$('>' * ($nestedPromptLevel + 1)) "
    }
}
