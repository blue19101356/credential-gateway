"""SSH key credential processor."""

from src.services.processors.base import BaseProcessor

_VALID_SSH_HEADERS = (
    "-----BEGIN OPENSSH PRIVATE KEY-----",
    "-----BEGIN RSA PRIVATE KEY-----",
    "-----BEGIN EC PRIVATE KEY-----",
    "-----BEGIN DSA PRIVATE KEY-----",
    "-----BEGIN PRIVATE KEY-----",
    "ssh-rsa ",
    "ssh-ed25519 ",
    "ecdsa-sha2-",
    "sk-ssh-ed25519 ",
    "sk-ecdsa-sha2-",
)


class SshKeyProcessor(BaseProcessor):
    def type_name(self) -> str:
        return "ssh_key"

    def validate(self, plaintext: str) -> bool:
        stripped = plaintext.strip()
        if not stripped:
            return False
        for header in _VALID_SSH_HEADERS:
            if stripped.startswith(header):
                return True
        return False
