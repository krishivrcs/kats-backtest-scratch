# KATS-ORB-CASH-EQ-LONG-V2 — S0 independent freeze review

**Review type:** independent, outcome-blind freeze review  
**Source commit:** `5d874a503261be4ce29ac25ba23526a8ec47e289`  
**Comparison base:** `9ee69422210923ba61db42acae59ad74c61c0ec3`  
**Branch:** `research/kats-orb-cash-eq-long-v2`  
**Scope:** source integrity, signal compatibility, workflow provenance, and holdout-isolation review only. No trading-engine implementation, cash-equity P&L, holdout opening, paper trade, or broker order.

## Verdict

`FINAL_VERDICT=S0_INDEPENDENT_ACCEPT_FREEZE`

S0 is acceptable to freeze as an outcome-blind compatibility checkpoint. The evidence supports source-byte identity and exact legacy-versus-V2 signal identity through the permitted validation boundary. It does **not** establish executable fills, profitability, or adequate executed-trade sample size.

## 1. Four-commit boundary and modified files

GitHub comparison from `9ee69422210923ba61db42acae59ad74c61c0ec3` to `5d874a503261be4ce29ac25ba23526a8ec47e289` reports exactly four commits, ahead by four and behind by zero.

| Commit | Purpose | File scope |
|---|---|---|
| `aca810314515627f156c1ba1839223da07b15800` | Initial bounded S0 implementation | Added S0 workflow, `s0/audit.py`, `s0/source_expected.json`, and S0 tests |
| `72d69cad80294ba65e48ed6f155534c1cb9b4a0e` | Correct test invocation and enforce pipeline failure propagation | S0 workflow and S0 test file only |
| `9116bdb1210db484b18932911706926f1a9dac9f` | Prevent the broad legacy workflow from running on the V2 research branch | Two-line safety guard in the older workflow only |
| `5d874a503261be4ce29ac25ba23526a8ec47e289` | Record immutable S0 evidence | Added the eight files under `cash_equity_long_v2/S0_RESULTS/` |

The complete unique modified-file set is:

1. `.github/workflows/kats_cash_equity_long_v2_s0.yml`
2. `.github/workflows/kats_orb_3stock_fresh.yml`
3. `experiments/kats-orb-3stock-fresh/cash_equity_long_v2/s0/audit.py`
4. `experiments/kats-orb-3stock-fresh/cash_equity_long_v2/s0/source_expected.json`
5. `experiments/kats-orb-3stock-fresh/tests/test_cash_equity_long_v2_s0.py`
6. `experiments/kats-orb-3stock-fresh/cash_equity_long_v2/S0_RESULTS/COMPATIBILITY_REPORT.md`
7. `experiments/kats-orb-3stock-fresh/cash_equity_long_v2/S0_RESULTS/SUMMARY.txt`
8. `experiments/kats-orb-3stock-fresh/cash_equity_long_v2/S0_RESULTS/compatibility_report.json`
9. `experiments/kats-orb-3stock-fresh/cash_equity_long_v2/S0_RESULTS/differences.json`
10. `experiments/kats-orb-3stock-fresh/cash_equity_long_v2/S0_RESULTS/legacy_signal_identities.csv`
11. `experiments/kats-orb-3stock-fresh/cash_equity_long_v2/S0_RESULTS/source_manifest.json`
12. `experiments/kats-orb-3stock-fresh/cash_equity_long_v2/S0_RESULTS/test_result.txt`
13. `experiments/kats-orb-3stock-fresh/cash_equity_long_v2/S0_RESULTS/v2_signal_identities.csv`

No frozen V2 specification, review addendum, legacy signal implementation, or prior ledger appears in the comparison.

## 2. Source-integrity review

The expected-source record, workflow, generated manifest, and workflow logs agree on:

- Release: `voletiramu/nse-fno-1min-data`, tag `v1.0.0`
- Asset: `stocks_1m_csvs.zip`, GitHub asset ID `410673470`
- Bytes: `485923642`
- SHA-256: `20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2`
- Timestamp conversion: Unix seconds interpreted as UTC and converted to `Asia/Kolkata`
- Dataset status: public research archive attributed to Zerodha Kite API; not exchange-authoritative

The S0 workflow downloaded the immutable release asset, checked complete-file bytes and SHA-256 before audit execution, and failed closed on mismatch. The manifest records zero duplicate timestamps, zero malformed timestamp/numeric records, zero invalid OHLCV records, and zero off-grid timestamps for the three admitted files. Missing minutes and out-of-ordinary-session rows were counted rather than silently repaired.

`SOURCE_INTEGRITY=PASS_WITH_DOCUMENTED_NON_EXCHANGE_PROVENANCE`

## 3. Implementation and test evidence

Independent source inspection found:

- `audit.py` imports the frozen `backtest.py` for legacy behavior instead of rewriting the legacy generator.
- The V2 path admits a five-minute bucket only when it contains exactly five unique, consecutive, valid one-minute bars.
- The module contains no entry, exit, charge, return, position sizing, or P&L calculation.
- The 12 tests cover complete buckets, missing constituent minutes, duplicate timestamps, invalid OHLC, off-grid timestamps, incomplete opening range, missing 20-session history, 09:30 and 12:00 boundaries, chronological rank, legacy missing-minute behavior, and holdout denial.
- Workflow run `37930174921` completed successfully and all 12 tests passed.
- The workflow asserted that prohibited entry/exit/P&L/return outputs did not exist before artifact upload.

`TEST_EVIDENCE=PASS_12_OF_12_WITH_SUCCESSFUL_ACTIONS_RUN_37930174921`

## 4. Independent signal reconciliation

The committed legacy and V2 identity ledgers each contain:

| Partition | Legacy | V2 |
|---|---:|---:|
| QA | 45 | 45 |
| Development | 5 | 5 |
| Validation | 92 | 92 |

`differences.json` is an empty array. Independent comparison of the committed identities confirms:

- Added: 0
- Removed: 0
- Shifted: 0
- Direction changed: 0
- Chronological rank changed: 0

The six incomplete strategy-window five-minute buckets were all in QA and did not change any signal identity.

An independent count of the V2 validation ledger gives:

- `VALIDATION_LONG_SIGNALS=47`
- `VALIDATION_SHORT_SIGNALS=45`
- `VALIDATION_TOTAL_SIGNALS=92`

Because the executable hypothesis is long-only, validation can supply at most 47 candidate long entries before affordability, risk, data, and execution rejections. It therefore cannot meet the frozen preference/adequacy requirement of 100 executed trades using validation alone. The sealed holdout must not be opened merely to overcome this shortfall.

`SIGNAL_COMPATIBILITY=PASS_EXACT_IDENTITY`  
`VALIDATION_MINIMUM_SAMPLE_FEASIBLE=NO`

## 5. GitHub Actions provenance

| Run | Workflow behavior | Backtest/P&L step | Date scope actually scored | V2 cash P&L | Sealed V2 holdout output |
|---|---|---|---|---|---|
| `37930174921` | Authorized V2 S0 integrity/compatibility workflow | No trading backtest; signal identity only | QA, development, and validation through 2025-10-31 | No | No |
| `37929799096` | Older broad legacy workflow; unit tests failed | Backtest step skipped | None | No | No |
| `37930174137` | Older broad legacy workflow; cancelled during data probe | Backtest step skipped | None | No | No |
| `37926920087` | Older broad legacy option workflow completed | Legacy `backtest.py` executed | 13 option sessions, 2024-10-15 through 2024-10-31 | No | No |
| `37925182761` | Older broad legacy option workflow completed | Legacy `backtest.py` executed | 13 option sessions, 2024-10-15 through 2024-10-31 | No | No |

The two completed legacy runs downloaded/probed a cash archive whose coverage extended to 2026-04-30, but their trading backtest target dates were derived from the 13-session October 2024 option archive. Their output reported five legacy signals and zero executable baseline trades. They did not implement or score KATS-ORB-CASH-EQ-LONG-V2 and did not generate sealed-holdout signal identities or P&L.

These earlier runs are acknowledged as real historical workflow executions; they are neither hidden nor relabeled as S0.

`PRIOR_BACKTEST_RUNS_ACCOUNTED_FOR=YES`  
`V2_CASH_PNL_PRODUCED=NO`  
`HOLDOUT_STRATEGY_OUTPUT_EXPOSURE=NO`

## 6. Legacy workflow scope exception

The older workflow had a broad push trigger covering `experiments/kats-orb-3stock-fresh/**`. An S0 commit therefore triggered a workflow capable of running the legacy option backtest. Commit `9116bdb1210db484b18932911706926f1a9dac9f` added this job-level guard:

```yaml
# Safety isolation: this branch authorizes S0 integrity/compatibility only.
if: github.ref != 'refs/heads/research/kats-orb-cash-eq-long-v2'
```

This two-line modification is a harmless and necessary documented scope exception. It changes neither signal logic nor results; it prevents an unauthorized legacy P&L workflow from running on the V2 research branch. It must be preserved.

`LEGACY_WORKFLOW_SCOPE_EXCEPTION=ACCEPTED_HARMLESS_SAFETY_ISOLATION`

## 7. Frozen-file and ledger integrity

Byte-for-byte connector reads at the comparison base and reviewed head confirm that these files are unchanged:

- `experiments/kats-orb-3stock-fresh/backtest.py`
- `experiments/kats-orb-3stock-fresh/cash_equity_long_v2/PREREGISTRATION.md`
- `experiments/kats-orb-3stock-fresh/cash_equity_long_v2/REVIEW_PROTOCOL_ADDENDUM.md`

The four-commit comparison contains no earlier trade-ledger modification.

`FROZEN_SPECIFICATIONS_CHANGED=NO`  
`EARLIER_TRADING_LEDGERS_CHANGED=NO`

## 8. Holdout-isolation review

The sealed holdout is 2025-11-01 through 2026-04-30.

Permitted behavior observed:

- Raw archive bytes were read to verify the full asset hash.
- Holdout rows were reduced during ingestion to aggregate integrity metadata such as row, duplicate, malformed, off-grid, missing-minute, first-timestamp, and last-timestamp counts.
- No holdout `Bar` objects were retained for strategy processing.
- Explicit guards reject signal access for holdout and post-validation dates.
- The workflow checks the result directory for prohibited strategy/P&L fields before upload.

No holdout ORB, RVOL, direction, decision, chronological rank, entry, exit, return, or P&L output was generated or exposed. Reading raw bytes and aggregate structural metadata for the authorized integrity gate is not equivalent to opening strategy outputs.

`HOLDOUT_STRATEGY_OUTPUT_EXPOSURE=NO`

## Final report

```text
SOURCE_COMMIT=5d874a503261be4ce29ac25ba23526a8ec47e289
REVIEW_COMMIT=RECORDED_BY_THIS_DOCUMENT_COMMIT
FILES_CHANGED=experiments/kats-orb-3stock-fresh/cash_equity_long_v2/S0_INDEPENDENT_REVIEW.md
SOURCE_INTEGRITY=PASS_WITH_DOCUMENTED_NON_EXCHANGE_PROVENANCE
SIGNAL_COMPATIBILITY=PASS_EXACT_IDENTITY
TEST_EVIDENCE=PASS_12_OF_12_WORKFLOW_37930174921
LEGACY_WORKFLOW_SCOPE_EXCEPTION=ACCEPTED_HARMLESS_SAFETY_ISOLATION
PRIOR_BACKTEST_RUNS_ACCOUNTED_FOR=YES
V2_CASH_PNL_PRODUCED=NO
HOLDOUT_STRATEGY_OUTPUT_EXPOSURE=NO
VALIDATION_LONG_SIGNALS=47
VALIDATION_SHORT_SIGNALS=45
VALIDATION_TOTAL_SIGNALS=92
VALIDATION_MINIMUM_SAMPLE_FEASIBLE=NO
FROZEN_SPECIFICATIONS_CHANGED=NO
FINAL_VERDICT=S0_INDEPENDENT_ACCEPT_FREEZE
NEXT_SINGLE_ACTION=STOP_AND_REQUIRE_SEPARATE_FOUNDER_AUTHORIZATION_FOR_ANY_S1_WORK
```
