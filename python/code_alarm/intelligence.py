"""
Rule-Based Failure Intelligence Engine for Code Alarm V2
Analyzes execution stdout/stderr and exit codes across Python, C/C++, JavaScript,
Dart/Flutter, Java, Rust, and Generic environments.
Strictly non-hallucinatory: Provides structured diagnosis only when evidence is clear.
"""

import re
import sys
from typing import Dict, Optional, Tuple

class FailureIntelligence:
    """
    Deterministic rule-based failure diagnosis engine.
    """

    @staticmethod
    def classify_status(exit_code: int, stderr: str = "", stdout: str = "") -> str:
        """
        Classify execution outcome into SUCCESS, FAILED, CRASHED, or TERMINATED.
        Crash is ONLY returned when reliable process-level crash evidence is present.
        """
        if exit_code == 0:
            return "SUCCESS"

        # User interruption / cancellation
        if exit_code in (130, -2, -15, 3221225786):  # 3221225786 is 0xC000013A (STATUS_CONTROL_C_EXIT)
            return "TERMINATED"

        combined = f"{stderr}\n{stdout}".lower()

        # Reliable Crash Signals:
        # Windows Access Violation: 0xC0000005 (or signed -1073741819 / unsigned 3221225477)
        # Windows Stack Overflow: 0xC00000FD (or -1073741571 / 3221225725)
        # Windows Abort: 0xC0000028
        crash_codes = {
            -1073741819, 3221225477, 0xC0000005,  # STATUS_ACCESS_VIOLATION
            -1073741571, 3221225725, 0xC00000FD,  # STATUS_STACK_OVERFLOW
            -1073741510, 3221225786, 0xC000013A,  # CONTROL_C
            -11,  # SIGSEGV (Linux/macOS)
            -6,   # SIGABRT
            -4,   # SIGILL
            -8,   # SIGFPE
            -7    # SIGBUS
        }

        if exit_code in crash_codes:
            if exit_code in (-1073741819, 3221225477, 0xC0000005, -11):
                return "CRASHED"
            if exit_code in (-1073741571, 3221225725, 0xC00000FD):
                return "CRASHED"
            if exit_code in (-6, -4, -8, -7):
                return "CRASHED"

        crash_keywords = [
            "segmentation fault",
            "sigsegv",
            "access violation",
            "fatal python error",
            "exception_access_violation",
            "status_stack_buffer_overrun",
            "core dumped",
            "abort() has been called",
            "pure virtual method called"
        ]

        for kw in crash_keywords:
            if kw in combined:
                return "CRASHED"

        # Default standard non-zero exit code
        return "FAILED"

    @classmethod
    def analyze(
        cls,
        exit_code: int,
        stdout: str = "",
        stderr: str = "",
        language: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Analyze stdout/stderr and produce (error_type, likely_cause, suggested_action).
        Returns deterministic diagnostic dictionary.
        """
        combined = f"{stderr}\n{stdout}".strip()
        if not combined and exit_code == 0:
            return {
                "error_type": "None",
                "likely_cause": "Process completed successfully.",
                "suggested_action": "No action required."
            }

        # ── 1. Python Rules ───────────────────────────────────────────────────
        # Python Startup: Can't open file / FileNotFoundError (Missing Script)
        m = re.search(r"can't open file\s+['\"]?(.+?)['\"]?:\s*\[Errno 2\]\s*No such file or directory", combined, re.IGNORECASE)
        if m:
            return {
                "error_type": "FileNotFoundError / Missing Python File",
                "likely_cause": "The specified Python script does not exist at the provided path.",
                "suggested_action": "Check the filename/path and current working directory, then run the correct script path."
            }

        # ModuleNotFoundError
        m = re.search(r"ModuleNotFoundError:\s+No module named\s+['\"]([^'\"]+)['\"]", combined)
        if m:
            pkg = m.group(1).split('.')[0]
            return {
                "error_type": "ModuleNotFoundError",
                "likely_cause": f"The Python package '{pkg}' is not installed in the active environment.",
                "suggested_action": f"Run `pip install {pkg}` or activate your project virtual environment."
            }

        # ImportError
        m = re.search(r"ImportError:\s+(.+)", combined)
        if m:
            return {
                "error_type": "ImportError",
                "likely_cause": f"Failed to import required symbol: {m.group(1).strip()}",
                "suggested_action": "Check for circular imports, spelling mistakes, or local filenames shadowing library names."
            }

        # SyntaxError
        m = re.search(r"SyntaxError:\s+(.+)", combined)
        if m:
            return {
                "error_type": "SyntaxError",
                "likely_cause": f"Invalid syntax encountered in Python script: {m.group(1).strip()}",
                "suggested_action": "Inspect the line number indicated in the traceback and fix missing colons, parentheses, or operators."
            }

        # IndentationError
        m = re.search(r"IndentationError:\s+(.+)", combined)
        if m:
            return {
                "error_type": "IndentationError",
                "likely_cause": f"Inconsistent tab or space indentation: {m.group(1).strip()}",
                "suggested_action": "Convert indentation to consistent 4 spaces."
            }

        # NameError
        m = re.search(r"NameError:\s+name\s+['\"]([^'\"]+)['\"]\s+is not defined", combined)
        if m:
            var_name = m.group(1)
            return {
                "error_type": "NameError",
                "likely_cause": f"Variable or function '{var_name}' is referenced before being defined or imported.",
                "suggested_action": f"Define or import '{var_name}' before using it."
            }

        # FileNotFoundError
        m = re.search(r"FileNotFoundError:\s+\[Errno 2\]\s+No such file or directory:\s+['\"]([^'\"]+)['\"]", combined)
        if m:
            target_f = m.group(1)
            return {
                "error_type": "FileNotFoundError",
                "likely_cause": f"The target file or directory '{target_f}' does not exist.",
                "suggested_action": f"Verify the file path exists or create '{target_f}'."
            }

        # PermissionError
        m = re.search(r"PermissionError:\s+\[Errno 13\]\s+(.+)", combined)
        if m:
            return {
                "error_type": "PermissionError",
                "likely_cause": f"Access denied: {m.group(1).strip()}",
                "suggested_action": "Check file permissions or verify that another process is not locking the file."
            }

        # MemoryError
        if "MemoryError" in combined:
            return {
                "error_type": "MemoryError",
                "likely_cause": "The system ran out of RAM or memory allocation exceeded OS limits.",
                "suggested_action": "Reduce batch size, use memory-mapped files/generators, or free system memory."
            }

        # ── 2. C / C++ Rules ──────────────────────────────────────────────────
        # Undefined Reference (Linker Error)
        m = re.search(r"undefined reference to\s+`([^']+)'", combined)
        if m:
            sym = m.group(1)
            return {
                "error_type": "LinkerError (Undefined Reference)",
                "likely_cause": f"The linker cannot find the implementation for symbol '{sym}'.",
                "suggested_action": "Include all relevant source `.cpp` files in the build command or link the missing library (`-l<lib>`)."
            }

        # Missing Header File
        m = re.search(r"fatal error:\s+([^:]+):\s+No such file or directory", combined)
        if m:
            hdr = m.group(1).strip()
            return {
                "error_type": "CompilationError (Missing Header)",
                "likely_cause": f"The C/C++ compiler could not locate header file '{hdr}'.",
                "suggested_action": f"Install the library containing '{hdr}' or add its include directory with `-I<path>`."
            }

        # Assignment of read-only variable
        m = re.search(r"error:\s+assignment of read-only variable\s+['\"]([^'\"]+)['\"]", combined)
        if m:
            var_name = m.group(1)
            return {
                "error_type": "CompilationError (Const Violation)",
                "likely_cause": f"Attempted to modify constant / read-only variable '{var_name}'.",
                "suggested_action": f"Remove the `const` qualifier on '{var_name}' or remove the assignment."
            }

        # General C/C++ compiler syntax error
        m = re.search(r"error:\s+(.+)", combined)
        if m and any(ext in combined for ext in (".c:", ".cpp:", ".h:", ".hpp:", "g++", "gcc", "clang")):
            return {
                "error_type": "CompilationError",
                "likely_cause": f"C/C++ compiler error: {m.group(1).strip()[:100]}",
                "suggested_action": "Check the line and column number reported by the compiler to resolve syntax or type mismatch."
            }

        # ── 3. JavaScript / Node.js Rules ─────────────────────────────────────
        m = re.search(r"Cannot find module\s+['\"]([^'\"]+)['\"]", combined)
        if m:
            mod = m.group(1)
            return {
                "error_type": "MODULE_NOT_FOUND",
                "likely_cause": f"Node.js package '{mod}' is not installed.",
                "suggested_action": f"Run `npm install {mod}` or `yarn add {mod}`."
            }

        if "npm ERR!" in combined:
            return {
                "error_type": "NpmError",
                "likely_cause": "NPM package installation or script execution failed.",
                "suggested_action": "Check `package.json` scripts, verify Node version compatibility, or run `npm install`."
            }

        # ── 4. Dart / Flutter Rules ───────────────────────────────────────────
        m = re.search(r"Target of URI doesn't exist:\s+['\"]([^'\"]+)['\"]", combined)
        if m:
            uri = m.group(1)
            return {
                "error_type": "DartMissingPackage",
                "likely_cause": f"Dart dependency '{uri}' is not resolved.",
                "suggested_action": "Run `flutter pub get` or add the package to `pubspec.yaml`."
            }

        # ── 5. Java Rules ─────────────────────────────────────────────────────
        m = re.search(r"ClassNotFoundException:\s+(\S+)", combined)
        if m:
            cls_name = m.group(1)
            return {
                "error_type": "ClassNotFoundException",
                "likely_cause": f"Java runtime could not locate class '{cls_name}'.",
                "suggested_action": "Verify your classpath (`-cp`) includes the compiled classes or `.jar` dependencies."
            }

        if "NullPointerException" in combined:
            return {
                "error_type": "NullPointerException",
                "likely_cause": "Attempted to invoke a method or access a field on a `null` reference.",
                "suggested_action": "Add null checks (`if (obj != null)`) or initialize the object before dereferencing."
            }

        # ── 6. Generic OS / Shell Rules ───────────────────────────────────────
        m = re.search(r"['\"]?([^'\"]+)['\"]?\s+is not recognized as an internal or external command", combined)
        if m:
            cmd = m.group(1).strip()
            return {
                "error_type": "CommandNotFound",
                "likely_cause": f"The program or command '{cmd}' was not found on your system PATH.",
                "suggested_action": f"Install '{cmd}' and ensure its installation directory is added to your Windows system PATH."
            }

        m = re.search(r"command not found:\s+(\S+)", combined)
        if m:
            cmd = m.group(1).strip()
            return {
                "error_type": "CommandNotFound",
                "likely_cause": f"The executable '{cmd}' was not found in PATH.",
                "suggested_action": f"Install '{cmd}' or verify system PATH."
            }

        # Crash fallback
        if cls.classify_status(exit_code, stderr, stdout) == "CRASHED":
            return {
                "error_type": "ProcessCrash",
                "likely_cause": f"Process terminated abnormally with exit code {exit_code} (access violation or signal).",
                "suggested_action": "Check for memory corruption, null pointer dereferences, stack overflows, or native library conflicts."
            }

        # Fallback for unrecognized failures
        raw_snippet = (stderr.strip() or stdout.strip() or f"Process returned non-zero exit code: {exit_code}")[:200]
        return {
            "error_type": "Unknown execution error",
            "likely_cause": f"Process exited with non-zero code {exit_code}.",
            "suggested_action": "Review the full captured output in the execution logs for details."
        }
