# KATS-ORB-CASH-EQ-11STOCK-LONG-V1 — independent causal review protocol addendum

**Document type:** independent methodological review resolution  
**Hypothesis:** `KATS-ORB-CASH-EQ-11STOCK-LONG-V1`  
**Frozen preregistration commit reviewed:** `f8a9ae9cc17db674a04e8c136915efcdfa1decd0`  
**Frozen preregistration blob:** `71fd943cf52b4d3b745850861e6ec9db564cfbc1`  
**Authorization boundary:** review documentation only. No implementation, signal generation, backtest, P&L, paper trade, live order, or sealed-holdout access.

## 1. Verdict and authority

`FINAL_VERDICT=ACCEPT_WITH_NON_ECONOMIC_ADDENDUM`

Both issues are resolved as causal-evidence and state-timing interpretations of the frozen rules. No universe, signal, ranking, direction, entry intent, stop, target, risk, cost, portfolio, partition, or economic decision rule changes.

This addendum does not edit or replace `PREREGISTRATION.md`. It controls the interpretation of sections 5, 6, 7, and 16. Any reading that conditions a reference-minute-open diagnostic on that minute's eventual volume or completed OHLC validity is rejected.

## 2. Causal clocks

For candidate c:

- `T_c`: completed breakout-candle availability time;
- `A1_c`: availability time of c's completed post-signal M1;
- `P_c`: time c actually becomes active after every higher-ranked candidate is causally resolved;
- `E_c = max(A1_c, P_c)`: causal eligibility-evaluation time;
- `delta_order > 0`: frozen nonzero submission latency;
- `R_c`: first full one-minute interval whose start is strictly later than `E_c`, so a hypothetical order could have been submitted after `E_c + delta_order` before the reference interval began.

At `R_c` start, only information available at or before that instant may affect admission. The eventual high, low, close, volume, or completed-bar validity of `R_c` is not available at its open and cannot retrospectively determine whether an entry at its open is accepted.

## 3. Diagnostic-entry hindsight resolution

The open of `R_c`, plus frozen ledger-specific adverse slippage and upward tick rounding, may be recorded only as:

```text
ENTRY_EVIDENCE_CLASS=CANDLE_DIAGNOSTIC_ONLY
BROKER_ENTRY_FILL_STATUS=UNRESOLVED
```

It is never an actual order, quote, displayed-depth observation, queue event, fill, or broker-verified entry. Candle diagnostics never count as broker-evidenced executions.

### Prohibited filtering

It is prohibited to:

1. assign `R_c.open` as entry;
2. inspect `R_c.volume/high/low/close`;
3. reject the entry because those later fields are zero, malformed, or unfavorable; and
4. promote a lower-ranked candidate as though the first entry never occurred.

Instead:

- later high, low, close, or volume cannot decide whether the diagnostic reference existed;
- zero eventual volume cannot retrospectively erase the reference or free the portfolio;
- later-discovered invalid OHLC, duplicate/off-grid time, zero volume, missing completed bar, or another integrity defect produces `CANDLE_ENTRY_DATA_INTEGRITY_UNRESOLVED`;
- that status stops numeric propagation in the affected diagnostic ledger;
- it blocks lower-ranked promotion;
- no favorable, neutral, stop, time-exit, or total-loss P&L is assigned;
- the observation remains in every applicable denominator.

If `R_c.open` itself is absent, nonnumeric, nonfinite, or cannot be associated with the predetermined timestamp, classify `CANDLE_ENTRY_REFERENCE_UNRESOLVED`. Do not invent a price or retrospectively promote another candidate.

For real execution, the eventual reference-minute candle is irrelevant. Eligibility uses completed M1 data followed by a fresh quote and broker events. Real IOC admission may not depend on future minute OHLCV.

## 4. Same-timestamp candidates

For two or more signals sharing a decision timestamp:

1. Preserve ranking by RVOL descending, normalized breakout distance descending, then symbol ascending.
2. Activate only the highest-ranked direction-eligible candidate.
3. Lower-ranked candidates do not have simultaneous independent access to the shared account.
4. Preserve all signals and ranks.
5. No later price, return, fill quality, or stop outcome can alter rank.

SHORT remains `INELIGIBLE_DIRECTION_LONG_ONLY`; its rejection is knowable without an entry attempt, so scanning may continue only while the portfolio and all order states are provably flat.

## 5. Earlier candidate fails pre-order admission

When an active LONG causally fails data/corporate-action, RMS, cash/risk, quote, or displayed-depth admission:

- record the exact rejection and its availability timestamp;
- activate the next candidate at that timestamp, not at the earlier shared signal time;
- set `P_c` to that rejection availability time;
- set `E_c = max(A1_c, P_c)`;
- re-evaluate cash, risk, quote freshness, depth, and cutoff from information available at `E_c`;
- submit only after the promoted candidate's own nonzero latency;
- for diagnostics, use only the first full minute starting strictly after `E_c`;
- never use the open of a minute already begun.

## 6. Earlier IOC confirms zero fill

A submitted IOC blocks every lower-ranked candidate until evidence confirms:

1. terminal IOC status;
2. filled quantity exactly zero;
3. no live entry remainder;
4. position quantity zero;
5. no protective or exit order; and
6. recorded reconciliation timestamp.

Only then can the next candidate activate:

`E_next = max(A1_next, zero_fill_terminal_reconciliation_time)`.

It requires a fresh quote, new risk/cash calculation, and new nonzero-latency submission. It cannot inherit the prior candidate's time, quote, depth, quantity, risk, or any minute open from before promotion.

Historical candles contain no IOC events. Price candles, volume, or a missed touch cannot prove zero fill. Without an evidenced zero-fill reconciliation timestamp, status is:

`LOWER_RANK_PROMOTION_TIMING_UNRESOLVED`.

That status blocks later candidates and numeric ledger propagation for the session.

## 7. Partial fill and delayed reconciliation

Any positive partial or full fill occupies the once-per-day portfolio immediately.

When cancellation, terminal status, protection acknowledgement, position reconciliation, or sell reconciliation takes longer than expected:

- lower candidates remain blocked throughout;
- no diagnostic reference minute may be assigned during the unresolved interval;
- no new timeout is invented;
- failure to prove terminal flat state becomes `ORDER_STATE_UNRESOLVED`;
- later prices cannot decide whether waiting would have been favorable.

Once a positive fill occurs, all later candidates remain `DAILY_PORTFOLIO_OCCUPIED`, even after exit.

## 8. Reference minute already begun or ended

A promoted candidate never uses the open of a minute begun before it became causally eligible to submit.

- Promotion inside a minute: earliest reference is the next full minute.
- Promotion exactly at a minute boundary: because `delta_order > 0`, earliest reference is the following full minute.
- Promotion after a proposed minute ended: that minute is prohibited.

If the required later minute is missing or ambiguous, classify `CANDLE_ENTRY_REFERENCE_UNRESOLVED`; do not fall back to an earlier open or promote another candidate.

The DELAYED_ENTRY ledger uses one additional full minute after the causally selected base reference. It does not recompute priority from later outcomes.

## 9. Final permissible entry time

The frozen cutoff is interpreted exactly:

```text
order_submission_time <= 12:01:00 Asia/Kolkata
```

A decision, quote, or promotion before 12:01 is insufficient if submission after `delta_order` would occur later.

If the next submission or diagnostic reference lies beyond the cutoff:

- record `ENTRY_CUTOFF_EXPIRED`;
- assign no order or diagnostic entry;
- reuse no earlier minute;
- promote no lower candidate after cutoff;
- preserve remaining signal identities and rejection statuses.

## 10. Ledger treatment

### ACTUAL_EXECUTABLE

Only actual quotes, orders, fills, cancellations, positions, protection, and exits establish timing/equity. Zero-fill promotion requires recorded terminal reconciliation.

### Candle diagnostics

Each ledger applies the same causal promotion rules independently. It cannot manufacture IOC outcomes from OHLCV. If promotion depends on unavailable hypothetical order events, the ledger becomes unresolved and stops numeric equity/quantity propagation.

Unresolved records remain in signal, long, collision/rank, entry-unresolved, and adequacy counts. They are not executions.

## 11. Why no economic rule changed

Unchanged:

- eleven-stock universe and selection provenance;
- opening range, RVOL 1.50, prior twenty sessions, completed five-minute signal;
- long-only filter and short-signal accounting;
- four ranking keys and their order;
- once-per-day shared portfolio;
- completed M1 wait and nonzero latency;
- BUY LIMIT IOC intent;
- opening-range-low stop and one-percent adverse SL-L band;
- no target and same-day exit;
- ₹20,000 full-cash account and exact 3% planned-risk ceiling;
- costs, scenario ledgers, partitions, denominators, sample threshold, and holdout gate.

The addendum removes a hindsight-permitting interpretation and specifies when frozen priority can advance. It may reduce historically scorable diagnostics, but evidence refusal is not an economic-rule change.

## 12. Review record

```text
SOURCE_COMMIT=f8a9ae9cc17db674a04e8c136915efcdfa1decd0
FILES_CHANGED=experiments/kats-orb-cash-eq-11stock-long-v1/REVIEW_PROTOCOL_ADDENDUM.md
DIAGNOSTIC_ENTRY_LOOKAHEAD=RESOLVED_NO_REFERENCE_MINUTE_FUTURE_OHLCV_MAY_CONDITION_ENTRY_AT_ITS_OPEN
CANDIDATE_TIMING_DETERMINISM=RESOLVED_PER_CANDIDATE_ACTIVATION_EVALUATION_SUBMISSION_AND_RECONCILIATION_CLOCKS
FUTURE_VOLUME_FILTERING_PREVENTED=YES_ZERO_OR_LATER_VOLUME_CANNOT_RETROACTIVELY_REJECT_OR_PROMOTE
UNRESOLVED_ENTRIES_PRESERVED=YES_BLOCK_PROMOTION_AND_NUMERIC_LEDGER_PROPAGATION
RANKING_RULE_PRESERVED=YES
ECONOMIC_RULES_CHANGED=NO
FROZEN_V2_CHANGED=NO
SIGNALS_GENERATED=NO
PNL_CALCULATED=NO
HOLDOUT_ACCESSED=NO
FINAL_VERDICT=ACCEPT_WITH_NON_ECONOMIC_ADDENDUM
NEXT_SINGLE_ACTION=INDEPENDENTLY_FREEZE_REVIEW_THE_PREREGISTRATION_AND_ADDENDUM_BEFORE_AUTHORIZING_S0_DATA_ADMISSION
```
