# KATS-ORB-CAUSAL-EXEC-V1 — exchange order-type feasibility audit

**Audit status:** definitive blocker recorded; no implementation authorized  
**Audited hypothesis:** `KATS-ORB-CAUSAL-EXEC-V1`  
**Source branch:** `research/kats-orb-causal-exec-v1`  
**Source commit:** `dbabc48369803f0eb6d07076c30dea5fc7a9def5`  
**Frozen preregistration blob:** `01340fe29d8ce26c30d7824c78509d6b5ab7d172`  
**Audit date:** 2026-10-09  
**Scope:** NSE exchange-native protective order compatibility for stock options only. No code, backtest, P&L, data or ledger changes.

## 1. Finding

`KATS-ORB-CAUSAL-EXEC-V1` is **SPECIFICATION_INFEASIBLE** for NSE stock options.

The frozen specification requires an exchange/broker-supported stop-market protective order and explicitly prohibits substituting a stop-limit order. NSE discontinued Stop Loss orders with Market condition (SL-M) for index options and stock options effective 27 September 2021. The Exchange stated that such orders would be rejected. NSE expressly reaffirmed this restriction in March 2022.

No later authoritative NSE rule was found that explicitly reverses or supersedes the restriction for index or stock options. Generic documentation saying that "stop-loss orders" exist is not evidence that SL-M is permitted, because SL-L remains an available stop-loss order type.

## 2. Primary-source evidence

### NSE/FAOP/49677 — 21 September 2021

Official PDF:

https://archives.nseindia.com/content/circulars/FAOP49677.pdf

NSE states:

- Stop Loss orders with Market condition (SL-M) for option contracts were discontinued with effect from 27 September 2021.
- Such orders would be rejected by the Exchange with the message `Function Not Available`.
- The change applies specifically to index-option and stock-option contracts.
- Stop Loss orders with Limit condition (SL-L) remain available.

This circular establishes both the prohibition and the only exchange-native stop-loss alternative identified in the circular.

### NSE/FAOP/51600 — 11 March 2022

Official PDF:

https://archives.nseindia.com/content/circulars/FAOP51600.pdf

In its section on market-order handling, NSE expressly notes that Stop Loss orders with Market price condition for index options and stock options are not allowed from 27 September 2021 and cites NSE/FAOP/49677.

This later circular confirms that the restriction remained effective after implementation.

## 3. Later-rule review

Official NSE material reviewed included:

- current NSE pages for NIFTY and individual-security derivatives that list a generic `Stop Loss Order`;
- later NSE pre-trade risk-control circulars concerning market-price protection, limit-price protection and stop-loss-limit validation;
- available official NSE circular-search results for `SL-M`, `Stop Loss orders with Market condition`, index options and stock options;
- current Futures & Options Non-NEAT protocol material describing stop-loss order structures.

No reviewed official source explicitly states that SL-M was restored for index options or stock options.

Generic `Stop Loss Order` wording is not a reversal. It is compatible with SL-L, which NSE/FAOP/49677 expressly preserved. Generic broker API support for an SL-M enum in other segments or instruments is also not exchange authorization for OPTSTK or OPTIDX.

**Later explicit reversal:** `NOT ESTABLISHED`.

If a future NSE circular expressly restores SL-M for option contracts, it would require a new dated feasibility review and a new hypothesis decision. It cannot retroactively make this frozen specification feasible.

## 4. Exact frozen conflict

Frozen section 7 of `PREREGISTRATION.md` states:

> Preferred protective order is a broker/exchange-supported stop-market order. If that order type is unavailable for the contract or its exact historical semantics are not documented, the candidate is ineligible. A stop-limit order is not substituted.

The rule is intentionally fail-closed:

1. SL-M is required.
2. SL-M is unavailable for NSE stock options.
3. SL-L substitution is prohibited.
4. Therefore every intended SBIN, DLF and RELIANCE stock-option candidate is ineligible before entry.
5. A causal trading engine implementing the frozen specification cannot execute any trade.

This is not a data-availability issue and cannot be repaired through improved quotes, depth, timestamp provenance or slippage modeling. The required exchange primitive is prohibited.

## 5. Rejected substitutions

The following are not implementations of the frozen hypothesis and were not adopted:

- SL-L;
- GTT or broker-held conditional orders;
- client-side or server-side synthetic stops;
- trigger-followed marketable-limit orders;
- polling plus emergency market orders;
- broker RMS approximations;
- unprotected entries;
- cash-equity, futures or index-option substitution.

Each alternative changes the execution primitive, protection guarantee, gap/non-fill behavior, latency and realized-loss distribution. Any one would require Founder authorization and a separately identified preregistered hypothesis.

## 6. Consequences

- `PREREGISTRATION_STATUS=FROZEN_BUT_INFEASIBLE`.
- The causal execution engine must not be implemented from the frozen specification.
- The hypothesis cannot proceed to historical backtest, paper trading or live trading.
- Previous parent ledgers and P&L remain unchanged and invalid as executable-profit evidence.
- No P&L calculation is warranted because the order compatibility gate fails before entry.
- No code, data, workflow, prior specification or ledger may be modified to force compatibility.

## 7. Methodological verdict

`FINAL_VERDICT=SPECIFICATION_INFEASIBLE`

The finding is based on an explicit exchange prohibition, not an assumption about broker behavior.

## 8. Only warranted next decision

No replacement hypothesis is authorized by this audit.

If the Founder later authorizes continued stock-option research, the closest exchange-compatible candidate would be a separately preregistered SL-L execution hypothesis with explicit non-fill, gap-through, limit-band, latency, cancellation and maximum-loss treatment. It must receive a new hypothesis ID and cannot inherit validation from `KATS-ORB-CAUSAL-EXEC-V1`.

Until that authorization:

`NEXT_STATUS=STOP_NO_IMPLEMENTATION`
