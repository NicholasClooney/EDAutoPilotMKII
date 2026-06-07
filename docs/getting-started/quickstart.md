# Quickstart

## Setup

1. Copy `config.example.toml` to `config.toml`.
2. Set `paths.journal_dir` and `paths.bindings_file` explicitly if auto-detection is not enough on this machine.
3. Make sure Terminal has macOS Accessibility permission, and Screen Recording permission if you plan to use capture-based diagnostics.
4. Start Elite Dangerous through CrossOver.

## First Checks

```sh
uv run python3 diagnostics.py --config config.toml
uv run python3 watch_journal.py --config config.toml
uv run python3 ship_controls.py --config config.toml --action SetSpeedZero --delay-seconds 3
```

## Main Runtime

```sh
uv run python3 control_room.py --config config.toml
```

Control Room is the primary operator surface for current routine work.

## Routine Harness

```sh
uv run python3 run_routine.py --config config.toml --routine jump --delay-seconds 5
uv run python3 run_routine.py --config config.toml --routine dock --delay-seconds 5 --log-events
uv run python3 run_routine.py --config config.toml --routine haul_loop
```

For current supported manual validation flows, see [../operators/manual-journal-routine-testing.md](../operators/manual-journal-routine-testing.md).
