"""Input validation utilities."""

import re
from src.utils.exceptions import ValidationError

_ED25519_PUBKEY_PATTERN = re.compile(r"^-----BEGIN PUBLIC KEY-----\n[A-Za-z0-9+/=\n]+-----END PUBLIC KEY-----$")
_X25519_PUBKEY_PATTERN = re.compile(r"^-----BEGIN PUBLIC KEY-----\n[A-Za-z0-9+/=\n]+-----END PUBLIC KEY-----$")
_CRED_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._\- ]{0,99}$")


def validate_ed25519_public_key(key: str) -> str:
    key = key.strip()
    if not _ED25519_PUBKEY_PATTERN.match(key):
        raise ValidationError("Invalid Ed25519 public key format (expected PEM)")
    return key


def validate_x25519_public_key(key: str) -> str:
    key = key.strip()
    if not _X25519_PUBKEY_PATTERN.match(key):
        raise ValidationError("Invalid X25519 public key format (expected PEM)")
    return key


def validate_credential_name(name: str) -> str:
    name = name.strip()
    if not _CRED_NAME_PATTERN.match(name):
        raise ValidationError(
            "Credential name must be 1-100 chars, alphanumeric with dots, dashes, underscores, or spaces"
        )
    return name


def validate_credential_type(type_: str) -> str:
    valid_types = {"api_key", "db_password", "ssh_key", "cloud_key", "generic"}
    type_ = type_.strip().lower()
    if type_ not in valid_types:
        raise ValidationError(f"Invalid credential type. Must be one of: {', '.join(sorted(valid_types))}")
    return type_
