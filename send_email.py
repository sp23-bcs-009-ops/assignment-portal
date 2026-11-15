"""Email the CI test report.

Usage: python send_email.py report.json

Settings come from environment variables (set as GitHub secrets / variables):
  EMAIL_TO       recipient address (configurable)
  SMTP_USERNAME  sender login, e.g. your Gmail address
  SMTP_PASSWORD  SMTP password, e.g. a Gmail App Password
  SMTP_SERVER    optional, default smtp.gmail.com
  SMTP_PORT      optional, default 465 (SSL)
"""
import json
import os
import smtplib
import sys
from email.message import EmailMessage


def build_message(report, sender, recipient):
    s = report["summary"]
    status = report["status"].upper()
    icon = "PASSED" if status == "PASSED" else "FAILED"
    sha = report["commit_sha"]

    lines = [
        f"Overall result: {icon}",
        "",
        f"Repository: {report['repository']}",
        f"Branch:     {report['branch']}",
        f"Commit:     {sha}",
        f"Run:        {report['run_id']}  ({report['run_url']})",
        f"Executed:   {report['executed_at']}",
        "",
        f"Total: {s['total']}   Passed: {s['passed']}   Failed: {s['failed']}",
        "",
        "Individual results:",
    ]
    for t in report["tests"]:
        lines.append(f"  [{t['result'].upper()}] {t['name']}")
        if t.get("failure_message"):
            for msg_line in t["failure_message"].splitlines():
                lines.append(f"      {msg_line}")
    if report.get("error"):
        lines += ["", f"Error: {report['error']}"]

    msg = EmailMessage()
    msg["Subject"] = f"[CI {icon}] {report['repository']} @ {sha[:7]} - {s['passed']}/{s['total']} passed"
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content("\n".join(lines))
    msg.add_attachment(
        json.dumps(report, indent=2).encode(),
        maintype="application",
        subtype="json",
        filename="test-report.json",
    )
    return msg


def main():
    report_path = sys.argv[1] if len(sys.argv) > 1 else "report.json"
    recipient = os.environ.get("EMAIL_TO", "").strip()
    username = os.environ.get("SMTP_USERNAME", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "")
    if not (recipient and username and password):
        print("::warning::Email not sent: EMAIL_TO, SMTP_USERNAME or SMTP_PASSWORD is not set.")
        return

    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)

    server = os.environ.get("SMTP_SERVER") or "smtp.gmail.com"
    port = int(os.environ.get("SMTP_PORT") or 465)
    msg = build_message(report, username, recipient)
    with smtplib.SMTP_SSL(server, port, timeout=30) as smtp:
        smtp.login(username, password)
        smtp.send_message(msg)
    print(f"Email sent to {recipient}: {msg['Subject']}")


if __name__ == "__main__":
    main()
