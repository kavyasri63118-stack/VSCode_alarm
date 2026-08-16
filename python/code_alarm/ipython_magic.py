"""
IPython & Jupyter Notebook Magic for VS Code (Code Alarm V2)
Provides:
- Cell Magic `%%alarm`
- Global Auto-Notify Hooks `%alarm_on` & `%alarm_off`
Alerts via speaker chimes and Windows toast notifications, and records jobs in central history.
"""

import time
import uuid
import argparse
from typing import Optional
from .laptop_alerts import trigger_laptop_alert
from .storage import storage
from .config import config
from .intelligence import FailureIntelligence

try:
    from IPython.core.magic import Magics, magics_class, cell_magic, line_magic
    from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
    from IPython import get_ipython
    HAS_IPYTHON = True
except ImportError:
    HAS_IPYTHON = False

# Global state for notebook auto-notify hooks
_auto_alarm_enabled = False
_auto_min_seconds = 3.0  # Only notify if cell ran >= 3 seconds
_auto_voice = False
_cell_start_time = 0.0
_cell_job_id = ""

if HAS_IPYTHON:
    @magics_class
    class CodeAlarmMagics(Magics):
        """IPython Magics for Code-Completion Alarm."""

        @magic_arguments()
        @argument("-t", "--title", type=str, default=None, help="Custom title for desktop notification")
        @argument("-v", "--voice", action="store_true", help="Enable spoken voice announcement")
        @argument("-m", "--min-seconds", type=float, default=0.0, help="Minimum execution time in seconds to trigger alert")
        @cell_magic
        def alarm(self, line, cell):
            """
            Cell Magic: Times cell execution and triggers laptop alarm ONLY after execution completes.
            
            Usage:
                %%alarm
                train_model()

                %%alarm -v -t "ResNet Training"
                fit_network()
            """
            args = parse_argstring(self.alarm, line)
            title = args.title or "Jupyter Cell"
            voice = args.voice
            min_sec = args.min_seconds

            start_t = time.time()
            job_id = f"job_{int(start_t)}_{uuid.uuid4().hex[:6]}"
            storage.create_job(
                job_id=job_id,
                command=f"%%alarm\n{cell[:80]}",
                program=title,
                language="Python",
                source="jupyter",
                start_time=start_t
            )

            error_occurred = False
            error_msg = ""

            try:
                # Execute the cell inside the notebook namespace
                self.shell.run_cell(cell)
            except Exception as e:
                error_occurred = True
                error_msg = f"{type(e).__name__}: {e}"
                raise e
            finally:
                end_t = time.time()
                elapsed = end_t - start_t
                status = "FAILED" if error_occurred else "SUCCESS"
                
                # Check if duration meets minimum threshold for alert
                if elapsed >= min_sec:
                    if error_occurred:
                        trigger_laptop_alert(
                            title="Code Alarm",
                            message=f"{title} failed\n{error_msg[:40]}\nClick for details",
                            pattern="ERROR",
                            voice=voice,
                            voice_message=f"{title} failed after {elapsed:.1f} seconds"
                        )
                    else:
                        pattern = "TRAIN_DONE" if elapsed > 30 else "SUCCESS"
                        trigger_laptop_alert(
                            title="Code Alarm",
                            message=f"{title} completed successfully\nRuntime: {elapsed:.2f}s",
                            pattern=pattern,
                            voice=voice,
                            voice_message=f"{title} completed in {elapsed:.1f} seconds"
                        )

                diag = FailureIntelligence.analyze(1, error_msg, language="Python") if (error_occurred and config.is_intelligence_enabled()) else {}
                storage.finish_job(
                    job_id=job_id,
                    end_time=end_t,
                    runtime_seconds=elapsed,
                    status=status,
                    exit_code=1 if error_occurred else 0,
                    stderr_summary=error_msg,
                    error_type=diag.get("error_type") if error_occurred else None,
                    likely_cause=diag.get("likely_cause") if error_occurred else None,
                    suggested_action=diag.get("suggested_action") if error_occurred else None
                )

        @line_magic
        def alarm_on(self, line):
            """
            Enable automatic alarm for EVERY cell in this notebook that takes longer than min_seconds.
            
            Usage:
                %alarm_on
                %alarm_on --min 5
                %alarm_on --voice
            """
            global _auto_alarm_enabled, _auto_min_seconds, _auto_voice
            _auto_alarm_enabled = True
            
            args = line.strip().split()
            if "--voice" in args or "-v" in args:
                _auto_voice = True
            else:
                _auto_voice = False

            for i, arg in enumerate(args):
                if arg in ("--min", "-m") and i + 1 < len(args):
                    try:
                        _auto_min_seconds = float(args[i + 1])
                    except ValueError:
                        pass

            print(f"🔔 Code-Alarm Auto-Notifier ENABLED (Threshold: >= {_auto_min_seconds}s, Voice: {_auto_voice})")
            print("   Every notebook cell will now chime & notify when execution completes!")

        @line_magic
        def alarm_off(self, line):
            """Disable automatic notebook cell alarm."""
            global _auto_alarm_enabled
            _auto_alarm_enabled = False
            print("🔕 Code-Alarm Auto-Notifier DISABLED.")


def _pre_cell_run_hook(*args, **kwargs):
    global _cell_start_time, _cell_job_id
    _cell_start_time = time.time()
    _cell_job_id = f"job_{int(_cell_start_time)}_{uuid.uuid4().hex[:6]}"
    storage.create_job(
        job_id=_cell_job_id,
        command="Jupyter Notebook Cell",
        program="Notebook Cell",
        language="Python",
        source="jupyter_hook",
        start_time=_cell_start_time
    )


def _post_cell_run_hook(result):
    """Triggered by IPython strictly AFTER any cell finishes execution."""
    global _auto_alarm_enabled, _auto_min_seconds, _auto_voice, _cell_start_time, _cell_job_id
    
    if not _auto_alarm_enabled:
        return

    end_t = time.time()
    elapsed = end_t - _cell_start_time
    
    is_error = result.error_in_exec is not None if hasattr(result, "error_in_exec") else False
    err_type = type(result.error_in_exec).__name__ if is_error else None
    err_str = str(result.error_in_exec) if is_error else ""

    # Only alert if cell took longer than the configured threshold
    if elapsed >= _auto_min_seconds:
        if is_error:
            trigger_laptop_alert(
                title="Code Alarm",
                message=f"Notebook cell failed\n{err_type}\nClick for details",
                pattern="ERROR",
                voice=_auto_voice,
                voice_message=f"Cell failed after {elapsed:.1f} seconds"
            )
        else:
            pattern = "TRAIN_DONE" if elapsed > 30 else "SUCCESS"
            trigger_laptop_alert(
                title="Code Alarm",
                message=f"Notebook cell completed successfully\nRuntime: {elapsed:.2f}s",
                pattern=pattern,
                voice=_auto_voice,
                voice_message=f"Notebook cell completed in {elapsed:.1f} seconds"
            )

    diag = FailureIntelligence.analyze(1, f"{err_type}: {err_str}", language="Python") if (is_error and config.is_intelligence_enabled()) else {}
    storage.finish_job(
        job_id=_cell_job_id,
        end_time=end_t,
        runtime_seconds=elapsed,
        status="FAILED" if is_error else "SUCCESS",
        exit_code=1 if is_error else 0,
        stderr_summary=f"{err_type}: {err_str}" if is_error else "",
        error_type=diag.get("error_type") if is_error else None,
        likely_cause=diag.get("likely_cause") if is_error else None,
        suggested_action=diag.get("suggested_action") if is_error else None
    )


def load_ipython_extension(ipython):
    """Called when user runs `%load_ext code_alarm` in a Jupyter Notebook."""
    if not HAS_IPYTHON:
        return

    magics = CodeAlarmMagics(ipython)
    ipython.register_magics(magics)

    try:
        ipython.events.register("pre_run_cell", _pre_cell_run_hook)
        ipython.events.register("post_run_cell", _post_cell_run_hook)
    except Exception:
        pass

    print("🔔 Code-Alarm extension loaded! Use `%%alarm` or `%alarm_on` in your cells.")


def unload_ipython_extension(ipython):
    """Called when user unloads extension."""
    try:
        ipython.events.unregister("pre_run_cell", _pre_cell_run_hook)
        ipython.events.unregister("post_run_cell", _post_cell_run_hook)
    except Exception:
        pass
