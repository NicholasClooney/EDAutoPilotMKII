from __future__ import annotations

from .base import ScreenCapture


def build_screen_capture(platform_name: str) -> ScreenCapture | None:
    normalized = platform_name.lower()
    if normalized == "macos":
        from .macos import MacOSScreenCapture

        return MacOSScreenCapture()
    return None
