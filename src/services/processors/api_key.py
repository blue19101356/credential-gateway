"""API Key credential processor."""

from src.services.processors.base import BaseProcessor


class ApiKeyProcessor(BaseProcessor):
    def type_name(self) -> str:
        return "api_key"

    def validate(self, plaintext: str) -> bool:
        stripped = plaintext.strip()
        if not stripped or len(stripped) < 8:
            return False
        if "\n" in stripped or "\r" in stripped:
            return False
        return True
