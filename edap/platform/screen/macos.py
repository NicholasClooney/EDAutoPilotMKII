from __future__ import annotations

from PIL import ImageGrab

from .base import ScreenCapture


class MacOSScreenCapture(ScreenCapture):
    def capture_region(self, x_left: int, y_top: int, x_right: int, y_bottom: int) -> object:
        return ImageGrab.grab(bbox=(x_left, y_top, x_right, y_bottom))
