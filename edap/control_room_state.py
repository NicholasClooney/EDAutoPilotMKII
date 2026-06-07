from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


@dataclass
class CommandHistoryEntry:
    raw: str
    command: str
    params: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""


@dataclass
class ControlRoomState:
    default_haul: dict[str, str] = field(default_factory=dict)
    history: list[CommandHistoryEntry] = field(default_factory=list)


def load_control_room_state(path: Path) -> ControlRoomState:
    if not path.exists():
        return ControlRoomState()

    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    if not isinstance(raw, dict):
        return ControlRoomState()

    default_haul = raw.get("default_haul", raw.get("haul_defaults", {}))
    if not isinstance(default_haul, dict):
        default_haul = {}

    raw_history = raw.get("history", [])
    history: list[CommandHistoryEntry] = []
    if isinstance(raw_history, list):
        for item in raw_history:
            if not isinstance(item, dict):
                continue
            raw_command = item.get("raw", "")
            command = item.get("command", "")
            params = item.get("params", {})
            timestamp = item.get("timestamp", "")
            if not isinstance(raw_command, str) or not isinstance(command, str):
                continue
            if not isinstance(params, dict):
                params = {}
            if not isinstance(timestamp, str):
                timestamp = ""
            history.append(
                CommandHistoryEntry(
                    raw=raw_command,
                    command=command,
                    params=params,
                    timestamp=timestamp,
                )
            )

    return ControlRoomState(
        default_haul={str(key): str(value) for key, value in default_haul.items()},
        history=history,
    )


def save_control_room_state(path: Path, state: ControlRoomState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "default_haul": state.default_haul,
        "history": [
            {
                "raw": entry.raw,
                "command": entry.command,
                "params": entry.params,
                "timestamp": entry.timestamp,
            }
            for entry in state.history
        ],
    }

    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_path = Path(handle.name)

    temp_path.replace(path)
