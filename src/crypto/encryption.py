"""ECIES hybrid encryption using X25519 + AES-256-GCM.

Wire format (before base64): ephemeral_pubkey(32) || nonce(12) || ciphertext || tag(16)
"""

import os
from base64 import b64encode, b64decode

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


_NONCE_LENGTH = 12
_EPHEMERAL_PUBKEY_BYTES = 32
_INFO = b"credential-gateway-ecies-v1"


def generate_encryption_keypair() -> tuple[X25519PrivateKey, X25519PublicKey]:
    private_key = X25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key


def serialize_x25519_public_key(public_key: X25519PublicKey) -> str:
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return pem.decode("utf-8")


def serialize_x25519_private_key(private_key: X25519PrivateKey) -> str:
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem.decode("utf-8")


def load_x25519_public_key(pem_str: str) -> X25519PublicKey:
    key = serialization.load_pem_public_key(pem_str.encode("utf-8"))
    if not isinstance(key, X25519PublicKey):
        raise ValueError("Key is not an X25519 public key")
    return key


def load_x25519_private_key(pem_str: str) -> X25519PrivateKey:
    key = serialization.load_pem_private_key(pem_str.encode("utf-8"), password=None)
    if not isinstance(key, X25519PrivateKey):
        raise ValueError("Key is not an X25519 private key")
    return key


def _derive_aes_key(shared_secret: bytes) -> AESGCM:
    derived = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=_INFO,
    ).derive(shared_secret)
    return AESGCM(derived)


def encrypt(plaintext: bytes, recipient_public_key: X25519PublicKey) -> bytes:
    ephemeral_private = X25519PrivateKey.generate()
    ephemeral_public = ephemeral_private.public_key()

    shared_secret = ephemeral_private.exchange(recipient_public_key)
    aesgcm = _derive_aes_key(shared_secret)

    nonce = os.urandom(_NONCE_LENGTH)
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, None)
    ciphertext = ciphertext_with_tag[:-16]
    tag = ciphertext_with_tag[-16:]

    ephemeral_pubkey_bytes = ephemeral_public.public_bytes_raw()

    return ephemeral_pubkey_bytes + nonce + ciphertext + tag


def encrypt_string(plaintext: str, recipient_public_key: X25519PublicKey) -> str:
    raw = encrypt(plaintext.encode("utf-8"), recipient_public_key)
    return b64encode(raw).decode("ascii")


def decrypt(encrypted_data: bytes, recipient_private_key: X25519PrivateKey) -> bytes:
    if len(encrypted_data) < _EPHEMERAL_PUBKEY_BYTES + _NONCE_LENGTH + 16:
        raise ValueError("Encrypted data is too short")

    ephemeral_pubkey_bytes = encrypted_data[:_EPHEMERAL_PUBKEY_BYTES]
    nonce = encrypted_data[_EPHEMERAL_PUBKEY_BYTES:_EPHEMERAL_PUBKEY_BYTES + _NONCE_LENGTH]
    ciphertext = encrypted_data[_EPHEMERAL_PUBKEY_BYTES + _NONCE_LENGTH:-16]
    tag = encrypted_data[-16:]

    ephemeral_public = X25519PublicKey.from_public_bytes(ephemeral_pubkey_bytes)
    shared_secret = recipient_private_key.exchange(ephemeral_public)
    aesgcm = _derive_aes_key(shared_secret)

    ciphertext_with_tag = ciphertext + tag
    return aesgcm.decrypt(nonce, ciphertext_with_tag, None)


def decrypt_string(encrypted_b64: str, recipient_private_key: X25519PrivateKey) -> str:
    raw = b64decode(encrypted_b64.encode("ascii"))
    return decrypt(raw, recipient_private_key).decode("utf-8")
