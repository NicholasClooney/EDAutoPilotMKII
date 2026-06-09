# Devlog 0002: Control Room Location Regression

## Summary

On 2026-06-09, a live Control Room session exposed a regression where:

- Ship Status showed the correct system but missed the current station.
- The Market panel showed the current station name but the wrong system.
- `edap/routines/haul_two_way.py` inferred the wrong current station/system for startup and resume.

This was not a journal ingestion failure. It was a consistency failure between multiple location readers.

## Root Cause

Two changes combined into a bad state shape:

1. The June 7 Control Room refactor moved bootstrap logic into `edap/control_room/bootstrap.py`.
   Bootstrap restored `system`, `status`, and other fields from `read_ship_state()`, but it did not restore `station`.

2. The June 8 two-way haul startup hardening added `_detect_start_phase()`, which tried to infer the current location from the trailing journal position event and then fell back to `Market.json` when fields were missing.

That created a split source of truth:

- the shared journal snapshot knew the current system/status
- the Control Room market header trusted `Market.json`
- haul startup mixed a partial journal event with `Market.json`

When the latest docked position was represented by a trailing `Docked` event without `StarSystem`, and `Market.json` still reflected an older market screen, the UI and haul logic diverged.

## Why The Tests Passed Before The Fix

The old tests exercised the happy path but not the stale-data path:

- Control Room tests proved that `Market.json` could seed station/system when bootstrap had no station.
- haul startup tests covered missing-journal-position fallback through `Market.json`.
- shared journal-state tests tracked `location` and `status`, but not persistent `station`.

What was missing:

- a journal snapshot test that asserted station persistence across docked bootstrap
- a Control Room bootstrap test where journal state and `Market.json` disagree
- a haul startup test where the latest docked state is valid but incomplete, and `Market.json` is stale

So the suite passed because it encoded the same assumption the regression depended on: that `Market.json` was an acceptable primary location source during docked startup.

## Fix Applied

- `edap/state.py` now carries `station` in the shared ship snapshot.
- Control Room bootstrap restores `station` from the shared journal snapshot.
- Control Room market headers prefer journal-derived docked location over `Market.json` metadata.
- `haul_two_way._detect_start_phase()` now derives current station/system from the full journal snapshot first, instead of reconstructing it from a trailing event plus `Market.json`.
- Regression tests now cover docked bootstrap and stale `Market.json` disagreement.

## Prevention

The main prevention rule is simple: current ship location must come from one canonical state reducer.

Future changes should follow these guardrails:

1. Treat `read_ship_state()` as the canonical bootstrap/resume source for current ship location.
   `Market.json` can enrich market contents, but it should not be the primary source for current station/system when journal state exists.

2. Do not rebuild current location from ad hoc trailing-event scans in feature code.
   If a routine needs more state, extend the shared snapshot instead of creating another partial reader.

3. Add disagreement tests whenever two files can report overlapping state.
   For this codebase that means journal vs `Market.json`, journal vs `Cargo.json`, and live event reducer vs bootstrap snapshot.

4. Prefer invariant-style tests over only happy-path tests.
   Useful invariant here: when docked, Ship Status, Market header, and haul startup should resolve the same current station/system from the same journal history.

5. Add one small bootstrap fixture set specifically for stale sidecar files.
   We should keep reusable fixtures where:
   - journal is authoritative
   - `Market.json` is stale
   - `Cargo.json` is stale
   - the latest event omits fields that an earlier event established

## Follow-Up Idea

If location/state drift shows up again, the next step should be a dedicated shared snapshot type for Control Room and routines rather than letting each consumer reshape journal facts independently.
