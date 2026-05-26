from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


DEFAULT_CONFIG_PATH = Path("config.toml")
EXAMPLE_CONFIG_PATH = Path("config.example.toml")

VALID_PLATFORMS = {"macos", "windows"}


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


class ConfigError(ValueError):
    """Raised when config parsing or validation fails."""


def _optional_path(value: object) -> Path | None:
    if not value:
        return None
    return Path(str(value)).expanduser()


def _require_table(raw: dict[str, object], key: str) -> dict[str, object]:
    value = raw.get(key, {})
    if not isinstance(value, dict):
        raise ConfigError(f"Config section `{key}` must be a table.")
    return value


def _string(raw: dict[str, object], key: str, default: str) -> str:
    value = raw.get(key, default)
    if not isinstance(value, str):
        raise ConfigError(f"Config value `{key}` must be a string.")
    return value


def _integer(raw: dict[str, object], key: str, default: int) -> int:
    value = raw.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"Config value `{key}` must be an integer.")
    return value


def _float(raw: dict[str, object], key: str, default: float) -> float:
    value = raw.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"Config value `{key}` must be a number.")
    return float(value)


def _boolean(raw: dict[str, object], key: str, default: bool) -> bool:
    value = raw.get(key, default)
    if not isinstance(value, bool):
        raise ConfigError(f"Config value `{key}` must be true or false.")
    return value


def _validate_path_shape(path: Path | None, *, key: str, should_be_dir: bool) -> None:
    if path is None or not path.exists():
        return
    if should_be_dir and not path.is_dir():
        raise ConfigError(f"Config path `{key}` must point to a directory: {path}")
    if not should_be_dir and not path.is_file():
        raise ConfigError(f"Config path `{key}` must point to a file: {path}")


def validate_config(config: AppConfig) -> AppConfig:
    if not config.controls.start_hotkey.strip():
        raise ConfigError("Config value `controls.start_hotkey` cannot be empty.")
    if not config.controls.stop_hotkey.strip():
        raise ConfigError("Config value `controls.stop_hotkey` cannot be empty.")
    if config.screen.resolution_width <= 0:
        raise ConfigError("Config value `screen.resolution_width` must be greater than 0.")
    if config.screen.resolution_height <= 0:
        raise ConfigError("Config value `screen.resolution_height` must be greater than 0.")
    if config.screen.scale <= 0:
        raise ConfigError("Config value `screen.scale` must be greater than 0.")
    if config.runtime.platform.lower() not in VALID_PLATFORMS:
        supported = ", ".join(sorted(VALID_PLATFORMS))
        raise ConfigError(
            f"Config value `runtime.platform` must be one of: {supported}."
        )

    _validate_path_shape(config.paths.journal_dir, key="paths.journal_dir", should_be_dir=True)
    _validate_path_shape(config.paths.bindings_file, key="paths.bindings_file", should_be_dir=False)
    if config.screen.capture_debug_path and config.screen.capture_debug_path.exists():
        if config.screen.capture_debug_path.is_dir():
            raise ConfigError(
                "Config value `screen.capture_debug_path` must point to a file, not a directory."
            )

    return config


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    if not isinstance(raw, dict):
        raise ConfigError("Config root must be a TOML table.")

    paths = _require_table(raw, "paths")
    controls = _require_table(raw, "controls")
    screen = _require_table(raw, "screen")
    runtime = _require_table(raw, "runtime")

    config = AppConfig(
        paths=PathsConfig(
            journal_dir=_optional_path(paths.get("journal_dir")),
            bindings_file=_optional_path(paths.get("bindings_file")),
        ),
        controls=ControlsConfig(
            start_hotkey=_string(controls, "start_hotkey", "home"),
            stop_hotkey=_string(controls, "stop_hotkey", "end"),
            scanner_mode=_string(controls, "scanner_mode", "off"),
        ),
        screen=ScreenConfig(
            resolution_width=_integer(screen, "resolution_width", 1920),
            resolution_height=_integer(screen, "resolution_height", 1080),
            scale=_float(screen, "scale", 1.0),
            capture_debug_path=_optional_path(screen.get("capture_debug_path")),
        ),
        runtime=RuntimeConfig(
            platform=_string(runtime, "platform", "macos"),
            debug=_boolean(runtime, "debug", True),
        ),
    )
    return validate_config(config)
