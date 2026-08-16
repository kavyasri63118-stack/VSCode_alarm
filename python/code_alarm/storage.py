"""
Persistent Storage Engine for Code Alarm V2 (SQLite)
Thread-safe, offline, portable across Windows, macOS, and Linux.
Stores structured execution history, status, and failure metadata.
"""

import os
import sys
import time
import sqlite3
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# ── Safe Portable Directory Resolution ─────────────────────────────────────────
def get_code_alarm_dir() -> Path:
    """
    Resolve the user-specific storage directory safely across all platforms.
    Prioritizes CODE_ALARM_DIR environment override if set.
    """
    env_dir = os.environ.get("CODE_ALARM_DIR")
    if env_dir:
        target = Path(env_dir)
    else:
        # User home directory + .code_alarm
        target = Path.home() / ".code_alarm"
    
    target.mkdir(parents=True, exist_ok=True)
    return target

def get_db_path() -> Path:
    return get_code_alarm_dir() / "history.db"


class StorageManager:
    """
    Thread-safe SQLite database manager for tracking multi-job executions.
    """
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StorageManager, cls).__new__(cls)
                cls._instance._init_db()
            return cls._instance

    def _get_connection(self) -> sqlite3.Connection:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path), timeout=15.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    command TEXT NOT NULL,
                    program TEXT NOT NULL,
                    cwd TEXT,
                    language TEXT,
                    source TEXT DEFAULT 'cli',
                    start_time REAL NOT NULL,
                    end_time REAL,
                    runtime_seconds REAL,
                    status TEXT NOT NULL,
                    exit_code INTEGER,
                    stdout_summary TEXT,
                    stderr_summary TEXT,
                    error_type TEXT,
                    likely_cause TEXT,
                    suggested_action TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_start_time ON jobs(start_time)")
                conn.commit()

    def create_job(
        self,
        job_id: str,
        command: str,
        program: str,
        cwd: Optional[str] = None,
        language: Optional[str] = None,
        source: str = "cli",
        start_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """Record a newly started job with status RUNNING."""
        st = start_time or time.time()
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO jobs (
                    job_id, command, program, cwd, language, source,
                    start_time, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'RUNNING')
                """, (job_id, command, program, cwd or os.getcwd(), language or "Generic", source, st))
                conn.commit()
        return self.get_job(job_id) or {}

    def update_job_status(self, job_id: str, status: str):
        """Update job status (e.g. RUNNING, TERMINATED)."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE jobs SET status = ? WHERE job_id = ?", (status, job_id))
                conn.commit()

    def finish_job(
        self,
        job_id: str,
        end_time: float,
        runtime_seconds: float,
        status: str,
        exit_code: int,
        stdout_summary: str = "",
        stderr_summary: str = "",
        error_type: Optional[str] = None,
        likely_cause: Optional[str] = None,
        suggested_action: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Record the completion / failure / crash details of a job."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                UPDATE jobs SET
                    end_time = ?,
                    runtime_seconds = ?,
                    status = ?,
                    exit_code = ?,
                    stdout_summary = ?,
                    stderr_summary = ?,
                    error_type = ?,
                    likely_cause = ?,
                    suggested_action = ?
                WHERE job_id = ?
                """, (
                    end_time,
                    runtime_seconds,
                    status,
                    exit_code,
                    stdout_summary,
                    stderr_summary,
                    error_type,
                    likely_cause,
                    suggested_action,
                    job_id
                ))
                conn.commit()
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full details of a specific job by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def list_jobs(self, limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List recent jobs with optional status filter."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM jobs WHERE status = ? ORDER BY start_time DESC LIMIT ?", (status, limit))
            else:
                cursor.execute("SELECT * FROM jobs ORDER BY start_time DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def get_running_jobs(self) -> List[Dict[str, Any]]:
        """Retrieve all currently active / running jobs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE status = 'RUNNING' ORDER BY start_time ASC")
            return [dict(r) for r in cursor.fetchall()]

    def get_quick_summary(self) -> Dict[str, Any]:
        """
        Level 1 Aggregate Summary:
        Computes Today's and All-Time statistics for Completed, Failed, Crashed, Running, Total Runtime.
        """
        now = datetime.now()
        start_of_today = datetime(now.year, now.month, now.day).timestamp()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Today stats
            cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'CRASHED' THEN 1 ELSE 0 END) as crashed,
                SUM(CASE WHEN status = 'RUNNING' THEN 1 ELSE 0 END) as running,
                SUM(CASE WHEN status = 'TERMINATED' THEN 1 ELSE 0 END) as terminated,
                COALESCE(SUM(runtime_seconds), 0.0) as total_runtime
            FROM jobs
            WHERE start_time >= ?
            """, (start_of_today,))
            today_row = dict(cursor.fetchone())

            # All-time stats
            cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'CRASHED' THEN 1 ELSE 0 END) as crashed,
                SUM(CASE WHEN status = 'RUNNING' THEN 1 ELSE 0 END) as running,
                COALESCE(SUM(runtime_seconds), 0.0) as total_runtime
            FROM jobs
            """)
            all_time_row = dict(cursor.fetchone())

        return {
            "today": today_row,
            "all_time": all_time_row,
            "generated_at": time.time()
        }

# Global singleton storage instance
storage = StorageManager()
