"""
Code Alarm V2: Intelligent Developer Execution & Alert System
Software-only audio chimes, Windows desktop notifications, multi-job tracking, and failure intelligence.
"""

import os
import time
import uuid
import functools
from typing import Optional, Callable

from .laptop_alerts import (
    trigger_laptop_alert,
    play_audio_alarm,
    show_desktop_notification,
    speak_voice_announcement
)
from .runner import run_command
from .storage import storage
from .config import config
from .intelligence import FailureIntelligence
from .summary import JobSummaryEngine
from .ipython_magic import load_ipython_extension, unload_ipython_extension

__version__ = "2.0.0"

def success(title: str = "Code Alarm", message: str = "Execution completed successfully", voice: bool = False):
    """Trigger laptop success chime + toast notification."""
    trigger_laptop_alert(title=title, message=message, pattern="SUCCESS", voice=voice)

def error(title: str = "Code Alarm", message: str = "Execution failed with an error", voice: bool = False):
    """Trigger laptop error warning chime + toast notification."""
    trigger_laptop_alert(title=title, message=message, pattern="ERROR", voice=voice)

def train_done(title: str = "Code Alarm", message: str = "Model training completed!", voice: bool = False):
    """Trigger laptop victory fanfare chime + toast notification."""
    trigger_laptop_alert(title=title, message=message, pattern="TRAIN_DONE", voice=voice)

def alert(message: str = "Code Alert", title: str = "Code Alarm", voice: bool = False):
    """Trigger laptop urgent alert chime + toast notification."""
    trigger_laptop_alert(title=title, message=message, pattern="ALERT", voice=voice)

class CodeAlarm:
    """
    Context manager for monitoring blocks of Python code with automatic job tracking and alerts.
    
    Example:
        with CodeAlarm("Training ResNet", voice=True):
            train_model()
    """
    def __init__(self, tag: Optional[str] = None, voice: bool = False):
        self.tag = tag or "Python Task"
        self.voice = voice
        self.start_time = 0.0
        self.job_id = ""

    def __enter__(self):
        self.start_time = time.time()
        self.job_id = f"job_{int(self.start_time)}_{uuid.uuid4().hex[:6]}"
        storage.create_job(
            job_id=self.job_id,
            command=f"with CodeAlarm('{self.tag}')",
            program=self.tag,
            cwd=os.getcwd(),
            language="Python",
            source="python_context",
            start_time=self.start_time
        )
        print(f"\n[🔔 CodeAlarm] Started monitoring: {self.tag} (ID: {self.job_id})...", flush=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        duration = end_time - self.start_time
        if exc_type is None:
            pattern = "TRAIN_DONE" if duration > 30 else "SUCCESS"
            print(f"[🔔 CodeAlarm] ✅ {self.tag} finished in {duration:.2f}s -> 🔔 Alert Triggered!", flush=True)
            trigger_laptop_alert(
                title="Code Alarm",
                message=f"{self.tag} completed successfully\nRuntime: {duration:.2f}s",
                pattern=pattern,
                voice=self.voice
            )
            storage.finish_job(
                job_id=self.job_id,
                end_time=end_time,
                runtime_seconds=duration,
                status="SUCCESS",
                exit_code=0
            )
        else:
            err_name = exc_type.__name__
            err_msg = str(exc_val)
            print(f"[🔔 CodeAlarm] ❌ {self.tag} failed after {duration:.2f}s with {err_name} -> ⚠️ Warning Alert!", flush=True)
            trigger_laptop_alert(
                title="Code Alarm",
                message=f"{self.tag} failed\n{err_name}\nClick for details",
                pattern="ERROR",
                voice=self.voice
            )
            diag = FailureIntelligence.analyze(1, f"{err_name}: {err_msg}", language="Python") if config.is_intelligence_enabled() else {}
            storage.finish_job(
                job_id=self.job_id,
                end_time=end_time,
                runtime_seconds=duration,
                status="FAILED",
                exit_code=1,
                stderr_summary=f"{err_name}: {err_msg}",
                error_type=diag.get("error_type", err_name),
                likely_cause=diag.get("likely_cause"),
                suggested_action=diag.get("suggested_action")
            )
        return False

def notify(name: Optional[str] = None, voice: bool = False):
    """
    Decorator to trigger laptop chime & toast alert when a function finishes or throws an exception.
    
    Example:
        @notify("Data Processing", voice=True)
        def process_large_dataset():
            ...
    """
    def decorator(func: Callable):
        func_tag = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            job_id = f"job_{int(start_time)}_{uuid.uuid4().hex[:6]}"
            storage.create_job(
                job_id=job_id,
                command=f"@{func_tag}()",
                program=func_tag,
                cwd=os.getcwd(),
                language="Python",
                source="python_decorator",
                start_time=start_time
            )
            print(f"\n[🔔 CodeAlarm] Running {func_tag}()...", flush=True)
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                duration = end_time - start_time
                pattern = "TRAIN_DONE" if duration > 30 else "SUCCESS"
                print(f"[🔔 CodeAlarm] ✅ {func_tag} finished in {duration:.2f}s -> 🔔 Alert Triggered!", flush=True)
                trigger_laptop_alert(
                    title="Code Alarm",
                    message=f"{func_tag} completed successfully\nRuntime: {duration:.2f}s",
                    pattern=pattern,
                    voice=voice
                )
                storage.finish_job(
                    job_id=job_id,
                    end_time=end_time,
                    runtime_seconds=duration,
                    status="SUCCESS",
                    exit_code=0
                )
                return result
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                err_name = type(e).__name__
                print(f"[🔔 CodeAlarm] ❌ {func_tag} failed after {duration:.2f}s -> ⚠️ Warning Alert!", flush=True)
                trigger_laptop_alert(
                    title="Code Alarm",
                    message=f"{func_tag} failed\n{err_name}\nClick for details",
                    pattern="ERROR",
                    voice=voice
                )
                diag = FailureIntelligence.analyze(1, f"{err_name}: {e}", language="Python") if config.is_intelligence_enabled() else {}
                storage.finish_job(
                    job_id=job_id,
                    end_time=end_time,
                    runtime_seconds=duration,
                    status="FAILED",
                    exit_code=1,
                    stderr_summary=f"{err_name}: {e}",
                    error_type=diag.get("error_type", err_name),
                    likely_cause=diag.get("likely_cause"),
                    suggested_action=diag.get("suggested_action")
                )
                raise e
        return wrapper
    return decorator
