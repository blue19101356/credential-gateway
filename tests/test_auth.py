"""Tests for authentication flow."""

import pytest
from src.crypto.ecc_manager import generate_signing_keypair, sign, serialize_public_key, serialize_private_key
from src.crypto.hashing import sha256


class TestAuthFlow:
    def test_signature_verification_flow(self):
        priv, pub = generate_signing_keypair()

        body = b'{"type":"api_key","name":"test-key","value":"sk-secret123"}'
        digest = sha256(body)
        sig = sign(priv, digest)

        from src.crypto.ecc_manager import verify, load_public_key

        pub_pem = serialize_public_key(pub)
        loaded_pub = load_public_key(pub_pem)
        assert verify(loaded_pub, sig, digest)

    def test_wrong_body_fails(self):
        priv, pub = generate_signing_keypair()

        body = b'{"type":"api_key","name":"test-key","value":"sk-secret123"}'
        digest = sha256(body)
        sig = sign(priv, digest)

        from src.crypto.ecc_manager import verify, load_public_key

        wrong_digest = sha256(b'{"type":"api_key","name":"test-key","value":"sk-evil"}')
        pub_pem = serialize_public_key(pub)
        loaded_pub = load_public_key(pub_pem)
        assert not verify(loaded_pub, sig, wrong_digest)

    def test_signature_is_deterministic_for_same_input(self):
        priv, _ = generate_signing_keypair()
        digest = sha256(b"same body")
        sig1 = sign(priv, digest)
        sig2 = sign(priv, digest)
        assert sig1 == sig2

    def test_signature_differs_for_different_input(self):
        priv, _ = generate_signing_keypair()
        sig1 = sign(priv, sha256(b"body one"))
        sig2 = sign(priv, sha256(b"body two"))
        assert sig1 != sig2
