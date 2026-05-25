from __future__ import annotations

from .base import ScreenCapture
from .macos import MacOSScreenCapture


def build_screen_capture(platform_name: str) -> ScreenCapture | None:
    normalized = platform_name.lower()
    if normalized == "macos":
        return MacOSScreenCapture()
    return None
