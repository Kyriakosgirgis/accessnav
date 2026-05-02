from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: int
    name: str
    email: str

    # Never include the password hash in the model
    # It stays in the database only

    def display_name(self) -> str:
        return self.name.split()[0] if self.name else self.email

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
        }

    @staticmethod
    def from_row(row) -> Optional["User"]:
        if row is None:
            return None
        return User(id=row["id"], name=row["name"], email=row["email"])