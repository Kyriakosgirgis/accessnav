import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
import data.database as db_module
from data.database import Database
from api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """Each test gets a clean isolated database."""
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "test.db"))
    Database._instance = None
    yield
    Database._instance = None


# ------------------------------------------------------------------ #
#  Health                                                              #
# ------------------------------------------------------------------ #

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ------------------------------------------------------------------ #
#  Auth                                                                #
# ------------------------------------------------------------------ #

def test_register_success():
    r = client.post("/register", json={
        "name": "Kyriakos", "email": "k@test.com", "password": "pass123"
    })
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "k@test.com"
    assert data["name"]  == "Kyriakos"
    assert "token" in data
    assert "password" not in data   # never leak the hash


def test_register_duplicate_email():
    client.post("/register", json={
        "name": "A", "email": "dup@test.com", "password": "pass123"
    })
    r = client.post("/register", json={
        "name": "B", "email": "dup@test.com", "password": "pass456"
    })
    assert r.status_code == 409


def test_register_short_password():
    r = client.post("/register", json={
        "name": "A", "email": "a@test.com", "password": "abc"
    })
    assert r.status_code == 422


def test_login_success():
    client.post("/register", json={
        "name": "Kyriakos", "email": "k@test.com", "password": "pass123"
    })
    r = client.post("/login", json={
        "email": "k@test.com", "password": "pass123"
    })
    assert r.status_code == 200
    assert r.json()["email"] == "k@test.com"


def test_login_wrong_password():
    client.post("/register", json={
        "name": "A", "email": "a@test.com", "password": "pass123"
    })
    r = client.post("/login", json={
        "email": "a@test.com", "password": "wrongpass"
    })
    assert r.status_code == 401


def test_login_unknown_email():
    r = client.post("/login", json={
        "email": "nobody@test.com", "password": "pass123"
    })
    assert r.status_code == 401


def test_login_case_insensitive():
    client.post("/register", json={
        "name": "A", "email": "a@test.com", "password": "pass123"
    })
    r = client.post("/login", json={
        "email": "A@TEST.COM", "password": "pass123"
    })
    assert r.status_code == 200


# ------------------------------------------------------------------ #
#  Spots                                                               #
# ------------------------------------------------------------------ #

def test_spots_empty():
    r = client.get("/spots")
    assert r.status_code == 200
    assert r.json() == []


def test_spots_with_location_filter():
    r = client.get("/spots?lat=34.678&lon=33.041&radius_m=500")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ------------------------------------------------------------------ #
#  Reports                                                             #
# ------------------------------------------------------------------ #

def _register_and_get_id(email="user@test.com"):
    r = client.post("/register", json={
        "name": "Test", "email": email, "password": "pass123"
    })
    return r.json()["id"]


def test_submit_report_success():
    uid = _register_and_get_id()
    r   = client.post("/report", json={
        "lat": 34.678, "lon": 33.041,
        "barrier_type": "missing_ramp",
        "description": "No ramp at the entrance",
        "user_id": uid,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["barrier_type"] == "missing_ramp"
    assert data["user_id"]      == uid


def test_submit_report_creates_spot():
    uid = _register_and_get_id()
    client.post("/report", json={
        "lat": 34.678, "lon": 33.041,
        "barrier_type": "broken_elevator",
        "description":  "Elevator out of service",
        "user_id": uid,
    })
    # The report should auto-create an unverified spot
    r = client.get("/spots?lat=34.678&lon=33.041&radius_m=100")
    assert len(r.json()) >= 1


def test_submit_report_invalid_user():
    r = client.post("/report", json={
        "lat": 34.678, "lon": 33.041,
        "barrier_type": "other",
        "description":  "test",
        "user_id": 99999,
    })
    assert r.status_code == 404


def test_submit_report_invalid_coords():
    uid = _register_and_get_id()
    r   = client.post("/report", json={
        "lat": 999, "lon": 33.041,
        "barrier_type": "other",
        "description":  "bad lat",
        "user_id": uid,
    })
    assert r.status_code == 422


def test_list_reports():
    uid = _register_and_get_id()
    client.post("/report", json={
        "lat": 34.678, "lon": 33.041,
        "barrier_type": "steep_slope",
        "description":  "Very steep",
        "user_id": uid,
    })
    r = client.get("/reports")
    assert r.status_code == 200
    assert len(r.json()) >= 1