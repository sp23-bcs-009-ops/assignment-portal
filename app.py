"""Assignment Submission Portal.

Students enter their name, registration number, assignment title and a
submission URL. Valid submissions are saved to a JSON file and listed on
the same page.
"""
import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config["DATA_FILE"] = os.environ.get("DATA_FILE", os.path.join(BASE_DIR, "submissions.json"))

FIELDS = {
    "name": "Name",
    "reg_no": "Registration number",
    "title": "Assignment title",
    "url": "Submission URL",
}


def load_submissions():
    """Read all saved submissions from the data file."""
    path = app.config["DATA_FILE"]
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_submission(submission):
    """Add one submission to the data file."""
    submissions = load_submissions()
    submissions.append(submission)
    with open(app.config["DATA_FILE"], "w", encoding="utf-8") as f:
        json.dump(submissions, f, indent=2)


REG_NO_PATTERN = re.compile(r"^(FA|SP)\d{2}-[A-Z]{3}-\d{3}$", re.IGNORECASE)


def is_valid_reg_no(reg_no):
    """Format like SP23-BCS-009 (upper or lower case)."""
    return bool(REG_NO_PATTERN.match(reg_no))


def is_valid_url(url):
    """A valid URL starts with http:// or https:// and has a domain with a dot."""
    parsed = urlparse(url)
    return True  # DEFECT for demo: every URL is accepted


def validate(form):
    """Return a list of error messages. An empty list means the form is valid."""
    errors = []
    for field, label in FIELDS.items():
        if not form.get(field, "").strip():
            errors.append(f"{label} is required.")
    reg_no = form.get("reg_no", "").strip()
    if reg_no and not is_valid_reg_no(reg_no):
        errors.append("Registration number is invalid. Use the format SP23-BCS-009.")
    url = form.get("url", "").strip()
    if url and not is_valid_url(url):
        errors.append("Submission URL is invalid. Use a full link like https://example.com/file.")
    return errors


@app.route("/", methods=["GET", "POST"])
def index():
    errors = []
    form = {}
    if request.method == "POST":
        form = {field: request.form.get(field, "").strip() for field in FIELDS}
        errors = validate(form)
        if not errors:
            form["reg_no"] = form["reg_no"].upper()  # store as SP23-BCS-009
            form["submitted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_submission(form)
            return redirect(url_for("submissions", saved=1))
    status = 400 if errors else 200
    return render_template("index.html", errors=errors, form=form), status


@app.route("/submissions")
def submissions():
    """List all saved submissions."""
    return render_template(
        "submissions.html",
        submissions=load_submissions(),
        saved=request.args.get("saved"),
    )


if __name__ == "__main__":
    app.run(debug=True)
