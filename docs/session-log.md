# Session Log

_This is the rolling short-form log for recent sessions. Keep entries concise and operational. Hard limit: 20 lines. If a new entry would exceed the limit, append the full current log to `docs/status-archive.md`, then reset this file to a fresh empty log template before writing the new entry._

## 2026-06-08

- Two-way haul startup now infers the active station/phase from journal position, `Cargo.json`, and `Market.json` fallback data. Added regression coverage for station-2 startup cases.
- Added test timing guardrails: `tools/check_test_timing.py`, CI guard for `tests/test_haul_loop.py`, and support for both single-target and full-suite `unittest discover` timing checks.
- Trimmed `docs/STATUS.md` into a compact handoff document and moved long-form status/history into `docs/status-archive.md`.
