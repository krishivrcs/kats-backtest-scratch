# KATS-FAILED-BREAKOUT-VWAP-LONG-V1 — preregistration

Frozen before any strategy outcome calculation on 2026-10-10. A pre-outcome causality review added the explicit T+60-second entry delay before implementation was executed; no market outcome had been inspected.

## Lineage and purpose

This is a new exploratory hypothesis. It is not a parameter variant of the rejected KATS 5EMA sprint and does not reuse its trade outcomes. It deliberately uses overlapping public history, so it is not statistically independent of earlier KATS research. The original sealed 2025-11-01–2026-04-30 holdout remains prohibited.

Fixed universe: AXISBANK, DLF, HAL, ICICIBANK, INFY, KOTAKBANK, SBIN, TCS.

Development: 2024-04-01–2025-02-28.
Conditional validation: 2025-03-01–2025-10-31.
Starting cash: INR 20,000. Long-only NSE cash equity, whole shares, no leverage, one shared position and at most one executed trade per date, no overnight exposure.

## Source and integrity

Use only `voletiramu/nse-fno-1min-data` release v1.0.0 `stocks_1m_csvs.zip`, exact SHA-256 `20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2`. It is free public research data, not exchange-authoritative quote evidence.

Reuse the strict parser and validation primitives frozen in `experiments/kats-profit-sprint-20261010/engine.py`: exact integer Unix seconds, UTC to Asia/Kolkata, interval-start labels, finite positive internally consistent OHLC, finite nonnegative volume, unique ordered minute grid, exactly 375 normal-session minutes, and exactly five valid constituent minutes per 5-minute bar. No repairs or interpolation. The known malformed HAL and ICICIBANK 2024-06-25 opening observations and every incomplete/nonstandard session fail closed for that symbol-date.

The development process may parse data only through 2025-02-28. Validation data, signals, prices and P&L may be accessed only if the development gate passes. No date after 2025-10-31 may be parsed for strategy use.

## Frozen setup

All decisions use completed five-minute candles.

1. Opening range: the three bars starting 09:15, 09:20 and 09:25. `OR_HIGH` and `OR_LOW` freeze when the 09:25 bar completes at 09:30.
2. Opening relative volume: 09:15–09:30 volume divided by the mean of exactly the prior 20 eligible symbol sessions' corresponding volume. The current session is excluded. Require RVOL >= 1.00; fewer than 20 valid prior sessions is ineligible.
3. VWAP: cumulative session VWAP through each completed 5-minute bar, using five-minute typical price `(high + low + close) / 3` multiplied by volume. Zero cumulative volume is ineligible. VWAP never uses the entry bar or later data.
4. Failed breakdown precursor: the first completed bar starting at or after 09:30 and ending no later than 12:30 that closes strictly below `OR_LOW`, has a low below `OR_LOW * 0.999`, and volume >= 1.20 times the median volume of the six immediately preceding completed five-minute bars.
5. Recovery confirmation: within the next three completed five-minute bars, the first bar that closes strictly above `OR_LOW`, closes above its open, and closes above the previous completed bar's close. If no such bar exists, the symbol-date expires. The breakdown extreme is the minimum low from breakdown through recovery.
6. At recovery completion, freeze the destination at that completed bar's VWAP. The destination must be above the eventual entry fill; a later-moving VWAP is never substituted.
7. Entry: the recovery bar completes at decision time T. The model waits one full source minute and uses the open of the one-minute bar stamped T+60 seconds; no OHLCV or volume from that fill minute may qualify the entry. Entry time must be no later than 12:45. Baseline buy fill is that raw open plus 5 bps, rounded upward to the INR 0.05 tick. This explicit delay prevents a zero-latency boundary fill.
8. Structural stop: one INR 0.05 tick below the breakdown extreme, rounded downward. It is never tightened for affordability.
9. Exit target: the frozen recovery-completion VWAP, rounded downward to the tick.
10. Prospective edge gate, evaluated using actual simulated entry fill but before future path: after selecting the maximum affordable/risk-compliant quantity, conservative net profit at the target must be at least 1.50 times all-in planned stop loss. Both include frozen slippage and estimated full round-trip costs. Target must be above entry.
11. Path: inspect one-minute bars from the entry minute onward. Gap below stop exits at the minute open. Otherwise stop or target touch exits at its price. If one minute touches both, stop is first. All exits receive adverse slippage and downward tick rounding. If neither occurs, exit at the 15:10 minute open. Missing exit evidence is unscorable.
12. Cross-sectional priority: entry timestamp ascending, RVOL descending, breakdown depth `OR_LOW / breakdown_low - 1` descending, symbol alphabetical. Candidates rejected immediately for data, cash, 1% risk or reward may promote the next causally available candidate. Once filled, the portfolio is occupied for that date. No future outcome affects promotion.

## Risk, cash, costs and sensitivity

Maximum all-in planned stop loss is 1.00% of current realized equity. Quantity is the greatest whole-share amount satisfying the risk ceiling and full cash purchase including buy charges. Cash may never be negative.

Reuse the date-effective research cost model frozen in the prior infrastructure: brokerage min(INR 20, 0.03% per side); STT 0.025% on sell; NSE cash transaction charge 0.00322% through 2024-09-30 and 0.00297% thereafter; SEBI 0.0001%; stamp 0.003% on buy; GST 18% on brokerage + exchange + SEBI; IPFT 0.0001%. Baseline slippage is 5 bps each side. Adverse sensitivity is 10 bps each side with all other rules unchanged.

These are cost and candle-fill assumptions, not contract-note or bid/ask proof. Broker executability remains unresolved.

## Sequential gates

Development passes only if all hold:
- at least 30 executed trades;
- baseline net P&L > 0, net PF > 1.15 and expectancy > 0;
- maximum realized-equity drawdown <= 15% of INR 20,000;
- at least 50% of traded months net positive;
- net P&L excluding the three largest winners > 0;
- adverse net P&L > 0 and adverse PF > 1.00.

If any development condition fails, verdict is `REJECT_DEVELOPMENT`; validation remains `NOT_ACCESSED`.

If development passes, validation is opened once and passes only if all hold:
- at least 20 validation trades and at least 50 combined trades;
- validation net P&L > 0, PF > 1.10, expectancy > 0;
- validation drawdown <= 15% of starting capital;
- at least 50% of traded validation months net positive;
- validation net excluding the three largest winners > 0;
- adverse validation net > 0 and adverse PF > 1.00.

Failure is `REJECT_VALIDATION`. Passing is `VALIDATED_CANDIDATE_REQUIRES_INDEPENDENT_REVIEW`. No parameter changes are permitted after either outcome. A paper-only engine may be prepared only after independent review; live orders are prohibited.

## Economic counterparty and failure thesis

The intended counterparty is a late breakdown seller or short who exits when support is reclaimed. The strongest objection is that genuine information-driven breakdowns will not mean-revert, candle VWAP is not an executable offer, the stop sits where liquidity can gap, and fees can consume a small cash-equity reversion. The hypothesis must earn its edge after all of these frictions; otherwise it is rejected.
