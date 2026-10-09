# KATS-ORB-CASH-EQ-LONG-V2 — independent review protocol addendum

**Document type:** methodological review resolution only  
**Hypothesis:** KATS-ORB-CASH-EQ-LONG-V2  
**Source commit reviewed:** 07679a3761a68fc8b3c394ac2ae63611f274ccf3  
**Review date:** 2026-10-09  
**Status:** accepted clarification for the next data gate  
**Authorization boundary:** documentation only; no implementation, compatibility audit, P&L calculation, validation/holdout outcome access, paper execution, or broker order.

## 1. Scope and authority

This addendum resolves two documentation ambiguities in the frozen V2 preregistration:

1. the sequencing of the complete-bucket compatibility audit relative to the sealed holdout; and
2. the separation of actual-executable evidence from independent candle-diagnostic equity paths.

It does not edit or replace `PREREGISTRATION.md`. It changes no economic or strategy rule. The frozen signal, thresholds, entry information clock, stop, 1% adverse SL-L band, slippage scenarios, costs, ₹20,000 starting capital, 3% planned-risk ceiling, partitions, and denominator requirements remain unchanged.

Where sections 3.3 and 13 could be read as permitting an early holdout signal-identity inspection, this addendum supplies the controlling staged access protocol. It does not authorize any stage.

## 2. Resolution A — staged compatibility and holdout-access protocol

### Stage 0 — immutable inputs and sealed-holdout commitment

Before any compatibility work:

- hash and record every source file;
- record the exact code commit, configuration, timezone interpretation, corporate-action conversion, date-effective tick sources, cost sources, and partition boundaries;
- place the holdout files or holdout slice behind a technical access gate;
- record its cryptographic manifest without deriving ORB, RVOL, direction, breakout, ranking, decision time, entry, exit, or P&L;
- ensure the person or process interpreting validation results cannot inspect holdout-derived strategy outputs.

The sealed holdout remains 2025-11-01 through 2026-04-30.

### Stage 1 — QA, development, and validation compatibility audit

After separate Founder authorization, an outcome-blind signal-identity comparison is permitted only for:

- WARMUP_AND_DATA_QA;
- DEVELOPMENT_DISCLOSED; and
- VALIDATION.

Permitted outputs are limited to data-integrity records and the legacy-versus-complete-bucket signal identity fields already defined by V2:

- date;
- symbol;
- direction;
- decision timestamp;
- compatibility reason/status.

No entry price, exit price, post-signal return, trade P&L, future path, favorable excursion, adverse excursion, or outcome-derived ranking may be computed or exposed by this audit.

If complete-bucket enforcement adds, removes, direction-changes, time-shifts, or re-ranks any signal in these partitions:

- set `FROZEN_SIGNAL_COMPATIBILITY=FAILED`;
- disclose the incompatibility without scoring it;
- stop before entry simulation or P&L;
- require Founder review.

The holdout remains unopened regardless of the Stage 1 result.

### Stage 2 — optional pre-gate holdout structural scan

Before the authorized holdout-opening gate, no holdout signal identity may be generated, compared, counted, ranked, or revealed.

If a holdout structural scan is operationally required to verify that the sealed files are readable, it must not execute signal logic. Its permitted inputs and outputs are restricted as follows.

Permitted integrity metadata:

- cryptographic file hashes and byte sizes;
- file/container format and schema names/types;
- encoding and compression metadata;
- timestamp unit, timezone declaration, and coverage start/end;
- total raw row count;
- aggregate duplicate-timestamp count;
- aggregate missing-minute count;
- aggregate malformed-OHLCV count;
- aggregate off-grid timestamp count;
- scanner/code version and scan timestamp;
- a coarse `PASS / FAIL / UNRESOLVED` integrity status;
- the hash of any detailed sealed scan artifact.

Forbidden pre-gate outputs:

- opening-range values;
- RVOL values or threshold pass/fail;
- signal existence, count, direction, date, symbol, decision time, ordering, or ranking;
- incomplete-bucket status tied to any candidate signal;
- entry/exit eligibility;
- prices beyond coverage metadata;
- future paths, returns, P&L, or any outcome statistic.

Any detailed row-, date-, symbol-, session-, or bucket-level scan artifact must remain sealed and inaccessible to the research decision maker until the holdout-opening gate. A pre-gate scan may validate file integrity only; it may not certify holdout signal compatibility.

### Stage 3 — authorized holdout-opening gate

The holdout may be opened only after all of the following are committed and independently reviewed:

1. implementation and unit tests;
2. source and cost manifests;
3. the Stage 1 compatibility result;
4. validation results and their interpretation;
5. confirmation that no V2 rule changed after validation;
6. explicit Founder authorization to open the holdout.

At that gate, the order is mandatory:

1. verify the holdout file hashes against the sealed manifest;
2. open any sealed structural-scan detail;
3. run the legacy-versus-complete-bucket holdout signal-identity comparison;
4. examine only compatibility outputs first;
5. if any signal is added, removed, direction-changed, time-shifted, or re-ranked, set `HOLDOUT_SIGNAL_COMPATIBILITY=FAILED`, stop immediately, do not calculate or reveal holdout P&L, and require Founder review;
6. only when compatibility is exact may a separately authorized holdout P&L stage begin.

Thus, holdout signal compatibility is checked before holdout P&L, but holdout signal identities are not accessed before the authorized opening gate.

### Stage 4 — outcome access, if separately authorized

Compatibility success does not itself authorize P&L. Any holdout scoring must use the already frozen implementation, manifests, and separate-ledger rules below. No rule may be changed between compatibility confirmation and scoring.

## 3. Resolution B — non-mixing ledger architecture

The following six ledgers are separate accounting universes:

1. `ACTUAL_EXECUTABLE`;
2. `CANDLE_DIAGNOSTIC_BASE`;
3. `CANDLE_DIAGNOSTIC_ADVERSE`;
4. `CANDLE_DIAGNOSTIC_SEVERE`;
5. `CANDLE_DIAGNOSTIC_DELAYED_ENTRY`;
6. `CANDLE_DIAGNOSTIC_STOP_NONFILL`.

No ledger may borrow a fill, exit, position state, cash balance, quantity, charge, or equity value from another ledger. Each record must carry `ledger_id`, chronological sequence, pre-trade equity status, planned-risk calculation, quantity decision, entry evidence class, exit evidence class, costs, post-trade equity status, and unresolved reason where applicable.

The same frozen signal stream and long-only/short-retention denominators feed every ledger. Scenario results may never be combined into a best-case composite.

## 4. ACTUAL_EXECUTABLE ledger

`ACTUAL_EXECUTABLE` admits only causally evidenced broker execution:

- synchronized quote/depth available at the decision;
- submitted-order event;
- terminal IOC entry status;
- actual filled quantity and average entry price;
- protective-order acknowledgement;
- stop/time-exit order events;
- confirmed exit fills;
- final order-book and position reconciliation;
- actual date-effective charges.

Historical candles alone provide none of these broker states. Therefore:

- no candle price is entered as an actual fill;
- no stop touch is entered as an actual exit;
- no historical trade P&L is entered as actual realized P&L;
- the ₹20,000 initial cash fact is recorded, but an actual historical equity path is not manufactured;
- from the first causally unresolved potential position onward, `ACTUAL_EXECUTABLE_EQUITY=UNRESOLVED`;
- downstream exact actual quantity and risk remain unresolved rather than assuming that the position did or did not occur.

A signal with insufficient broker evidence remains visible with the appropriate unresolved status. It is not silently converted into a no-trade, win, loss, or zero-P&L event.

`ACTUAL_EXECUTABLE_PNL` is numeric only if every admitted entry, exit, charge, and portfolio state is causally evidenced. Otherwise it is `UNRESOLVED`.

## 5. Independent candle-diagnostic ledgers

Each candle-diagnostic ledger begins independently at hypothetical equity ₹20,000 and processes signals chronologically using only its named frozen scenario.

For ledger `L` before candidate `i`:

- `E_L_i` is that ledger's own last fully resolved hypothetical net equity;
- `MAX_PLANNED_RISK_L_i = 0.03 × E_L_i`;
- the frozen entry bound, structural stop, 1% adverse SL-L limit band, date-effective ticks, whole-share enumeration, cash affordability, and dated costs are applied within that ledger;
- quantity is the maximum whole-share quantity passing both full-cash funding and the exact 3% planned-risk inequality for that ledger;
- the quantity may not be copied from another scenario;
- the ledger's hypothetical net result, when fully resolved under its own diagnostic convention, is applied before sizing the next candidate.

For a fully resolved diagnostic trade:

`E_L_(i+1) = E_L_i + hypothetical_gross_PnL_L_i - hypothetical_costs_L_i`.

This is labeled hypothetical diagnostic equity, never actual realized equity or executable capital.

### CANDLE_DIAGNOSTIC_BASE

Uses only the frozen BASE candle-pricing and slippage assumptions. It carries forward only its own resolved hypothetical net equity.

### CANDLE_DIAGNOSTIC_ADVERSE

Uses only the frozen ADVERSE candle-pricing and slippage assumptions. It independently recalculates quantity and 3% risk from its own prior hypothetical net equity.

### CANDLE_DIAGNOSTIC_SEVERE

Uses only the frozen SEVERE candle-pricing and slippage assumptions. It independently recalculates quantity and 3% risk from its own prior hypothetical net equity.

### CANDLE_DIAGNOSTIC_DELAYED_ENTRY

Uses only the frozen delayed-entry diagnostic timing and its associated frozen pricing/cost convention. The delay may not be changed after outcomes. It independently carries its own hypothetical net equity.

### CANDLE_DIAGNOSTIC_STOP_NONFILL

Retains triggered-but-unfilled, gap-below-limit, missing-bid, and otherwise conditionally unresolved exits as unresolved. It never substitutes the protective limit, time-exit price, last traded price, zero, or another scenario's exit.

At its first unresolved open-position outcome:

- retain the position and exit as `UNRESOLVED`;
- set that ledger's post-event equity to `UNRESOLVED`;
- do not assign a favorable, neutral, stop-limit, or total-loss value;
- do not size later candidates numerically because the exact 3% risk ceiling and available cash are no longer knowable;
- retain later signals in chronological order as `NOT_SIZED_UPSTREAM_EQUITY_UNRESOLVED`;
- report the unresolved event and all downstream affected signals.

## 6. Unresolved exits in any diagnostic ledger

The nonfill rule is universal, although it is expected to be most visible in `CANDLE_DIAGNOSTIC_STOP_NONFILL`.

Whenever a named diagnostic's own frozen convention cannot determine a conditional exit without inventing execution:

1. record the entry diagnostic and position state;
2. record the exit as `UNRESOLVED`;
3. do not book P&L or costs that depend on the unknown fill;
4. set that ledger's equity path to `UNRESOLVED`;
5. stop numeric sizing and equity propagation in that ledger;
6. continue recording later signals and their audit status without trades or performance metrics;
7. do not switch to another scenario, fallback exit, or favorable assumption.

A ledger with unresolved equity cannot report numeric ending equity, net return, profit factor, expectancy, drawdown, or portfolio P&L beyond the last resolved event. It must report the relevant metric as `UNRESOLVED` and separately report the last fully resolved prefix.

This rule prevents survival bias from silently deleting difficult exits and prevents a fictitious equity value from influencing later 3% sizing.

## 7. Common denominator and reporting requirements

For every ledger, preserve:

- all bidirectional frozen signals;
- eligible long signals;
- short signals marked `INELIGIBLE_DIRECTION_LONG_ONLY`;
- incomplete-bucket/provenance failures;
- cash/risk rejections;
- entry-fill-unresolved records;
- stop-fill-unresolved records;
- last fully resolved chronological prefix;
- downstream records blocked by unresolved equity.

Reports must place `ACTUAL_EXECUTABLE` first and clearly separate it from every candle diagnostic. No candle-diagnostic P&L may be described as actual, executable, verified, or deployable.

## 8. Review findings

The section 3.3/13 conflict is resolved by staged access:

- compatibility comparison is permitted pre-holdout for QA, development, and validation;
- pre-gate holdout inspection is limited to non-strategy integrity metadata;
- holdout signal identities remain sealed;
- after explicit holdout-opening authorization, signal compatibility is checked before any P&L;
- any incompatibility stops scoring and requires Founder review.

The equity ambiguity is resolved by six independent ledgers:

- `ACTUAL_EXECUTABLE` never fabricates historical execution or realized equity;
- each candle scenario has its own hypothetical chronological cash/equity path and exact 3% sizing;
- unresolved exits poison only their own ledger's downstream numeric equity, while all signals remain visible.

These are review and accounting controls. They do not alter the economic hypothesis.

## 9. Resolution record

SOURCE_COMMIT=07679a3761a68fc8b3c394ac2ae63611f274ccf3  
HOLDOUT_ACCESS_RESOLVED=YES_STAGED_GATE_WITH_NO_PRE_GATE_SIGNAL_IDENTITY_ACCESS  
DIAGNOSTIC_LEDGER_RESOLVED=YES_SIX_NON_MIXING_LEDGERS_WITH_INDEPENDENT_CHRONOLOGICAL_EQUITY  
STRATEGY_RULES_CHANGED=NO  
SEALED_HOLDOUT_ACCESSED=NO  
COMPATIBILITY_AUDIT_EXECUTED=NO  
BACKTEST_RUN=NO  
P&L_CALCULATED=NO  

FINAL_VERDICT=ACCEPT_FOR_NEXT_DATA_GATE
