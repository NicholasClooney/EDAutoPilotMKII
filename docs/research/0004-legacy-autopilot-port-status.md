# Legacy Autopilot Architecture and Port Status

Date: 2026-05-26

## Scope

This note maps the original (upstream EDAutopilot) autopilot architecture against what has been ported into the macOS-first `edap/` package, and records the still-unverified pieces on the new platform.

The intent is to give future work a clear "what exists, what is stub, what is not ported, and what is unproven" map without having to re-read the legacy code each time.

## Original Autopilot, In One Page

The legacy autopilot lives almost entirely in `dev_autopilot.py` and runs a journal-event-driven state machine wrapped around an OpenCV alignment loop.

### Loop shape

`dev_autopilot.py:1284-1305` is the main loop. While the ship has a target:

1. read the journal via `ship()` (`dev_autopilot.py:151-248`) and update derived state
2. inspect status flags (`in_space`, `in_supercruise`, `starting_hyperspace`, `starting_docking`, ...)
3. dispatch the next mode in order: `align` -> `jump` -> `refuel` -> `position`
4. actuate by resolving Elite XML bindings to scancodes and pressing keys via `src/directinput.py`

State transitions are driven by journal events: `StartJump` + `JumpType` -> `starting_hyperspace` or `starting_supercruise`; `FSDJump`, `SupercruiseEntry` -> `in_supercruise`; `SupercruiseExit`, `Undocked`, `DockingCancelled`, `Location.Docked=false` -> `in_space`; `DockingRequested` -> `starting_docking`; `Music.MusicTrack=="DockingComputer"` plus status transitions -> `in_docking` or `in_undocking`; `Docked` -> `in_station`.

### Modes

- **Align** (`dev_autopilot.py:1020-1114`). Navigate toward the current target.
  - Sensors: HSV sun-brightness mask `[0,100,240]-[180,255,255]`; CLAHE-equalized capture; template matches against `templates/compass.png`, `templates/navpoint.png`, `templates/destination.png`.
  - Pipeline: capture the middle third of the screen, find the compass, isolate the blue navpoint dot inside it (coarse heading), then switch to full center region and match the orange destination marker (fine alignment).
  - Actuates roll / pitch / yaw button presses with hold times scaled by offset magnitude. Exits on alignment threshold or jump initiation.
- **Jump** (`dev_autopilot.py:1128-1154`). Trigger FSD.
  - Sensors: journal status polling, waits for `starting_hyperspace` then `in_supercruise`.
  - Actuates `HyperSuperCombination` (hold 1s); rechecks status after 16s; up to 3 retries with a re-align in between.
- **Refuel** (`dev_autopilot.py:1169-1196`). Scoop fuel from scoopable stars.
  - Sensors: journal-derived star class and fuel percent.
  - Condition: fuel < 33% AND star class in `{F, O, G, K, B, A, M}`.
  - Actuates `SetSpeed100` -> `SetSpeedZero` x3, then polls journal until `FuelLevel == FuelCapacity`.
- **Position / Scan** (`dev_autopilot.py:1227-1253`). Reposition and trigger discovery scanner between jumps.
  - Sensors: scanner state (held in tray UI state), sun brightness.
  - Actuates `PrimaryFire` or `SecondaryFire` hold, pitch up, set speed 100, more pitch up, then waits until sun < 3% (or 5-20s depending on whether a refuel happened).
- **Dock** (`dev_autopilot.py:955-992`). Request and confirm a station dock.
  - Sensors: journal status polling -> `starting_docking` -> `in_docking` -> `in_station`.
  - Actuates `UIFocus`, `UI_*` navigation, `UI_Select` to drive the menu; sets speed zero; retries menu on failure.
- **Undock** (`dev_autopilot.py:916-940`). Leave the station and reach `in_space`.
  - Sensors: journal status -> `in_undocking` -> `in_space`.
  - Actuates a flurry of `UI_Back`, then down, select; waits on the docking-computer music cue; sets speed zero; polls until status leaves the station.

### Sensors in detail

- **Journal parsing** (`dev_autopilot.py:151-248`): reads the latest `Journal.*` file line by line as JSON, extracts `FuelLevel`, `FuelCapacity`, interprets a `FuelScoop` event timestamp to detect active scooping.
- **Compass offsets** (`dev_autopilot.py:810-856, 869-900`):
  - `get_compass_image()` finds the compass template in the middle-bottom of the screen and returns a cropped image plus its dimensions.
  - `get_navpoint_offset()` matches the blue navpoint dot inside the compass and computes `(x, y)` relative to the compass center; uses history smoothing to reject flicker.
  - `get_destination_offset()` matches the orange destination marker in the screen center third.
- **Sun guard** (`dev_autopilot.py:746-754`): counts bright pixels (`HSV V > 215`) in the center third as a percentage of the frame. Alignment blocks until the sun share drops below 5%.

### Actuation

`dev_autopilot.py:387-420` parses Elite XML bindings, converts them to DirectInput scancodes, and calls `PressKey()` / `ReleaseKey()` from `src/directinput.py`. Default modifier delay 10ms, default key hold 200ms, default repeat interval 100ms.

## Port Status, Capability by Capability

| Capability | Status | Evidence |
| --- | --- | --- |
| Journal parsing | Ported | `edap/state.py:33-115` reads ship state with the same event vocabulary; tested against real journals. |
| Bindings XML -> canonical keys | Ported | `edap/bindings.py`, `edap/binding_lookup.py` parse Elite XML and normalize keys / modifiers; tested. |
| Action dispatch | Ported | `edap/actions.py:ActionDispatcher.tap_action()`, `edap/ship_controls.py:ShipControls` apply the 0.1s minimum / 0.2s continuous dwell policy. |
| macOS input backend | Ported (CGEvent) | `edap/platform/input/macos.py` uses Quartz `CGEventCreateKeyboardEvent` + `CGEventPost` with modifier flags; flight controls confirmed in-game (devlog 0001:28-56). |
| Screen capture (one-shot) | Ported | `edap/platform/screen/macos.py` plus `edap/capture.py` cover one-shot capture with normalized regions; verified via diagnostics. |
| CV pipeline (compass, navpoint, destination) | Not ported | No template matching, no OpenCV plumbing in `edap/` yet. |
| Align loop | Not ported | Depends on the CV pipeline above. |
| Jump sequencing | Stub | `HyperSuperCombination` action exists; journal status polling exists; the sequenced retry loop does not. |
| Refuel sequencing | Stub | Fuel and star-class state are read; the scoop sequence is not wired. |
| Position / scan sequencing | Not ported | No scanner state tracking, no reposition routine. |
| Dock sequencing | Stub | UI navigation actions exist; the menu walk is not ported. |
| Undock sequencing | Stub | UI actions exist; the menu walk is not ported. |
| Hotkey registration | Not ported | Config has `start_hotkey` / `stop_hotkey` slots but no runtime registration; the legacy `keyboard` library does not work on macOS. |

## Unverified on macOS / CrossOver

These are places where the new platform abstractions should cover the legacy behavior, but no live test has actually proven it. Each entry names what would falsify the assumption.

- **CV templates on Retina + CrossOver.** Templates `compass.png`, `navpoint.png`, `destination.png` were authored against 1080p Windows captures. Nothing has run `cv2.matchTemplate` against a real CrossOver Elite window on this machine. To falsify: port `get_compass_image()`, run on a live capture, verify a match score above the legacy threshold. If templates do not match, they will need to be re-baked at the macOS capture resolution.
- **Real-time capture loop.** Diagnostics has only ever captured a single frame. The legacy align loop captures continuously. Frame rate, capture cost, and window-tracking behavior on Retina / CrossOver are unmeasured.
- **Journal write latency vs poll rate.** Legacy reads the file fresh each iteration. The new `edap/state.py` does the same on demand. We have not measured how quickly Elite (through CrossOver) flushes journal events to disk relative to a 0.5-1s poll, so we do not know whether tight state machines will miss transitions.
- **Sustained held flight controls under modifier combos.** Modifier combos were tap-tested through CGEvent and confirmed to work, but no test has held a `Ctrl+...` flight binding for multiple seconds the way an align loop would.
- **Hotkeys on macOS.** No replacement for the legacy `keyboard` library is in place. The expected path is `Quartz.CGEventTapCreate` + a runloop, but that is not implemented or proven yet.
- **Window focus and input routing during autopilot.** `CGEventPost(kCGHIDEventTap, ...)` is global on macOS; behavior across focus loss, hidden CrossOver windows, and multi-monitor setups during a live autopilot run is untested.
- **Compass / navpoint offset math under Retina scaling.** The math is resolution-independent in principle, but it has not been re-validated against macOS captures where logical and physical pixels differ.

## Implication For Next Work

The plumbing layer (journal, bindings, dispatch, input, one-shot capture) is in place. The actual autopilot loop is essentially zero-ported. Two distinct workstreams emerge:

1. Journal-only routines (auto-honk on `FSDJump`, auto-refuel when scoopable + low fuel, supercruise-exit watchdog). These can be built today on what is already ported and would exercise the runtime end-to-end.
2. CV pipeline rebuild. This is the harder workstream and the gating dependency for align / dock / undock. Either re-bake templates against macOS captures or move to a non-template approach (color masking, ROI heuristics, edge detection).

The two workstreams are independent and could proceed in parallel.
