"""Client-side key generation utilities.

Provides functions to generate and serialize Ed25519 (signing) and
X25519 (encryption) key pairs for use with the credential gateway.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crypto.ecc_manager import (
    generate_signing_keypair,
    serialize_private_key,
    serialize_public_key,
)
from src.crypto.encryption import (
    generate_encryption_keypair,
    serialize_x25519_private_key,
    serialize_x25519_public_key,
)


def generate_and_save_keys(output_dir: str = ".") -> dict:
    signing_priv, signing_pub = generate_signing_keypair()
    enc_priv, enc_pub = generate_encryption_keypair()

    keys = {
        "ed25519_private_key": serialize_private_key(signing_priv),
        "ed25519_public_key": serialize_public_key(signing_pub),
        "x25519_private_key": serialize_x25519_private_key(enc_priv),
        "x25519_public_key": serialize_x25519_public_key(enc_pub),
    }

    for filename, content in [
        ("ed25519_private.pem", keys["ed25519_private_key"]),
        ("ed25519_public.pem", keys["ed25519_public_key"]),
        ("x25519_private.pem", keys["x25519_private_key"]),
        ("x25519_public.pem", keys["x25519_public_key"]),
    ]:
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w") as f:
            f.write(content)

    return keys
