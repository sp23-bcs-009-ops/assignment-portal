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
```bash
python receiver.py
```
The receiver listens on http://localhost:8000. Each CI run posts its test report
there, and the receiver saves it as `test-report.json` in the project folder.
