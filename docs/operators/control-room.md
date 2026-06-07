# Control Room

`control_room.py` is the main live operator surface.

Run it with:

```sh
uv run python3 control_room.py --config config.toml
uv run python3 control_room.py --config config.toml --market aluminium
```

## Panels

- `SHIP STATUS`: commander, system, station, flight state, fuel, credits, cargo, FSD target
- `ACTIVITY`: live event log plus routine progress lines
- `MARKET`: commodity table from `Market.json`, with filtering and lock/unlock controls

## Main Commands

- `dock`
- `undock`
- `jump`
- `buy <item> [N|max]`
- `sell`
- `sell <item> [N|max]`
- `haul [commodity]`
- `dest <system>`
- `set_dest <system>`

## Other Commands

- `market filter <name>`
- `market`
- `market clear`
- `market lock`
- `market unlock`
- `replay`
- `commands`
- `help [command]`
- `q`, `quit`, `exit`

## Notes

- Only one routine runs at a time.
- `Ctrl-R` opens replay/history from the command bar.
- In replay/history, typing applies a simple prefix filter; `Backspace` deletes the filter.
- `Ctrl-C` and `Ctrl-D` cancel the active routine without closing the TUI; when idle they exit the app.
- `sell` with no explicit item falls back to `Cargo.json` if the in-memory cargo manifest is empty.
- Cross-session command history and one saved default haul profile are persisted in `.control_room_state.json` by default.
