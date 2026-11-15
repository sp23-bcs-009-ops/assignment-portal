# Assignment Submission Portal

DevOps Lab Mid (CSC418): a simple portal where students submit an assignment link.
Every push is tested automatically by GitHub Actions, and the test report is sent
to a local receiver that saves it as `test-report.json`.

## Features
- Form with name, registration number, assignment title and submission URL
- Checks that all fields are filled in and that the URL is a valid `http`/`https` link
- Saves valid submissions to `submissions.json` and lists them on the page

## Project files
| File | Purpose |
|------|---------|
| `app.py` | Flask web app (the portal) |
| `templates/index.html` | Form and submissions list page |
| `test_app.py` | Automated tests (pytest) |
| `receiver.py` | Local HTTP server that receives the CI test report |
| `.github/workflows/ci.yml` | CI pipeline (GitHub Actions) |
| `requirements.txt` | Python packages |

## Setup
Requires Python 3.10+ and Git.

```bash
git clone https://github.com/sp23-bcs-009-ops/assignment-portal.git
cd assignment-portal
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
```

## Run the application
```bash
python app.py
```
Open http://localhost:5000 in a browser.

## Run the tests
```bash
pytest -v
```

## Start the report receiver
The CI pipeline runs on a GitHub server, so it reaches the receiver on your PC
through a Cloudflare tunnel.

1. Create a secret token (once):
   ```bash
   python -c "import secrets; open('.report_token','w').write(secrets.token_hex(24))"
   ```
2. Start the receiver (keep this terminal open):
   ```bash
   python receiver.py
   ```
   It listens on http://localhost:8000.
3. In a second terminal, start the tunnel (install once with
   `winget install Cloudflare.cloudflared`):
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```
   Copy the `https://....trycloudflare.com` link it prints.
4. Save the link and token as GitHub repository secrets:
   ```bash
   gh secret set RECEIVER_URL --body "https://....trycloudflare.com"
   gh secret set REPORT_TOKEN < .report_token
   ```
   The tunnel link changes each time cloudflared restarts, so repeat the
   `RECEIVER_URL` command after a restart.

After every push, the pipeline sends its report (for passing and failing runs)
and the receiver saves it as `test-report.json`. A copy of each run is also
kept in `reports/<run_id>-<passed|failed>.json`.

## How the pipeline works (`.github/workflows/ci.yml`)
1. Runs on every push and checks out the pushed commit.
2. Installs Python and the requirements.
3. Runs `pytest`. If any test fails, this step fails and the pipeline fails.
4. Always (pass or fail): `build_report.py` builds `report.json` with the
   repository, branch, commit SHA, run id, timestamp, each test's result and
   failure message, and total / passed / failed counts with the overall status.
5. Always: sends the report to `RECEIVER_URL` with the `X-Report-Token` header,
   and uploads it as a run artifact.
