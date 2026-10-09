# KATS-ORB-RVOL-3STOCK-FRESH-V1 — preregistration

Status: frozen before any P&L calculation.

The exact authoritative specification of `KATS-ORB-RVOL-3STOCK-V1` was not
accessible. This is therefore a new conventional fallback, not a reproduction.
The earlier reported ₹34,045 and its trade ledger are not inputs.

## Data gate

Option outcomes may be calculated only from genuine historical option-contract
OHLCV containing underlying, strike, CE/PE, expiry and timestamp. Underlying
prices must never be substituted for option premiums. Missing option prices are
not interpolated. Data integrity and contract coverage are evaluated before P&L.

## Universe and clock

- Cash underlyings: SBIN, DLF, RELIANCE.
- NSE trading day; timestamps interpreted in Asia/Kolkata only after the source
  semantics are verified.
- Signal bars: completed five-minute cash-underlying candles.
- Opening range: 09:15:00 through 09:29:59 (three completed bars).
- Breakout window: after 09:30 through 12:00; all positions exit by 15:15.
- One executed trade per day across one shared portfolio. No re-entry.

## Signal

- Opening relative volume is the current 09:15–09:30 cash volume divided by the
  mean for the same window in exactly the prior 20 valid sessions. The current
  day is excluded. Fewer than 20 valid sessions means no signal.
- RVOL must be at least 1.50.
- Long: a later completed five-minute close is strictly above opening-range high.
- Short: a later completed five-minute close is strictly below opening-range low.
- Simultaneous candidates rank by RVOL descending, normalized breakout distance
  descending, then symbol alphabetically.

## Contract selection and fill

- Long buys a CE; short buys a PE.
- Select the nearest listed monthly expiry having at least five calendar days
  remaining. Select the strike nearest the underlying breakout close; an exact
  tie selects the lower strike for CE and higher strike for PE.
- The contract must exist and have positive volume at the decision/entry time.
- Entry is the next option one-minute candle open strictly after the completed
  breakout bar. No same-bar fill. If absent for more than two minutes: NO_FILL.

## Risk, exits and portfolio

- Starting cash ₹20,000; cash funded, no leverage, whole historical lots.
- Maximum planned loss including estimated round-trip costs is 1.00% of current
  equity. This is a ceiling, not a sizing target. If one lot is unaffordable or
  breaches the ceiling, reject the trade.
- Premium stop is 20% below actual option entry; target is 40% above entry (2R).
- Manage on option one-minute OHLC. If stop and target touch in one candle, stop
  wins. A gap through a level fills at the adverse candle open. Otherwise fill at
  the touched level plus scenario slippage. Forced exit uses the first available
  candle open at or after 15:15.

## Costs and execution scenarios

For the 2024 sample, frozen historical cash-option charges are: ₹20 brokerage per
executed order; STT 0.10% of sell premium; NSE transaction charge 0.03503% on
both legs; SEBI charge ₹10/crore on both legs; GST 18% on brokerage, transaction
and SEBI charges; stamp duty 0.003% of buy premium. Results must retain the exact
source/date caveat.

- Baseline: adverse 0.50% per fill, minimum ₹0.05.
- Adverse: adverse 1.00% per fill, minimum ₹0.10.
- Severe: adverse 2.00% per fill, minimum ₹0.20.

No bid/ask data means candle-based execution remains unverified regardless of
profit.

## Partitions and rejection criteria

Eligible dates are ordered chronologically before results: first 60% development,
next 20% validation, final 20% holdout (floor boundaries at 0.60N and 0.80N).
No parameters change after P&L inspection.

Classify as underpowered when total executed trades are below 100 or holdout
trades below 30. Reject economic promise if holdout net P&L is non-positive,
severe-stress net P&L is non-positive, net P&L excluding the five largest winners
is non-positive, or maximum drawdown exceeds 10% of starting capital.

