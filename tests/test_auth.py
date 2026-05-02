import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.auth_service import AuthService
from data.database import Database


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """Each test gets its own clean in-memory database."""
    import data.database as db_module
    test_db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(db_module, "DB_PATH", test_db_path)
    Database._instance = None
    yield
    Database._instance = None


# ------------------------------------------------------------------ #
#  Registration tests                                                  #
# ------------------------------------------------------------------ #

def test_register_success():
    auth = AuthService()
    ok, msg = auth.register("Alice Smith", "alice@example.com", "password123")
    assert ok is True
    assert msg == "OK"


def test_register_hashes_password():
    auth = AuthService()
    auth.register("Alice Smith", "alice@example.com", "password123")
    row = auth.db.fetchone("SELECT password FROM users WHERE email = 'alice@example.com'")
    assert row is not None
    # Stored value must NOT be the plain text
    assert row["password"] != "password123"
    # Must look like a bcrypt hash
    assert row["password"].startswith("$2b$")


def test_register_duplicate_email():
    auth = AuthService()
    auth.register("Alice Smith", "alice@example.com", "password123")
    ok, msg = auth.register("Alice Two", "alice@example.com", "password456")
    assert ok is False
    assert "already exists" in msg.lower()


def test_register_email_case_insensitive():
    auth = AuthService()
    auth.register("Alice Smith", "Alice@Example.COM", "password123")
    ok, msg = auth.register("Alice Two", "alice@example.com", "password456")
    assert ok is False


def test_register_missing_name():
    auth = AuthService()
    ok, msg = auth.register("", "alice@example.com", "password123")
    assert ok is False
    assert "name" in msg.lower()


def test_register_invalid_email():
    auth = AuthService()
    ok, msg = auth.register("Alice", "not-an-email", "password123")
    assert ok is False
    assert "email" in msg.lower()


def test_register_short_password():
    auth = AuthService()
    ok, msg = auth.register("Alice", "alice@example.com", "abc")
    assert ok is False
    assert "6" in msg


# ------------------------------------------------------------------ #
#  Login tests                                                         #
# ------------------------------------------------------------------ #

def test_login_success():
    auth = AuthService()
    auth.register("Alice Smith", "alice@example.com", "password123")
    user = auth.login("alice@example.com", "password123")
    assert user is not None
    assert user.email == "alice@example.com"
    assert user.name == "Alice Smith"


def test_login_wrong_password():
    auth = AuthService()
    auth.register("Alice Smith", "alice@example.com", "password123")
    user = auth.login("alice@example.com", "wrongpassword")
    assert user is None


def test_login_unknown_email():
    auth = AuthService()
    user = auth.login("nobody@example.com", "password123")
    assert user is None


def test_login_email_case_insensitive():
    auth = AuthService()
    auth.register("Alice Smith", "alice@example.com", "password123")
    user = auth.login("ALICE@EXAMPLE.COM", "password123")
    assert user is not None


def test_login_empty_fields():
    auth = AuthService()
    assert auth.login("", "password123") is None
    assert auth.login("alice@example.com", "") is None


# ------------------------------------------------------------------ #
#  Change password tests                                               #
# ------------------------------------------------------------------ #

def test_change_password_success():
    auth = AuthService()
    auth.register("Alice Smith", "alice@example.com", "password123")
    user = auth.login("alice@example.com", "password123")
    ok, msg = auth.change_password(user.id, "password123", "newpassword99")
    assert ok is True
    assert auth.login("alice@example.com", "newpassword99") is not None


def test_change_password_wrong_old():
    auth = AuthService()
    auth.register("Alice Smith", "alice@example.com", "password123")
    user = auth.login("alice@example.com", "password123")
    ok, msg = auth.change_password(user.id, "wrongold", "newpassword99")
    assert ok is False