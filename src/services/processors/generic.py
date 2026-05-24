"""Generic credential processor (pass-through validation)."""

from src.services.processors.base import BaseProcessor


class GenericProcessor(BaseProcessor):
    def type_name(self) -> str:
        return "generic"

    def validate(self, plaintext: str) -> bool:
        return bool(plaintext.strip())
