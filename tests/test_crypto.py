"""Tests for Ed25519 key management and ECIES encryption."""

import pytest
from src.crypto.ecc_manager import (
    generate_signing_keypair,
    serialize_private_key,
    serialize_public_key,
    load_private_key,
    load_public_key,
    sign,
    verify,
)
from src.crypto.encryption import (
    generate_encryption_keypair,
    serialize_x25519_private_key,
    serialize_x25519_public_key,
    load_x25519_private_key,
    load_x25519_public_key,
    encrypt_string,
    decrypt_string,
)


class TestEd25519:
    def test_generate_and_serialize_roundtrip(self):
        priv, pub = generate_signing_keypair()
        priv_pem = serialize_private_key(priv)
        pub_pem = serialize_public_key(pub)

        loaded_priv = load_private_key(priv_pem)
        loaded_pub = load_public_key(pub_pem)

        assert serialize_public_key(loaded_pub).strip() == pub_pem.strip()
        assert serialize_private_key(loaded_priv).strip() == priv_pem.strip()

    def test_sign_and_verify(self):
        priv, pub = generate_signing_keypair()
        message = b"authenticate this request"

        sig = sign(priv, message)
        assert verify(pub, sig, message)

    def test_verify_wrong_message_fails(self):
        priv, pub = generate_signing_keypair()
        sig = sign(priv, b"correct message")
        assert not verify(pub, sig, b"wrong message")

    def test_verify_wrong_key_fails(self):
        priv, _ = generate_signing_keypair()
        _, other_pub = generate_signing_keypair()
        sig = sign(priv, b"message")
        assert not verify(other_pub, sig, b"message")


class TestECIES:
    def test_encrypt_decrypt_roundtrip(self):
        priv, pub = generate_encryption_keypair()
        plaintext = "my-super-secret-password-123!"
        ciphertext = encrypt_string(plaintext, pub)
        decrypted = decrypt_string(ciphertext, priv)
        assert decrypted == plaintext

    def test_long_message(self):
        priv, pub = generate_encryption_keypair()
        plaintext = "x" * 10000
        ciphertext = encrypt_string(plaintext, pub)
        decrypted = decrypt_string(ciphertext, priv)
        assert decrypted == plaintext

    def test_empty_message(self):
        priv, pub = generate_encryption_keypair()
        plaintext = ""
        ciphertext = encrypt_string(plaintext, pub)
        decrypted = decrypt_string(ciphertext, priv)
        assert decrypted == plaintext

    def test_unicode_message(self):
        priv, pub = generate_encryption_keypair()
        plaintext = "cafe" + chr(0x0301) + " - " + chr(0x4F60) + chr(0x597D)
        ciphertext = encrypt_string(plaintext, pub)
        decrypted = decrypt_string(ciphertext, priv)
        assert decrypted == plaintext

    def test_tampered_ciphertext_fails(self):
        priv, pub = generate_encryption_keypair()
        ciphertext = encrypt_string("secret", pub)
        with pytest.raises(Exception):
            decrypt_string(ciphertext + "xxxx", priv)

    def test_wrong_key_fails(self):
        priv, pub = generate_encryption_keypair()
        _, other_pub = generate_encryption_keypair()
        ciphertext = encrypt_string("secret", other_pub)
        with pytest.raises(Exception):
            decrypt_string(ciphertext, priv)

    def test_serialize_deserialize_x25519_keys(self):
        priv, pub = generate_encryption_keypair()
        priv_pem = serialize_x25519_private_key(priv)
        pub_pem = serialize_x25519_public_key(pub)

        loaded_priv = load_x25519_private_key(priv_pem)
        loaded_pub = load_x25519_public_key(pub_pem)

        test = encrypt_string("hello", loaded_pub)
        assert decrypt_string(test, loaded_priv) == "hello"

    def test_deterministic_encryption(self):
        _, pub = generate_encryption_keypair()
        # Each encryption should produce different ciphertext due to random ephemeral key
        c1 = encrypt_string("same text", pub)
        c2 = encrypt_string("same text", pub)
        assert c1 != c2
