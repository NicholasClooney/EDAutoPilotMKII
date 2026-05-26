from __future__ import annotations

from dataclasses import dataclass
from time import sleep
from typing import Callable, Protocol

from edap.actions import ActionDispatchResult


class SupportsSetSpeedZero(Protocol):
    def set_speed_zero(self, repeat: int = 1, hold_s: float = 0.0) -> ActionDispatchResult:
        """Dispatch the SetSpeedZero action."""


@dataclass(frozen=True)
class RoutineResult:
    action: str
    dispatch: ActionDispatchResult
    wait_s: float = 0.0


def set_speed_zero_then_wait(
    controls: SupportsSetSpeedZero,
    *,
    repeat: int = 1,
    hold_s: float = 0.0,
    wait_s: float = 0.0,
    sleeper: Callable[[float], None] = sleep,
) -> RoutineResult:
    if wait_s < 0:
        raise ValueError("wait_s must be non-negative")

    dispatch = controls.set_speed_zero(repeat=repeat, hold_s=hold_s)
    if dispatch.status == "ok" and wait_s > 0:
        sleeper(wait_s)

    return RoutineResult(
        action="SetSpeedZero",
        dispatch=dispatch,
        wait_s=wait_s,
    )
