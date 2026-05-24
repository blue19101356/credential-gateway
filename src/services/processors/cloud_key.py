"""Cloud provider key credential processor."""

import re
from src.services.processors.base import BaseProcessor

_AWS_AKID_PATTERN = re.compile(r"^AKIA[0-9A-Z]{16}$")
_GCP_JSON_KEY_FIELD = re.compile(r'"type"\s*:\s*"service_account"')


class CloudKeyProcessor(BaseProcessor):
    def type_name(self) -> str:
        return "cloud_key"

    def validate(self, plaintext: str) -> bool:
        stripped = plaintext.strip()
        if not stripped:
            return False
        if _AWS_AKID_PATTERN.match(stripped):
            return True
        if stripped.startswith("{") and _GCP_JSON_KEY_FIELD.search(stripped):
            return True
        return len(stripped) >= 8
