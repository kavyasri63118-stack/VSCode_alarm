# ═══════════════════════════════════════════════════════════════════════════
# PowerShell / VS Code Terminal Quick Aliases
# ═══════════════════════════════════════════════════════════════════════════
# To enable this in your VS Code terminal permanently:
# 1. Open your PowerShell profile:
#    notepad $PROFILE
# 2. Paste the lines below and save!
# ═══════════════════════════════════════════════════════════════════════════

function notify {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
    if ($Args.Count -eq 0) {
        python -m code_alarm.cli --help
    } else {
        python -m code_alarm.cli run $Args
    }
}

# Example usage in any VS Code terminal:
#   notify python train.py
#   notify pytest
#   notify cargo build
#   notify npm run build
