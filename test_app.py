"""Automated tests for the Assignment Submission Portal."""
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


def test_valid_submission_is_saved_and_listed(client):
    """Complete details and a valid URL -> saved and shown in the list."""
    response = client.post("/", data=VALID, follow_redirects=True)

    assert response.status_code == 200
    assert b"Submission saved successfully." in response.data
    assert len(load_submissions()) == 1
    assert b"FA22-BCS-001" in response.data
    assert b"https://example.com/lab1.pdf" in response.data


def test_missing_registration_number_is_rejected(client):
    """Missing registration number -> rejected with a validation message."""
    data = {**VALID, "reg_no": ""}
    response = client.post("/", data=data)

    assert response.status_code == 400
    assert b"Registration number is required." in response.data
    assert load_submissions() == []


@pytest.mark.parametrize("reg_no", ["12345", "SP23BCS009", "XY23-BCS-009", "SP23-BCS-9", "SP2-BCS-009"])
def test_wrong_registration_format_is_rejected(client, reg_no):
    """Registration number must look like SP23-BCS-009."""
    response = client.post("/", data={**VALID, "reg_no": reg_no})

    assert response.status_code == 400
    assert b"Registration number is invalid." in response.data
    assert load_submissions() == []


def test_lowercase_registration_is_accepted_and_saved_uppercase(client):
    """sp23-bcs-009 is accepted and saved as SP23-BCS-009."""
    response = client.post("/", data={**VALID, "reg_no": "sp23-bcs-009"}, follow_redirects=True)

    assert response.status_code == 200
    assert load_submissions()[0]["reg_no"] == "SP23-BCS-009"


def test_invalid_url_is_rejected_and_not_saved(client):
    """Invalid submission URL -> rejected and not saved."""
    data = {**VALID, "url": "not-a-link"}
    response = client.post("/", data=data)

    assert response.status_code == 400
    assert b"Submission URL is invalid." in response.data
    assert load_submissions() == []
