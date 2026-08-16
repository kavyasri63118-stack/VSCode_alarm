"""
REST API & Web Server for Code Alarm V2 Dashboard
Provides API endpoints for multi-job monitoring, 3-level job summaries,
and the Alert Control Center.
Binds to 127.0.0.1 for secure local operation.
"""

import sys
import os
import json
import http.server
import socketserver
import webbrowser
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from typing import Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent / "python"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code_alarm.storage import storage
from code_alarm.config import config
from code_alarm.summary import JobSummaryEngine
from code_alarm.laptop_alerts import play_audio_alarm
from code_alarm.resources import get_dashboard_dir

PORT = 8088
HOST = "127.0.0.1"

# Callback function when a wake/open-dashboard signal is received from second instance
_on_wake_callback = None

def set_wake_callback(cb):
    global _on_wake_callback
    _on_wake_callback = cb

class CodeAlarmAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        directory = str(get_dashboard_dir())
        super().__init__(*args, directory=directory, **kwargs)

    def log_message(self, format, *args):
        # Suppress routine GET logging to avoid console clutter
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/ping":
            self._send_json({"status": "ok", "app": "CodeAlarm", "version": "2.0.0"})
            return

        if path == "/api/summary":
            summary = storage.get_quick_summary()
            self._send_json(summary)
            return

        if path == "/api/jobs":
            query = parse_qs(parsed.query)
            status = query.get("status", [None])[0]
            limit = int(query.get("limit", [50])[0])
            jobs = storage.list_jobs(limit=limit, status=status)
            self._send_json({"jobs": jobs, "total": len(jobs)})
            return

        if path.startswith("/api/jobs/"):
            job_id = path.split("/api/jobs/")[1]
            job = storage.get_job(job_id)
            if job:
                self._send_json({"job": job})
            else:
                self._send_json({"error": "Job not found"}, status=404)
            return

        if path == "/api/settings":
            raw_s = config.get_all()
            eff_s = config.get_effective_all()
            self._send_json({
                "settings": raw_s,
                "effective": eff_s,
                "quiet_mode": raw_s.get("quiet_mode", False),
                "master_alert_system": raw_s.get("master_alert_system", True)
            })
            return

        if path == "/api/running":
            running = storage.get_running_jobs()
            self._send_json({"running": running, "count": len(running)})
            return

        # Fall back to serving static files (index.html, style.css, app.js)
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            payload = json.loads(post_body.decode("utf-8"))
        except Exception:
            payload = {}

        if path == "/api/settings":
            updated = config.set_many(payload)
            self._send_json({"settings": updated, "message": "Settings updated successfully"})
            return

        if path == "/api/wake":
            if _on_wake_callback:
                try:
                    _on_wake_callback()
                except Exception:
                    pass
            self._send_json({"status": "ok", "message": "Window woken"})
            return

        if path == "/api/test-sound":
            pattern = payload.get("pattern", "SUCCESS")
            try:
                play_audio_alarm(pattern)
                self._send_json({"status": "ok", "played": pattern})
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        self._send_json({"error": "Endpoint not found"}, status=404)


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

_global_server = None

def start_server(open_browser: bool = True, host: str = HOST, port: int = PORT):
    global _global_server
    try:
        with ThreadingTCPServer((host, port), CodeAlarmAPIHandler) as httpd:
            _global_server = httpd
            url = f"http://{host}:{port}"
            print(f"\n[INFO] Code Alarm V2 Dashboard active at: {url}")
            if open_browser:
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n[INFO] Server stopped.")
    except Exception as e:
        print(f"[ERROR] Server exception on port {port}: {e}")

def stop_server():
    global _global_server
    if _global_server:
        try:
            _global_server.shutdown()
            _global_server.server_close()
        except Exception:
            pass
        _global_server = None

if __name__ == "__main__":
    start_server(open_browser=True)
