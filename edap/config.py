from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


DEFAULT_CONFIG_PATH = Path("config.toml")
EXAMPLE_CONFIG_PATH = Path("config.example.toml")


@dataclass(frozen=True)
class PathsConfig:
    journal_dir: Path | None
    bindings_file: Path | None


@dataclass(frozen=True)
class ControlsConfig:
    start_hotkey: str
    stop_hotkey: str
    scanner_mode: str


@dataclass(frozen=True)
class ScreenConfig:
    resolution_width: int
    resolution_height: int
    scale: float
    capture_debug_path: Path | None


@dataclass(frozen=True)
class RuntimeConfig:
    platform: str
    debug: bool


@dataclass(frozen=True)
class AppConfig:
    paths: PathsConfig
    controls: ControlsConfig
    screen: ScreenConfig
    runtime: RuntimeConfig


def _optional_path(value: object) -> Path | None:
    if not value:
        return None
    return Path(str(value)).expanduser()


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    paths = raw.get("paths", {})
    controls = raw.get("controls", {})
    screen = raw.get("screen", {})
    runtime = raw.get("runtime", {})

    return AppConfig(
        paths=PathsConfig(
            journal_dir=_optional_path(paths.get("journal_dir")),
            bindings_file=_optional_path(paths.get("bindings_file")),
        ),
        controls=ControlsConfig(
            start_hotkey=str(controls.get("start_hotkey", "home")),
            stop_hotkey=str(controls.get("stop_hotkey", "end")),
            scanner_mode=str(controls.get("scanner_mode", "off")),
        ),
        screen=ScreenConfig(
            resolution_width=int(screen.get("resolution_width", 1920)),
            resolution_height=int(screen.get("resolution_height", 1080)),
            scale=float(screen.get("scale", 1.0)),
            capture_debug_path=_optional_path(screen.get("capture_debug_path")),
        ),
        runtime=RuntimeConfig(
            platform=str(runtime.get("platform", "macos")),
            debug=bool(runtime.get("debug", True)),
        ),
    )
