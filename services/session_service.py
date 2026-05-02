import json
import os

SESSION_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "session.json"
)


class SessionService:
    """
    Persists the logged-in user to a local JSON file so the session
    survives the app being closed and reopened.

    The file stores only non-sensitive data: user id, name, email.
    The password hash is never written here.
    """

    def save(self, user) -> None:
        """Write user data to disk after a successful login."""
        try:
            with open(SESSION_PATH, "w") as f:
                json.dump(user.to_dict(), f)
        except Exception as e:
            print(f"[SessionService] Could not save session: {e}")

    def load(self):
        """
        Read the saved session from disk.
        Returns a dict with id/name/email, or None if no session exists.
        """
        if not os.path.exists(SESSION_PATH):
            return None
        try:
            with open(SESSION_PATH, "r") as f:
                data = json.load(f)
            # Validate the file has the expected keys
            if all(k in data for k in ("id", "name", "email")):
                return data
            return None
        except Exception as e:
            print(f"[SessionService] Could not load session: {e}")
            return None

    def clear(self) -> None:
        """Delete the session file on logout."""
        try:
            if os.path.exists(SESSION_PATH):
                os.remove(SESSION_PATH)
        except Exception as e:
            print(f"[SessionService] Could not clear session: {e}")

    def exists(self) -> bool:
        """Quick check — is there a saved session on disk?"""
        return os.path.exists(SESSION_PATH)