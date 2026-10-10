# KATS-5EMA-CASH-LONG-SPRINT-V1 — outcome-independent freeze

Frozen before any strategy return or P&L calculation on 2026-10-10.

## Lineage and scope

This is a new exploratory hypothesis, not a continuation or modification of any frozen KATS experiment. It does not claim to reproduce a proprietary trader method. No production repository, prior ledger, or sealed 2025-11-01–2026-04-30 holdout may be read or changed.

Universe (fixed): AXISBANK, DLF, HAL, ICICIBANK, INFY, KOTAKBANK, SBIN, TCS.

Starting cash: INR 20,000. Long cash equity only, whole shares, no leverage, one shared account, at most one executed position per trading date, no overnight exposure.

Partitions:
- DEVELOPMENT: 2024-04-01 through 2025-02-28.
- UNTOUCHED VALIDATION: 2025-03-01 through 2025-10-31.
- Dates after 2025-10-31 are forbidden to the loader.

## Source admission

The only run input is the public research archive `stocks_1m_csvs.zip`, release v1.0.0 from `voletiramu/nse-fno-1min-data`, exact SHA-256 `20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2`. It is discovery-grade, not exchange-authoritative.

Timestamps must be exact integer Unix seconds interpreted UTC then converted to Asia/Kolkata and must label one-minute interval starts. Every accepted row must have finite positive OHLC, low <= open/close <= high, finite nonnegative volume, unique strictly increasing minute timestamps, and lie on the minute grid. No repair, interpolation, forward fill, rescaling, or row substitution.

A normal session is eligible only when all 375 distinct valid bars from 09:15 through 15:29 exist. Consequently every 5-minute bucket is exactly five consecutive valid source bars. The known malformed ICICIBANK and HAL observations on 2024-06-25 09:15 make those symbol-sessions ineligible. All exclusions remain in the audit ledger with reasons and are never based on returns.

## Frozen signal rules

All calculations use completed 5-minute bars. A bar timestamp is its interval start and becomes available five minutes later.

1. Opening range is the three completed bars starting 09:15, 09:20, and 09:25. `OR_HIGH` and `OR_LOW` freeze at 09:30.
2. Opening relative volume is current 09:15–09:30 volume divided by the mean of exactly the prior 20 eligible symbol sessions' 09:15–09:30 volumes. The current date never enters its lookback. Fewer than 20 prior eligible sessions is ineligible. Require RVOL >= 1.25.
3. Session-local EMA(5), pandas-compatible `adjust=False`, is calculated on completed 5-minute closes only.
4. Trend breakout: first bar starting at or after 09:30 and ending no later than 12:00 that (a) closes above `OR_HIGH * 1.001`, (b) closes above EMA5, (c) EMA5 is greater than its value two completed bars earlier, and (d) its volume is at least 1.20 times the median volume of the six immediately preceding completed 5-minute bars. The breakout freezes an impulse high.
5. Pullback: within the next six completed bars after breakout, the first bar whose low is at or below EMA5, close is at or above EMA5, low is at or above `OR_HIGH * 0.999`, and close is below the frozen impulse high qualifies. A close below EMA5 or low below `OR_LOW` invalidates the symbol for the date before entry. No re-arm.
6. Continuation trigger: after a qualified pullback and no later than a bar ending at 13:25, the first completed bar that closes above the previous completed bar high, above EMA5, and above the pullback-bar high.
7. Entry is the next valid 5-minute bar open, never the trigger close or same bar. Its start time must be no later than 13:30. Baseline fill is open increased by 5 basis points and rounded upward to the INR 0.05 tick.
8. Structural stop is one tick below the minimum low from the qualified pullback through the trigger, rounded downward to the tick. It must be positive and below the entry fill. No artificial tightening.
9. Target is entry plus 2.0 times the entry-to-stop price risk, rounded downward to the tick.
10. Exit at first occurrence of stop or target, inspected causally in the underlying one-minute path after entry. A gap below the stop exits at that minute open; a stop touch exits at stop. A target touch exits at target. If the same minute touches both, stop wins. Exit receives 5 basis points adverse slippage and downward tick rounding. If neither occurs, exit at the 15:10 minute open with adverse slippage. Missing required post-entry evidence makes the candidate unscorable, never a fabricated fill.
11. Cross-sectional order: entry timestamp ascending, opening RVOL descending, normalized breakout distance `breakout_close / OR_HIGH - 1` descending, symbol alphabetically. Once a trade is accepted, all other candidates that date are rejected as portfolio occupied. No future return influences selection.

## Cash, risk, and costs

Quantity is the greatest whole-share quantity satisfying both:
- entry premium plus estimated buy charges <= available cash;
- planned stop loss including baseline adverse entry/stop slippage and estimated round-trip charges <= 1.00% of current realized equity.

If quantity < 1, reject. Cash is debited for purchase and buy-side costs, credited for sale less sell-side costs, and must never be negative. Realized equity alone determines the next date's risk ceiling.

Cost model (computed per side, preserved component-by-component): Zerodha equity-intraday brokerage min(INR 20, 0.03% of side turnover); STT 0.025% of sell turnover; NSE cash transaction charge 0.00322% through 2024-09-30 and 0.00297% thereafter; SEBI charge 0.0001% of total turnover; stamp duty 0.003% on buy turnover; GST 18% of brokerage + exchange + SEBI; NSE IPFT 0.0001% of total turnover. Monetary components retain full precision. These are research assumptions and must be disclosed, not treated as contract notes.

Adverse sensitivity is frozen at 10 basis points on entry and every exit, with all other rules identical.

## Outcome and validation gates

Report development and validation separately, with trades, gross P&L, costs, net P&L, profit factor, expectancy, maximum drawdown, monthly results, symbol results, top-winner concentration, and adverse sensitivity.

`VALIDATED_CANDIDATE` requires all of:
- at least 50 validation trades;
- validation net P&L > 0, profit factor > 1.10, and net expectancy > 0;
- validation maximum drawdown <= 15% of starting capital;
- at least 50% of validation calendar months with trades are net positive;
- validation net P&L excluding the three largest winners remains > 0;
- adverse validation net P&L > 0 and adverse profit factor > 1.00.

Failure of any gate is `REJECT`; insufficient executable evidence is `INSUFFICIENT_EVIDENCE`. No parameter changes follow observed outcomes. A paper-only engine may be implemented only after every validation gate passes. Live orders are prohibited.
