# S0 11-stock source-data admission report

This report contains structural integrity metadata only. No ORB, RVOL, signals, rankings, entries, exits, returns or P&L were calculated.

- Archive SHA-256 verified: **True**
- Members found: **10/11**
- Timestamp interpretation: **Unix-second epoch interpreted UTC then converted to Asia/Kolkata; interval-label semantics require independent source confirmation**

| Symbol | Member | Rows | Schema | Duplicates | Invalid/parse | Off-grid | Missing minutes (QA/DEV/VAL/HOLDOUT) | Admission |
|---|---:|---:|---|---:|---:|---:|---|---|
| HDFCBANK | YES | 192595 | PASS | 0 | 1 | 0 | 275/0/690/0 | BLOCKED |
| ICICIBANK | YES | 192593 | PASS | 0 | 1 | 0 | 275/0/690/2 | BLOCKED |
| SBIN | YES | 192595 | PASS | 0 | 0 | 0 | 275/0/690/0 | ADMITTED_WITH_RECORDED_GAPS |
| RELIANCE | YES | 192592 | PASS | 0 | 0 | 0 | 275/0/690/3 | ADMITTED_WITH_RECORDED_GAPS |
| INFY | YES | 192595 | PASS | 0 | 0 | 0 | 275/0/690/0 | ADMITTED_WITH_RECORDED_GAPS |
| AXISBANK | YES | 192593 | PASS | 0 | 0 | 0 | 275/0/690/2 | ADMITTED_WITH_RECORDED_GAPS |
| KOTAKBANK | YES | 192592 | PASS | 0 | 0 | 0 | 275/0/690/3 | ADMITTED_WITH_RECORDED_GAPS |
| HAL | YES | 192594 | PASS | 0 | 1 | 0 | 275/0/690/1 | BLOCKED |
| TATAMOTORS | NO | 0 | FAIL | - | - | - | - | BLOCKED | 
| TCS | YES | 192592 | PASS | 0 | 0 | 0 | 275/0/690/3 | ADMITTED_WITH_RECORDED_GAPS |
| DLF | YES | 192592 | PASS | 0 | 0 | 0 | 275/0/690/3 | ADMITTED_WITH_RECORDED_GAPS |

## Membership and corporate-action status

- RELIANCE: official 1:1 bonus evidence identified; archive price-basis reconciliation remains required before scoring.
- TATAMOTORS: no exact TATAMOTORS archive member was found; the 2025 demerger and TATAMOTORS→TMPV identity/price-basis continuity also remains unresolved. No substitute was used.
- Other candidates: date-effective official eligibility and exhaustive corporate-action reconciliation remain required.

## Official daily cross-check

UNRESOLVED: no exchange daily files are embedded in this data-only artifact. Primary daily reconciliation must pass before scoring.

## Separate execution blocker

ENTRY_TIMING_CLARIFICATION=REQUIRED_BEFORE_SIMULATION. The diagnostic reference must occur after S_c = E_c + delta_order; submission cutoff and later diagnostic-price timestamp remain unresolved. S0 does not simulate entries.

FINAL_VERDICT=S0_BLOCKED_DATA_INTEGRITY
