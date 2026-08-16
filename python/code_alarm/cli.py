"""
Command-Line Interface for Code Alarm V2 (Intelligent Developer Execution System)
"""

import sys
import os
import argparse
from typing import List

from .runner import run_command
from .laptop_alerts import trigger_laptop_alert
from .config import config, DEFAULT_SETTINGS
from .storage import storage
from .summary import JobSummaryEngine

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def _cmd_summary(args):
    """Display Level 1 Quick Aggregate Summary."""
    print()
    print(JobSummaryEngine.get_level1_summary())
    print()

def _cmd_list(args):
    """List recent tracked execution jobs."""
    jobs = storage.list_jobs(limit=args.limit)
    if not jobs:
        print("\nNo jobs recorded yet. Run commands with `n <command>` or `code-alarm run <command>`.\n")
        return

    print("\n╔══════════════════════════════════════════════════════════════════════════════════════════════════╗")
    print("║                                      RECENT EXECUTION JOBS                                       ║")
    print("╠══════════════════════════════════════════════════════════════════════════════════════════════════╣")
    print(f"║ {'STATUS':<10} | {'JOB ID':<20} | {'PROGRAM':<15} | {'RUNTIME':<10} | {'COMMAND':<28} ║")
    print("╠══════════════════════════════════════════════════════════════════════════════════════════════════╣")
    for j in jobs:
        st = j.get("status", "UNKNOWN")
        icon = "✅" if st == "SUCCESS" else ("❌" if st == "FAILED" else ("💥" if st == "CRASHED" else ("⏹️" if st == "TERMINATED" else "🔄")))
        dur = f"{j.get('runtime_seconds', 0.0):.2f}s" if j.get("runtime_seconds") is not None else "running..."
        print(f"║ {icon} {st:<7} | {j.get('job_id', ''):<20} | {j.get('program', '')[:15]:<15} | {dur:<10} | {j.get('command', '')[:28]:<28} ║")
    print("╚══════════════════════════════════════════════════════════════════════════════════════════════════╝")
    print("💡 Tip: Use `code-alarm details <job_id>` or `code-alarm analyze <job_id>` for deep failure breakdown.\n")

def _cmd_details(args):
    """Display Level 2 Job Details."""
    out = JobSummaryEngine.get_level2_details(args.job_id)
    if not out:
        print(f"\n❌ Error: Job ID '{args.job_id}' not found in history.\n")
        return
    print()
    print(out)
    print()

def _cmd_analyze(args):
    """Display Level 3 Execution Failure Analysis."""
    out = JobSummaryEngine.get_level3_analysis(args.job_id)
    if not out:
        print(f"\n❌ Error: Job ID '{args.job_id}' not found in history.\n")
        return
    print()
    print(out)
    print()

def _cmd_settings(args):
    """Display the 7 Alert Control Center settings with live override statuses."""
    raw = config.get_all()
    eff = config.get_effective_all()
    master = raw.get("master_alert_system", True)
    quiet = raw.get("quiet_mode", False)

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║               ⚙️  ALERT CONTROL CENTER                   ║")
    print("╠══════════════════════════════════════════════════════════╣")
    for k in ["master_alert_system", "success_sound", "failure_sound", "desktop_notification", "failure_intelligence", "job_summary", "quiet_mode"]:
        label = k.replace("_", " ").title()
        raw_val = raw.get(k, True)

        if k in ("success_sound", "failure_sound", "desktop_notification"):
            if quiet and raw_val:
                val_str = "🟡 MUTED (Quiet Mode)"
            elif not master and raw_val:
                val_str = "🟡 MUTED (Master OFF)"
            else:
                val_str = "🟢 ON" if raw_val else "🔴 OFF"
        else:
            val_str = "🟢 ON" if raw_val else "🔴 OFF"

        print(f"║  {label:<24} : {val_str:<22} ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("💡 To toggle: `code-alarm set <setting_name> <on|off>` or `code-alarm quiet on`\n")

def _cmd_set(args):
    """Update a specific setting."""
    key = args.setting.lower().replace("-", "_")
    if key not in DEFAULT_SETTINGS:
        print(f"\n❌ Unknown setting: '{args.setting}'. Available settings:")
        for k in DEFAULT_SETTINGS:
            print(f"   - {k}")
        print()
        return

    val = args.value.lower() in ("on", "true", "1", "yes", "enable")
    config.set(key, val)
    print(f"\n✅ Updated setting: {key} = {'ON' if val else 'OFF'}\n")

def _cmd_quiet(args):
    """Convenience shortcut for Quiet Mode."""
    val = args.state.lower() in ("on", "true", "1", "yes", "enable")
    config.set("quiet_mode", val)
    print(f"\n🤫 Quiet Mode is now {'ENABLED (all alerts suppressed)' if val else 'DISABLED'}\n")

def _cmd_master(args):
    """Convenience shortcut for Master Alert System."""
    val = args.state.lower() in ("on", "true", "1", "yes", "enable")
    config.set("master_alert_system", val)
    print(f"\n🔔 Master Alert System is now {'ENABLED' if val else 'DISABLED (monitoring continues, alerts muted)'}\n")

def _cmd_test(args):
    sound = args.sound.upper()
    print(f"\n🔔 Testing Code Alarm: Pattern = {sound}, Voice = {args.voice}")
    trigger_laptop_alert(
        title=f"Code Alarm Test: {sound}",
        message=f"Test alert notification for {sound} pattern.",
        pattern=sound,
        voice=args.voice,
        voice_message=f"Code alarm test pattern {sound}"
    )
    print("✅ Played audio chime and displayed Windows toast notification on your laptop screen!\n")

def _cmd_dashboard(args):
    """Launch the Code Alarm V2 Web Dashboard & REST API server."""
    import sys
    from pathlib import Path
    dashboard_dir = Path(__file__).parent.parent.parent / "web_dashboard"
    if str(dashboard_dir) not in sys.path:
        sys.path.insert(0, str(dashboard_dir))
    
    try:
        from server import start_server
        start_server(open_browser=True)
    except Exception as e:
        print(f"❌ Failed to start dashboard server: {e}")

def _cmd_notify(args):
    msg = " ".join(args.message) if isinstance(args.message, list) else args.message
    title = args.title or "Code Alarm"
    print(f"\n🔔 Sending alert: {title} - {msg}")
    trigger_laptop_alert(
        title=title,
        message=msg,
        pattern="SUCCESS",
        voice=args.voice,
        voice_message=msg
    )
    print("✅ Alert triggered!\n")

def main():
    parser = argparse.ArgumentParser(
        prog="code-alarm",
        description="Code Alarm V2: Intelligent Developer Execution & Alert System"
    )
    parser.add_argument("--voice", "-v", action="store_true", help="Enable spoken voice announcement via Windows TTS")

    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # `run` command
    parser_run = subparsers.add_parser("run", help="Run a command and monitor execution")
    parser_run.add_argument("--tag", "-t", type=str, default=None, help="Custom task name")
    parser_run.add_argument("--voice", "-v", action="store_true", help="Enable spoken voice announcement")
    parser_run.add_argument("cmd", nargs=argparse.REMAINDER, help="The command to execute")

    # `summary` command (Level 1)
    subparsers.add_parser("summary", help="Display Level 1 Quick Aggregate Job Summary")

    # `list` command
    parser_list = subparsers.add_parser("list", help="List recent execution jobs")
    parser_list.add_argument("--limit", "-n", type=int, default=20, help="Number of jobs to list")

    # `details` command (Level 2)
    parser_details = subparsers.add_parser("details", help="Display Level 2 Job Details")
    parser_details.add_argument("job_id", type=str, help="Job ID to inspect")

    # `analyze` command (Level 3)
    parser_analyze = subparsers.add_parser("analyze", help="Display Level 3 Execution Failure Analysis")
    parser_analyze.add_argument("job_id", type=str, help="Job ID to analyze")

    # `settings` command
    subparsers.add_parser("settings", help="Display the 7 Alert Control Center settings")

    # `set` command
    parser_set = subparsers.add_parser("set", help="Update a specific Alert Control Center setting")
    parser_set.add_argument("setting", type=str, help="Setting name (e.g. master_alert_system, quiet_mode, success_sound)")
    parser_set.add_argument("value", type=str, choices=["on", "off", "true", "false", "1", "0"], help="on or off")

    # `quiet` command
    parser_quiet = subparsers.add_parser("quiet", help="Toggle Quiet Mode")
    parser_quiet.add_argument("state", type=str, choices=["on", "off"], help="on or off")

    # `master` command
    parser_master = subparsers.add_parser("master", help="Toggle Master Alert System")
    parser_master.add_argument("state", type=str, choices=["on", "off"], help="on or off")

    # `test` command
    parser_test = subparsers.add_parser("test", help="Test laptop buzzer tones & toast notifications")
    parser_test.add_argument("sound", nargs="?", default="SUCCESS", choices=["SUCCESS", "ERROR", "TRAIN_DONE", "ALERT"], help="Sound pattern to test")
    parser_test.add_argument("--voice", "-v", action="store_true", help="Enable voice announcement")

    # `notify` command
    parser_notify = subparsers.add_parser("notify", help="Send a custom alert message directly to your desktop")
    parser_notify.add_argument("message", nargs="+", help="Message text")
    parser_notify.add_argument("--title", type=str, default="Code Alarm", help="Notification title")
    parser_notify.add_argument("--voice", "-v", action="store_true", help="Speak the message")

    # `dashboard` command
    subparsers.add_parser("dashboard", help="Launch the Code Alarm V2 Web Dashboard & REST API server")

    # Shorthand fallback: e.g. `code-alarm python train.py`
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        known_cmds = ["run", "summary", "list", "details", "analyze", "settings", "set", "quiet", "master", "test", "notify", "dashboard", "-h", "--help"]
        if first_arg not in known_cmds:
            voice_enabled = False
            cmd_args = sys.argv[1:]
            if "--voice" in cmd_args or "-v" in cmd_args:
                voice_enabled = True
                cmd_args = [a for a in cmd_args if a not in ("--voice", "-v")]

            if cmd_args:
                exit_code = run_command(cmd_args, voice=voice_enabled)
                sys.exit(exit_code)

    args = parser.parse_args()

    if args.command == "run":
        if not args.cmd:
            print("Error: No command specified to run. Example: code-alarm run python train.py")
            sys.exit(1)
        exit_code = run_command(args.cmd, tag=args.tag, voice=args.voice)
        sys.exit(exit_code)
    elif args.command == "summary":
        _cmd_summary(args)
    elif args.command == "list":
        _cmd_list(args)
    elif args.command == "details":
        _cmd_details(args)
    elif args.command == "analyze":
        _cmd_analyze(args)
    elif args.command == "settings":
        _cmd_settings(args)
    elif args.command == "set":
        _cmd_set(args)
    elif args.command == "quiet":
        _cmd_quiet(args)
    elif args.command == "master":
        _cmd_master(args)
    elif args.command == "test":
        _cmd_test(args)
    elif args.command == "notify":
        _cmd_notify(args)
    elif args.command == "dashboard":
        _cmd_dashboard(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
