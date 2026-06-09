# Session Log

_This is the rolling short-form log for recent sessions. Keep entries concise and operational. Hard limit: 20 lines. If a new entry would exceed the limit, append the full current log to `docs/status-archive.md`, then reset this file to a fresh empty log template before writing the new entry._

## 2026-06-09

- Market `buy ... max` already used free cargo space rather than full hold capacity; it now also clamps the hold-time estimate to current station `Stock`, so MAX buys stop at the smaller of free space and supply. Verified with `uv run python3 -m unittest tests/test_routines.py` and `uv run python3 -m unittest discover -s tests` (`313` tests, `0.126s`).
