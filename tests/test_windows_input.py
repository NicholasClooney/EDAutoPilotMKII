from __future__ import annotations

import unittest

from edap.platform.input.windows import KEY_CODES, WindowsInputController


class FakeBackend:
    def __init__(self) -> None:
        self.events: list[tuple] = []

    def send(self, scan_code: int, down: bool) -> None:
        self.events.append(("down" if down else "up", scan_code))

    def sleep(self, duration: float) -> None:
        self.events.append(("sleep", duration))


def _build() -> tuple[WindowsInputController, FakeBackend]:
    backend = FakeBackend()
    return (
        WindowsInputController(sender=backend.send, sleeper=backend.sleep),
        backend,
    )


class WindowsInputControllerTests(unittest.TestCase):
    def test_tap_letter_with_hold(self) -> None:
        controller, backend = _build()

        controller.tap_key("a", hold_s=0.1)

        self.assertEqual(
            backend.events,
            [
                ("down", KEY_CODES["a"]),
                ("sleep", 0.1),
                ("up", KEY_CODES["a"]),
            ],
        )

    def test_tap_with_modifier_presses_modifier_first(self) -> None:
        controller, backend = _build()

        controller.tap_key("x", modifier="control", hold_s=0.05)

        self.assertEqual(
            backend.events,
            [
                ("down", KEY_CODES["left_control"]),
                ("down", KEY_CODES["x"]),
                ("sleep", 0.05),
                ("up", KEY_CODES["x"]),
                ("up", KEY_CODES["left_control"]),
            ],
        )

    def test_press_and_release_with_modifier_are_split(self) -> None:
        controller, backend = _build()

        controller.press_key("left", modifier="right_control")
        controller.release_key("left", modifier="right_control")

        self.assertEqual(
            backend.events,
            [
                ("down", KEY_CODES["right_control"]),
                ("down", KEY_CODES["left"]),
                ("up", KEY_CODES["left"]),
                ("up", KEY_CODES["right_control"]),
            ],
        )

    def test_type_text_uses_shift_for_uppercase(self) -> None:
        controller, backend = _build()

        controller.type_text("Sol", char_delay_s=0.0)

        self.assertEqual(
            backend.events,
            [
                ("down", KEY_CODES["left_shift"]),
                ("down", KEY_CODES["s"]),
                ("up", KEY_CODES["s"]),
                ("up", KEY_CODES["left_shift"]),
                ("down", KEY_CODES["o"]),
                ("up", KEY_CODES["o"]),
                ("down", KEY_CODES["l"]),
                ("up", KEY_CODES["l"]),
            ],
        )

    def test_type_text_supports_shifted_punctuation(self) -> None:
        controller, backend = _build()

        controller.type_text("?", char_delay_s=0.0)

        self.assertEqual(
            backend.events,
            [
                ("down", KEY_CODES["left_shift"]),
                ("down", KEY_CODES["/"]),
                ("up", KEY_CODES["/"]),
                ("up", KEY_CODES["left_shift"]),
            ],
        )

    def test_unsupported_key_raises(self) -> None:
        controller, _ = _build()

        with self.assertRaises(ValueError):
            controller.tap_key("not_a_real_key")

    def test_unsupported_modifier_raises(self) -> None:
        controller, _ = _build()

        with self.assertRaises(ValueError):
            controller.tap_key("a", modifier="weird")

    def test_unsupported_character_raises(self) -> None:
        controller, _ = _build()

        with self.assertRaises(ValueError):
            controller.type_text("\u00e9", char_delay_s=0.0)
