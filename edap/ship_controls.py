from __future__ import annotations

from pathlib import Path

from edap.actions import ActionDispatchResult, ActionDispatcher
from edap.binding_lookup import BindingLookup, load_binding_lookup
from edap.platform.input.base import InputController


DEFAULT_SHIP_CONTROL_ACTIONS = [
    "SetSpeedZero",
    "SetSpeed100",
    "RollLeftButton",
    "RollRightButton",
    "UI_Select",
]


class ShipControls:
    """Narrow runtime-facing ship control wrapper for binding-driven actions."""

    def __init__(self, dispatcher: ActionDispatcher) -> None:
        self._dispatcher = dispatcher

    @classmethod
    def from_binding_lookup(
        cls,
        binding_lookup: BindingLookup,
        input_controller: InputController,
    ) -> ShipControls:
        return cls(ActionDispatcher(binding_lookup, input_controller))

    @classmethod
    def from_bindings_file(
        cls,
        bindings_file: Path,
        input_controller: InputController,
        actions: list[str] | None = None,
    ) -> ShipControls:
        binding_lookup = load_binding_lookup(bindings_file, actions=actions or DEFAULT_SHIP_CONTROL_ACTIONS)
        return cls.from_binding_lookup(binding_lookup, input_controller)

    def tap_action(self, action: str, repeat: int = 1, hold_s: float = 0.0) -> ActionDispatchResult:
        return self._dispatcher.tap_action(action, repeat=repeat, hold_s=hold_s)

    def set_speed_zero(self, repeat: int = 1, hold_s: float = 0.0) -> ActionDispatchResult:
        return self.tap_action("SetSpeedZero", repeat=repeat, hold_s=hold_s)

    def set_speed_full(self, repeat: int = 1, hold_s: float = 0.0) -> ActionDispatchResult:
        return self.tap_action("SetSpeed100", repeat=repeat, hold_s=hold_s)

    def roll_left(self, repeat: int = 1, hold_s: float = 0.0) -> ActionDispatchResult:
        return self.tap_action("RollLeftButton", repeat=repeat, hold_s=hold_s)

    def roll_right(self, repeat: int = 1, hold_s: float = 0.0) -> ActionDispatchResult:
        return self.tap_action("RollRightButton", repeat=repeat, hold_s=hold_s)

    def ui_select(self, repeat: int = 1, hold_s: float = 0.0) -> ActionDispatchResult:
        return self.tap_action("UI_Select", repeat=repeat, hold_s=hold_s)
