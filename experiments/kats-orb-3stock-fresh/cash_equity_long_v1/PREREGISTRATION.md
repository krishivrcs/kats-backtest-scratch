# KATS-ORB-CASH-EQ-LONG-V1 — preregistration

**Status:** frozen before implementation or outcome inspection  
**Hypothesis ID:** KATS-ORB-CASH-EQ-LONG-V1  
**Preregistration date:** 2026-10-09  
**Parent commit:** 9bf9e08807f4d77defb0d45d69e5890f00b1d569  
**Research branch:** research/kats-orb-cash-eq-long-v1  
**Universe:** SBIN, DLF, RELIANCE, NSE cash equity  
**Starting realized equity:** ₹20,000  
**Authorization boundary:** this document only; no code, P&L backtest, paper order or live order is authorized.

## 1. Hypothesis and lineage

This is a new, long-only, fully cash-funded NSE cash-equity expression of the previously frozen underlying ORB-RVOL signal. It is not an option strategy, not a repair of the rejected GTT proposal, and not identical to the original bidirectional signal portfolio.

Hypothesis:

> After an unusually high-volume opening range, a completed long breakout in SBIN, DLF or RELIANCE may retain positive same-day continuation after a causal entry, an opening-range-low structural stop, whole-share cash sizing, all costs and conservative execution treatment.

The opposing side is a trader or liquidity provider selling into the breakout. No evidence has established that this counterparty loses systematically. This preregistration permits that claim to be tested; it does not assume it.

Multiple-testing lineage, frozen before this hypothesis is scored:

- four prior outcome-bearing option configurations: original 1% control, 3% ceiling variant, fixed ₹1 premium-stop variant, and 3% capital-aware option-contract ladder;
- one separately preregistered causal option execution model later found infeasible because NSE stock options prohibit SL-M;
- one proposed Upstox GTT V2 route rejected at feasibility and never preregistered;
- this document is the first cash-equity long-only outcome hypothesis.

Any change to a rule below creates a new hypothesis ID and cannot be reported as validation of V1.

## 2. Signal rules inherited unchanged

The signal engine remains the frozen KATS-ORB-RVOL-3STOCK-FRESH-V1 underlying engine.

### Universe and clock

- Symbols: SBIN, DLF, RELIANCE.
- Timezone: Asia/Kolkata, admitted only after source timestamp semantics pass section 11.
- Source signal bars: completed five-minute cash-underlying candles.
- Opening range: 09:15:00 through 09:29:59 IST, comprising three completed five-minute bars.
- Signal window: strictly after the completed 09:30 boundary through decision time 12:00 IST.
- No signal condition may use an incomplete candle.

### RVOL

For each symbol and session:

- current opening volume is the sum of the fifteen one-minute bars from 09:15 through 09:29;
- reference volume is the arithmetic mean of the same window in exactly the prior twenty valid sessions;
- the current session is excluded;
- fewer than twenty valid prior sessions means no signal;
- RVOL must be at least 1.50.

A valid opening session has exactly fifteen unique one-minute bars, positive and internally consistent OHLC, and non-negative volume. Missing or suspicious bars are not repaired.

### Direction and ordering

- Original long signal: the first later completed five-minute close strictly above opening-range high.
- Original short signal: the first later completed five-minute close strictly below opening-range low.
- All original signals remain in the audit ledger.
- Simultaneous signals rank by decision timestamp ascending, RVOL descending, normalized breakout distance descending, then symbol alphabetically.
- At most one executed long trade per session across the shared portfolio.
- No re-entry that session.

## 3. Long-only expression and denominator integrity

LONG_ONLY_FILTER=Only original LONG signals may enter the execution gate.

SHORT_SIGNAL_ACCOUNTING=Every original SHORT signal is retained with status INELIGIBLE_DIRECTION_LONG_ONLY.

Mandatory reporting denominators:

1. all frozen bidirectional signals;
2. eligible-direction long signals;
3. ineligible short signals;
4. cash/risk/execution-rejected long signals;
5. executed long trades.

Win rate, profit factor and expectancy use executed long trades only, but reports must display all five counts together. Short signals may never be silently deleted, relabeled or treated as missing data. V1 cannot be compared to the original bidirectional system without this distinction.

## 4. Structural stop

STOP_RULE=Completed 09:15–09:30 opening-range low, converted to the date-effective tradable price basis and rounded conservatively to a valid tick.

For an eligible long signal:

- conceptual_stop is the minimum low of the fifteen completed one-minute opening bars;
- stop_trigger = floor_to_tick(conceptual_stop, date-effective tick);
- the stop is structural and never tightened merely to satisfy the risk ceiling;
- if entry_bound is not strictly above stop_trigger, reject NONPOSITIVE_STOP_DISTANCE;
- there is no fixed profit target and no trailing stop in V1.

The protective exchange order candidate is an Upstox regular NSE_EQ sell SL-L, product I, DAY validity:

- trigger price = stop_trigger;
- limit price = floor_to_tick(stop_trigger × 0.99);
- the 1.00% adverse trigger-to-limit band is frozen ex ante as an execution-protection band, not as the strategy stop;
- limit price must be strictly below trigger by at least one date-effective tick;
- if the exchange/broker rejects this relationship for the admitted security/date, reject the trade rather than alter the stop.

This SL-L order does not cap realized loss. A gap below the limit, absent bids, a circuit, rejection, outage or cancellation can leave it unfilled.

Primary order references:

- Upstox Place Order V3: https://upstox.com/developer/api-documentation/v3/place-order/
- NSE cash trading system: https://www.nseindia.com/static/products-services/equity-market-trading-system
- NSE cash tick circular NSE/CMTR/62174: https://nsearchives.nseindia.com/content/circulars/CMTR62174.pdf

## 5. Tick validity

The tick size is obtained causally from the date-effective NSE cash security master and cross-checked against the Upstox BOD instrument file.

NSE/CMTR/62174 introduced monthly price-linked ticks in 2024: eligible cash securities below ₹250 use ₹0.01; otherwise ₹0.05, with monthly determination from the preceding month-end close. The actual date-effective master remains authoritative.

Rounding rules:

- buy entry limits: upward to the next valid tick;
- structural sell-stop trigger: downward to the next valid tick;
- SL-L sell limit: downward to the next valid tick;
- time-exit sell limit: downward to the next valid tick;
- costs retain full precision and are rounded only when the actual broker/exchange rule requires it.

Missing or contradictory tick evidence causes TICK_SIZE_UNRESOLVED and rejection. A generic ₹0.05 assumption is prohibited.

## 6. Causal entry

ENTRY_RULE=One full minute after the completed signal decision, using a fresh quote and an IOC limit order; no same-bar fill.

Let T be the frozen completed-candle decision timestamp.

Operational sequence:

1. No entry action occurs before T.
2. Earliest entry evaluation is T + 60 seconds.
3. At that time, require a synchronized NSE_EQ quote whose exchange timestamp is no older than one second, with positive best bid, best ask and displayed ask quantity.
4. Determine tentative quantity using sections 9 and 10.
5. Require displayed best-ask quantity at least equal to tentative quantity. This is an admission condition, not a fill guarantee.
6. entry_limit = ceil_to_tick(current best ask).
7. Submit one Upstox NSE_EQ BUY LIMIT order, product I, validity IOC, for the tentative whole-share quantity.
8. The IOC remainder cannot rest. Zero fill means NO_FILL and no trade.
9. Filled quantity and actual average fill are accepted only from an Upstox order event/status response. Positive candle volume or touching the limit is not proof.
10. Recalculate actual planned risk for the filled quantity. Because fill cannot exceed entry_limit, it must not exceed the pre-entry bound. Any inconsistency triggers immediate flattening and an integrity failure.
11. Immediately submit the protective SL-L for the confirmed filled quantity.

If quote, clock synchronization, depth, order status or timestamp evidence is missing or stale, reject EXECUTION_EVIDENCE_UNVERIFIED.

No new entry order may be submitted after 12:01 IST. This one-minute allowance exists solely because the last inherited signal decision may occur at 12:00.

## 7. Entry-to-protection and order-state handling

The engine must persist every transition and be restart-safe.

### Partial entry

- IOC may fill zero, part or all of the quantity.
- Zero fill: no position and no retry.
- Partial fill: accept only the actually filled whole-share quantity; the IOC remainder is cancelled.
- Submit protection for the filled quantity only.
- Do not send another entry order.

### Protection acknowledgement

- Protective submission starts immediately after the first terminal IOC entry response.
- If the SL-L is not acknowledged within two seconds, submit an emergency exit IOC sell limit at the current best bid.
- Repeat emergency IOC attempts once per second using a fresh non-stale best bid until flat or exchange session closure.
- Every fill below the planned protective limit is RISK_OVERRUN.
- A protection rejection is not repaired by changing the structural stop.

### Triggered but unfilled stop

- When SL-L triggers, continue monitoring order and position events.
- If it remains open with positive position quantity for more than two seconds, cancel its unfilled remainder and enter the same emergency IOC exit loop.
- If cancellation state is unknown, reconcile order book and position before submitting another sell, preventing accidental short exposure.
- Never assume that trigger means fill.

### Entry rejection/cancellation

- Rejected or zero-filled entry: no trade.
- A broker/exchange rejection reason is recorded exactly.
- No alternative price, order type or same-day re-entry is allowed.

### Circuits, halts and missing bids

- If no valid bid exists, no fictitious exit is recorded.
- Continue monitoring and attempting only when a fresh valid bid is available.
- A position not flattened by the session deadline is OVERNIGHT_SAFETY_FAILURE and terminates the experiment.
- The realized economic loss may exceed 3%; the 3% rule is an admission ceiling, not a guarantee.

### Cancellation and stale protective orders

After any confirmed exit:

1. cancel every remaining protective order;
2. reconcile position quantity to zero;
3. reconcile pending sell quantity to zero;
4. block further entries that session.

Unknown cancellation state blocks all further orders.

## 8. No target and mandatory time exit

No fixed profit target is used. An open position exits on the first of:

1. completed protective-stop execution; or
2. mandatory time-exit process.

The voluntary time exit begins at 14:50:00 IST:

- cancel the untriggered protective order and confirm cancellation or reconcile its exact state;
- submit an NSE_EQ SELL LIMIT IOC at the fresh best bid for the remaining position;
- repeat once per second with a fresh best bid until flat;
- prohibit simultaneous live protective and time-exit quantities that together exceed the position.

The date-effective Upstox RMS cutoff must be preserved in the data manifest. A session is eligible only when 14:50 is at least ten minutes before the documented cutoff. If not, define the time exit as documented cutoff minus ten minutes before opening that session; if the cutoff is unavailable, reject RMS_CUTOFF_UNRESOLVED.

Current timing evidence is not applied retroactively:

- Upstox 2026 revised timings: https://upstox.com/announcements/revised-timings/
- Upstox RMS policy: https://upstox.com/files/RmsPolicy.pdf

RMS square-off is a failure fallback, never the planned exit, and its charge and fill must be recorded if it occurs.

## 9. Cash affordability

One shared cash account begins at ₹20,000. Equity changes only through realized net P&L. There is no leverage, borrowing, fractional share or assumed intraday multiplier.

Before entry:

- available_cash = current realized cash equity;
- reserve the conservative round-trip charge estimate;
- entry_bound = entry_limit;
- cash_quantity = floor((available_cash - charge_reserve) / entry_bound).

Reject when cash_quantity is below one.

The internal no-leverage rule is not relaxed merely because Upstox blocks less cash for product I. Total planned purchase value plus charge reserve must not exceed available cash.

## 10. Dynamic 3% planned-risk gate

MAX_PLANNED_RISK = 0.03 × current realized equity.

The pre-entry protective exit bound is the frozen SL-L limit price, not the trigger price.

For quantity q:

- price_risk = q × (entry_bound - protective_limit);
- cost_risk = date-effective estimated charges for entry at entry_bound and exit at protective_limit;
- planned_risk = price_risk + cost_risk;
- risk_quantity = floor((MAX_PLANNED_RISK - fixed_cost_component) / per_share_price_and_variable_cost_risk), implemented using exact enumeration to avoid approximation error;
- final_quantity = min(cash_quantity, risk_quantity, displayed best-ask quantity).

Implementation must enumerate whole-share quantities from one upward or from the cash cap downward and select the maximum quantity satisfying both:

- q × entry_bound + estimated entry-side charges ≤ available_cash;
- exact planned_risk(q) ≤ MAX_PLANNED_RISK.

If no q ≥ 1 passes, reject CAPITAL_OR_RISK_CONSTRAINT.

Actual fill below entry_bound cannot be used to increase quantity after the order. Realized loss may exceed planned risk because the SL-L can fail or emergency exits may occur below its limit.

## 11. Data provenance and admission

### Primary signal/research source

Existing audited archive:

- GitHub release: https://github.com/voletiramu/nse-fno-1min-data
- claimed origin: Zerodha Kite API;
- archive SHA256 already observed: 20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2;
- SBIN, DLF and RELIANCE one-minute OHLCV;
- observed range: 2024-04-01 09:15 IST through 2026-04-30 15:29 IST;
- timestamp field: Unix seconds, parsed as UTC and converted to Asia/Kolkata according to the source README.

Before P&L, implementation must independently verify:

- Unix unit and UTC interpretation;
- first bars aligning to 09:15 IST and ordinary sessions to expected NSE minutes;
- duplicates, monotonic order, missing minutes and irregular sessions;
- OHLC validity and non-negative volume;
- raw-versus-adjusted price and volume basis;
- corporate actions;
- exact downloaded bytes and SHA256.

A failed timestamp-semantic check blocks the backtest.

### Independent candle cross-check

Preserved independent source:

https://github.com/rahulkanadia/IndianMarkets_DataBackfill

It claims one-minute Nifty 500 coverage from 2018 through 31 December 2025 and provides SBIN.parquet, DLF.parquet and RELIANCE.parquet. Before use, hash and audit all three files independently. Compare overlapping minute OHLCV after explicit corporate-action normalization.

Material unexplained disagreement blocks scoring. Agreement between two retail/API-derived archives is not exchange-authoritative fill evidence.

### Missing executable history

Neither identified source contains historical bid/ask, displayed depth, queue position, order acknowledgements or fills. Therefore:

- historical results are CANDLE_BASED_RESEARCH only;
- LIVE_EXECUTABILITY remains UNRESOLVED regardless of profit;
- a later prospective shadow/paper feed must capture timestamped quote/depth and simulated order-state evidence;
- candle volume never proves a fill.

## 12. RELIANCE corporate-action conversion

NSE/NCL sources establish a 1:1 RELIANCE bonus, adjustment factor 2, ex/effective date 28 October 2024:

- https://nsearchives.nseindia.com/content/circulars/FAOP64621.pdf
- https://nsearchives.nseindia.com/content/circulars/CMPT64652.pdf

The primary archive is observed to be retroactively adjusted. V1 freezes:

- signal calculations remain on the internally consistent adjusted source series;
- for dates through 25 October 2024, tradable-price-basis OHLC and the opening-range stop are adjusted_source_price × 2;
- from 28 October 2024 onward, factor = 1;
- 26–27 October were non-trading weekend dates;
- price conversion occurs before tick rounding, affordability, risk, fill and P&L;
- share quantity is not retroactively doubled within a same-day trade;
- volume remains on the source basis used by the frozen signal; it is not modified merely to manufacture RVOL continuity.

Any additional corporate action or evidence that the archive basis differs from this rule causes CORPORATE_ACTION_BASIS_UNRESOLVED and blocks affected sessions. The independent source must be normalized separately before comparison.

## 13. Frozen date partitions

No return or exit outcome from these windows may be inspected before implementation, tests and a data manifest are committed.

- WARMUP_AND_DATA_QA: 2024-04-01 through 2024-10-14. Used only for prior-session history, provenance and data-quality checks. No scored P&L.
- DEVELOPMENT_DISCLOSED: 2024-10-15 through 2024-10-31. Previously observed signal window; development only and excluded from validation/holdout claims.
- VALIDATION: 2024-11-01 through 2025-10-31.
- SEALED_HOLDOUT: 2025-11-01 through 2026-04-30.

The validation period is opened first. The holdout remains sealed until:

1. implementation and unit tests are frozen;
2. primary and cross-check manifests are committed;
3. validation output and interpretation are committed without parameter changes;
4. an independent review confirms no leakage or post-outcome modification.

No dates may move between partitions.

## 14. Historical candle proxy

Because historical quotes are absent, the research backtest must clearly separate a candle proxy from executable evidence.

Base causal proxy:

- decision at T;
- entry reference is the open of the one-minute bar timestamped T + 60 seconds, only after timestamp semantics are verified;
- entry fill = reference open plus adverse slippage, rounded upward;
- no entry if that minute is absent, malformed or zero-volume;
- protection is considered active only after entry;
- if entry-minute low reaches the stop trigger, stop handling applies conservatively in that minute;
- time-exit reference is the first valid one-minute open at or after 14:51 IST;
- no same-bar information is used to set an earlier fill.

SL-L candle treatment:

- if a positive-volume bar reaches stop_trigger and its open is at or above protective_limit, research exit is protective_limit;
- if the first triggered bar opens below protective_limit, classify STOP_GAP_BELOW_LIMIT;
- if subsequent bars never trade at or above protective_limit before the time exit, the protective order is not assumed filled;
- such a trade is execution-unresolved; it remains in counts and causes executable NET_PNL=UNRESOLVED;
- a separate marked candle diagnostic may use the first later bar open with adverse slippage, but it may not be called an executable fill.

If no valid time-exit bar exists, classify NO_CAUSAL_EXIT_DATA and do not fabricate a price.

## 15. Frozen slippage sensitivities

These are assumptions, not measured spreads:

- BASE: 0.05% adverse per ordinary entry/time-exit fill, minimum one tick.
- ADVERSE: 0.10% adverse per ordinary entry/time-exit fill, minimum two ticks.
- SEVERE: 0.25% adverse per ordinary entry/time-exit fill, minimum five ticks.
- DELAYED_ENTRY: otherwise BASE, but entry reference moves one additional completed minute later.
- STOP_NONFILL: explicit SL-L non-fill logic from section 14; no favorable substitution.

The protective SL-L research fill is already priced at its adverse limit and receives no fictitious price below that limit. Emergency exits are separate risk-overrun diagnostics.

No sensitivity may be selected as the reported result because it performs best.

## 16. Cost model

COST_MODEL=DATE_EFFECTIVE_NSE_CASH_INTRADAY_ALL_IN.

Every trade includes, using the schedule effective on its date:

- Upstox brokerage: ₹20 per executed order or 0.1% of order value, whichever is lower;
- STT for equity intraday on sell value;
- NSE cash transaction charges on both sides;
- SEBI turnover charges on both sides;
- NSE IPFT where applicable;
- GST on the exact taxable broker/exchange/regulatory components;
- stamp duty on buy value;
- broker auto-square-off/call-and-trade charge if incurred;
- slippage from section 15.

Known NSE cash transaction schedules to encode and independently verify:

- 0.00322% each side through 30 September 2024;
- 0.00297% each side from 1 October 2024 through 28 February 2026;
- 0.00307% each side from 1 March 2026.

Primary references:

- https://upstox.com/brokerage-charges/
- https://nsearchives.nseindia.com/content/circulars/FA64232.pdf
- https://www.nseindia.com/static/invest/first-time-investor-sebi-turnover-fees-stt-other-levies

Before backtest, archive or hash the applicable primary rate evidence for every date regime and reconcile formulas against the Upstox calculator for fixed test transactions. If any historical rate, tax base or rounding convention remains unresolved, report GROSS_PNL only and NET_PNL=UNRESOLVED.

## 17. Reporting requirements

Report at minimum:

- all bidirectional signals;
- eligible long signals;
- ineligible short signals;
- every long rejection reason;
- executable and execution-unresolved trades;
- gross P&L, every cost component and net P&L;
- ending realized equity;
- profit factor, win rate, expectancy, average and median trade;
- maximum drawdown and maximum consecutive losses;
- symbol, month and chronological-block results;
- top-one and top-five winner contribution;
- result excluding top one and top five winners;
- base, adverse, severe, delayed-entry and stop-nonfill results;
- costs as a percentage of gross profit;
- affordability and planned-risk diagnostics;
- all gaps, rejected stops, partial fills and missing exits.

No result is “profitable” when net costs are unresolved.

## 18. Walk-forward and holdout procedure

Rules never retrain or optimize.

Validation is reported in four fixed chronological blocks:

1. 2024-11-01 through 2025-01-31;
2. 2025-02-01 through 2025-04-30;
3. 2025-05-01 through 2025-07-31;
4. 2025-08-01 through 2025-10-31.

Each block runs the identical frozen rules and carries realized portfolio equity chronologically. The blocks are diagnostics, not selection folds. No rule changes between them.

After the sealed-holdout gate in section 13 passes, holdout runs once for 2025-11-01 through 2026-04-30 with the validation-frozen implementation and manifest.

## 19. Evidence and decision gates

Historical classification:

- fewer than 100 executed long trades: INSUFFICIENT_SAMPLE;
- any lookahead, partition leakage or manifest drift: INVALID_EXPERIMENT;
- unresolved timestamp/corporate-action/cost basis: BLOCKED_EVIDENCE;
- executable NET_PNL unresolved because of stop non-fill cases: EXECUTION_UNRESOLVED;
- meaningful-sample net PF ≤ 1.0: REJECT;
- net expectancy ≤ 0: REJECT;
- total net P&L ≤ 0: REJECT;
- holdout net P&L ≤ 0 or holdout PF ≤ 1.0: REJECT;
- severe-stress net P&L ≤ 0: REJECT;
- net P&L excluding top five winners ≤ 0: REJECT;
- maximum drawdown greater than 10% of ₹20,000: REJECT;
- material contradiction between validation and holdout: REJECT_OR_UNSTABLE;
- costs consuming most gross edge: ECONOMICALLY_FRAGILE.

Passing historical gates permits only prospective paper/shadow consideration after Founder approval. It does not permit live trading.

## 20. Prospective paper/shadow kill criteria

If a later Founder authorization permits prospective paper/shadow operation:

- minimum evaluation horizon: 50 causally eligible trades;
- immediate kill on any overnight position;
- immediate kill on any unauthorized order or real-money order;
- immediate kill on lookahead or risk-gate bypass;
- kill at ₹2,000 or 10% peak-to-trough simulated-equity drawdown, whichever is reached first;
- kill after three protection/order-state failures in any rolling twenty eligible trades;
- kill if any single planned risk exceeds 3% of pre-trade realized equity;
- after fifty trades, reject if net expectancy ≤ 0 or net PF ≤ 1.0 after all costs;
- pause and independently review after any data, broker, exchange, tick, RMS or regulatory rule change.

These are safety and falsification gates, not deployment criteria.

## 21. Fail-closed blockers

A trade or experiment is blocked when any required primitive is unavailable or contradictory, including:

- unverified minute timestamp semantics;
- missing date-effective tick;
- missing or stale quote/depth;
- no causal next-minute candle for historical proxy;
- unknown corporate-action basis;
- entry at or below structural stop;
- no whole share satisfying cash and planned-risk gates;
- broker/API rejection of the frozen SL-L relationship;
- inability to reconcile partial fill, order or position state;
- unverified RMS cutoff;
- missing cost schedule;
- absent causal exit data;
- manifest/checksum drift;
- any attempt to replace the opening-range-low stop after observing results.

No indicator stop, percentage stop, ATR stop, GTT, option-premium stop or outcome-selected substitute is allowed under this ID.

## 22. Authorization status

HYPOTHESIS_ID=KATS-ORB-CASH-EQ-LONG-V1  
PARENT_COMMIT=9bf9e08807f4d77defb0d45d69e5890f00b1d569  
NEW_BRANCH=research/kats-orb-cash-eq-long-v1  
STOP_RULE=OPENING_RANGE_LOW_TRIGGER_WITH_1_PERCENT_ADVERSE_SL_L_LIMIT_BAND  
ENTRY_RULE=T_PLUS_60_SECONDS_FRESH_QUOTE_IOC_LIMIT; HISTORICAL_PROXY_NEXT_MINUTE_OPEN  
LONG_ONLY_FILTER=ORIGINAL_LONG_SIGNALS_ONLY  
SHORT_SIGNAL_ACCOUNTING=RETAIN_AS_INELIGIBLE_DIRECTION_LONG_ONLY  
COST_MODEL=DATE_EFFECTIVE_NSE_CASH_INTRADAY_ALL_IN  
DATA_PARTITIONS=QA_2024-04-01_TO_2024-10-14; DEVELOPMENT_2024-10-15_TO_2024-10-31; VALIDATION_2024-11-01_TO_2025-10-31; SEALED_HOLDOUT_2025-11-01_TO_2026-04-30  
RISK_GATE=MIN_CASH_AFFORDABILITY_AND_EXACT_3_PERCENT_CURRENT_REALIZED_EQUITY  
EXECUTION_BLOCKERS=HISTORICAL_QUOTE_DEPTH_ABSENT; SL_L_NONFILL_AND_GAP_RISK; COST_AND_RMS_DATE_EVIDENCE_REQUIRED; LIVE_FILL_BEHAVIOR_UNVERIFIED  
READY_FOR_IMPLEMENTATION=NO_PENDING_INDEPENDENT_REVIEW_AND_FOUNDER_AUTHORIZATION  
READY_FOR_BACKTEST=NO_PENDING_IMPLEMENTATION_TESTS_DATA_MANIFEST_COST_AUDIT_AND_INDEPENDENT_REVIEW  
LIVE_TRADING_ALLOWED=NO

FINAL_VERDICT=PREREGISTERED_READY_FOR_INDEPENDENT_REVIEW
