# KATS-ODPC-V0 frozen discovery backtest

This repository contains the one-shot, non-optimized implementation of the
Opening Drive Pullback Continuation specification frozen before outcomes.
It is research-only: it does not connect to a broker and cannot place orders.

## Reproducibility boundary

- Universe: SBIN, RELIANCE, HDFCBANK, ICICIBANK, INFY, TCS, BHARTIARTL,
  TATASTEEL, ITC, LT.
- Data: public one-minute parquet files from
  `rahulkanadia/IndianMarkets_DataBackfill`, downloaded only inside Actions.
- Raw data is never committed.
- The manifest (schema, row counts, file SHA256s, valid-session counts and
  corporate-action gap flags) is written before any strategy outcome loop.
- Naive source timestamps are interpreted as Asia/Kolkata exchange-local time.
- A valid session must contain the exact 375-minute grid from 09:15 through
  15:29, with no duplicate, nonfinite or malformed OHLCV row.
- Opening volume uses `[09:15, 09:45)`, matching the six explicitly frozen
  five-minute candles.
- A day satisfying both long and short drive thresholds is skipped as
  `AMBIGUOUS_BIDIRECTIONAL_OPENING_DRIVE`.
- Suspected corporate-action discontinuities (absolute overnight gap at least
  15%) are reported and excluded without price adjustment.

## Execution and friction

- Five basis points of adverse slippage are applied to each entry and exit.
- Breakeven management is simulated on the one-minute source path.
- If a one-minute bar still cannot establish event order, stop-first is used.
- Forced exit is the 15:10 one-minute opening price, with adverse slippage.
- Portfolio sizing uses cash only and at most 1% of current closed-trade equity.

The cash-intraday schedule captured before outcomes on 2026-10-08 uses:

- Zerodha brokerage: 0.03% or INR 20 per executed order, whichever is lower.
- Intraday STT: 0.025% of sell turnover.
- NSE cash transaction outflow: 0.00307% each side.
- SEBI turnover fee: INR 10/crore.
- GST: 18% of brokerage, exchange, SEBI and NSE-IPFT service charges.
- Non-delivery stamp duty: 0.003% of buy turnover.

Sources:

- https://zerodha.com/charges/
- https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- https://www.nseindia.com/static/invest/first-time-investor-sebi-turnover-fees-stt-other-levies

The same current schedule is applied uniformly across 2018-2025. Component
rounding on an actual broker contract note is not reproduced; calculations
retain sub-paise precision. Both limitations are explicit in `results.json`.

## Commands

```bash
python -m pytest
PYTHONPATH=src python -m kats_odpc.run \
  --data-dir data/raw \
  --output-dir results \
  --source-commit <commit>
```
