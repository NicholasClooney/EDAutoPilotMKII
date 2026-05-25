from __future__ import annotations

from pathlib import Path

from .base import GamePaths


class MacOSGamePaths(GamePaths):
    def default_journal_dir(self) -> Path | None:
        candidates = [
            Path("~/Library/Application Support/CrossOver/Bottles").expanduser(),
            Path("~/Library/Application Support/CrossOver/").expanduser(),
        ]
        for root in candidates:
            if not root.exists():
                continue
            for path in root.glob("**/users/*/Saved Games/Frontier Developments/Elite Dangerous"):
                if path.is_dir():
                    return path
        return None

    def default_bindings_file(self) -> Path | None:
        candidates = [
            Path("~/Library/Application Support/CrossOver/Bottles").expanduser(),
            Path("~/Library/Application Support/CrossOver/").expanduser(),
        ]
        for root in candidates:
            if not root.exists():
                continue
            binds = sorted(
                root.glob("**/users/*/Local Settings/Application Data/Frontier Developments/Elite Dangerous/Options/Bindings/*.binds")
            )
            if binds:
                return binds[-1]
        return None
