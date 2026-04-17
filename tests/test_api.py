"""
tests/test_api.py
Basic integration tests for all API endpoints.
Run:  pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient

# Ensure src imports work when running from project root
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import app

client = TestClient(app)


# ── Auth ──────────────────────────────────────────────────────────────────────
def test_register_and_login():
    """Register a new user then login with same creds."""
    username = f"testuser_{os.urandom(4).hex()}"
    payload = {"username": username, "password": "TestPass123!"}

    # Register
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert "access_token" in data
    assert data["username"] == username

    # Login
    r2 = client.post("/api/auth/login", json=payload)
    assert r2.status_code == 200
    data2 = r2.json()
    assert "access_token" in data2


def test_login_wrong_password():
    """Logging in with wrong password after account exists must return 401."""
    username = f"testuser_{os.urandom(4).hex()}"
    client.post("/api/auth/register", json={"username": username, "password": "correct"})
    r = client.post("/api/auth/login", json={"username": username, "password": "wrong"})
    assert r.status_code == 401


def test_feed_without_token():
    """Feed endpoint must require auth."""
    r = client.get("/api/jobs/feed")
    assert r.status_code == 401


def test_tracker_without_token():
    """Tracker endpoint must require auth."""
    r = client.get("/api/jobs/tracker")
    assert r.status_code == 401


def test_upload_without_token():
    """Resume upload must require auth."""
    r = client.post("/api/resume/upload", files={"file": ("test.pdf", b"fake", "application/pdf")})
    assert r.status_code == 401


def test_upload_wrong_file_type():
    """Only PDFs should be accepted."""
    # Register + get token
    username = f"testuser_{os.urandom(4).hex()}"
    reg = client.post("/api/auth/register", json={"username": username, "password": "Pass123!"})
    token = reg.json()["access_token"]

    r = client.post(
        "/api/resume/upload",
        files={"file": ("resume.txt", b"some text", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400
    assert "PDF" in r.json()["error"]


def test_interview_start_validation():
    """difficulty must be 1-10."""
    r = client.post("/api/interview/start", json={"role": "Engineer", "difficulty": 99})
    assert r.status_code == 422
