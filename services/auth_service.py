import re
import bcrypt
from typing import Tuple, Optional

from data.database import Database
from models.user import User


# ------------------------------------------------------------------ #
#  Constants                                                           #
# ------------------------------------------------------------------ #

MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 128
MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 254
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
BCRYPT_ROUNDS = 12  # Work factor — higher = slower hash = harder to brute-force


# ------------------------------------------------------------------ #
#  AuthService                                                         #
# ------------------------------------------------------------------ #

class AuthService:
    """
    Handles user registration and login.

    All passwords are hashed with bcrypt before storage.
    Plain-text passwords are never written to the database.
    """

    def __init__(self):
        self.db = Database()
        self.db.connect()

    # -------------------------------------------------------------- #
    #  Public API                                                      #
    # -------------------------------------------------------------- #

    def register(self, name: str, email: str, password: str) -> Tuple[bool, str]:
        """
        Register a new user.

        Returns:
            (True,  "OK")            on success
            (False, "error message") on failure
        """
        # 1 — validate inputs
        error = self._validate_registration(name, email, password)
        if error:
            return False, error

        name  = name.strip()
        email = email.strip().lower()

        # 2 — check for duplicate email
        existing = self.db.fetchone(
            "SELECT id FROM users WHERE email = ?", (email,)
        )
        if existing:
            return False, "An account with this email already exists."

        # 3 — hash the password
        password_hash = self._hash_password(password)

        # 4 — insert user
        try:
            self.db.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password_hash),
            )
            return True, "OK"
        except Exception as e:
            return False, f"Registration failed. Please try again. ({e})"

    def login(self, email: str, password: str) -> Optional[User]:
        """
        Verify credentials and return the User on success, None on failure.
        Never reveals whether the email or password was wrong — always
        returns the same generic message to prevent email enumeration.
        """
        if not email or not password:
            return None

        email = email.strip().lower()

        # Fetch the stored hash
        row = self.db.fetchone(
            "SELECT id, name, email, password FROM users WHERE email = ?",
            (email,),
        )

        if row is None:
            # Run a dummy check anyway so the response time is the same
            # whether or not the email exists — prevents timing attacks
            self._dummy_check()
            return None

        # Verify password against stored hash
        stored_hash = row["password"]
        if not self._verify_password(password, stored_hash):
            return None

        return User.from_row(row)

    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> Tuple[bool, str]:
        """
        Change the password for an existing user after verifying the old one.
        """
        row = self.db.fetchone(
            "SELECT password FROM users WHERE id = ?", (user_id,)
        )
        if not row:
            return False, "User not found."

        if not self._verify_password(old_password, row["password"]):
            return False, "Current password is incorrect."

        error = self._validate_password(new_password)
        if error:
            return False, error

        new_hash = self._hash_password(new_password)
        self.db.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (new_hash, user_id),
        )
        return True, "Password updated."

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        row = self.db.fetchone(
            "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
        )
        return User.from_row(row)

    # -------------------------------------------------------------- #
    #  Validation                                                      #
    # -------------------------------------------------------------- #

    def _validate_registration(
        self, name: str, email: str, password: str
    ) -> Optional[str]:
        """Returns an error string or None if everything is valid."""

        # Name
        name = name.strip()
        if not name:
            return "Full name is required."
        if len(name) < 2:
            return "Name must be at least 2 characters."
        if len(name) > MAX_NAME_LENGTH:
            return f"Name must be under {MAX_NAME_LENGTH} characters."

        # Email
        email = email.strip()
        if not email:
            return "Email address is required."
        if len(email) > MAX_EMAIL_LENGTH:
            return "Email address is too long."
        if not EMAIL_REGEX.match(email):
            return "Enter a valid email address."

        # Password
        return self._validate_password(password)

    def _validate_password(self, password: str) -> Optional[str]:
        if not password:
            return "Password is required."
        if len(password) < MIN_PASSWORD_LENGTH:
            return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        if len(password) > MAX_PASSWORD_LENGTH:
            return f"Password must be under {MAX_PASSWORD_LENGTH} characters."
        return None

    # -------------------------------------------------------------- #
    #  Hashing helpers                                                 #
    # -------------------------------------------------------------- #

    def _hash_password(self, plain: str) -> str:
        """Hash a plain-text password with bcrypt. Returns a string."""
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def _verify_password(self, plain: str, stored_hash: str) -> bool:
        """Compare a plain-text password against a stored bcrypt hash."""
        try:
            return bcrypt.checkpw(
                plain.encode("utf-8"),
                stored_hash.encode("utf-8"),
            )
        except Exception:
            return False

    def _dummy_check(self):
        """
        Run a bcrypt check against a fake hash so failed lookups
        take the same amount of time as real ones.
        Prevents attackers from discovering valid emails via response timing.
        """
        fake_hash = "$2b$12$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        try:
            bcrypt.checkpw(b"dummy", fake_hash.encode("utf-8"))
        except Exception:
            pass