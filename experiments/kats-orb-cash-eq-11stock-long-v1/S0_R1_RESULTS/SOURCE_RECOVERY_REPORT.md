# KATS 11-stock S0-R1 source recovery report

## Verdict

`RECOVERY_PARTIAL_REQUIRES_SOURCE_VERIFICATION`

The frozen archive is authentic by its preregistered SHA-256, but it still has no exact `TATAMOTORS_1m.csv.gz` member. It contains `TMPV_1m.csv.gz` with data back to 2024-04-01; this is evidence of retrospective renaming or transformation, not proof that the file is an authentic, raw TATAMOTORS series. It is not admitted or substituted.

## TATAMOTORS recovery

- Official pre-restructure identity: NSE symbol `TATAMOTORS`, equity ISIN `INE155A01022`.
- Official change: NSE records TATAMOTORS → TMPV effective 2025-10-24. The current Upstox NSE master maps TMPV to `NSE_EQ|INE155A01022` and separately maps TMCV to `NSE_EQ|INE1TAE01010`.
- Upstox V3 provider claim: one-minute candles from January 2022, candle timestamp represents interval start, OHLCV plus OI response layout, maximum one-month retrieval for 1–15 minute intervals.
- Measured availability: not established. Historical candle requests require an OAuth bearer token; no credential was available or requested in this gate.
- Zerodha Kite historical candles likewise require authenticated API access. No request was made.
- TMPV economic-price continuity through the demerger remains unverified. Same ISIN/symbol lineage does not prove an unadjusted, tradable price series.

## Three malformed records

All occur at 2024-06-25 09:15 IST and violate the normal OHLC containment invariant:

| Symbol | Defect | Official daily evidence | Classification |
|---|---|---|---|
| HDFCBANK | minute open below minute low | NSE daily record obtained; daily data cannot prove minute H/L | UNRESOLVED |
| ICICIBANK | minute open below minute low | official daily open matches archive open; minute H/L unverified | UNRESOLVED |
| HAL | minute open above minute high | official daily open matches archive open; minute H/L unverified | UNRESOLVED |

The common 09:15 timestamp could reflect a source construction convention involving the pre-open equilibrium price, or erroneous minute high/low fields. Neither explanation is proven. No row was repaired.

## Frozen S0 validation-kernel audit

Fourteen isolated regression tests passed. The frozen implementation was not modified.

| Condition | Frozen S0 behavior |
|---|---|
| zero OHLC | not rejected when internally ordered — defect |
| negative OHLC | not rejected when internally ordered — defect |
| nonfinite OHLC/volume | rejected |
| invalid high/low relationship | rejected |
| negative volume | rejected |
| duplicate timestamps | counted but not included in final blocking gate |
| out-of-order timestamps | neither detected nor rejected |
| off-grid timestamps | detected and blocks |
| malformed numeric row | detected and blocks |
| missing minutes | counted; member may remain admitted-with-gaps |

No additional nonpositive OHLC anomalies were found in the three investigated members. No out-of-order or duplicate step was found in those three members. The broader eleven-member source must nevertheless be revalidated under a corrected kernel before any data gate can pass.

## Official evidence and limitations

- Official NSE 2024-06-25 EQ bhavcopy was retrieved for HDFCBANK, ICICIBANK and HAL. It is daily—not minute-level—evidence.
- NSE capital-market circular `NSE/CMTR/70614` documents the special pre-open session for TATAMOTORS on 2025-10-14.
- NSE F&O circular `NSE/FAOP/70882` documents the TATAMOTORS→TMPV symbol/name change effective 2025-10-24.
- Official filings identify TATAMOTORS/TMPV under ISIN `INE155A01022`; TMCV is a distinct listed security under `INE1TAE01010`.
- RELIANCE's October 2024 bonus adjustment basis remains unresolved and blocked.

## Scope attestation

No signals, ORB, RVOL, rankings, entries, exits, returns or P&L were generated. Sealed-holdout strategy output was not accessed. No broker order or credential was used. The eleven-stock universe and every frozen S0 file remain unchanged.

## Next gate

Obtain a Founder-authorized, credential-safe Upstox V3 read-only extraction for bounded QA/development/validation dates covering TATAMOTORS (`INE155A01022`) and the three disputed 2024-06-25 minutes, recording raw responses and hashes without committing tokens or private exports. This is data verification only and does not authorize signals or P&L.
