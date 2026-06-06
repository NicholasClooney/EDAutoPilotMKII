from __future__ import annotations

import json
from pathlib import Path
from time import monotonic, sleep
from typing import Callable

from edap.actions import ActionDispatchResult
from edap.routines._base import RoutineResult, SupportsGalaxyMapControls


def _read_navroute_destination(journal_dir: Path) -> str | None:
    navroute_path = journal_dir / "NavRoute.json"
    try:
        with navroute_path.open() as fh:
            data = json.load(fh)
        route = data.get("Route", [])
        if route:
            return str(route[-1].get("StarSystem", ""))
        return None
    except (OSError, json.JSONDecodeError):
        return None


def set_gal_map_destination(
    controls: SupportsGalaxyMapControls,
    *,
    destination: str,
    journal_dir: Path,
    open_check_fn: Callable[[], bool] | None = None,
    open_timeout_s: float = 10.0,
    open_settle_s: float = 3.0,
    search_settle_s: float = 2.0,
    plot_timeout_s: float = 15.0,
    step_delay_s: float = 0.5,
    zoom_select_hold_s: float = 0.75,
    max_results: int = 5,
    time_fn: Callable[[], float] = monotonic,
    sleeper: Callable[[float], None] = sleep,
    progress_fn: Callable[[str], None] | None = None,
) -> RoutineResult:
    """Odyssey galaxy map flow: open map, search by name, plot route, verify NavRoute."""
    if max_results < 1:
        raise ValueError("max_results must be at least 1")

    def _err(action: str, reason: str, phase: str, **extra: object) -> RoutineResult:
        return RoutineResult(
            action=action,
            dispatch=ActionDispatchResult(action=action, status="error", reason=reason),
            details={"phase": phase, **extra},
        )

    # Step 1: open the galaxy map
    if progress_fn is not None:
        progress_fn("Opening galaxy map...")
    dispatch = controls.galaxy_map_open()
    if dispatch.status != "ok":
        return RoutineResult(action="GalaxyMapOpen", dispatch=dispatch, details={"phase": "open"})

    # Step 2: wait for map to be ready (OCR check or fixed settle)
    if open_check_fn is not None:
        if progress_fn is not None:
            progress_fn("Waiting for galaxy map (CARTOGRAPHICS check)...")
        deadline = time_fn() + open_timeout_s
        while time_fn() < deadline:
            if open_check_fn():
                break
            sleeper(0.5)
        else:
            if progress_fn is not None:
                progress_fn("Galaxy map open check timed out, proceeding anyway...")
    elif open_settle_s > 0:
        sleeper(open_settle_s)

    # Step 3: navigate to search field (UI_Up + UI_Select)
    if progress_fn is not None:
        progress_fn("Navigating to search field...")
    dispatch = controls.ui_up()
    if dispatch.status != "ok":
        return RoutineResult(action="UI_Up", dispatch=dispatch, details={"phase": "navigate_to_search"})
    if step_delay_s > 0:
        sleeper(step_delay_s)

    dispatch = controls.ui_select()
    if dispatch.status != "ok":
        return RoutineResult(action="UI_Select", dispatch=dispatch, details={"phase": "navigate_to_search"})
    if step_delay_s > 0:
        sleeper(step_delay_s)

    # Step 4: type destination + Enter to commit search
    if progress_fn is not None:
        progress_fn(f"Typing destination: {destination!r}")
    controls.type_text(destination)
    if step_delay_s > 0:
        sleeper(step_delay_s)

    if progress_fn is not None:
        progress_fn("Committing search (Enter)...")
    controls.type_text("\n")
    if search_settle_s > 0:
        sleeper(search_settle_s)

    # Steps 5-6: select results and verify, retrying on mismatch
    last_plot_dispatch: ActionDispatchResult | None = None
    for attempt in range(1, max_results + 1):
        if attempt == 1:
            if progress_fn is not None:
                progress_fn("Selecting first search result...")
            dispatch = controls.ui_right()
            if dispatch.status != "ok":
                return RoutineResult(action="UI_Right", dispatch=dispatch, details={"phase": "select_result", "attempt": attempt})
            if step_delay_s > 0:
                sleeper(step_delay_s)

            dispatch = controls.ui_select()
            if dispatch.status != "ok":
                return RoutineResult(action="UI_Select", dispatch=dispatch, details={"phase": "select_result", "attempt": attempt})
            if step_delay_s > 0:
                sleeper(step_delay_s)
        else:
            if progress_fn is not None:
                progress_fn(f"Trying next result (attempt {attempt}/{max_results})...")
            dispatch = controls.ui_down()
            if dispatch.status != "ok":
                return RoutineResult(action="UI_Down", dispatch=dispatch, details={"phase": "next_result", "attempt": attempt})
            if step_delay_s > 0:
                sleeper(step_delay_s)

            dispatch = controls.ui_select()
            if dispatch.status != "ok":
                return RoutineResult(action="UI_Select", dispatch=dispatch, details={"phase": "next_result", "attempt": attempt})
            if step_delay_s > 0:
                sleeper(step_delay_s)

        # CamZoomIn (Z) + UI_Select held to plot the route
        if progress_fn is not None:
            progress_fn("Plotting route (CamZoomIn + UI_Select)...")
        dispatch = controls.cam_zoom_in()
        if dispatch.status != "ok":
            return RoutineResult(action="CamZoomIn", dispatch=dispatch, details={"phase": "plot_route", "attempt": attempt})
        if step_delay_s > 0:
            sleeper(step_delay_s)

        last_plot_dispatch = controls.ui_select(hold_s=zoom_select_hold_s)
        if last_plot_dispatch.status != "ok":
            return RoutineResult(action="UI_Select", dispatch=last_plot_dispatch, details={"phase": "plot_route", "attempt": attempt})

        # Poll NavRoute.json until destination matches or timeout
        if progress_fn is not None:
            progress_fn(f"Waiting for route to {destination!r} (up to {plot_timeout_s:.0f}s)...")
        deadline = time_fn() + plot_timeout_s
        actual: str | None = None
        while time_fn() < deadline:
            actual = _read_navroute_destination(journal_dir)
            if actual is not None and actual.lower() == destination.lower():
                break
            sleeper(0.5)

        if actual is not None and actual.lower() == destination.lower():
            if progress_fn is not None:
                progress_fn(f"Route set to {actual!r}")
            if progress_fn is not None:
                progress_fn("Closing galaxy map...")
            controls.galaxy_map_open()
            assert last_plot_dispatch is not None
            return RoutineResult(
                action="GalaxyMapOpen",
                dispatch=last_plot_dispatch,
                details={"destination": destination, "actual": actual, "attempts": attempt},
            )

        if progress_fn is not None:
            got = actual or "unknown"
            progress_fn(f"Route not confirmed after {plot_timeout_s:.0f}s (got {got!r}), trying next result...")

    # Exhausted all results -- close map and return error
    controls.galaxy_map_open()
    return _err("GalaxyMapOpen", f"no matching result after {max_results} attempts", "verify_route", destination=destination)
