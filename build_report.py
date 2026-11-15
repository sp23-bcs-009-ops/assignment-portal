"""Build the JSON test report from pytest's JUnit XML output.

Usage: python build_report.py junit.xml report.json

Pipeline details (repository, branch, commit, run id) come from the
environment variables GitHub Actions sets on every run.
"""
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


def read_tests(junit_path):
    """Return a list of {name, result, failure_message} from a JUnit XML file."""
    tests = []
    root = ET.parse(junit_path).getroot()
    for case in root.iter("testcase"):
        result, message = "passed", None
        for tag in ("failure", "error"):
            node = case.find(tag)
            if node is not None:
                result = "failed"
                message = (node.get("message") or "").strip() or (node.text or "").strip()
                break
        if case.find("skipped") is not None:
            result = "skipped"
        tests.append({"name": case.get("name"), "result": result, "failure_message": message})
    return tests


def build_report(junit_path):
    env = os.environ
    server = env.get("GITHUB_SERVER_URL", "https://github.com")
    repo = env.get("GITHUB_REPOSITORY", "local")
    run_id = env.get("GITHUB_RUN_ID", "local")

    error = None
    try:
        tests = read_tests(junit_path)
    except (FileNotFoundError, ET.ParseError) as e:
        # Tests never ran (e.g. install failed) - still send a report.
        tests, error = [], f"No test results found: {e}"

    passed = sum(t["result"] == "passed" for t in tests)
    failed = sum(t["result"] == "failed" for t in tests)
    status = "passed" if tests and failed == 0 and not error else "failed"

    return {
        "repository": repo,
        "branch": env.get("GITHUB_REF_NAME", "local"),
        "commit_sha": env.get("GITHUB_SHA", "local"),
        "run_id": run_id,
        "run_number": env.get("GITHUB_RUN_NUMBER"),
        "run_attempt": env.get("GITHUB_RUN_ATTEMPT"),
        "run_url": f"{server}/{repo}/actions/runs/{run_id}",
        "executed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tests": tests,
        "summary": {"total": len(tests), "passed": passed, "failed": failed},
        "status": status,
        "error": error,
    }


if __name__ == "__main__":
    junit_file = sys.argv[1] if len(sys.argv) > 1 else "junit.xml"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "report.json"
    report = build_report(junit_file)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    s = report["summary"]
    print(f"Report: {report['status'].upper()} - {s['passed']}/{s['total']} passed, {s['failed']} failed")
