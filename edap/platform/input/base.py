from __future__ import annotations

from abc import ABC, abstractmethod


class InputController(ABC):
    @abstractmethod
    def press_key(self, key: str, modifier: str | None = None) -> None:
        """Press a key, optionally with a modifier."""

    @abstractmethod
    def release_key(self, key: str, modifier: str | None = None) -> None:
        """Release a key, optionally with a modifier."""

    @abstractmethod
    def tap_key(self, key: str, modifier: str | None = None, hold_s: float = 0.0) -> None:
        """Press and release a key sequence."""
