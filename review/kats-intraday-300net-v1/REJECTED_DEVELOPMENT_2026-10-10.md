# KATS-INTRADAY-300NET-V1 — development verdict (2026-10-10)

**REJECT_DEVELOPMENT. No live trading, no paper promotion, no optimization on viewed historical outcomes.**

This record preserves the actual GitHub Actions results from run [38048375225](https://github.com/krishivrcs/kats-backtest-scratch/actions/runs/38048375225) at frozen hypothesis source commit `326dbdd5fdc92c14c596ede7ac32dba997537fb8`. This review note is **not independent verification**, and CI success means the code ran and its trade ledgers reconciled, not profitability.

## Tested goal and constraints

INR 20,000 starting cash, one intraday NSE equity MIS trade per trading day max, research-only +INR 300 net target on winning trades, planned cost-inclusive stop-out loss <=min(INR 200,1% current account), no leverage, Upstox Plus approximate 2024-25 statutory costs and 5bps per-side modeled slippage (15bps adverse). No live orders.

## Actual development outcomes: 2024-04-01 through 2025-02-28

- 227 admitted calendar trading sessions in the selected source data.
- 760 algorithmic candidates before eligibility/portfolio filtering.
- BASE: 129 modeled trades, 32 profitable trades/days (24.8% win rate); **5** trades actually reach the modeled +INR 300 target; 98 no-trade days; gross P&L **−INR 2,674.25**; costs **INR 4,993.89**; cumulative **−INR 7,668.14**; ending modeled cash **INR 12,331.86**; maximum realized drawdown approximately **INR 7,669.69**; profit factor **0.282**.
- ADVERSE: 104 modeled trades, 21 profitable trades/days, only **2** net-300 targets; gross **−INR 4,553.65**; costs **INR 3,681.40**; net **−INR 8,235.05**; ending **INR 11,764.95**; profit factor **0.163**.
- Development profit gate FAIL; **validation never accessed**.
- Historical source is an adjusted, discovery-grade minute-bar archive, not broker fills. Reported modeled stop-loss cap does not guarantee actual stop fills or a limit on daily losses.

## Verified automated checks
- 14/14 unit tests passed.
- Sha-pinned input archive verified.
- CI recalculated trade-ledger net/gross/cost totals and asserted <=1% planned risk, <=INR200 estimated stop risk and >=INR300 prospective reward for recorded entries.
- No live broker functionality in the experiment.

## Decision
Do not trade this strategy. Do not claim that programming a profit target creates a profitable edge. Do not tune to the development sample, promote to live, or access the frozen KATS original holdout. To make a credible strategy, the *probability of reaching a price target relative to stops/charges* must be independently demonstrated, and net returns must survive genuinely untouched samples and independent execution evidence.

Review status: ARCHIVED_NEGATIVE_RESULT.
