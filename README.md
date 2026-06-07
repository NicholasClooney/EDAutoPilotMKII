# EDAutopilot MK II

macOS-first Elite Dangerous automation tooling for CrossOver, with future Windows compatibility kept as a constraint rather than the current target.

The current operator surface is [`control_room.py`](control_room.py). The project is not a full autopilot yet; it is a live runtime and routine stack built around journal parsing, bindings lookup, synthetic input, and early workflow automation.

See [docs/STATUS.md](docs/STATUS.md) for the maintained status, validation notes, and next recommended work.

## Current Surface

What works today:

- macOS journal, bindings, screen-capture, and Quartz input plumbing
- journal-driven `jump`, `dock`, `undock`, `buy`, `sell`, `haul`, and `dest` flows
- a live Control Room TUI with ship status, activity log, market panel, replay history, and saved default haul setup

What is not done:

- the legacy CV-driven align loop is still not ported into the active runtime
- the repo still needs a real tracked Control Room screenshot; the asset slot is reserved under `docs/assets/`

## Primary Entrypoints

- `uv run python3 control_room.py --config config.toml`
- `uv run python3 run_routine.py --config config.toml --routine haul_loop`
- `uv run python3 diagnostics.py --config config.toml`
- `uv run python3 ship_controls.py --config config.toml --action SetSpeedZero --delay-seconds 3`

## Routine Overview

`haul` is the strongest current end-to-end routine. Around it, the active routine surface includes:

- `dock`
- `undock`
- `jump`
- `buy`
- `sell`
- `dest`

These are built to be manually exercised against a live Elite session running through CrossOver, not left unattended.

## Repo Layout

- `control_room.py`, `run_routine.py`, `diagnostics.py`, `ship_controls.py`: active operator and validation entrypoints
- `edap/`: active runtime code
- `tools/scratch/`: exploratory probes and one-off validation helpers
- `archive/legacy-windows/`: Windows-era behavior reference code, kept for historical context only

## Docs Map

- [docs/getting-started/quickstart.md](docs/getting-started/quickstart.md)
- [docs/operators/control-room.md](docs/operators/control-room.md)
- [docs/operators/manual-journal-routine-testing.md](docs/operators/manual-journal-routine-testing.md)
- [docs/diagnostics/cli-reference.md](docs/diagnostics/cli-reference.md)
- [docs/diagnostics/bindings-reference.md](docs/diagnostics/bindings-reference.md)
- [docs/README.md](docs/README.md)

## Development

Use the repo `uv` environment for tests:

```sh
uv run python3 -m unittest discover -s tests
```

For commits, use Conventional Commits.

Examples:

- `feat: add config loader`
- `refactor: split platform adapters from autopilot logic`
- `docs: update macos roadmap`
- `fix: validate missing journal path`
