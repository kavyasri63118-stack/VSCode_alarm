"""
Process Runner for Code Alarm V2
Executes commands with:
1. True zero-latency real-time live terminal streaming to stdout/stderr.
2. Concurrent output buffering for history and Failure Intelligence.
3. Fast alert triggering immediately upon process exit.
4. Multi-job SQLite tracking and deterministic status classification.
5. Strict respect for Alert Control Center settings.
"""

import sys
import os
import time
import uuid
import subprocess
import threading
from typing import List, Optional, Union

from .storage import storage
from .config import config
from .intelligence import FailureIntelligence
from .laptop_alerts import trigger_laptop_alert

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Simple ANSI color helpers
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

def _detect_language(cmd: str) -> str:
    lower = cmd.lower()
    if any(x in lower for x in ("python", ".py", "pytest")):
        return "Python"
    if any(x in lower for x in ("g++", "gcc", "clang", ".cpp", ".c", ".h")):
        return "C/C++"
    if any(x in lower for x in ("flutter", "dart", ".dart")):
        return "Dart/Flutter"
    if any(x in lower for x in ("npm", "node", "yarn", "pnpm", "npx", ".js", ".ts")):
        return "JavaScript/Node"
    if any(x in lower for x in ("cargo", "rustc", ".rs")):
        return "Rust"
    if any(x in lower for x in ("javac", "java", ".java", "gradle", "mvn")):
        return "Java"
    if any(x in lower for x in ("go run", "go build", ".go")):
        return "Go"
    if any(x in lower for x in ("zig run", "zig build", ".zig")):
        return "Zig"
    return "Generic"

def _format_duration(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = seconds % 60
    if hrs > 0:
        return f"{hrs}h {mins:02d}m {secs:04.1f}s"
    elif mins > 0:
        return f"{mins}m {secs:04.1f}s"
    else:
        return f"{secs:.2f}s"

def run_command(
    command: Union[str, List[str]],
    tag: Optional[str] = None,
    voice: bool = False,
    source: str = "cli"
) -> int:
    """
    Run arbitrary CLI command with zero-latency live output streaming,
    multi-job tracking, failure intelligence, and alert dispatch.
    """
    if isinstance(command, str):
        cmd_str = command
    else:
        cmd_str = subprocess.list2cmdline(command)
    task_name = tag or os.path.basename(cmd_str.split()[0] if cmd_str else "Command")
    language = _detect_language(cmd_str)

    # 1. Generate unique Job ID and register RUNNING state
    job_id = f"job_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    start_time = time.time()
    storage.create_job(
        job_id=job_id,
        command=cmd_str,
        program=task_name,
        cwd=os.getcwd(),
        language=language,
        source=source,
        start_time=start_time
    )

    display_tag = f" [{tag}]" if tag else ""
    print(f"\n{CYAN}{BOLD}+------------------------------------------------------------+{RESET}")
    print(f"{CYAN}{BOLD}| [!] CODE ALARM V2 MONITORING{display_tag:<31}|{RESET}")
    print(f"{CYAN}{BOLD}| >> Job ID : {job_id:<47}|{RESET}")
    print(f"{CYAN}{BOLD}| >> Running: {cmd_str[:45]:<47}|{RESET}")
    print(f"{CYAN}{BOLD}+------------------------------------------------------------+{RESET}\n", flush=True)

    exit_code = 1
    captured_output_bytes = bytearray()

    # 2. Execute process with real-time live streaming to user's terminal
    try:
        process = subprocess.Popen(
            cmd_str,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=sys.stdin,
            bufsize=0
        )

        # Stream stdout in real-time with zero delay
        if process.stdout:
            while True:
                # Read chunks immediately
                chunk = process.stdout.read(1024)
                if not chunk:
                    break
                try:
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.buffer.flush()
                except Exception:
                    sys.stdout.write(chunk.decode("utf-8", errors="replace"))
                    sys.stdout.flush()
                captured_output_bytes.extend(chunk)

        process.wait()
        exit_code = process.returncode if process.returncode is not None else 0

    except KeyboardInterrupt:
        print(f"\n{YELLOW}[CODE-ALARM] Process interrupted by user (Ctrl+C){RESET}", flush=True)
        exit_code = 130
    except Exception as e:
        print(f"\n{RED}[CODE-ALARM] Execution error: {e}{RESET}", flush=True)
        exit_code = 1

    end_time = time.time()
    elapsed = end_time - start_time
    duration_str = _format_duration(elapsed)

    # 3. Decode captured output for error analysis
    captured_text = captured_output_bytes.decode("utf-8", errors="replace")

    # 4. Determine reliable status
    status = FailureIntelligence.classify_status(exit_code, captured_text)

    # 5. Fast Alert Triggering (Do not make user wait for heavy DB/analysis)
    print()
    if status == "SUCCESS":
        print(f"{GREEN}{BOLD}============================================================{RESET}")
        print(f"{GREEN}{BOLD} ✅ SUCCESS in {duration_str} (Exit Code: 0) -> 🔔 Alert Triggered!{RESET}")
        print(f"{GREEN}{BOLD}============================================================{RESET}", flush=True)

        pattern = "TRAIN_DONE" if elapsed > 30 else "SUCCESS"
        title = f"Code Alarm"
        msg = f"{task_name} completed successfully\nRuntime: {duration_str}"
        voice_msg = f"Task {task_name} completed successfully in {duration_str}"

        trigger_laptop_alert(
            title=title,
            message=msg,
            pattern=pattern,
            voice=voice,
            voice_message=voice_msg
        )

    elif status == "CRASHED":
        print(f"{MAGENTA}{BOLD}============================================================{RESET}")
        print(f"{MAGENTA}{BOLD} 💥 CRASHED in {duration_str} (Exit Code: {exit_code}) -> ⚠️ Warning Alert!{RESET}")
        print(f"{MAGENTA}{BOLD}============================================================{RESET}", flush=True)

        title = f"Code Alarm"
        msg = f"{task_name} crashed (Exit: {exit_code})\nClick for details"
        voice_msg = f"Task {task_name} crashed"

        trigger_laptop_alert(
            title=title,
            message=msg,
            pattern="ERROR",
            voice=voice,
            voice_message=voice_msg
        )

    elif status == "TERMINATED":
        print(f"{YELLOW}{BOLD}============================================================{RESET}")
        print(f"{YELLOW}{BOLD} ⏹️ TERMINATED in {duration_str} (Cancelled by User){RESET}")
        print(f"{YELLOW}{BOLD}============================================================{RESET}", flush=True)

    else:  # FAILED
        print(f"{RED}{BOLD}============================================================{RESET}")
        print(f"{RED}{BOLD} ❌ FAILED in {duration_str} (Exit Code: {exit_code}) -> ⚠️ Warning Alert!{RESET}")
        print(f"{RED}{BOLD}============================================================{RESET}", flush=True)

        title = f"Code Alarm"
        # Extract error type for short notification if available
        quick_diag = FailureIntelligence.analyze(exit_code, captured_text) if config.is_intelligence_enabled() else {}
        err_header = quick_diag.get("error_type", "Failed")
        msg = f"{task_name} failed\n{err_header}\nClick for details"
        voice_msg = f"Task {task_name} failed"

        trigger_laptop_alert(
            title=title,
            message=msg,
            pattern="ERROR",
            voice=voice,
            voice_message=voice_msg
        )

    # 6. Detailed Failure Intelligence & Storage Update
    diag = {}
    if status in ("FAILED", "CRASHED") and config.is_intelligence_enabled():
        diag = FailureIntelligence.analyze(exit_code, captured_text, language=language)

    # Keep summary of output (last 20KB to avoid excessive storage)
    out_summary = captured_text[-20000:] if len(captured_text) > 20000 else captured_text

    storage.finish_job(
        job_id=job_id,
        end_time=end_time,
        runtime_seconds=elapsed,
        status=status,
        exit_code=exit_code,
        stdout_summary=out_summary,
        stderr_summary="",
        error_type=diag.get("error_type"),
        likely_cause=diag.get("likely_cause"),
        suggested_action=diag.get("suggested_action")
    )

    # Brief delay for audio playback to complete cleanly
    time.sleep(0.4)
    return exit_code
