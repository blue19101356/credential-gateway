"""Credential type processor registry."""

from src.services.processors.base import BaseProcessor
from src.services.processors.api_key import ApiKeyProcessor
from src.services.processors.db_password import DbPasswordProcessor
from src.services.processors.ssh_key import SshKeyProcessor
from src.services.processors.cloud_key import CloudKeyProcessor
from src.services.processors.generic import GenericProcessor

_registry: dict[str, BaseProcessor] = {}

_processors = [
    ApiKeyProcessor(),
    DbPasswordProcessor(),
    SshKeyProcessor(),
    CloudKeyProcessor(),
    GenericProcessor(),
]

for p in _processors:
    _registry[p.type_name()] = p


def get_processor(type_name: str) -> BaseProcessor:
    return _registry[type_name]


__all__ = ["BaseProcessor", "get_processor"]
