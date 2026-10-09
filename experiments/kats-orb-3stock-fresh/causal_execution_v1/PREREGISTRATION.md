# KATS-ORB-CAUSAL-EXEC-V1 — preregistration

**Status:** frozen specification; no profitability run authorized  
**Hypothesis ID:** `KATS-ORB-CAUSAL-EXEC-V1`  
**Preregistered from:** `f1b24038dfc2ff68eab34dcbc38a1beaaae215bf`  
**Parent capital-aware experiment:** `KATS-ORB-3STOCK-CAPITAL-AWARE-CONTRACTS`  
**Parent frozen commit:** `5e90960ebe858a5b2ccdaf93188f63af62363ad3`  
**Original base:** `8fcbae2ca0386661237e98201b10b048fde72095`  
**Purpose:** replace the invalid same-option-minute-open execution model with a separate causal, fail-closed execution hypothesis. This document does not repair, rescore, or validate the parent ledger.

## 1. Established parent finding

The four parent development entries are not valid executable-profit evidence. Contract eligibility used completed OHLC, volume and OI from the same option minute whose opening price was assigned as the fill. The source's `:59` timestamp convention is undocumented. Historical bid/ask and depth were absent. The parent results remain development artifacts and must never be relabeled as results of this hypothesis.

No result from those four trades was used to set any rule below.

## 2. Frozen invariants

The following remain unchanged:

- starting cash: INR 20,000;
- one shared cash account;
- no leverage or borrowing;
- whole historical option lots only;
- intraday positions only and one executed trade per session;
- frozen ORB-RVOL underlying signal, direction and signal decision time;
- CE for a long underlying signal and PE for a short underlying signal;
- nearest eligible expiry at least five calendar days from the signal day;
- ATM, then directional OTM1, OTM2 and successively farther OTM;
- first fully eligible contract only; stop examining farther strikes after selection;
- RELIANCE dated cash/strike basis and historical bonus/lot treatment from the parent;
- conceptual stop at 80% of the actual entry fill;
- conceptual target at 140% of the actual entry fill;
- maximum planned loss of 3% of current equity;
- frozen baseline slippage function `max(0.5% of reference price, INR 0.05)`;
- frozen charge model: INR 40 round-trip brokerage, STT at 0.1% of sell premium turnover, exchange charge at 0.03503% of buy plus sell premium turnover, SEBI charge at 0.0001% of buy plus sell premium turnover, GST at 18% of brokerage plus exchange plus SEBI charges, and stamp duty at 0.003% of buy premium turnover;
- no future-P&L-based contract selection;
- stop/target collision without finer causal evidence is stop-first;
- forced session exit remains 15:15 IST.

The charge rates above are preserved experiment inputs. Their applicability to a future test period must be date-verified before that period is admitted.

## 3. Causal clock and data definitions

- `T`: event time at which the frozen underlying 5-minute signal candle is complete.
- `R_T`: local monotonic receipt time of the signal event.
- `L`: nonzero operational latency floor, frozen at 1.000 second.
- `E = R_T + L`: earliest eligibility-evaluation time.
- `Q`: an option quote/order-book snapshot first received at or after `E`.
- `S`: recorded order-submission time, which must be at or after receipt of all information used for selection.
- `A`: exchange or broker acknowledgement time.
- `F`: fill time. It must satisfy `F >= A >= S >= Q_receipt >= E`.

Exchange timestamps and local receipt timestamps must both be retained. If clock synchronization, timezone, timestamp meaning, or ordering cannot be demonstrated, the event is rejected. Timestamps may not be repaired by assuming that `:59` means minute start or minute end.

A completed option minute may be used only when the data provider documents:

1. whether its timestamp labels the interval start or end;
2. the timezone;
3. when the complete OHLCV record becomes available;
4. whether OI is contemporaneous, delayed, revised or end-of-day;
5. the volume unit.

The most recent completed option candle used for diagnostics or a positive-volume condition must have an availability time no later than `E). The option candle containing `S` or `F` is never used to qualify its own open or any earlier fill.

## 4. Deterministic causal sequence

1. At `T`, accept only the frozen completed-candle underlying signal.
2. Load the date-effective official contract master that was available before the session. Construct the eligible expiry and strike ladder using only the frozen underlying reference at `T`.
3. Wait until `E`. A zero-latency or same-event fill is prohibited.
4. For each ladder candidate in order, obtain a post-`E` timestamped executable quote/order-book snapshot. Candidate evaluation is sequential and cannot inspect later price paths.
5. Require the data, liquidity, cash, stop-executability and planned-risk gates in this document.
6. Select the first candidate passing every gate. Stop examining farther strikes.
7. Form a tick-valid marketable limit buy from the admitted ask/depth snapshot and frozen slippage buffer.
8. Record `S` and `A`. No fill may precede acknowledgement.
9. Historical scoring requires a causally subsequent executable quote/trade with sufficient quantity at or within the submitted limit. Prospective paper trading uses the broker/exchange simulator's actual acknowledgement and fill receipt.
10. If the order is not completely filled for one whole lot within the admitted event sequence, cancel/reject it. Partial lots are not positions and must be flattened according to a separately documented operational-error procedure; they are not a scored strategy trade.
11. Manage the filled position using the tick-valid stop, target, gap and forced-exit rules below.

A completed candle's positive volume never proves that the submitted order was executable.

## 5. Entry-price rule

For candidate best ask `ask_Q` and date-effective tick `tick`:

- `entry_buffer = max(0.005 * ask_Q, INR 0.05)`;
- `entry_limit = ceil_to_tick(ask_Q + entry_buffer, tick)`.

The buy price used in planned-risk and cash tests is `entry_limit`, not candle open, close, midpoint or last traded price. A historical fill is admitted only if the post-acknowledgement order-book/quote sequence demonstrates sufficient sell quantity for one whole lot at prices no worse than `entry_limit`. The conservative scored entry is the worse of the demonstrated volume-weighted executable price and `entry_limit`; if this relationship cannot be established, reject rather than fabricate a fill.

## 6. Tick provenance and rounding

Official evidence:

- NSE circular [NSE/FAOP/70382, 23 September 2025](https://nsearchives.nseindia.com/content/circulars/FAOP70382.pdf) states that the then-current stock-option tick was INR 0.05 and introduces INR 0.01 only for stock options with underlying price below INR 250 from trade date 3 November 2025. Therefore INR 0.05 applies to the 2024 stock-option period in scope.
- NSE's [Individual Securities F&O specification](https://www.nseindia.com/static/products-services/equity-derivatives-individual-securities) identifies OPTSTK fields and directs users to the date-effective `NSE_FO_contract_ddmmyyyy.csv.gz` file for applicable contract and lot information.
- NSE circulars from 2024, including [NSE/FAOP/64277](https://nsearchives.nseindia.com/content/circulars/FAOP64277.pdf), document distribution of the daily NSE F&O contract file. An exact official October 2024 contract-master archive for every tested day has not been preserved in this repository: **UNRESOLVED**.

Every order, trigger, limit and modeled execution price must be an integer number of the date-effective ticks.

Rounding is adverse and deterministic:

- buy entry limit: round upward;
- conceptual stop `0.80 * actual_entry_fill`: round downward to obtain the protective trigger; never round upward because that would tighten the frozen stop;
- conceptual target `1.40 * actual_entry_fill`: round upward; never round downward because that would reduce the frozen target;
- estimated adverse stop fill: subtract the frozen sell-slippage buffer from the tick-valid stop trigger and round downward;
- modeled sell/exit price: round downward;
- cash and rupee risk: retain full precision; round only final report presentation, never eligibility arithmetic.

These operations preserve the conceptual 20% stop and +40% target while making orders mechanically expressible. They are rules of this new execution hypothesis, not corrections to the parent ledger.

## 7. Stop, target and gaps

Preferred protective order is a broker/exchange-supported stop-market order. If that order type is unavailable for the contract or its exact historical semantics are not documented, the candidate is ineligible. A stop-limit order is not substituted.

After an actual entry fill `P`:

- conceptual stop: `0.80 * P`;
- stop trigger: `floor_to_tick(0.80 * P)`;
- target limit: `ceil_to_tick(1.40 * P)`.

The trigger price is not a promised fill price. On a gap through the trigger, the exit uses the first causally available executable bid/depth after triggering, including all adverse movement and frozen sell slippage. Actual realized loss may exceed 3% because of gaps, disappearing depth, rejected orders, latency or market disruption.

For historical scoring, a stop or target requires quote/trade sequencing after entry acknowledgement. Minute OHLC alone cannot establish a fill. If stop and target order cannot be established from finer causal evidence, apply stop-first only after confirming both were reachable after entry; otherwise mark the trade unscorable.

Forced exit at 15:15 uses the first causally available executable bid/depth at or after the forced-exit event, with the frozen sell-slippage buffer and tick rounding. A candle open is not automatically an executable exit.

## 8. Liquidity gate

Every candidate must satisfy all of the following causally:

1. An exact contract identifier from the date-effective official contract master.
2. A documented whole-lot quantity and volume/depth unit.
3. The last completed option minute available by `E` exists, is structurally valid and has strictly positive volume in a documented unit.
4. A post-`E` quote snapshot supplies best bid, best ask, displayed quantities, exchange timestamp and local receipt timestamp.
5. Bid and ask are positive, tick-valid and not crossed.
6. Displayed ask-side quantity at executable prices up to `entry_limit` is at least one whole lot.
7. The quote used for selection is still the latest received state when the order is submitted; any intervening quote update requires re-evaluation before submission.
8. The actual or historically reconstructed fill occurs after acknowledgement and is supported by sufficient executable quantity.
9. OI is used only if its publication timing and unit are documented. If admitted, it must be positive and timestamped no later than `E`. Otherwise record `OI=UNKNOWN`; OI never substitutes for bid/ask depth.
10. Positive candle volume by itself never passes the gate.

No arbitrary spread estimate is invented. The observed spread is recorded. Its economic effect enters through the actual ask-side entry, bid-side stop/exit, frozen slippage buffer, costs and 3% risk gate.

If quotes, depth, units, acknowledgement ordering or execution quantity are missing, set `BROKER_EXECUTABILITY_UNRESOLVED` and reject the trade from executable scoring.

## 9. Missing, stale and unsynchronized data

Fail closed for any of the following:

- undocumented candle timestamp semantics or timezone;
- missing exchange or local receipt timestamps;
- event ordering inconsistent with `F >= A >= S >= Q_receipt >= E`;
- unavailable or stale contract master;
- missing contract, expiry, strike, option type, lot size or tick;
- missing, malformed or unsynchronized underlying/option data;
- missing previous completed option minute;
- zero or undocumented-unit completed-minute volume;
- missing or crossed bid/ask;
- insufficient displayed depth for one lot;
- missing order acknowledgement or fill evidence;
- unverified stop-order semantics;
- missing same-day exit evidence;
- unresolved corporate-action price basis;
- calculated required cash or planned loss above the permitted limit.

There is no forward search for a favorable bar, quote or contract after a failed candidate except the frozen sequential progression to the next strike using newly timestamped information. Each candidate's evaluation record must state exactly which data were known at that time.

## 10. Cash and planned-risk accounting

Before order submission, use current realized account equity and free cash. Unrealized profits and future sale proceeds are unavailable.

For one whole lot of quantity `q`:

- `premium_outlay = entry_limit * q`;
- `estimated_stop_fill = floor_to_tick(stop_trigger - max(0.005 * stop_trigger, INR 0.05))`, bounded below by zero;
- calculate the frozen round-trip charges using `entry_limit` and `estimated_stop_fill`;
- `planned_loss = (entry_limit - estimated_stop_fill) * q + estimated_round_trip_charges`;
- `risk_ceiling = 0.03 * current_equity`;
- `required_cash = premium_outlay + estimated_round_trip_charges`.

The contract passes only when:

- `required_cash <= free_cash`;
- `planned_loss <= risk_ceiling`;
- one whole lot is supported by quote depth;
- no other position or pending entry order exists;
- all execution gates pass.

No quantity is reduced below one lot, no funds are borrowed, and the stop is never tightened to manufacture eligibility. Cash is debited on the actual fill and charges; proceeds are credited only on actual exit. Entry orders reserve their full worst-case premium and estimated charges until filled, cancelled or expired.

Planned risk is an admission ceiling, not a guarantee of realized loss. Gap and execution-failure overruns are reported separately and never clipped to 3%.

## 11. Historical-data admission requirements

A profitability backtest is prohibited until one immutable manifest establishes:

- actual NSE stock-option contracts for SBIN, DLF and RELIANCE;
- date-effective official contract masters, ticks, lots, expiries and corporate actions;
- documented option candle interval, timezone and availability semantics;
- timestamped bid, ask and displayed depth sufficient to reconstruct one-lot execution;
- documented volume and OI units and publication timing;
- order acknowledgement/fill ordering or an authoritative historical event sequence;
- transaction-cost rates applicable on every historical date;
- input SHA-256 checksums, licensing basis, date coverage and missing-data report;
- exclusion of the 15–31 October 2024 development sessions from untouched scoring.

The currently preserved development dataset lacks documented option timestamp semantics and historical bid/ask/depth. It is therefore **NOT ADMITTED** for executable-profit testing under this hypothesis.

## 12. Multiple-testing lineage

Known lineage before this specification:

1. fresh ORB-RVOL control;
2. 3% risk-ceiling variant;
3. fixed one-point-stop variant;
4. capital-aware ATM-to-OTM contract ladder;
5. this causal execution hypothesis.

The broader number of KATS variants examined outside this repository lineage is **UNKNOWN**. Any future statistical interpretation must disclose at least the five known variants and must not treat this hypothesis as the first attempt.

## 13. Explicit failure criteria

The hypothesis fails or remains unscorable if:

- any entry uses information completed after its assumed fill;
- timestamp semantics are assumed rather than proven;
- a price is not valid for the date-effective tick;
- planned loss exceeds 3% of current equity;
- one whole lot cannot be fully cash-funded;
- a fill is inferred only from OHLCV;
- quote/depth/order evidence is missing;
- any position remains open overnight;
- an implementation changes the frozen signal, ladder, expiry, stop percentage, target or risk ceiling;
- an untouched test with a meaningful sample has net profit factor at or below 1.0 after all costs;
- implementation and ledger reconciliation are not exact.

No failed requirement may be replaced by a near-equivalent primitive under this hypothesis.

## 14. Proposed prospective paper-trading gates — Founder approval required

These are preregistered proposals, not authorization to trade:

- no live trading;
- paper execution only after independent code review and causal replay tests;
- immediate operational kill on lookahead, timestamp inversion, leverage, overnight exposure, missing protective stop, cash/risk breach or contract-master mismatch;
- financial paper kill at 10% peak-to-trough equity drawdown;
- terminate the hypothesis after at least 100 causally executable paper trades if net expectancy is not positive or net profit factor is at or below 1.0 after all costs;
- do not promote before at least 100 paper trades and adequate regime/month coverage;
- any rule change creates a new hypothesis ID and restarts evidence collection.

Founder approval is required before these paper gates are activated and again before any later live proposal.

## 15. Conditions before implementation and testing

A fail-closed engine and data recorder may be implemented from this document. A historical profitability backtest may not begin until:

1. timestamp semantics and quote availability are proven;
2. historical L1/depth and exact volume units are available;
3. date-effective contract masters and cost schedules are frozen;
4. a manifest and untouched date partition are committed before outcome generation;
5. automated causality, tick, depth, cash, gap and order-sequence tests pass;
6. an independent reviewer confirms no same-bar or future-data dependency.

**Implementation readiness:** YES, for a fail-closed engine and evidence recorder.  
**Historical backtest readiness:** NO — blocked by timestamp, quote/depth and exact contract-master provenance.  
**Live trading:** NOT ALLOWED.
