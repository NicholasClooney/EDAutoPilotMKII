# TODOs

## Parked

### Previous Python environment cleanup

- Figure out which Python environment previously held the working project dependencies before `mise` became the active `python3`.
- Identify where those packages were installed.
- Decide whether that older environment should be removed or kept as a reference.
- If removing it, document the cleanup steps before deletion.

### OpenCV and Python version compatibility

- Current `mise` / `uv` setup is on Python `3.12`.
- The pinned `opencv-python~=4.2.0.34` does not resolve on Python `3.12`.
- Decide later whether to:
  - move to a newer OpenCV version compatible with `3.12`, or
  - use an older Python version for legacy dependency compatibility.

## Active

### Manual control path

- Use `ship_controls.py` as the current live manual control entry point instead of `diagnostics.py`.
- Extend it as needed for direct action testing beyond `SetSpeedZero`.
- Confirmed on the current setup: flight controls respond when the macOS backend sends real key-down, short dwell, and key-up events.
- Use this path as the baseline for further ship-control testing instead of the older tap-style `keystroke` behavior.

### Manual harness

- Keep `ship_controls.py` as the human test surface for live in-game control testing.
- Add only the smallest features that materially improve manual verification loops.
- Avoid turning it into a second app, console, or long-term runtime surface.
- Good future candidates: `--interval-seconds`, `--dry-run`, and explicit `tap|press|release` mode selection.
