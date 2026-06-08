from __future__ import annotations

from .base import InputController


def build_input_controller(platform_name: str) -> InputController | None:
    normalized = platform_name.lower()
    if normalized == "macos":
        from .macos import MacOSInputController

        return MacOSInputController()
    if normalized == "windows":
        from .windows import WindowsInputController

        return WindowsInputController()
    return None
