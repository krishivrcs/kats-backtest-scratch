# KATS-5EMA-CASH-LONG-SPRINT-V1 — independent rejection freeze

**Status:** REJECTED / NOT DEPLOYABLE  
**Immutable tested source commit:** `f3cfc86f619721d15f6cb9dafd55abdf285506f3`  
**GitHub Actions run:** https://github.com/krishivrcs/kats-backtest-scratch/actions/runs/38027809783  
**Evidence artifact ID:** `11661221117`  
**Downloaded artifact ZIP SHA-256:** `1fa265ebacbabc9c0dbd07ba7f6c4b00766c63514dcc33e54f4d2e826330450d`  
**Frozen public archive SHA-256:** `20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2`

## Verified outcome

| Measure | Development (2024-04-01–2025-02-28) | Validation (2025-03-01–2025-10-31) |
|---|---:|---:|
| Modeled trades | 20 | 12 |
| Gross P&L | −INR 837.05 | −INR 741.20 |
| Costs | INR 376.10 | INR 233.29 |
| Net P&L | **−INR 1,213.15** | **−INR 974.49** |
| Net profit factor | 0.29593 | 0.09567 |

Validation had one winning trade (8.33% win rate), negative net results in every traded validation month, and INR 974.49 modeled closed-equity drawdown. Frozen 10-bps adverse validation: **−INR 1,096.28**, PF 0.09275.

GitHub Actions completed successfully, all **14 tests passed**, frozen archive hash passed, accounting reconciliation passed, and the signed research artifacts were downloaded and independently examined. Success of the CI job does **not** mean success of the strategy.

## Scientific and operational interpretation

- `FINAL_VERDICT=REJECT`: loss in development and validation, adverse sensitivity loss, and only 12 validation modeled trades versus 50 minimum required by preregistration.
- Results are OHLCV candle-scenario estimates, **not evidenced executable fills**, and cannot substantiate earnings.
- Preserve all original source, preregistration, parameters, strategy implementation, partitions, and outcome files.
- **Do not fit, retune, re-rank, or revalidate this strategy on the same observed periods under the same hypothesis name.**
- `PAPER_ENGINE_STATUS=NOT_IMPLEMENTED_VALIDATION_FAILED`; `LIVE_ORDERS=NONE`.
- `SEALED_HOLDOUT_2025_11_01_TO_2026_04_30=UNTOUCHED`.
- Follow-on profitable-strategy discovery must use a new uniquely identified hypothesis, disclose the earlier tested periods/multiple comparisons, and reserve independent evaluation evidence.
