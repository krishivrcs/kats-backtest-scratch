# KATS 11-stock S0-R3 strict source-integrity report

## Scope

This gate implements an isolated source-integrity validator only. It does not calculate ORB, RVOL, signals, rankings, entries, exits, returns, or P&L. The frozen S0 audit, manifests, preregistration, review addendum, and S0-R1 evidence remain unchanged.

## Strict validation policy

- OHLC prices must be finite, strictly positive, and internally consistent (`low <= open/close <= high`).
- Volume must be finite and nonnegative.
- Timestamps must be unique, strictly increasing in source order, IST-aware, and aligned to the exact minute grid.
- Every expected session remains in the structural denominator, including missing sessions and sessions containing failed observations.
- Opening-range eligibility requires all fifteen valid unique minutes from 09:15 through 09:29 IST.
- Every admitted five-minute bucket requires exactly five valid, unique, consecutive one-minute observations and becomes available only at the bucket-end timestamp.
- No interpolation, repair, rescaling, or substitution is permitted.

## Frozen QA exceptions

The following public-archive observations are recorded without repair. Authenticated Upstox V3 returned matching provider candles, but that agreement is not exchange-authoritative and does not prove source independence.

| Symbol | Timestamp | Structural result | Session result |
|---|---|---|---|
| HDFCBANK | 2024-06-25 09:15 IST | open is below low | opening range ineligible |
| ICICIBANK | 2024-06-25 09:15 IST | open is below low | opening range ineligible |
| HAL | 2024-06-25 09:15 IST | open is above high | opening range ineligible |

The full histories are retained; only the affected observations and derived structural units fail closed.

## TATAMOTORS status

- Upstox V3 historical minute data are available under `NSE_EQ|INE155A01022` for the bounded verified dates.
- The 2025-10-14 special session begins at 10:00 IST and contains 330 candles, so it cannot satisfy the frozen 09:15 opening-range requirement.
- October 2025 demerger price-basis reconciliation remains **UNRESOLVED**.
- The archive's `TMPV` member is not substituted for TATAMOTORS without verified legal-security identity and economic-price continuity.

## Safety attestation

Validation and sealed-holdout strategy outputs were not accessed. No credentials or raw private market data are committed. No strategy rules or frozen files are changed. No broker order was submitted.

FINAL_VERDICT=S0_R3_STRICT_INTEGRITY_READY
