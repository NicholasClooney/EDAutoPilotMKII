# 0005: Market Trading Routine

## Status

Proposed. Gated on three open questions — see below. No code written yet.

## Why

The mid-term goal is automated trade runs: dock at a station, buy a cargo of target commodities, jump to a buyer, sell. This plan covers the in-station buy/sell leg. Galaxy map routing (plan 0006, not yet written) covers the jump leg.

## Data Sources

### Market.json

Elite Dangerous writes `Market.json` to the journal directory whenever the player opens the commodities market screen in-game. It is the only in-process source for commodity listings. The journal itself does not carry this data.

Relevant fields per item:

| Field | Meaning |
| --- | --- |
| `Name_Localised` | Human-readable commodity name |
| `Category_Localised` | Category (Metals, Chemicals, etc.) |
| `BuyPrice` | Price to buy from station (0 = not for sale) |
| `SellPrice` | Price station pays (0 = not accepted) |
| `Stock` | Units available to buy |
| `StockBracket` | Supply level 0–3 (0 = none, 3 = high) |
| `Demand` | Station demand for selling to it |
| `DemandBracket` | Demand level 0–3 |

`scratch_market.py` is the live probe for reading and inspecting this file.

### Journal events

- `MarketBuy` — written on each completed purchase: commodity name, count, price paid.
- `MarketSell` — written on each completed sale: commodity name, count, price received.
- These are useful for confirming a trade completed and for the activity log.

## Proposed Design

### `market_buy(ctx, items: list[dict], *, timeout_s: float = 120)`

Each item in `items` is `{"name": "Gold", "qty": 10}`. Name must match the `Name_Localised` value in Market.json (case-insensitive).

Steps:
1. Read `Market.json` to build an ordered list of items available for purchase. Fail fast if the file is missing or stale (older than ~60s).
2. Navigate to the commodities buy tab via the station services UI.
3. For each target item: find its position in the Market.json list order, scroll down by that count, confirm selection, enter quantity, confirm purchase.
4. After each purchase, wait for the corresponding `MarketBuy` journal event to confirm the transaction landed before moving to the next item.
5. Return a summary of what was bought (name, qty, total cost).

### `market_sell(ctx, items: list[dict] | str, *, timeout_s: float = 120)`

If `items == "all"`, sell everything in cargo (read from the most recent `Cargo` journal event). Otherwise same shape as buy.

Steps:
1. Navigate to the sell tab.
2. For each item: find in Market.json, scroll, select quantity, confirm.
3. Wait for `MarketSell` journal event per item.

### Market tracker (session state)

A session-level dict keyed by `MarketID` stores the last-seen Market.json snapshot per station. The monitoring CLI reads this to show supply/demand comparisons across visited stations and to drive the `go <station>` command.

## Open Questions (gate implementation)

These must be answered from a live session before writing the routine.

1. **Does the in-game market list order match the order of items in Market.json?**
   **Answered (2026-06-06).** The in-game market sorts categories alphabetically and items within each category alphabetically. `scratch_market.py` now mirrors this layout. Positional navigation must use the same alphabetical order, not raw Market.json order.

2. **Does the game accept typed numeric input for quantity, or is it increment/decrement only?**
   **Answered (2026-06-06).** Increment/decrement only via `UI_Right` / `UI_Left`. Holding accelerates to max. For `amount == "MAX"`, hold `UI_Right` for 10 seconds; for a specific count, tap `UI_Right` N times.

3. **What is the exact UI key path from the docked lobby to the commodities buy tab?**
   **Answered (2026-06-06).** Starting from the station services screen (where the refuel routine leaves off):
   - `UI_Select` — enter station services
   - `UI_Down` — move to Commodities Market entry
   - `UI_Select` — open market; lands on BUY tab with sidebar focus
   - `UI_Right` — enter the commodity list (cursor on first item)
   - `UI_Down` x N — navigate to target item (category headers are non-navigable separators)
   - `UI_Select` — open buy/sell dialog
   - `UI_Right` (hold 10s or tap N times) — set quantity
   - `UI_Down` — move to BUY button
   - `UI_Select` — confirm
   For SELL tab: after opening the market, press `UI_Down` (sidebar BUY → SELL), `UI_Select` to enter SELL, then same flow.
   Exiting the commodity screen returns to the station services Missions entry.

## Dependencies

- `scratch_market.py` is the verification tool for assumption #1.
- Plan 0003 (journal-driven routines) provides `JournalWatcher` which this routine needs for `MarketBuy`/`MarketSell` confirmation.
- No CV dependency — navigation is positional, not screen-reading.

## Not in Scope

- Price comparison across stations (that is the monitoring CLI / plan 0004 concern).
- Choosing what to buy/sell (caller provides the item list).
- Galaxy map routing to the next trade destination (plan 0006).
