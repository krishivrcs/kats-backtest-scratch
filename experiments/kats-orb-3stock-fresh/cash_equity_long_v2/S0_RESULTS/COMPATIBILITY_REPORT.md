# KATS-ORB-CASH-EQ-LONG-V2 — S0 integrity and compatibility report

**Source commit:** `9ee69422210923ba61db42acae59ad74c61c0ec3`  
**Audit implementation commit:** `72d69cad80294ba65e48ed6f155534c1cb9b4a0e`  
**Workflow run:** https://github.com/krishivrcs/kats-backtest-scratch/actions/runs/37930174921  
**Artifact:** `kats-cash-equity-long-v2-s0` (`11615529093`)  
**Scope:** source integrity and signal identity only; no entry, exit, return, cost, P&L, paper trade, or broker order.

## Verdict

`FROZEN_SIGNAL_COMPATIBILITY=PASS`

The frozen legacy generator and V2 complete-five-minute-bucket interpretation produced identical signal identities through the permitted validation boundary of 31 October 2025.

| Partition | Legacy signals | V2 signals |
|---|---:|---:|
| QA | 45 | 45 |
| Development | 5 | 5 |
| Validation | 92 | 92 |

| Difference class | Count |
|---|---:|
| ADDED_SIGNAL | 0 |
| REMOVED_SIGNAL | 0 |
| SHIFTED_SIGNAL | 0 |
| DIRECTION_CHANGED | 0 |
| RANK_CHANGED | 0 |

Six incomplete five-minute buckets occurred in the strategy-relevant window, all in QA. They did not add, remove, shift, reverse, or re-rank any signal.

## Source integrity

- Release: `voletiramu/nse-fno-1min-data`, tag `v1.0.0`, asset `stocks_1m_csvs.zip`.
- Observed bytes: `485923642`.
- Observed SHA-256: `20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2`.
- SHA-256 and byte size matched the GitHub release metadata.
- Schema matched the documented eight columns for SBIN, DLF, and RELIANCE.
- Total inspected rows: `577779`.
- Duplicate timestamps: `0`.
- Malformed timestamps/numerics: `0`.
- Invalid OHLCV rows: `0`.
- Off-grid timestamps: `0`.
- Rows outside the ordinary 09:15–15:29 window: `180`.
- Missing ordinary-session minutes: `1770` across all three files. This includes irregular/nonordinary sessions and was recorded without repair.

The source documents Unix seconds and demonstrates parsing as UTC followed by conversion to `Asia/Kolkata`. The observed ordinary sessions begin at 09:15 and end at 15:29 IST, supporting interval-start labels for completed-candle construction. The archive is a public research dataset attributed to Zerodha Kite API and is not exchange-authoritative.

## Holdout isolation

The sealed holdout is 1 November 2025 through 30 April 2026.

- Holdout rows were reduced during ingestion to permitted aggregate integrity metadata.
- No holdout OHLCV bar object was retained.
- The signal-access guard rejects every holdout date.
- No holdout ORB, RVOL, signal, direction, decision timestamp, rank, entry, return, or P&L field was generated.
- `HOLDOUT_SIGNAL_ACCESSED=NO`.

## Safeguards

All 12 deterministic tests passed, covering complete buckets, missing minutes, duplicate timestamps, invalid OHLC, off-grid timestamps, incomplete opening range, insufficient 20-session history, 09:30 and 12:00 boundaries, ranking, legacy missing-minute behavior, and holdout denial.

## Scope invariants

`FROZEN_FILES_CHANGED=NO`  
`HOLDOUT_SIGNAL_ACCESSED=NO`  
`BACKTEST_RUN=NO`  
`PNL_CALCULATED=NO`  
`BROKER_ORDERS=NO`

This pass authorizes no P&L work by itself.
