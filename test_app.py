"""Automated tests for the Assignment Submission Portal.

Tests 1-3 are the three test cases required by the Lab Mid PDF.
Tests 4-10 check the rest of the portal's behaviour.
"""
import pytest

from app import app, load_submissions

VALID = {
    "name": "Ali Khan",
    "reg_no": "FA22-BCS-001",
    "title": "Lab 1",
    "url": "https://example.com/lab1.pdf",
}


@pytest.fixture
def client(tmp_path):
    """Give each test a fresh, empty data file."""
    app.config["TESTING"] = True
    app.config["DATA_FILE"] = str(tmp_path / "submissions.json")
    with app.test_client() as client:
        yield client


# ---------- Required by the PDF ----------

def test_valid_submission_is_saved_and_listed(client):
    """1. Complete details and a valid URL -> saved and shown in the list."""
    response = client.post("/", data=VALID, follow_redirects=True)

    assert response.status_code == 200
    assert b"Submission saved successfully." in response.data
    assert len(load_submissions()) == 1
    assert b"FA22-BCS-001" in response.data
    assert b"https://example.com/lab1.pdf" in response.data


def test_missing_registration_number_is_rejected(client):
    """2. Missing registration number -> rejected with a validation message."""
    response = client.post("/", data={**VALID, "reg_no": ""})

    assert response.status_code == 400
    assert b"Registration number is required." in response.data
    assert load_submissions() == []


def test_invalid_url_is_rejected_and_not_saved(client):
    """3. Invalid submission URL -> rejected and not saved."""
    response = client.post("/", data={**VALID, "url": "not-a-link"})

    assert response.status_code == 400
    assert b"Submission URL is invalid." in response.data
    assert load_submissions() == []


# ---------- Extra checks ----------

def test_home_page_shows_the_form(client):
    """4. The home page opens and has all four input fields."""
    response = client.get("/")

    assert response.status_code == 200
    for field in (b'name="name"', b'name="reg_no"', b'name="title"', b'name="url"'):
        assert field in response.data


def test_empty_form_shows_every_required_message(client):
    """5. Submitting an empty form lists an error for every field."""
    response = client.post("/", data={})

    assert response.status_code == 400
    for label in (b"Name", b"Registration number", b"Assignment title", b"Submission URL"):
        assert label + b" is required." in response.data
    assert load_submissions() == []


def test_wrong_registration_format_is_rejected(client):
    """6. Registration number must look like SP23-BCS-009."""
    for bad in ["12345", "SP23BCS009", "SP23 BCS 009", "XY23-BCS-009", "SP23-BCS-9"]:
        response = client.post("/", data={**VALID, "reg_no": bad})

        assert response.status_code == 400, bad
        assert b"Registration number is invalid." in response.data
    assert load_submissions() == []


def test_lowercase_registration_is_saved_in_capitals(client):
    """7. sp23-bcs-009 is accepted and saved as SP23-BCS-009."""
    client.post("/", data={**VALID, "reg_no": "sp23-bcs-009"})

    assert load_submissions()[0]["reg_no"] == "SP23-BCS-009"


def test_url_must_use_http_or_https(client):
    """8. Links without http(s):// or without a real domain are rejected."""
    for bad in ["www.example.com", "ftp://example.com/file", "https://localhost"]:
        response = client.post("/", data={**VALID, "url": bad})

        assert response.status_code == 400, bad
    assert load_submissions() == []


def test_submissions_page_lists_every_entry_newest_first(client):
    """9. Two submissions are both saved and listed, newest first."""
    client.post("/", data=VALID)
    client.post("/", data={**VALID, "name": "Sara Ahmed", "reg_no": "SP23-BCS-050"})

    response = client.get("/submissions")
    page = response.data.decode()

    assert len(load_submissions()) == 2
    assert "Saved Submissions (2)" in page
    assert page.index("SP23-BCS-050") < page.index("FA22-BCS-001")


def test_extra_spaces_are_removed_and_blank_fields_rejected(client):
    """10. Spaces around values are trimmed; a field of only spaces counts as empty."""
    client.post("/", data={**VALID, "name": "  Ali Khan  ", "title": "  Lab 1 "})
    assert load_submissions()[0]["name"] == "Ali Khan"
    assert load_submissions()[0]["title"] == "Lab 1"

    response = client.post("/", data={**VALID, "name": "   "})
    assert response.status_code == 400
    assert b"Name is required." in response.data
    assert len(load_submissions()) == 1
