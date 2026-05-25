from __future__ import annotations

from abc import ABC, abstractmethod


class ScreenCapture(ABC):
    @abstractmethod
    def capture_region(self, x_left: int, y_top: int, x_right: int, y_bottom: int) -> object:
        """Capture a screen region and return an image-like object."""
