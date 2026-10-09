# KATS — ORB capital-appropriate expression gate

**Audit date:** 2026-10-09  
**Mode:** feasibility audit only; no strategy implementation, backtest, P&L, paid data, or broker orders  
**Repository:** https://github.com/krishivrcs/kats-backtest-scratch  
**Research branch:** research/kats-orb-causal-exec-v1  
**Preserved parent:** 28d94821d8d69c51d7a1ea586190f52bb6aeb10c  
**Parent finding:** KATS-ORB-CAUSAL-EXEC-V1 is frozen but infeasible for NSE stock options.

## 1. Decision

GTT_V2_STATUS=REJECTED_FEASIBILITY  
GTT_V2_PREREGISTERED=NO

The proposed KATS-ORB-UPSTOX-GTT-LIMIT-EXEC-V2 was investigated but was never authorized or preregistered. It must not be implemented.

The same frozen underlying ORB-RVOL signal is not structurally blocked from a separate, fully cash-funded NSE cash-equity investigation. Whole-share affordability and regular NSE_EQ order support are materially better than the stock-option expression. However, the option-premium stop and target do not transfer to shares. A cash-equity exit and protection rule must be a new Founder-authorized, outcome-independent hypothesis before any P&L is calculated.

FINAL_VERDICT=CASH_ORB_WORTH_NEW_HYPOTHESIS

This verdict means “worth preregistering and testing,” not “profitable,” “validated,” or “ready to trade.”

## 2. Closed GTT V2 investigation

The GTT V2 route is rejected for the following cumulative reasons:

1. A fresh Upstox GTT calculates stop/target percentages from the primary trigger condition, not the eventual entry average fill. After the primary leg executes, percentage modifications are based on LTP rather than the original actual fill.
2. Upstox states that a triggered GTT always places a limit order. Its GTT policy refers to internal market-price protection but does not publish the exact percentage, calculation base, tick rounding, or deterministic generated limit price.
3. The public API market_protection parameter applies to MARKET and SL-M orders and is ignored for LIMIT and SL orders. It does not resolve the undocumented internal GTT limit-price rule.
4. For intraday GTT, target and stop legs are not placed until the primary leg fills completely. A partial fill can therefore create an unprotected position.
5. A triggered exit limit can remain unfilled after a gap or rapid move.
6. Upstox documentation conflicts on whether F&O GTT accepts intraday product I: the formal GTT policy permits intraday F&O while a segment help article says F&O GTT is normally NRML and not intraday.
7. Current sandbox documentation lists ordinary Place/Modify order APIs, not the full GTT lifecycle.
8. The historical option dataset has candle OHLCV but no contemporaneous bid/ask, depth, order-event, or fill evidence.

Primary broker sources:

- GTT API: https://upstox.com/developer/api-documentation/place-gtt-order/
- GTT percentage basis: https://upstox.com/help-center/how-are-good-till-triggered-gtt-stop-loss-or-target-percentages-calculated-261061/
- Partial-fill behavior: https://upstox.com/help-center/how-are-stop-loss-and-target-orders-placed-in-case-of-a-partial-execution-of-the-primary-leg-of-a-gtt-order-253650/
- GTT policy: https://upstox.com/files/terms-and-condition/conditional-orders.pdf
- Conflicting segment guidance: https://upstox.com/help-center/in-which-segments-can-a-good-till-triggered-gtt-order-be-placed-253081/
- Sandbox list: https://upstox.com/developer/api-documentation/sandbox/

No GTT V2 code, preregistration, simulated trade, or P&L is authorized by this audit.

## 3. Frozen signal inheritance boundary

A future cash-equity hypothesis may inherit only:

- SBIN, DLF and RELIANCE universe;
- the frozen underlying ORB definition;
- frozen RVOL definition and threshold;
- completed-candle decision time;
- frozen signal direction and chronological ranking;
- ₹20,000 starting equity;
- maximum 3% planned-risk ceiling based on current equity;
- one shared account;
- no leverage under the research capital ledger;
- intraday-only exposure and mandatory same-day exit;
- no future data and no outcome-based selection.

It may not inherit:

- option contract selection, expiry, strike, lot size, CE/PE mapping, premium liquidity filters or option quote assumptions;
- the 20% option-premium stop;
- the +40% option-premium target;
- option brokerage/statutory rates;
- GTT behavior;
- prior option P&L or the four development trades.

EXIT_RULE_STATUS=NEW_HYPOTHESIS_REQUIRED  
NET_PROFITABILITY=UNKNOWN

## 4. Cash-equity affordability

CASH_EQUITY_AFFORDABILITY=YES_FOR_AT_LEAST_ONE_SHARE_ON_OBSERVED_DEVELOPMENT_SIGNALS; DATE_SPECIFIC_RECALCULATION_REQUIRED

Existing frozen artifact evidence from Actions run 37889737398 records five underlying signal closes:

| Symbol | Date | Frozen signal close |
|---|---:|---:|
| RELIANCE | 2024-10-15 | ₹1,356.00 |
| DLF | 2024-10-23 | ₹805.20 |
| SBIN | 2024-10-28 | ₹798.40 |
| DLF | 2024-10-28 | ₹811.90 |
| SBIN | 2024-10-30 | ₹825.95 |

Each is far below ₹20,000, so at least one whole share was arithmetically affordable before charges. This does not freeze a cash entry price or quantity.

The new hypothesis must reserve estimated charges and adverse entry slippage before sizing:

cash_quantity = floor((available_cash - conservative_cost_reserve) / executable_entry_price)

A trade is rejected when cash_quantity is below one. Notional exposure must remain at or below available cash even if the broker makes intraday margin available.

Short signals require a same-day cash-market short sale and buyback. The research ledger can impose notional less than or equal to cash, but the broker product remains an intraday margin product operationally. Failure to buy back because of an upper circuit, suspension, order rejection, outage, or absent liquidity can create auction/close-out exposure. That tail risk must be explicit in a new hypothesis.

## 5. Cash data availability

CASH_DATA_AVAILABILITY=AVAILABLE_FOR_CANDLE_BASED_RESEARCH; EXECUTABLE_QUOTE_HISTORY_UNAVAILABLE

### Existing source already audited

Actions artifact 11598595665 from run 37889737398 records:

- source: GitHub release voletiramu/nse-fno-1min-data v1.0.0;
- claimed origin: Zerodha Kite API;
- archive SHA256: 20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2;
- range for all three symbols: 2024-04-01 09:15 IST through 2026-04-30 15:29 IST;
- DLF: 192,592 rows;
- RELIANCE: 192,592 rows;
- SBIN: 192,595 rows;
- zero duplicate timestamps, bad timestamps, or malformed OHLCV rows reported by the frozen probe;
- one-minute OHLCV and Unix timestamps converted to Asia/Kolkata;
- no bid, ask, depth, exchange sequence, or order events.

Source: https://github.com/voletiramu/nse-fno-1min-data  
Artifact: https://github.com/krishivrcs/kats-backtest-scratch/actions/runs/37889737398/artifacts/11598595665

This source contains many dates outside the 2024-10-15 through 2024-10-31 development window. Those dates can be frozen as chronologically untouched, but they are not source-independent because they come from the same archive.

### Independent cross-check source

A second public repository claims one-minute Nifty 500 stock data from 2018 through 31 December 2025 and contains SBIN.parquet, DLF.parquet and RELIANCE.parquet:

https://github.com/rahulkanadia/IndianMarkets_DataBackfill

This provides a plausible independent candle-source cross-check. Before admission, its three files must be hashed and audited for schema, timestamp meaning, duplicates, session completeness, corporate actions and raw-versus-adjusted price basis. Its README is not exchange certification.

No reviewed free source provides historical cash-market bid/ask, full depth and order-event history for the complete proposed validation period. Therefore a candle backtest can be discovery evidence only; executable spread/fill credibility must come from a prospective paper/shadow feed.

RELIANCE requires special handling: the existing signal source is retroactively bonus-adjusted. Direct cash P&L, affordability and stop levels require actual date-effective tradable prices or a frozen causal de-adjustment procedure. The prior option contract-selection factor is not automatically a cash-execution rule.

## 6. NSE_EQ order compatibility

CASH_ORDER_TYPE_COMPATIBILITY=DOCUMENTED_FOR_REGULAR_NSE_EQ_INTRADAY_ORDERS; LIVE_ACCOUNT_BEHAVIOR_UNVERIFIED

Upstox V3 documents:

- product I for intraday;
- quantity in equity units;
- DAY and IOC validity;
- MARKET, LIMIT, SL and SL-M order types;
- order modification and cancellation;
- an explicit NSE_EQ intraday LIMIT example;
- an explicit NSE_EQ intraday SL-M example;
- order status/history fields including average_price, filled_quantity and pending_quantity;
- portfolio WebSocket/webhook order updates;
- sandbox support for Place Order V3 and Modify Order V3.

Sources:

- Place Order V3: https://upstox.com/developer/api-documentation/v3/place-order/
- NSE_EQ examples: https://upstox.com/developer/api-documentation/example-code/orders/place-order/
- Order stream: https://upstox.com/developer/api-documentation/get-portfolio-stream-feed/
- Order status: https://upstox.com/developer/api-documentation/get-order-details/
- Sandbox: https://upstox.com/developer/api-documentation/sandbox/

NSE describes the cash market as an order-driven market supporting regular, market and stop-loss orders. A stop may become an active limit or market order when triggered. This supports structural compatibility but does not guarantee a fill:

- https://www.nseindia.com/static/products-services/equity-market-trading-system
- https://www.nseindia.com/static/trade/pan-based-self-trade-prevention-check-mechanisms-faqs

The explicit NSE_EQ examples are documentation evidence, not evidence that a specific account, symbol and date will accept or fill an order. No live order was submitted.

## 7. Causal execution feasibility

CASH_CAUSAL_EXECUTION_FEASIBILITY=STRUCTURALLY_FEASIBLE_AFTER_NEW_EXIT_PREREGISTRATION; HISTORICAL_EXECUTABILITY_UNPROVEN

A causal engine can be specified in this order:

1. Wait for the frozen underlying breakout candle to complete.
2. At or after the frozen decision timestamp, read a timestamped NSE_EQ quote/depth snapshot.
3. Apply a preregistered nonzero decision and network latency.
4. Submit the preregistered entry order.
5. Treat no position as filled until an order event reports filled quantity and average price.
6. Handle every partial fill deterministically; never protect or size an unfilled quantity.
7. Submit the newly preregistered protective exit for the confirmed filled quantity.
8. Require broker acknowledgement and monitor order, position and market streams.
9. Handle trigger, partial exit, rejection, cancellation, non-fill, disconnection, RMS action and emergency square-off deterministically.
10. Force an acknowledged same-day exit before the broker's applicable date-effective RMS window.

Regular-order sandbox testing can validate request/response state handling without funds. It cannot prove live queue position, spread, depth, slippage, outage behavior or actual fills.

One-minute OHLCV alone cannot prove the ordering of signal completion, quote observation, submission, exchange acknowledgement and fill within the same minute. A historical hypothesis must therefore use a conservative later-bar fill rule or obtain timestamped historical quotes; the choice must be frozen before P&L.

## 8. Risk sizing feasibility

RISK_SIZING_FEASIBILITY=CONDITIONALLY_FEASIBLE_ONLY_AFTER_EXIT_RULE_AND_EXECUTION_BOUND_ARE_FROZEN

The maximum planned risk is 3% of current equity; initially ₹600.

For a long position, a future admission formula may take the general form:

planned_risk_per_share = entry_bound - protective_exit_bound  
quantity_risk = floor((0.03 × current_equity - conservative_cost_reserve) / planned_risk_per_share)  
quantity = min(quantity_cash, quantity_risk)

A short position requires the mirrored adverse buyback bound plus explicit upper-circuit/auction treatment.

These formulas are feasibility structure, not a stop rule. They cannot be evaluated until the Founder authorizes a new cash-equity hypothesis defining:

- stop signal;
- stop trigger and submitted order type;
- limit/market protection, tick rounding and gap handling;
- entry and exit latency;
- partial fills;
- stop non-fill;
- forced exit;
- worst-case admission bound;
- short-sale failure and auction treatment.

Planned risk is not guaranteed realized loss. Gaps, stop non-fill, upper circuits, broker/exchange rejection and outages can exceed 3%. If a bounded executable risk estimate cannot be formed, the trade must fail closed.

## 9. Costs and execution evidence required

A future historical run must select the rule set effective on each trade date and preserve primary-source copies or hashes. At minimum:

1. Upstox equity-intraday brokerage: ₹20 per executed order or 0.1%, whichever is lower.
2. Cash-intraday STT: sell-side rate effective on the trade date.
3. NSE cash transaction charge:
   - applicable pre-1 October 2024 schedule;
   - ₹2.97 per lakh each side from 1 October 2024 under NSE/FA/64232;
   - applicable revision from 1 March 2026.
4. SEBI turnover charge effective on the date.
5. GST base and rate.
6. Buy-side stamp duty.
7. NSE IPFT treatment effective on the date.
8. Any broker auto-square-off/call-and-trade fee.
9. No DP charge for a correctly closed intraday trade; a failed intraday close must not assume this treatment.
10. Historical bid/ask spread, available quantity, latency and slippage evidence. If unavailable, use preregistered conservative sensitivities and label executable net profitability unresolved.

Primary references:

- Upstox charges and dated schedules: https://upstox.com/brokerage-charges/
- NSE/FA/64232: https://nsearchives.nseindia.com/content/circulars/FA64232.pdf
- NSE levy overview: https://www.nseindia.com/static/invest/first-time-investor-sebi-turnover-fees-stt-other-levies
- Upstox RMS policy: https://upstox.com/files/RmsPolicy.pdf

## 10. Assumptions that require a new hypothesis

The following cannot be inherited or chosen after observing outcomes:

- cash stop definition and distance;
- cash target or trailing rule;
- entry order type and price offset;
- long/short order sequencing;
- whether short signals are admitted;
- partial-fill policy;
- SL-M versus SL-L versus another exit primitive;
- market-protection percentage;
- gap and stop-non-fill treatment;
- spread/slippage bounds;
- forced-exit timestamp relative to RMS;
- corporate-action conversion for executable prices;
- handling of CAS and other date-effective market-structure changes;
- data partition boundaries and kill criteria.

The opposing side of an ORB trade is a trader or liquidity provider selling into a long breakout or buying into a short breakdown. No evidence in this audit shows that those counterparties lose systematically after cash-market costs. That question remains for untouched testing only after preregistration.

## 11. Final gate

CASH_EQUITY_AFFORDABILITY=YES_FOR_AT_LEAST_ONE_SHARE_ON_OBSERVED_DEVELOPMENT_SIGNALS  
CASH_ORDER_TYPE_COMPATIBILITY=DOCUMENTED_FOR_NSE_EQ_REGULAR_ORDERS; LIVE_EXECUTION_UNVERIFIED  
CASH_DATA_AVAILABILITY=TWO_PUBLIC_1MIN_CANDLE_SOURCES_IDENTIFIED; QUOTE_DEPTH_HISTORY_UNAVAILABLE  
CASH_CAUSAL_EXECUTION_FEASIBILITY=STRUCTURALLY_FEASIBLE_WITH_COMPLETED_SIGNAL_THEN_CONFIRMED_FILL_THEN_PROTECTION  
RISK_SIZING_FEASIBILITY=CONDITIONAL_ON_NEW_STOP_AND_EXECUTION_BOUND  
EXIT_RULE_STATUS=NEW_HYPOTHESIS_REQUIRED  
NET_PROFITABILITY=UNKNOWN  
FINAL_VERDICT=CASH_ORB_WORTH_NEW_HYPOTHESIS

## 12. Single next warranted action

Founder decision only: authorize or decline a separate outcome-independent cash-equity execution preregistration. If authorized, that document must freeze the stop/exit primitive, causal order state machine, conservative 3% admission bound, short-sale treatment, costs, untouched dates, corporate-action basis and prospective kill criteria before any cash P&L is calculated.
