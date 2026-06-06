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

These must be answered from a live session before writing the routine. Use `scratch_market.py` to help answer #1.

1. **Does the in-game market list order match the order of items in Market.json?**
   If yes, positional navigation (scroll N times) is reliable. If not, we need a different selection strategy.

2. **Does the game accept typed numeric input for quantity, or is it increment/decrement only?**
   If typed input works, large quantities are fast. If scroll-only, we need a key-repeat approach for large buys.

3. **What is the exact UI key path from the docked lobby to the commodities buy tab?**
   Need to trace: station services menu key → commodities entry → buy tab. The existing dock routine only goes as far as the station lobby.

## Dependencies

- `scratch_market.py` is the verification tool for assumption #1.
- Plan 0003 (journal-driven routines) provides `JournalWatcher` which this routine needs for `MarketBuy`/`MarketSell` confirmation.
- No CV dependency — navigation is positional, not screen-reading.

## Not in Scope

- Price comparison across stations (that is the monitoring CLI / plan 0004 concern).
- Choosing what to buy/sell (caller provides the item list).
- Galaxy map routing to the next trade destination (plan 0006).
