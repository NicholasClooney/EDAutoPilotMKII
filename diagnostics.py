from __future__ import annotations

import argparse
import json
import sys

from edap.config import DEFAULT_CONFIG_PATH, EXAMPLE_CONFIG_PATH, load_config
from edap.diagnostics import DiagnosticsOptions, run_diagnostics


def main() -> int:
    parser = argparse.ArgumentParser(description="EDAutopilot diagnostic runner")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to config TOML file",
    )
    parser.add_argument(
        "--capture-screen",
        action="store_true",
        help="Capture a full-screen debug image using the configured resolution and scale",
    )
    args = parser.parse_args()

    config_path = args.config
    try:
        config = load_config(config_path)
        using_fallback = False
    except FileNotFoundError:
        if config_path == str(DEFAULT_CONFIG_PATH) and EXAMPLE_CONFIG_PATH.exists():
            config = load_config(EXAMPLE_CONFIG_PATH)
            using_fallback = True
            config_path = str(EXAMPLE_CONFIG_PATH)
        else:
            sys.stderr.write(
                f"Config file not found: {config_path}\n"
                f"Create `config.toml` from `config.example.toml`, or pass `--config /path/to/config.toml`.\n"
            )
            return 2
    options = DiagnosticsOptions(
        capture_screen=args.capture_screen,
    )
    result = run_diagnostics(config, options)
    result["config_path"] = config_path
    result["used_example_config_fallback"] = using_fallback

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
