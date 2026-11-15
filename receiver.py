"""Local HTTP receiver for CI test reports.

Listens on http://localhost:8000. When the CI pipeline POSTs a JSON report,
it is saved as test-report.json (latest run) and also copied to
reports/<run_id>-<status>.json so every run is kept.

If a token is set (REPORT_TOKEN environment variable, or a .report_token file
next to this script), requests must send the same value in the
X-Report-Token header; others are rejected.
"""
import hmac
import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_FILE = os.path.join(BASE_DIR, "test-report.json")
HISTORY_DIR = os.path.join(BASE_DIR, "reports")
PORT = int(os.environ.get("RECEIVER_PORT", "8000"))
TOKEN_FILE = os.path.join(BASE_DIR, ".report_token")
TOKEN = os.environ.get("REPORT_TOKEN", "")
if not TOKEN and os.path.exists(TOKEN_FILE):
    with open(TOKEN_FILE, encoding="utf-8") as f:
        TOKEN = f.read().strip()
MAX_SIZE = 1_000_000  # 1 MB


class ReportHandler(BaseHTTPRequestHandler):
    def reply(self, code, message):
        body = json.dumps({"message": message}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.reply(200, "Receiver is running. POST test reports to this URL.")

    def do_POST(self):
        if TOKEN and not hmac.compare_digest(self.headers.get("X-Report-Token", ""), TOKEN):
            return self.reply(401, "Invalid or missing token.")

        length = int(self.headers.get("Content-Length") or 0)
        if not 0 < length <= MAX_SIZE:
            return self.reply(400, "Empty or too large body.")

        try:
            report = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            return self.reply(400, "Body is not valid JSON.")
        if not isinstance(report, dict) or "tests" not in report:
            return self.reply(400, "JSON is not a test report.")

        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        os.makedirs(HISTORY_DIR, exist_ok=True)
        run_id = "".join(c for c in str(report.get("run_id", "unknown")) if c.isalnum())
        status = "passed" if report.get("status") == "passed" else "failed"
        with open(os.path.join(HISTORY_DIR, f"{run_id}-{status}.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        s = report.get("summary", {})
        print(
            f"[{datetime.now():%H:%M:%S}] Report saved: {status.upper()} | "
            f"commit {str(report.get('commit_sha', ''))[:7]} | run {run_id} | "
            f"{s.get('passed')}/{s.get('total')} passed, {s.get('failed')} failed"
        )
        self.reply(200, "Report saved.")

    def log_message(self, fmt, *args):
        pass  # keep the console clean; reports are printed above


if __name__ == "__main__":
    print(f"Receiver listening on http://localhost:{PORT}")
    print("Token check:", "ON" if TOKEN else "OFF (set REPORT_TOKEN to enable)")
    print(f"Reports will be saved to {REPORT_FILE}")
    HTTPServer(("127.0.0.1", PORT), ReportHandler).serve_forever()
