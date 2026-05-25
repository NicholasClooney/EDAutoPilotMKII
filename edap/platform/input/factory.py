from __future__ import annotations

from .base import InputController
from .macos import MacOSInputController


def build_input_controller(platform_name: str) -> InputController | None:
    normalized = platform_name.lower()
    if normalized == "macos":
        return MacOSInputController()
    return None
