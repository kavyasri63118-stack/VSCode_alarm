"""
Three-Level Job Summary Engine for Code Alarm V2
Provides:
Level 1: Quick Aggregate Summary
Level 2: Individual Job Details
Level 3: Deep Execution & Failure Analysis
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional
from .storage import storage

def format_duration(seconds: Optional[float]) -> str:
    if seconds is None or seconds <= 0:
        return "0.0s"
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = seconds % 60
    if hrs > 0:
        return f"{hrs}h {mins:02d}m {secs:04.1f}s"
    elif mins > 0:
        return f"{mins}m {secs:04.1f}s"
    else:
        return f"{secs:.2f}s"

def format_timestamp(ts: Optional[float]) -> str:
    if not ts:
        return "N/A"
    return datetime.fromtimestamp(ts).strftime("%I:%M:%S %p")

class JobSummaryEngine:
    """
    Formats the 3-level job summaries for CLI and Dashboard presentation.
    """

    @classmethod
    def get_level1_summary(cls) -> str:
        """
        Level 1: Quick Summary CLI format.
        """
        data = storage.get_quick_summary()
        today = data.get("today", {})
        all_time = data.get("all_time", {})

        today_completed = today.get("completed", 0) or 0
        today_failed = today.get("failed", 0) or 0
        today_crashed = today.get("crashed", 0) or 0
        today_running = today.get("running", 0) or 0
        today_runtime = format_duration(today.get("total_runtime", 0.0))

        lines = [
            "╔══════════════════════════════════════════════════════════╗",
            "║                  📊 JOB SUMMARY: TODAY                   ║",
            "╠══════════════════════════════════════════════════════════╣",
            f"║  ✅ Completed : {today_completed:<6}                               ║",
            f"║  ❌ Failed    : {today_failed:<6}                               ║",
            f"║  💥 Crashed   : {today_crashed:<6}                               ║",
            f"║  🔄 Running   : {today_running:<6}                               ║",
            f"║  ⏱️  Total Time: {today_runtime:<40} ║",
            "╠══════════════════════════════════════════════════════════╣",
            f"║  All-Time Total Jobs: {all_time.get('total', 0):<34} ║",
            "╚══════════════════════════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @classmethod
    def get_level2_details(cls, job_id: str) -> Optional[str]:
        """
        Level 2: Job Details CLI format.
        """
        job = storage.get_job(job_id)
        if not job:
            return None

        status = job.get("status", "UNKNOWN")
        status_icon = "✅" if status == "SUCCESS" else ("❌" if status == "FAILED" else ("💥" if status == "CRASHED" else "🔄"))
        runtime_str = format_duration(job.get("runtime_seconds"))
        start_str = format_timestamp(job.get("start_time"))
        end_str = format_timestamp(job.get("end_time"))

        lines = [
            "╔══════════════════════════════════════════════════════════╗",
            f"║ 📄 JOB DETAILS: {job.get('program', 'Command')[:38]:<39} ║",
            "╠══════════════════════════════════════════════════════════╣",
            f"║ Job ID   : {job.get('job_id'):<45} ║",
            f"║ Command  : {job.get('command', '')[:45]:<45} ║",
            f"║ Status   : {status_icon} {status:<42} ║",
            f"║ Runtime  : {runtime_str:<45} ║",
            f"║ Started  : {start_str:<45} ║",
            f"║ Finished : {end_str:<45} ║",
            f"║ Language : {job.get('language', 'Generic'):<45} ║",
            f"║ Exit Code: {str(job.get('exit_code', 'N/A')):<45} ║",
            f"║ Directory: {job.get('cwd', '')[:45]:<45} ║",
            "╚══════════════════════════════════════════════════════════╝"
        ]
        return "\n".join(lines)

    @classmethod
    def get_level3_analysis(cls, job_id: str) -> Optional[str]:
        """
        Level 3: Deep Execution & Failure Analysis CLI format.
        """
        job = storage.get_job(job_id)
        if not job:
            return None

        status = job.get("status", "UNKNOWN")
        error_type = job.get("error_type") or "Unknown execution error"
        likely_cause = job.get("likely_cause") or "Process exited with an error."
        suggested_action = job.get("suggested_action") or "Review logs for more information."
        stderr = job.get("stderr_summary") or job.get("stdout_summary") or "No captured error text."

        lines = [
            "╔══════════════════════════════════════════════════════════╗",
            "║                🔍 EXECUTION FAILURE ANALYSIS             ║",
            "╠══════════════════════════════════════════════════════════╣",
            f"║ Job      : {job.get('program', 'Command')[:45]:<45} ║",
            f"║ Status   : {status:<45} ║",
            f"║ Runtime  : {format_duration(job.get('runtime_seconds')):<45} ║",
            "╠══════════════════════════════════════════════════════════╣",
            f"║ ⚠️ ERROR TYPE:                                           ║",
            f"║   {error_type[:54]:<54} ║",
            "║                                                          ║",
            "║ 💡 LIKELY CAUSE:                                         ║",
            f"║   {likely_cause[:54]:<54} ║",
            "║                                                          ║",
            "║ 🛠️  SUGGESTED ACTION:                                     ║",
            f"║   {suggested_action[:54]:<54} ║",
            "╠══════════════════════════════════════════════════════════╣",
            "║ 📋 RECENT ERROR OUTPUT:                                  ║"
        ]
        # Append truncated error snippet
        for l in stderr.strip().splitlines()[-6:]:
            lines.append(f"║   {l[:54]:<54} ║")
        lines.append("╚══════════════════════════════════════════════════════════╝")
        return "\n".join(lines)
