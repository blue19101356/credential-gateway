"""Tests for credential type processors."""

import pytest
from src.services.processors import get_processor
from src.services.processors.base import BaseProcessor


class TestApiKeyProcessor:
    def setup_method(self):
        self.processor = get_processor("api_key")

    def test_valid_api_key(self):
        assert self.processor.validate("sk-abc123def456")

    def test_reject_empty(self):
        assert not self.processor.validate("")

    def test_reject_newline(self):
        assert not self.processor.validate("key\nwith\nnewlines")

    def test_reject_too_short(self):
        assert not self.processor.validate("ab")


class TestDbPasswordProcessor:
    def setup_method(self):
        self.processor = get_processor("db_password")

    def test_valid_connection_string(self):
        assert self.processor.validate("postgresql://user:pass@localhost:5432/db")

    def test_valid_password(self):
        assert self.processor.validate("s3cureP@ss!")

    def test_reject_empty(self):
        assert not self.processor.validate("")

    def test_reject_too_short(self):
        assert not self.processor.validate("ab")


class TestSshKeyProcessor:
    def setup_method(self):
        self.processor = get_processor("ssh_key")

    def test_valid_openssh_key(self):
        assert self.processor.validate("-----BEGIN OPENSSH PRIVATE KEY-----\nAAA...\n-----END OPENSSH PRIVATE KEY-----")

    def test_valid_rsa_key(self):
        assert self.processor.validate("-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----")

    def test_valid_public_key(self):
        assert self.processor.validate("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... user@host")

    def test_reject_random_text(self):
        assert not self.processor.validate("not a key at all")


class TestCloudKeyProcessor:
    def setup_method(self):
        self.processor = get_processor("cloud_key")

    def test_valid_aws_access_key(self):
        assert self.processor.validate("AKIAIOSFODNN7EXAMPLE")

    def test_valid_gcp_service_account(self):
        assert self.processor.validate('{"type":"service_account","project_id":"my-project"}')

    def test_reject_empty(self):
        assert not self.processor.validate("")


class TestGenericProcessor:
    def setup_method(self):
        self.processor = get_processor("generic")

    def test_accepts_anything(self):
        assert self.processor.validate("anything goes here")

    def test_reject_empty(self):
        assert not self.processor.validate("")


class TestRegistry:
    def test_all_types_registered(self):
        for type_name in ["api_key", "db_password", "ssh_key", "cloud_key", "generic"]:
            processor = get_processor(type_name)
            assert isinstance(processor, BaseProcessor)
            assert processor.type_name() == type_name

    def test_unknown_type_raises(self):
        with pytest.raises(KeyError):
            get_processor("nonexistent")
