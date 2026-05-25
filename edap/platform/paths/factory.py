from __future__ import annotations

from .base import GamePaths
from .macos import MacOSGamePaths
from .windows import WindowsGamePaths


def build_game_paths(platform_name: str) -> GamePaths | None:
    normalized = platform_name.lower()
    if normalized == "macos":
        return MacOSGamePaths()
    if normalized == "windows":
        return WindowsGamePaths()
    return None
