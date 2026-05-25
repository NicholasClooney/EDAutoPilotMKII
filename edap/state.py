from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from json import loads
from pathlib import Path


@dataclass(frozen=True)
class ShipState:
    time_since_log_update_s: int
    status: str | None
    ship_type: str | None
    location: str | None
    star_class: str | None
    target: str | None
    fuel_capacity: float | None
    fuel_level: float | None
    fuel_percent: int
    is_scooping: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def get_latest_journal_log(journal_dir: Path) -> Path | None:
    logs = sorted(journal_dir.glob("Journal.*"), key=lambda item: item.stat().st_mtime)
    if not logs:
        return None
    return logs[-1]


def read_ship_state(log_path: Path) -> ShipState:
    last_modified = datetime.fromtimestamp(log_path.stat().st_mtime)
    ship = {
        "time_since_log_update_s": int((datetime.now() - last_modified).total_seconds()),
        "status": None,
        "ship_type": None,
        "location": None,
        "star_class": None,
        "target": None,
        "fuel_capacity": None,
        "fuel_level": None,
        "fuel_percent": 10,
        "is_scooping": False,
    }

    with log_path.open(encoding="utf-8") as handle:
        for line in handle:
            log = loads(line)
            event = log.get("event")

            if event == "StartJump":
                ship["status"] = f"starting_{log['JumpType']}".lower()
                if log["JumpType"] == "Hyperspace":
                    ship["star_class"] = log.get("StarClass")
            elif event in {"SupercruiseEntry", "FSDJump"}:
                ship["status"] = "in_supercruise"
            elif (
                event in {"SupercruiseExit", "DockingCancelled", "Undocked"}
                or (event == "Music" and ship["status"] == "in_undocking")
                or (event == "Location" and log.get("Docked") is False)
            ):
                ship["status"] = "in_space"
            elif event == "DockingRequested":
                ship["status"] = "starting_docking"
            elif event == "Music" and log.get("MusicTrack") == "DockingComputer":
                if ship["status"] == "starting_undocking":
                    ship["status"] = "in_undocking"
                elif ship["status"] == "starting_docking":
                    ship["status"] = "in_docking"
            elif event == "Docked":
                ship["status"] = "in_station"

            if event in {"LoadGame", "Loadout"}:
                ship["ship_type"] = log.get("Ship")

            if "FuelLevel" in log and ship["ship_type"] != "TestBuggy":
                ship["fuel_level"] = log["FuelLevel"]
            if "FuelCapacity" in log and ship["ship_type"] != "TestBuggy":
                fuel_capacity = log["FuelCapacity"]
                if isinstance(fuel_capacity, dict):
                    ship["fuel_capacity"] = fuel_capacity.get("Main")
                else:
                    ship["fuel_capacity"] = fuel_capacity
            if event == "FuelScoop" and "Total" in log:
                ship["fuel_level"] = log["Total"]
            if ship["fuel_level"] and ship["fuel_capacity"]:
                ship["fuel_percent"] = round((ship["fuel_level"] / ship["fuel_capacity"]) * 100)
            else:
                ship["fuel_percent"] = 10

            ship["is_scooping"] = bool(
                event == "FuelScoop"
                and ship["time_since_log_update_s"] < 10
                and ship["fuel_percent"] < 100
            )

            if event in {"Location", "FSDJump"} and "StarSystem" in log:
                ship["location"] = log["StarSystem"]

            if event == "FSDTarget":
                if log.get("Name") == ship["location"]:
                    ship["target"] = None
                else:
                    ship["target"] = log.get("Name")
            elif event == "FSDJump" and ship["location"] == ship["target"]:
                ship["target"] = None

    return ShipState(**ship)
