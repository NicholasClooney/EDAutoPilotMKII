from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from time import sleep

from edap.bindings import read_bindings
from edap.config import AppConfig
from edap.platform.input.factory import build_input_controller
from edap.platform.paths.factory import build_game_paths
from edap.platform.screen.factory import build_screen_capture
from edap.state import get_latest_journal_log, read_ship_state


@dataclass(frozen=True)
class DiagnosticsOptions:
    capture_screen: bool = False
    send_test_key: bool = False
    test_key: str = "space"
    test_modifier: str | None = None
    hold_s: float = 0.0
    delay_s: float = 0.0
    repeat: int = 1


def _path_status(path: Path | None) -> str:
    if path is None:
        return "not configured"
    if path.exists():
        return "ok"
    return "missing"


def run_diagnostics(config: AppConfig, options: DiagnosticsOptions) -> dict[str, object]:
    game_paths = build_game_paths(config.runtime.platform)
    configured_journal_dir = config.paths.journal_dir
    configured_bindings_file = config.paths.bindings_file
    default_journal_dir = game_paths.default_journal_dir() if game_paths else None
    default_bindings_file = game_paths.default_bindings_file() if game_paths else None
    effective_journal_dir = configured_journal_dir or default_journal_dir
    effective_bindings_file = configured_bindings_file or default_bindings_file

    result: dict[str, object] = {
        "platform": config.runtime.platform,
        "debug": config.runtime.debug,
        "controls": {
            "start_hotkey": config.controls.start_hotkey,
            "stop_hotkey": config.controls.stop_hotkey,
            "scanner_mode": config.controls.scanner_mode,
        },
        "paths": {
            "journal_dir": str(configured_journal_dir) if configured_journal_dir else None,
            "journal_dir_status": _path_status(configured_journal_dir),
            "bindings_file": str(configured_bindings_file) if configured_bindings_file else None,
            "bindings_file_status": _path_status(configured_bindings_file),
            "default_journal_dir": str(default_journal_dir) if default_journal_dir else None,
            "default_bindings_file": str(default_bindings_file) if default_bindings_file else None,
            "effective_journal_dir": str(effective_journal_dir) if effective_journal_dir else None,
            "effective_bindings_file": str(effective_bindings_file) if effective_bindings_file else None,
        },
        "options": asdict(options),
    }

    if effective_journal_dir and effective_journal_dir.exists():
        latest_log = get_latest_journal_log(effective_journal_dir)
        result["latest_log"] = str(latest_log) if latest_log else None
        if latest_log:
            ship_state = read_ship_state(latest_log)
            result["ship_state"] = ship_state.to_dict()

    if effective_bindings_file and effective_bindings_file.exists():
        bindings, missing = read_bindings(effective_bindings_file)
        result["bindings"] = {name: binding.to_dict() for name, binding in sorted(bindings.items())}
        result["missing_bindings"] = missing

    if options.capture_screen:
        result["screen_capture"] = run_screen_capture_diagnostic(config)

    if options.send_test_key:
        result["input_test"] = run_input_diagnostic(config, options)

    return result


def run_screen_capture_diagnostic(config: AppConfig) -> dict[str, object]:
    screen_capture = build_screen_capture(config.runtime.platform)
    if screen_capture is None:
        return {"status": "unsupported"}

    width = int(config.screen.resolution_width * config.screen.scale)
    height = int(config.screen.resolution_height * config.screen.scale)
    image = screen_capture.capture_region(0, 0, width, height)

    output_path = config.screen.capture_debug_path
    saved_path = None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        saved_path = str(output_path)

    return {
        "status": "ok",
        "width": getattr(image, "width", width),
        "height": getattr(image, "height", height),
        "saved_path": saved_path,
    }


def run_input_diagnostic(config: AppConfig, options: DiagnosticsOptions) -> dict[str, object]:
    try:
        input_controller = build_input_controller(config.runtime.platform)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    if input_controller is None:
        return {"status": "unsupported"}

    try:
        if options.delay_s > 0:
            sleep(options.delay_s)
        for _ in range(max(1, options.repeat)):
            input_controller.tap_key(
                options.test_key,
                modifier=options.test_modifier,
                hold_s=options.hold_s,
            )
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    return {
        "status": "ok",
        "test_key": options.test_key,
        "test_modifier": options.test_modifier,
        "hold_s": options.hold_s,
        "delay_s": options.delay_s,
        "repeat": options.repeat,
    }
