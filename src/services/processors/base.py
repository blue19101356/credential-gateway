"""Abstract base class for credential type processors."""

from abc import ABC, abstractmethod


class BaseProcessor(ABC):
    @abstractmethod
    def validate(self, plaintext: str) -> bool:
        ...

    @abstractmethod
    def type_name(self) -> str:
        ...
