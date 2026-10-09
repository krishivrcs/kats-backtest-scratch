# KATS-ORB-CASH-EQ-LONG-V2 — causal-correction preregistration

**Status:** frozen before implementation, scoring, or outcome inspection  
**Hypothesis ID:** KATS-ORB-CASH-EQ-LONG-V2  
**Preregistration date:** 2026-10-09  
**Source commit:** bac30f9c42268c9b66c54c6cdc74b2e79901a0a6  
**Research branch:** research/kats-orb-cash-eq-long-v2  
**Supersedes for future testing:** KATS-ORB-CASH-EQ-LONG-V1  
**Universe:** SBIN, DLF, RELIANCE, NSE cash equity  
**Starting realized equity:** ₹20,000  
**Authorization boundary:** this document only. No implementation, P&L calculation, validation/holdout inspection, paper execution, or broker order is authorized.

## 1. Methodological verdict on V1

V1 remains immutable at its original commit. It is rejected at methodological review before scoring because:

1. its historical proxy could require completed OHLCV, including volume, from the same minute whose opening price it assigned as the entry;
2. its candle stop diagnostic could be read as an SL-L execution even though a stop trigger and a limit-order fill are separate events and the archive has no post-trigger bid/depth or order events;
3. the inherited function `aggregate_5m()` emits a five-minute bar from any nonempty bucket and does not require all five unique constituent one-minute bars.

V1 produced no authorized cash-equity score. Nothing in this document retroactively repairs or validates V1.

V2 is a new outcome-independent hypothesis. Its changes are limited to causal availability, executable-evidence classification, complete-bucket admission, and explicit state reconciliation. It does not use previous option trades as cash-equity evidence.

## 2. Preserved invariants

V2 preserves:

- the frozen KATS-ORB-RVOL-3STOCK-FRESH-V1 signal formula, thresholds, direction rules, chronological ordering, and current-day exclusion;
- symbols SBIN, DLF, and RELIANCE;
- completed five-minute signal decisions;
- opening range 09:15:00–09:29:59 IST;
- RVOL equal to current opening volume divided by the mean of exactly the prior twenty valid sessions;
- RVOL threshold 1.50;
- first completed close above opening-range high as LONG and first completed close below opening-range low as SHORT;
- signal window strictly after 09:30 through decision time 12:00 IST;
- explicit long-only execution;
- every original SHORT signal retained as `INELIGIBLE_DIRECTION_LONG_ONLY`;
- one shared ₹20,000 cash account, whole shares, no leverage, and at most one executed long per session;
- maximum planned risk of 3% of current realized equity;
- opening-range-low conceptual stop;
- date-effective tick conversion;
- SL-L trigger at the tick-valid structural stop and limit at `floor_to_tick(trigger × 0.99)`;
- no profit target;
- same-day mandatory time exit with date-effective RMS provenance;
- date-effective all-in costs;
- RELIANCE corporate-action conversion;
- the V1 data partitions;
- prior frozen experiments and evidence.

Changing any strategy threshold, delay, stop, 1% band, slippage schedule, partition, or denominator after outcome inspection creates a new hypothesis.

## 3. Signal completeness and compatibility gate

### 3.1 Valid one-minute input

Every admitted minute must have:

- one unique timestamp on the verified Asia/Kolkata minute grid;
- finite positive O/H/L/C;
- `low <= min(open, close) <= max(open, close) <= high`;
- finite non-negative volume;
- no duplicate timestamp.

Suspicious data are rejected, not repaired, forward-filled, interpolated, or copied from another source.

### 3.2 Complete five-minute candle

For a nominal bucket starting at minute `b`, the bar exists only when the source contains exactly the five unique minutes:

`b, b+1, b+2, b+3, b+4`.

The timestamps must be consecutive after verified source timestamp semantics. A bucket with zero through four valid minutes, a duplicate, an off-grid minute, or a malformed constituent is `INCOMPLETE_5M_BUCKET` and no OHLCV bar may be emitted.

Open is the first constituent open, high is the maximum high, low is the minimum low, close is the fifth constituent close, and volume is the sum of all five volumes. This aggregation uses only constituents available by the bucket completion time.

The 09:15–09:29 opening range continues to require exactly fifteen unique valid minutes. Every later five-minute candle examined for a signal must independently pass the five-constituent rule.

### 3.3 Frozen-engine compatibility audit

The parent code at source commit uses `aggregate_5m()` without a five-minute count/grid check. Before any future implementation or P&L:

1. hash and freeze the source archives;
2. run a structural, outcome-blind missing-minute audit across QA, development, validation, and sealed holdout dates;
3. produce a legacy-versus-complete-bucket signal identity report containing only date, symbol, direction, decision timestamp, and reason—not returns or later prices;
4. compare the entire inherited signal ledger under legacy aggregation and V2 complete aggregation.

If any signal is added, removed, direction-changed, or time-shifted, set `FROZEN_SIGNAL_COMPATIBILITY=FAILED`, publish the incompatibility counts, keep all affected records visible, and stop before entry simulation or P&L pending Founder review. V2 may not silently rewrite earlier signal outcomes.

Until that audit is performed under separate authorization:

`FROZEN_SIGNAL_COMPATIBILITY=UNRESOLVED_PENDING_OUTCOME_BLIND_BUCKET_AUDIT`.

## 4. Timestamp provenance and information clock

No entry or signal may be evaluated until the data manifest proves whether each timestamp denotes interval start or interval end, its timezone, and when the completed bar becomes available.

Define:

- `T`: availability time of the completed five-minute breakout candle, after source latency;
- `M1`: first complete one-minute interval beginning at or after T;
- `A1`: availability time of completed M1, no earlier than M1 end;
- `delta_order`: nonzero operational latency between an eligibility decision and order submission.

V2 freezes historical eligibility evaluation at `A1`, nominally T+60 seconds only when timestamp semantics establish that M1 is exactly one full minute. All M1 OHLCV may be used only at or after A1. None of M1 high, low, close, or volume may support an assumed fill at M1 open.

If T, M1, A1, or their availability ordering cannot be proven, classify the signal `TIMESTAMP_CAUSALITY_UNRESOLVED`. No fill or P&L is assigned.

## 5. Real quote-driven entry specification

Historical candles and live execution are separate evidence classes.

For a future quote-driven implementation, subject to separate Founder authorization:

1. At T, record the inherited completed signal. Do not submit an order.
2. Observe M1 in full.
3. At A1, use only completed M1 fields and information already available before A1 for data-quality and session eligibility.
4. After A1, obtain a synchronized NSE_EQ quote with exchange timestamp no older than one second, positive bid and ask, and displayed ask quantity.
5. Calculate the maximum tentative whole-share quantity under sections 9 and 10 using a tick-valid adverse entry bound at or above the current ask.
6. Require displayed ask quantity at least equal to tentative quantity. This is an admission test, not a fill guarantee.
7. At `A1 + delta_order`, where `delta_order > 0`, submit one BUY LIMIT IOC, product I, for that quantity.
8. Accept filled quantity, fill timestamps, and actual average price only from broker order events/status reconciliation.
9. Zero fill is `NO_FILL`; no retry and no trade.
10. Partial fill is accepted only for the confirmed whole-share filled quantity; the IOC remainder must be terminally cancelled before protection sizing.
11. Submit protection only after terminal entry reconciliation establishes exact filled quantity and no live entry remainder.

Completed candle volume, a traded price, or a candle touching the limit never proves that this IOC filled.

## 6. Historical entry classification

The identified archives do not contain contemporaneous quotes, displayed depth, order acknowledgements, queue position, IOC events, or fills. Therefore they cannot verify the real entry process in section 5.

For each historically eligible long signal:

- M1 can be used only after it completes at A1;
- M1 open is prohibited as an entry price after using M1 high, low, close, or volume;
- the next candle open is not automatically an executable fill because the real order would be submitted after A1 with nonzero latency;
- a candle-only, outcome-independent diagnostic may use the first full minute beginning after A1 as a reference price plus the frozen adverse slippage schedule, but it must be labeled `CANDLE_ENTRY_DIAGNOSTIC_ONLY`;
- positive volume or a low/high crossing does not upgrade that diagnostic to a fill;
- without quote and order-event evidence, executable entry status is `BROKER_ENTRY_FILL_UNRESOLVED`.

An executable trade and executable P&L may not be reported from the diagnostic price. The record remains in all strategy denominators.

## 7. Structural protection and stop causality

The conceptual stop remains the completed 09:15–09:29 opening-range low on the date-effective tradable basis.

- `stop_trigger = floor_to_tick(conceptual_stop)`;
- `protective_limit = floor_to_tick(stop_trigger × 0.99)`;
- the 1% band is an execution band, not a new strategy stop;
- the stop may not be tightened to satisfy risk;
- there is no profit target or trailing stop.

After a confirmed entry fill:

1. reconcile the terminal IOC entry state and actual position quantity;
2. submit one SELL SL-L, product I, DAY, for exactly the confirmed position;
3. require broker acknowledgement within the frozen two-second window;
4. until protection is acknowledged, the position is `ENTRY_FILLED_PROTECTION_PENDING`;
5. rejection or missing acknowledgement starts the frozen emergency IOC exit process;
6. an SL-L trigger changes only order state; it does not prove an execution;
7. after trigger, fill quantity and average price require broker order events plus position reconciliation;
8. if triggered but unfilled for more than two seconds, cancel the outstanding remainder, confirm cancellation or reconcile exact state, and only then begin emergency IOC exits;
9. no new sell quantity may make total live sell quantity exceed the confirmed long position.

A gap, circuit, missing bid, protection rejection, broker outage, or unfilled limit can cause realized loss above planned risk. The 3% gate is an admission ceiling, never a loss guarantee.

## 8. Historical stop classification

A completed candle whose range reaches `stop_trigger` proves only that a trigger condition may have occurred under the verified trade-price convention. It does not prove:

- trigger timing inside the minute;
- bid availability;
- displayed depth;
- queue priority;
- a trade at or above `protective_limit` after the trigger;
- order acceptance or fill.

When post-trigger bid/depth and order events are absent:

- classify the exit `STOP_TRIGGER_OBSERVED_FILL_UNRESOLVED`;
- do not assign `protective_limit` or any candle price as a verified fill;
- retain the signal/trade record in all denominators;
- report the intended protective bound and any candle-only conditional diagnostics separately;
- set executable trade P&L to `UNRESOLVED`.

Permitted conditional diagnostics, never executable fills:

- `CANDLE_STOP_TRIGGER_ONLY`: first complete candle whose low reaches the trigger;
- `CANDLE_LIMIT_COMPATIBLE_PATH_UNKNOWN`: post-trigger candle range includes the limit but ordering, bid, and queue are unknown;
- `CANDLE_GAP_BELOW_LIMIT`: first observable post-trigger price is below the limit;
- `CANDLE_NO_RETURN_TO_LIMIT`: no later candle range reaches the limit before time exit.

No unresolved stop may be discarded from trade count, win-rate denominator, signal denominator, or concentration analysis. Verified executable aggregate P&L is `UNRESOLVED` if any included position lacks a verified causal exit.

## 9. Cash and planned-risk gate

Starting realized cash equity is ₹20,000. There is one shared account, whole shares only, no borrowing, no leverage, and no assumed broker multiplier.

Before entry:

- `max_planned_risk = 0.03 × current_realized_equity`;
- entry bound is the tick-valid adverse IOC limit;
- protective exit bound is the frozen SL-L limit, not the trigger;
- planned price risk is quantity × (entry bound − protective limit);
- planned cost risk includes the date-effective estimated entry and protective-exit charges;
- cash use is quantity × entry bound plus reserved entry charges;
- exact whole-share enumeration selects the maximum quantity satisfying both available-cash and planned-risk inequalities;
- displayed ask quantity may further reduce quantity but never increase it.

Reject when no quantity of at least one share passes. A favorable actual fill cannot be used to increase the already-submitted quantity. Partial fills are rechecked only to verify, never enlarge, risk.

Planned risk excludes unknown gap/non-fill overrun from its admission arithmetic but must display:

- intended planned loss;
- planned risk percentage;
- actual realized loss when known;
- risk overrun;
- unresolved contingent loss when the position lacks an evidenced exit.

## 10. Order and position state machine

Required durable states are:

`SIGNAL_RECORDED -> M1_OBSERVING -> ENTRY_ELIGIBILITY_EVALUATED -> ENTRY_SUBMITTED -> ENTRY_TERMINAL_RECONCILED -> PROTECTION_SUBMITTED -> PROTECTION_ACKNOWLEDGED -> EXIT_PENDING -> FLAT_RECONCILED`.

Alternative terminal states include:

- `INELIGIBLE_DIRECTION_LONG_ONLY`;
- `DATA_UNRESOLVED`;
- `ENTRY_REJECTED`;
- `NO_FILL`;
- `PARTIAL_FILL_PROTECTED`;
- `PROTECTION_FAILED_EMERGENCY_EXIT`;
- `STOP_TRIGGERED_UNFILLED`;
- `EXECUTION_UNRESOLVED`;
- `OVERNIGHT_SAFETY_FAILURE`.

No exit replacement is submitted until order book, pending quantity, and position quantity are reconciled. Unknown cancellation state blocks additional sell orders to prevent unintended short exposure. After a confirmed exit, cancel any residual protective order and reconcile both position and pending sell quantity to zero before the session is closed.

## 11. Mandatory intraday exit and RMS provenance

There is no target. An admitted position exits through verified protective execution or the mandatory time-exit process.

The intended voluntary time exit remains 14:50 IST. Before each admitted historical regime or prospective session, the manifest must establish the date-effective Upstox RMS cutoff. The chosen exit must be at least ten minutes earlier. If 14:50 fails that condition, use the documented cutoff minus ten minutes, frozen before the session. Unknown cutoff means `RMS_CUTOFF_UNRESOLVED` and rejection.

Time exit requires:

1. cancel/reconcile the protective order;
2. obtain a fresh valid bid;
3. submit SELL LIMIT IOC for no more than the reconciled remaining position;
4. reconcile partial fills before any retry;
5. repeat according to the frozen emergency cadence until flat or session closure.

RMS square-off is a safety failure, not the planned exit. Its actual charges and fill are recorded only from evidence. An unclosed position is `OVERNIGHT_SAFETY_FAILURE` and terminates the experiment.

Historical time-exit candles are diagnostics only unless executable quote/order evidence exists.

## 12. Costs, ticks, corporate action, and data

V2 inherits V1 unchanged:

- date-effective NSE cash ticks from the applicable security master, with missing or contradictory tick evidence failing closed;
- entry limits rounded upward; stop triggers, protective limits, and sell limits rounded downward;
- date-effective brokerage, STT, exchange transaction charges, SEBI charges, IPFT where applicable, GST, stamp duty, and any actual RMS/call-and-trade charge;
- frozen BASE, ADVERSE, SEVERE, delayed-entry, and stop-nonfill diagnostic scenarios, without selecting the best result;
- RELIANCE 1:1 bonus conversion: through 25 October 2024 adjusted source prices ×2 for tradable-price calculations; from 28 October 2024 factor 1, subject to manifest verification;
- archive hashing, timezone checks, malformed/duplicate/missing-minute checks, and independent source comparison.

If any historical charge, tax base, tick, RMS cutoff, timestamp, or corporate-action basis is unresolved, executable net P&L remains `UNRESOLVED`.

## 13. Frozen partitions and holdout protection

Partitions are unchanged:

- `WARMUP_AND_DATA_QA`: 2024-04-01 through 2024-10-14; no scored P&L;
- `DEVELOPMENT_DISCLOSED`: 2024-10-15 through 2024-10-31; development only;
- `VALIDATION`: 2024-11-01 through 2025-10-31;
- `SEALED_HOLDOUT`: 2025-11-01 through 2026-04-30.

This preregistration does not authorize reading returns, entries, exits, or P&L in validation or holdout.

A future structural completeness audit may read timestamps and OHLCV validity solely to determine whether five constituent bars exist. It must not expose future returns or entry/exit outcomes. If signal identity changes, stop before scoring.

The holdout remains sealed until implementation, tests, source manifests, compatibility audit, and validation interpretation are committed and independently reviewed without rule changes.

## 14. Denominators and executable-P&L classification

Every report must retain:

1. all frozen bidirectional signals;
2. eligible LONG signals;
3. SHORT signals marked `INELIGIBLE_DIRECTION_LONG_ONLY`;
4. incomplete-bucket or provenance failures;
5. cash/risk rejected longs;
6. broker-entry-fill-unresolved longs;
7. stop-fill-unresolved positions;
8. candle diagnostic trades;
9. fully evidenced executable trades.

Candle diagnostics may report conditional gross/cost/net values only under labels beginning `CANDLE_DIAGNOSTIC_`. They are not broker-executable P&L.

`EXECUTABLE_PNL` is numeric only when every included entry and exit has causal quote/order/position evidence. Otherwise:

`EXECUTABLE_PNL=UNRESOLVED`.

Unresolved records remain visible and may not be reclassified as wins, losses, no-trades, or exclusions to improve metrics.

## 15. Outcome integrity and multiple-testing lineage

Prohibited before new authorization:

- implementing V2;
- running a P&L backtest;
- inspecting validation or holdout returns;
- using the prior four option trades as cash-equity evidence;
- tuning the entry delay, stop, 1% band, slippage, time exit, or filters;
- changing partitions;
- dropping unresolved or short signals;
- substituting an indicator or percentage stop;
- treating candle volume as a fill.

Lineage now includes V1 as a preregistered but methodologically rejected cash-equity hypothesis and V2 as its first causal-correction hypothesis. Any later modification is V3 or another uniquely identified hypothesis.

The counterparty to a long breakout is a seller or liquidity provider selling into opening momentum. V2 assumes no persistent loss by that counterparty. Only independent net evidence could support an edge.

## 16. Preconditions for future implementation or scoring

Independent review must first confirm:

- the information clock has no same-minute open hindsight;
- historical diagnostics cannot be mislabeled executable;
- stop trigger and fill are separate;
- incomplete five-minute buckets fail closed;
- denominators retain unresolved and short signals;
- state transitions cannot over-sell;
- exact cash and 3% risk gates are preserved;
- partitions and holdout remain sealed.

Even after review, separate Founder authorization is required for implementation. Before scoring, implementation tests and manifests must be committed, and the outcome-blind signal compatibility audit must pass with zero signal changes. Any change stops the experiment for Founder review.

Historical OHLCV alone cannot satisfy broker executability. A future prospective shadow feed would need synchronized bid/ask/depth, broker order events, position events, and timestamps. No paper or live operation is authorized here.

## 17. Authorization record

V1_STATUS=REJECTED_METHODOLOGICAL_REVIEW  
NEW_HYPOTHESIS_ID=KATS-ORB-CASH-EQ-LONG-V2  
SOURCE_COMMIT=bac30f9c42268c9b66c54c6cdc74b2e79901a0a6  
NEW_BRANCH=research/kats-orb-cash-eq-long-v2  

ENTRY_LOOKAHEAD_CORRECTED=YES_INFORMATION_CLOCK_SEPARATES_COMPLETED_M1_FROM_ANY_ENTRY_REFERENCE  
STOP_FILL_INFERENCE_CORRECTED=YES_TRIGGER_WITHOUT_POST_TRIGGER_EXECUTION_EVIDENCE_IS_UNRESOLVED  
INCOMPLETE_SIGNAL_BUCKET_HANDLING=EXACTLY_FIVE_UNIQUE_VALID_MINUTES_OR_FAIL_CLOSED  
EXECUTABLE_PNL_CLASSIFICATION=UNRESOLVED_WITHOUT_CAUSAL_ENTRY_AND_EXIT_ORDER_EVIDENCE  
FROZEN_SIGNAL_COMPATIBILITY=UNRESOLVED_PENDING_OUTCOME_BLIND_BUCKET_AUDIT  
RISK_GATE_PRESERVED=YES_EXACT_3_PERCENT_CURRENT_REALIZED_EQUITY_AND_FULL_CASH_FUNDING  
HOLDOUT_UNTOUCHED=YES  

READY_FOR_INDEPENDENT_REVIEW=YES  
READY_FOR_IMPLEMENTATION=NO  
READY_FOR_BACKTEST=NO  
LIVE_TRADING_ALLOWED=NO  

FINAL_VERDICT=V2_PREREGISTERED_READY_FOR_REVIEW
