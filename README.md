# Assignment Submission Portal

DevOps Lab Mid (CSC418): a simple portal where students submit an assignment link.
Every push is tested automatically by GitHub Actions, and the test report is sent
to a local receiver that saves it as `test-report.json`.

## Features
- Form with name, registration number, assignment title and submission URL
- Checks that all fields are filled in, that the registration number looks like
  `SP23-BCS-009` (FA/SP, year, 3-letter program, 3-digit number; any case, saved
  in capitals), and that the URL is a valid `http`/`https` link
- Saves valid submissions to `submissions.json` and lists them on the page

## Project files
| File | Purpose |
|------|---------|
| `app.py` | Flask web app (the portal) |
| `templates/index.html` | Form and submissions list page |
| `test_app.py` | Automated tests (pytest) |
| `receiver.py` | Local HTTP server that receives the CI test report |
| `build_report.py` | Builds the JSON test report in CI |
| `send_email.py` | Emails the test report (bonus) |
| `site/index.html` | Static demo published to GitHub Pages (bonus) |
| `DEMO.md`, `evidence/` | Pass / fail / fix demonstration evidence |
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

   If cloudflared cannot start a tunnel, use localhost.run instead (needs only
   SSH, which is built into Windows 10/11):
   ```bash
   ssh -R 80:127.0.0.1:8000 nokey@localhost.run
   ```
   Copy the `https://....lhr.life` link it prints.
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
1. Runs on every push and every pull request, and checks out that commit.
2. Installs Python and the requirements.
3. Runs `pytest`. If any test fails, this step fails and the pipeline fails.
4. Always (pass or fail): `build_report.py` builds `report.json` with the
   repository, branch, commit SHA, run id, timestamp, each test's result and
   failure message, and total / passed / failed counts with the overall status.
5. Always: sends the report to `RECEIVER_URL` with the `X-Report-Token` header,
   emails it, and uploads it as a run artifact.
6. Only if all tests passed and the push was to `main`: the `deploy` job
   publishes the static demo in `site/` to GitHub Pages.

## Bonus: GitHub Pages (conditional deployment)
Live demo: https://sp23-bcs-009-ops.github.io/assignment-portal/

`site/index.html` is a static version of the portal (same validation rules,
submissions stored in the browser). The `deploy` job has `needs: test`, so a
failing run skips deployment and the previously published version stays live.
The page footer shows the commit it was deployed from.

## Bonus: Email report
`send_email.py` emails the report after every run (passed or failed), with the
commit, overall result, counts, each test's result, and `test-report.json`
attached. Credentials are never in the code:

```bash
gh variable set EMAIL_TO --body "someone@example.com"   # recipient (configurable)
gh secret set SMTP_USERNAME                             # sender Gmail address
gh secret set SMTP_PASSWORD                             # Gmail App Password
```
For Gmail, create an App Password at https://myaccount.google.com/apppasswords
(2-Step Verification must be on). Other providers: also set the `SMTP_SERVER`
and `SMTP_PORT` variables (SSL). If the settings are missing, the step is skipped
with a warning.
