# Quickstart

## Setup

### macOS + CrossOver

1. Copy `config.example.toml` to `config.toml`.
2. Set `paths.journal_dir` and `paths.bindings_file` explicitly if auto-detection is not enough on this machine.
3. Leave `runtime.platform` unset unless you want to make the backend choice explicit in a shared config. When omitted, it defaults to the host OS.
4. Make sure Terminal has macOS Accessibility permission, and Screen Recording permission if you plan to use capture-based diagnostics.
5. Start Elite Dangerous through CrossOver.

### Windows with `uv`

1. Install Python 3.12 and `uv`.
2. Run `uv sync`.
3. Copy `config.example.toml` to `config.toml`.
4. Leave `runtime.platform` unset unless you want to make the backend choice explicit in a shared config. When omitted, it defaults to the host OS.
5. Set `paths.journal_dir` and `paths.bindings_file` explicitly.
6. Start Elite Dangerous.

### Windows without `uv`

1. Install Python 3.12.
2. Create a virtual environment:

```sh
python -m venv .venv
```

3. Activate it:

```sh
.venv\Scripts\activate
```

4. Install runtime deps:

```sh
pip install -r requirements.txt
```

5. Copy `config.example.toml` to `config.toml`.
6. Leave `runtime.platform` unset unless you want to make the backend choice explicit in a shared config. When omitted, it defaults to the host OS.
7. Set `paths.journal_dir` and `paths.bindings_file` explicitly.
8. Start Elite Dangerous.

## First Checks

On macOS:

```sh
uv run python3 diagnostics.py --config config.toml
uv run python3 watch_journal.py --config config.toml
uv run python3 ship_controls.py --config config.toml --action SetSpeedZero --delay-seconds 3
```

On Windows with `uv`:

```sh
uv run python diagnostics.py --config config.toml --send-test-key
uv run python ship_controls.py --config config.toml --action SetSpeedZero --delay-seconds 3
```

On Windows without `uv`:

```sh
python diagnostics.py --config config.toml --send-test-key
python ship_controls.py --config config.toml --action SetSpeedZero --delay-seconds 3
```

Validate `diagnostics.py --send-test-key` first on Windows. That proves the `SendInput` path reaches Elite before you debug bindings or routines.

## Main Runtime

```sh
uv run python3 control_room.py --config config.toml
```

Control Room is the primary operator surface for current routine work.

Windows equivalents:

```sh
uv run python control_room.py --config config.toml
python control_room.py --config config.toml
```

## Routine Harness

```sh
uv run python3 run_routine.py --config config.toml --routine jump --delay-seconds 5
uv run python3 run_routine.py --config config.toml --routine dock --delay-seconds 5 --log-events
uv run python3 run_routine.py --config config.toml --routine haul_loop
```

Windows equivalents:

```sh
uv run python run_routine.py --config config.toml --routine jump --delay-seconds 5
python run_routine.py --config config.toml --routine jump --delay-seconds 5
```

For current supported manual validation flows, see [../operators/manual-journal-routine-testing.md](../operators/manual-journal-routine-testing.md).
