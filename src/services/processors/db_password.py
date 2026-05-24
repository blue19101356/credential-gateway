"""Database password / connection string credential processor."""

import re
from src.services.processors.base import BaseProcessor

_CONN_STRING_PATTERN = re.compile(
    r"^(postgresql|mysql|sqlite|mssql|oracle)(\+[a-z]+)?://[^\s]+$",
    re.IGNORECASE,
)


class DbPasswordProcessor(BaseProcessor):
    def type_name(self) -> str:
        return "db_password"

    def validate(self, plaintext: str) -> bool:
        stripped = plaintext.strip()
        if not stripped or len(stripped) < 4:
            return False
        if "\n" in stripped or "\r" in stripped:
            return False
        if _CONN_STRING_PATTERN.match(stripped):
            return True
        return len(stripped) >= 4
