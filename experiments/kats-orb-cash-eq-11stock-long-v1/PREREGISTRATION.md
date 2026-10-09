# KATS-ORB-CASH-EQ-11STOCK-LONG-V1 — preregistration

**Status:** frozen before implementation, signal generation, scoring, or outcome inspection  
**Hypothesis ID:** `KATS-ORB-CASH-EQ-11STOCK-LONG-V1`  
**Preregistration date:** 2026-10-09  
**Exact parent commit:** `919f17a955dc4c7110f23d21797fe2b66385136b`  
**Research branch:** `research/kats-orb-cash-eq-11stock-long-v1`  
**Starting realized equity:** ₹20,000  
**Authorization boundary:** this document only. No code implementation, signal calculation, backtest, P&L, paper order, or live order is authorized.

## 1. Hypothesis, purpose, and lineage

This is a new economic hypothesis, not a modification or extension of the frozen three-stock `KATS-ORB-CASH-EQ-LONG-V2` result.

Hypothesis:

> Across a fixed, pre-period universe of eleven historically liquid NSE cash equities, an opening-range breakout accompanied by opening relative volume of at least 1.50 may exhibit positive same-day continuation after causal long entry, full-cash whole-share sizing, an opening-range-low structural stop, conservative execution treatment, and all date-effective costs.

The opposing side is a seller or liquidity provider selling into opening momentum. No evidence establishes that this counterparty loses persistently. This preregistration permits that proposition to be falsified; it does not assume an edge.

The eleven-stock expansion changes the opportunity set and which signal receives the shared portfolio. It is therefore separately identified even though it preserves the parent signal formula and causal-execution safeguards.

### Multiple-testing lineage

The disclosed lineage includes:

1. original one-percent stock-option control;
2. three-percent stock-option risk variant;
3. fixed ₹1 option-premium-stop variant;
4. capital-aware option-contract ladder;
5. causal stock-option execution model rejected on order-type feasibility;
6. proposed Upstox GTT option route rejected at feasibility;
7. cash-equity long V1, rejected on methodological review before scoring;
8. cash-equity long V2 causal correction;
9. the three-stock V2 source/signal compatibility audit;
10. this eleven-stock long-only universe hypothesis.

Feasibility studies without outcome scoring remain disclosed but are not treated as successful independent tests. Any later alteration of the universe, ordering, entry timing, signal threshold, stop, risk, costs, partitions, or execution assumptions creates another uniquely identified hypothesis.

## 2. Fixed universe and selection provenance

The universe is frozen as:

```text
HDFCBANK
ICICIBANK
SBIN
RELIANCE
INFY
AXISBANK
KOTAKBANK
HAL
TATAMOTORS
TCS
DLF
```

Selection provenance:

- HDFCBANK, ICICIBANK, SBIN, RELIANCE, INFY, AXISBANK, KOTAKBANK, HAL, TATAMOTORS, and TCS are the ten companies in NSE Market Pulse August 2024, Table 99, ranked by July 2024 stock-futures turnover.
- DLF is added solely to preserve every member of the original three-stock universe.
- The selection evidence predates the validation boundary of 1 November 2024.
- Derivatives turnover is a universe-selection proxy, not proof of cash-market spread, depth, or fill.

Primary provenance:

- https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Market_Pulse_August_2024.pdf
- https://www.nseindia.com/static/research/publications-reports-nse-market-pulse

All eleven remain in the research denominator. No name may be removed or replaced because of archive inconvenience, signal scarcity, unfavorable results, corporate-action complexity, affordability rejection, suspension, rename, or delisting. A failed security/date is recorded fail-closed; it does not authorize a substitute.

## 3. Frozen signal engine

The underlying ORB-RVOL calculation is inherited unchanged from the frozen three-stock V2 and its legacy source.

### 3.1 Clock and opening range

- Timezone: `Asia/Kolkata`, admitted only after timestamp provenance passes.
- Source bars: completed one-minute NSE cash-equity bars.
- Derived signal bars: completed five-minute candles.
- Every five-minute candle must contain exactly five unique, valid, consecutive one-minute bars on the expected minute grid.
- Opening range: 09:15:00 through 09:29:59 IST, exactly fifteen valid one-minute bars and three complete five-minute candles.
- `opening_high`: maximum high of those fifteen bars.
- `opening_low`: minimum low of those fifteen bars.
- No incomplete or silently repaired bucket is admitted.

### 3.2 Relative volume

For each symbol and session:

- `current_opening_volume` is the sum of volume from 09:15 through 09:29;
- reference volume is the arithmetic mean of the identical window across exactly the prior twenty valid sessions for that symbol;
- the current session is excluded;
- fewer than twenty prior valid sessions means `INSUFFICIENT_20_SESSION_HISTORY`;
- nonpositive reference volume fails closed;
- `RVOL = current_opening_volume / mean(prior_20_valid_opening_volumes)`;
- require `RVOL >= 1.50`.

Validity is evaluated causally and independently for every symbol. A missing session is not replaced by a later session and is never imputed.

### 3.3 First breakout

After the completed 09:30 boundary and through decision time 12:00 IST:

- LONG: first completed five-minute candle whose close is strictly greater than `opening_high`;
- SHORT: first completed five-minute candle whose close is strictly less than `opening_low`;
- only the first breakout direction for each symbol/session is recorded;
- if neither occurs, status is `NO_BREAKOUT`.

The completed-candle decision timestamp equals the start timestamp of the qualifying five-minute candle plus five minutes, subject to proven source labeling and availability latency.

Normalized breakout distance is frozen as:

- LONG: `(breakout_close / opening_high) - 1`;
- SHORT: `(opening_low / breakout_close) - 1`.

No signal condition uses an incomplete candle, future volume, future price, subsequent return, or portfolio outcome.

## 4. Long-only expression and denominator integrity

Only original LONG signals may enter data, cash, risk, quote, and order gates.

Every SHORT signal is retained with:

`INELIGIBLE_DIRECTION_LONG_ONLY`.

Mandatory reporting layers are:

1. all frozen bidirectional signals;
2. long signals;
3. short signals retained as direction-ineligible;
4. long signals rejected by data/corporate-action eligibility;
5. long signals rejected by cash/risk eligibility;
6. long signals rejected by quote/order eligibility;
7. zero-fill entry attempts;
8. partial/full conditional candle-diagnostic entries;
9. broker-evidenced executable entries;
10. execution-unresolved positions and exits.

Shorts, unresolved observations, and rejected candidates remain visible. They may not be silently removed from the strategy denominator.

## 5. Frozen cross-sectional ordering

All same-session signal records are ordered exactly by:

1. decision timestamp ascending;
2. RVOL descending;
3. normalized breakout distance descending;
4. NSE symbol alphabetically ascending.

All numerical comparisons use full unrounded internal precision. Display rounding cannot affect rank. Exact ties reach the alphabetical rule.

The ordering is established from information available at each completed decision candle. A later signal cannot displace an earlier signal after observing subsequent prices.

### 5.1 Sequential candidate state machine

For the ordered candidate stream:

1. Record the signal and rank before execution eligibility checks.
2. SHORT is marked direction-ineligible and scanning continues while the portfolio is provably flat.
3. A LONG that fails data, corporate-action, cash, risk, RMS, quote, or order-admission checks is retained with the exact rejection reason; scanning continues only when there is no position, no live entry order, no live exit order, and no unresolved order state.
4. A BUY IOC rejected or terminally reconciled with zero fill is `NO_FILL`; no retry is permitted for that candidate. Scanning may continue to the next ranked candidate only after terminal zero-position reconciliation.
5. Any positive partial or full fill immediately occupies the portfolio for the session.
6. A partial fill accepts only the confirmed whole-share quantity. The IOC remainder must be terminally cancelled, then protection is sized for the confirmed position.
7. Once any positive entry fill occurs, no later candidate may enter that session, even after the position exits.
8. Unknown entry, cancellation, order, protection, or position state blocks all later candidates for that session.
9. No future price, return, stop outcome, or fill quality can promote a lower-ranked candidate.

### 5.2 Once-per-day portfolio occupation

The shared account permits at most one positively filled long position per NSE session across all eleven symbols. Zero fill is not portfolio occupation. Any positive partial fill is portfolio occupation. No re-entry is permitted that day.

Every skipped candidate after occupation is recorded as `DAILY_PORTFOLIO_OCCUPIED`, preserving its original signal identity and rank.

## 6. Causal information clock and entry

Define:

- `T`: availability time of the completed five-minute breakout candle, after source latency;
- `M1`: first full one-minute interval beginning at or after T;
- `A1`: availability time of completed M1, no earlier than its interval end;
- `delta_order > 0`: nonzero operational latency after eligibility is decided.

Sequence:

1. At T, record the completed signal. Do not submit an order.
2. Observe M1 completely.
3. At A1, use completed M1 information and earlier information for session/data eligibility.
4. After A1, obtain a synchronized NSE_EQ quote with exchange timestamp no older than one second, positive best bid and ask, and displayed ask quantity.
5. Derive a tick-valid adverse entry bound at or above the ask.
6. Enumerate tentative whole-share quantity under the cash and risk gates.
7. Require displayed ask quantity at least equal to tentative quantity; this is not a fill guarantee.
8. At `A1 + delta_order`, submit one BUY LIMIT IOC, product `I`.
9. Accept fill quantity, timestamp, and average price only from broker order events/status and position reconciliation.
10. Submit protection only after the entry IOC is terminally reconciled and no live entry remainder exists.

If T, M1, A1, their ordering, quote freshness, or broker state cannot be proven, reject or classify `TIMESTAMP_CAUSALITY_UNRESOLVED`. Completed candle volume or a traded-price touch never proves a fill.

No new entry may be submitted after 12:01 IST. This one-minute allowance exists only for an inherited 12:00 decision.

## 7. Historical entry classification

Historical OHLCV lacks contemporaneous bid/ask, displayed depth, queue position, acknowledgements, order events, and fills.

Therefore:

- M1 fields may be used only after A1;
- M1 open is prohibited as an assumed fill after using M1 high, low, close, or volume;
- the first full minute beginning after A1 may serve only as a candle-diagnostic reference;
- diagnostic entry applies its frozen scenario slippage and upward tick rounding;
- positive volume or a candle crossing the diagnostic price does not create a broker fill;
- executable status remains `BROKER_ENTRY_FILL_UNRESOLVED` without quote/order evidence.

Historical diagnostic trades are not broker-evidenced executions and never count toward the broker-verified sample.

## 8. Structural stop and protection

The conceptual long stop is the completed 09:15–09:29 opening-range low on the admitted date-effective tradable basis.

- `conceptual_stop = opening_low`;
- `stop_trigger = floor_to_tick(conceptual_stop)`;
- `protective_limit = floor_to_tick(stop_trigger × 0.99)`;
- the one-percent band is an adverse execution band, not a new strategy stop;
- the structural stop may not be tightened to obtain affordability;
- entry bound must be strictly greater than protective limit;
- there is no profit target or trailing stop.

After a confirmed positive entry fill:

1. terminally reconcile the entry IOC and exact position;
2. submit one SELL SL-L, product `I`, DAY validity, for exactly that quantity;
3. require broker acknowledgement within two seconds;
4. until acknowledgement, state is `ENTRY_FILLED_PROTECTION_PENDING`;
5. rejection or missing acknowledgement begins the frozen emergency IOC exit process;
6. an SL-L trigger changes order state only and does not prove execution;
7. fill quantity and average price require broker events and position reconciliation;
8. if triggered but unfilled for more than two seconds, cancel its remaining quantity, reconcile cancellation/position, then begin emergency exits;
9. cumulative live sell quantity must never exceed the confirmed long position.

A gap, lower circuit, absent bid, rejection, outage, or non-fill can exceed planned risk. The 3% gate is an admission ceiling, not a realized-loss guarantee.

## 9. Mandatory same-day exit

There is no target. Exit occurs through verified stop execution or mandatory time exit.

The intended voluntary exit starts at 14:50 IST. For every historical regime or prospective session, the manifest must prove the date-effective Upstox RMS cutoff. The voluntary exit must be at least ten minutes earlier. If not, use the documented cutoff minus ten minutes, frozen before the session. Unknown cutoff means `RMS_CUTOFF_UNRESOLVED` and rejection.

Time exit:

1. cancel and reconcile the protective order;
2. obtain a fresh valid bid;
3. submit SELL LIMIT IOC for no more than the reconciled remaining quantity;
4. reconcile partial fills before retry;
5. repeat using the frozen emergency cadence until flat or session close.

RMS square-off is a safety failure, not the intended exit. Any position not flat by the session deadline is `OVERNIGHT_SAFETY_FAILURE` and terminates the experiment.

## 10. Order and position state machine

The persisted state sequence is:

`SIGNAL_RECORDED -> RANKED -> DIRECTION_GATE -> DATA_GATE -> CASH_RISK_GATE -> M1_OBSERVING -> ENTRY_ELIGIBILITY_EVALUATED -> ENTRY_SUBMITTED -> ENTRY_TERMINAL_RECONCILED -> PROTECTION_SUBMITTED -> PROTECTION_ACKNOWLEDGED -> EXIT_PENDING -> FLAT_RECONCILED`.

Explicit terminal/intermediate states include:

- `INELIGIBLE_DIRECTION_LONG_ONLY`;
- `DATA_OR_CORPORATE_ACTION_INELIGIBLE`;
- `CAPITAL_OR_RISK_CONSTRAINT`;
- `NO_FILL`;
- `ENTRY_REJECTED`;
- `PARTIAL_FILL_PROTECTED`;
- `ENTRY_FILLED_PROTECTION_PENDING`;
- `PROTECTION_REJECTED`;
- `STOP_TRIGGERED_UNFILLED`;
- `EMERGENCY_EXIT_PENDING`;
- `TIME_EXIT_PENDING`;
- `ORDER_STATE_UNRESOLVED`;
- `DAILY_PORTFOLIO_OCCUPIED`;
- `OVERNIGHT_SAFETY_FAILURE`.

Confirmed order and position reconciliation is required before submitting an order that could overlap quantity. Unknown state fails closed.

## 11. Full-cash affordability and dynamic risk

One shared account begins at ₹20,000 realized cash equity. No leverage, borrowing, fractional shares, or assumed intraday multiplier is permitted.

For each scenario/ledger independently:

- `available_cash = current realized or scenario-specific hypothetical net equity`;
- `max_planned_risk = 0.03 × current equity`;
- `entry_bound` is the tick-valid adverse IOC limit;
- `planned_price_risk(q) = q × (entry_bound - protective_limit)`;
- `planned_cost_risk(q)` includes date-effective estimated entry and protective-exit charges;
- `planned_risk(q) = planned_price_risk(q) + planned_cost_risk(q)`;
- cash use is `q × entry_bound + estimated entry charges`.

Enumerate whole-share quantities exactly and select the maximum q satisfying both:

1. `q × entry_bound + estimated entry charges <= available_cash`;
2. `planned_risk(q) <= 0.03 × current equity`;
3. `q <= displayed ask quantity` for quote-driven execution.

Reject if no q of at least one share passes. A favorable fill cannot increase submitted quantity. A partial fill is rechecked only to verify risk, never enlarge it.

Unknown gap/non-fill overrun is excluded from admission arithmetic but reported separately as realized risk overrun where actual evidence exists.

## 12. Tick validity

Obtain tick size causally from the date-effective NSE cash security master and cross-check the broker instrument record.

Rounding:

- buy entry limits upward;
- stop triggers downward;
- protective sell limits downward;
- time/emergency sell limits downward;
- cost rounding only where the applicable rule requires it.

Price-linked ₹0.01/₹0.05 rules must be applied by effective date and security. Missing or contradictory evidence is `TICK_SIZE_UNRESOLVED`; a generic tick assumption is prohibited.

## 13. Corporate actions, legal identity, and membership

Every symbol/date requires:

- NSE EQ-series eligibility;
- legal-security identity and ISIN;
- symbol-to-ISIN continuity;
- date-effective tick;
- date-effective corporate-action record;
- internally consistent tradable price and volume basis;
- NSE daily OHLCV/turnover cross-check.

Symbol equality alone never proves economic continuity.

### 13.1 RELIANCE

The frozen parent treatment is preserved, subject to manifest verification:

- 1:1 bonus, adjustment factor 2, effective/ex-date 28 October 2024;
- through 25 October 2024, retroactively adjusted source prices are multiplied by 2 for tradable-price calculations;
- from 28 October 2024, factor is 1;
- signal calculations stay on the internally consistent adjusted source series;
- conversion occurs before tick, affordability, risk, and diagnostic pricing;
- source volume is not modified merely to manufacture RVOL continuity.

Contradictory source basis is `CORPORATE_ACTION_BASIS_UNRESOLVED`.

### 13.2 TATAMOTORS / TMPV

The stated TATAMOTORS-to-TMPV symbol change effective 24 October 2025 and related corporate restructuring must be verified against NSE primary circulars, security masters, ISINs, entitlement/allotment terms, and archive behavior before admission.

Frozen refusal rules:

- do not concatenate `TATAMOTORS` and `TMPV` solely because a public label changed;
- do not assume identical security identity, price basis, or economic continuity;
- do not back-adjust or forward-fill without a committed, primary-source conversion;
- affected dates remain in denominators as `CORPORATE_ACTION_BASIS_UNRESOLVED` when continuity cannot be proven;
- no replacement security is permitted;
- no post-event outcome may influence the treatment.

### 13.3 Other candidates

For HDFCBANK, ICICIBANK, SBIN, INFY, AXISBANK, KOTAKBANK, HAL, TCS, and DLF, inspect all applicable splits, bonuses, mergers, demergers, renames, suspensions, and other actions. Dividends do not automatically require mechanical intraday OHLC rescaling, but their ex-date status and source adjustment behavior must be recorded. Absence of a known action is not evidence of absence.

## 14. Source and per-symbol data admission

Primary research archive identity:

- repository: https://github.com/voletiramu/nse-fno-1min-data
- release: `v1.0.0`;
- asset: `stocks_1m_csvs.zip`;
- bytes: `485923642`;
- SHA-256: `20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2`;
- publisher-stated source: Zerodha Kite API;
- documented coverage: 2024-04-01 through 2026-04-30;
- format: per-symbol gzip CSV, Unix seconds and one-minute OHLCV;
- evidence class: public research data, not exchange-authoritative.

Separate admission is mandatory for all eleven symbols. SBIN, DLF, and RELIANCE's earlier S0 evidence does not waive this hypothesis's manifest. HAL and TATAMOTORS remain explicitly `UNVERIFIED` until their actual archive members are inspected.

Per-symbol admission requires:

1. exact archive member existence and member hash;
2. expected schema and numeric types;
3. Unix unit, UTC interpretation, IST conversion, interval-start semantics, and availability convention;
4. monotonic timestamps, duplicates, off-grid bars, malformed numerics, invalid OHLCV, and negative volume;
5. exactly five valid constituent minutes per admitted five-minute bucket;
6. exactly fifteen valid opening minutes;
7. missing-minute/session accounting without repair;
8. date-effective NSE EQ-series eligibility, ISIN and symbol mapping;
9. corporate-action and raw/adjusted-basis reconciliation;
10. NSE official daily OHLCV/volume/turnover cross-check;
11. independent minute-source comparison where lawfully available;
12. immutable manifest frozen before signal generation.

Material unexplained disagreement fails closed. No fabricated or interpolated bar is permitted.

## 15. Partitions and access control

Partitions are frozen:

- `QA`: 2024-04-01 through 2024-10-14;
- `DEVELOPMENT`: 2024-10-15 through 2024-10-31;
- `VALIDATION`: 2024-11-01 through 2025-10-31;
- `SEALED_HOLDOUT`: 2025-11-01 through 2026-04-30.

During this preregistration, no signal identity, rank, direction, entry, path, return, or P&L may be calculated for any new symbol.

Before the authorized holdout gate:

- raw holdout bytes may be hashed;
- only aggregate integrity metadata may be exposed;
- holdout signals, counts, directions, ranks, decisions, prices, returns, and P&L remain inaccessible.

At a later explicitly authorized holdout-opening gate:

1. verify hashes and access controls;
2. verify complete-bucket compatibility before P&L;
3. stop on any signal incompatibility;
4. require separate authorization before outcome scoring.

Validation access never automatically opens holdout.

## 16. Independent ledger architecture

No ledger may borrow fills, exits, quantity, costs, cash, or equity from another.

Required ledgers:

1. `ACTUAL_EXECUTABLE`;
2. `CANDLE_DIAGNOSTIC_BASE`;
3. `CANDLE_DIAGNOSTIC_ADVERSE`;
4. `CANDLE_DIAGNOSTIC_SEVERE`;
5. `CANDLE_DIAGNOSTIC_DELAYED_ENTRY`;
6. `CANDLE_DIAGNOSTIC_STOP_NONFILL`.

Each ledger carries its own chronological equity and applies:

`MAX_PLANNED_RISK_L_i = 0.03 × E_L_i`.

### ACTUAL_EXECUTABLE

Only broker-evidenced quotes, order events, fills, costs, positions, and exits may change actual realized equity. Missing actual entry or exit evidence leaves downstream equity unresolved. Candle touches are never actual fills.

### Candle diagnostics

- BASE: 0.05% adverse ordinary entry/time-exit slippage, minimum one tick.
- ADVERSE: 0.10%, minimum two ticks.
- SEVERE: 0.25%, minimum five ticks.
- DELAYED_ENTRY: BASE assumptions with diagnostic entry one additional complete minute later.
- STOP_NONFILL: preserves triggered-but-unfilled SL-L state without assigning a favorable or invented exit.

A historical base diagnostic may reference the first full minute beginning after A1, using only its open as the diagnostic reference before adding frozen adverse slippage. Missing/malformed/zero-volume reference minutes fail closed.

Any unresolved exit stops numeric equity propagation in that ledger. It may not silently assign favorable, neutral, stop-limit, or total-loss equity.

## 17. Costs

`COST_MODEL=DATE_EFFECTIVE_NSE_CASH_INTRADAY_ALL_IN`.

Every diagnostic or actual trade includes, as applicable:

- Upstox brokerage: ₹20 per executed order or 0.1% of order value, whichever is lower, subject to date-effective verification;
- STT on equity-intraday sell value;
- NSE cash transaction charges on both sides;
- SEBI turnover charges;
- NSE IPFT where applicable;
- GST on the applicable taxable components;
- stamp duty on buy value;
- actual RMS/call-and-trade charge if incurred;
- the ledger's frozen slippage treatment.

NSE cash transaction-rate regimes inherited for verification:

- 0.00322% each side through 30 September 2024;
- 0.00297% each side from 1 October 2024 through 28 February 2026;
- 0.00307% each side from 1 March 2026.

Before scoring, archive/hash primary rate evidence, implement exact tax bases and rounding, and reconcile fixed test transactions against broker evidence. If any historical rate or base remains unresolved, `NET_PNL=UNRESOLVED`; gross output cannot be called profitable.

## 18. Sample adequacy and evidence classes

The frozen adequacy threshold is at least 100 trades. It is not reduced because this universe may produce fewer observations.

Report separately:

- gross bidirectional signals;
- gross long signals;
- short signals;
- causally eligible long candidates;
- data/corporate-action rejections;
- cash/risk rejections;
- quote/order rejections;
- candle-diagnostic modeled trades;
- broker-evidenced executable trades;
- unresolved entries/exits.

Only broker-evidenced entries and exits count as broker-verified executions. Historical OHLCV-only diagnostics never do.

The number of symbols does not forecast or guarantee signal or trade count. Fewer than 100 trades in the stated evidence class is `INSUFFICIENT_SAMPLE`.

## 19. Robustness and chronological analysis

No optimization or retraining is permitted.

Validation must be reported in the four fixed blocks:

1. 2024-11-01 through 2025-01-31;
2. 2025-02-01 through 2025-04-30;
3. 2025-05-01 through 2025-07-31;
4. 2025-08-01 through 2025-10-31.

Rules and universe remain identical across blocks. Portfolio equity carries chronologically within each ledger. No block selects parameters.

Required robustness reports, without rule changes:

- BASE;
- ADVERSE;
- SEVERE;
- DELAYED_ENTRY;
- STOP_NONFILL;
- symbol contribution;
- sector/correlation concentration;
- monthly results;
- top-one and top-five winner contribution;
- net result excluding top one and top five winners;
- costs as percentage of gross profit;
- maximum drawdown and losing streak;
- ranking collisions and lower-ranked rejection counts;
- corporate-action and missing-data exclusions.

## 20. Falsification and decision gates

Before any outcome is seen, the hypothesis fails or blocks as follows:

- fewer than 100 trades in the reported evidence class: `INSUFFICIENT_SAMPLE`;
- signal lookahead, partition leakage, holdout leakage, or manifest drift: `INVALID_EXPERIMENT`;
- unexplained source disagreement: `BLOCKED_DATA_INTEGRITY`;
- unresolved timestamp, membership, tick, corporate-action, RMS, or cost basis: `BLOCKED_EVIDENCE`;
- unresolved actual entry/exit evidence: `ACTUAL_EXECUTABLE_PNL=UNRESOLVED`;
- meaningful-sample net PF <= 1.0: `REJECT`;
- net expectancy <= 0: `REJECT`;
- total net P&L <= 0: `REJECT`;
- severe diagnostic net P&L <= 0: `REJECT`;
- net P&L excluding top five winners <= 0: `REJECT`;
- maximum drawdown greater than 10% of starting ₹20,000: `REJECT`;
- material validation/holdout contradiction: `REJECT_OR_UNSTABLE`;
- costs consume most gross edge: `ECONOMICALLY_FRAGILE`;
- any result dependent on outcome-based universe removal or ranking change: `INVALID_EXPERIMENT`;
- holdout net P&L <= 0 or holdout PF <= 1.0 after an authorized opening: `REJECT`.

Historical passage permits only separate Founder consideration of prospective shadow/paper testing. It never permits live trading.

## 21. Prospective shadow/paper kill criteria

If separately authorized later:

- minimum evaluation horizon: 50 causally eligible prospective trades;
- immediate kill on any overnight position;
- immediate kill on any real-money or unauthorized order;
- immediate kill on lookahead, rank bypass, universe substitution, or risk-gate bypass;
- kill at ₹2,000 or 10% peak-to-trough simulated-equity drawdown, whichever occurs first;
- kill after three protection/order-state failures within any rolling twenty eligible trades;
- kill if any planned risk exceeds 3% of pre-trade realized equity;
- after fifty trades, reject if net expectancy <= 0 or net PF <= 1.0 after costs;
- pause for independent review after any data, broker, exchange, tick, RMS, corporate-action, symbol, or regulatory change.

These are falsification and safety gates, not deployment criteria.

## 22. Fail-closed blockers

Block the affected candidate, session, ledger, or experiment as applicable for:

- missing archive member or hash mismatch;
- unverified timestamp semantics;
- incomplete opening range or five-minute bucket;
- fewer than twenty prior valid sessions;
- missing date-effective EQ eligibility, ISIN, tick, corporate action, or price basis;
- HAL or TATAMOTORS archive membership remaining unverified;
- stale/missing quote or insufficient displayed ask;
- no causal diagnostic reference minute;
- entry bound not strictly above protective limit;
- no whole share satisfying full-cash and exact 3% planned-risk gates;
- broker rejection of the frozen SL-L relationship;
- unknown IOC, cancellation, protection, order, or position state;
- unverified RMS cutoff;
- missing cost schedule;
- absent causal exit evidence;
- unresolved TATAMOTORS/TMPV continuity;
- any attempt to substitute a candidate security or alter rank after outcomes.

No ATR stop, percentage stop, GTT, option-premium stop, leverage, short sale, target, alternate indicator, or outcome-selected substitute is allowed under this ID.

## 23. Authorization record

```text
SOURCE_COMMIT=919f17a955dc4c7110f23d21797fe2b66385136b
NEW_BRANCH=research/kats-orb-cash-eq-11stock-long-v1
HYPOTHESIS_ID=KATS-ORB-CASH-EQ-11STOCK-LONG-V1
FIXED_UNIVERSE=HDFCBANK,ICICIBANK,SBIN,RELIANCE,INFY,AXISBANK,KOTAKBANK,HAL,TATAMOTORS,TCS,DLF
SELECTION_PROVENANCE=NSE_MARKET_PULSE_AUGUST_2024_TABLE_99_JULY_TOP_10_STOCK_FUTURES_TURNOVER_PLUS_DLF_PARENT_RETENTION
CROSS_SECTIONAL_RANKING=DECISION_TIMESTAMP_ASC,RVOL_DESC,NORMALIZED_BREAKOUT_DISTANCE_DESC,SYMBOL_ASC
ENTRY_RULE=COMPLETED_SIGNAL_THEN_COMPLETE_M1_THEN_A1_FRESH_QUOTE_PLUS_NONZERO_LATENCY_BUY_LIMIT_IOC
STOP_RULE=OPENING_RANGE_LOW_TRIGGER_WITH_1_PERCENT_ADVERSE_SELL_SL_L_LIMIT_BAND
RISK_GATE=FULL_CASH_MAX_WHOLE_SHARES_WITH_EXACT_3_PERCENT_CURRENT_LEDGER_EQUITY_PLANNED_RISK
CORPORATE_ACTION_POLICY=DATE_EFFECTIVE_NSE_EQ_ISIN_AND_TRADABLE_BASIS;_RELIANCE_BONUS_RULE_PRESERVED;_TATAMOTORS_TMPV_UNRESOLVED_FAIL_CLOSED
COST_MODEL=DATE_EFFECTIVE_NSE_CASH_INTRADAY_ALL_IN
DATA_ADMISSION_REQUIREMENTS=ARCHIVE_MEMBER_AND_HASH,TIMESTAMP_PROVENANCE,COMPLETE_BUCKETS,NSE_EQ_ISIN_MEMBERSHIP,CORPORATE_ACTION_BASIS,NSE_DAILY_CROSSCHECK,MISSING_DATA_ACCOUNTING,HOLDOUT_ISOLATION
SAMPLE_ADEQUACY_RULE=AT_LEAST_100_TRADES_IN_EXPLICITLY_REPORTED_EVIDENCE_CLASS;_OHLCV_DIAGNOSTICS_ARE_NOT_BROKER_VERIFIED
MULTIPLE_TESTING_LINEAGE=ADDITIONAL_UNIVERSE_VARIANT_NUMBER_10_IN_DISCLOSED_LINEAGE
SEALED_HOLDOUT_STATUS=SEALED_NO_SIGNAL_COUNT_DIRECTION_RANK_ENTRY_PATH_RETURN_OR_PNL_ACCESS
FROZEN_V2_CHANGED=NO
NEW_SYMBOL_SIGNALS_GENERATED=NO
PNL_CALCULATED=NO
BROKER_ORDERS=NO
READY_FOR_IMPLEMENTATION=NO_PENDING_INDEPENDENT_REVIEW_AND_FOUNDER_AUTHORIZATION
READY_FOR_BACKTEST=NO_PENDING_IMPLEMENTATION_TESTS_DATA_ADMISSION_MANIFEST_AND_INDEPENDENT_REVIEW
LIVE_TRADING_ALLOWED=NO
FINAL_VERDICT=PREREGISTERED_READY_FOR_INDEPENDENT_REVIEW
NEXT_SINGLE_ACTION=INDEPENDENTLY_REVIEW_THIS_PREREGISTRATION_BEFORE_ANY_IMPLEMENTATION_OR_DATA_SIGNAL_ACCESS
```
