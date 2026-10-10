# KATS GUARD V1 — independent rejection record

Recorded 2026-10-10 from the review results supplied by the independent reviewer. This is an **archive of supplied audit findings**, not a new run of the review, and it does not amend the frozen GUARD V1 repository/worktree.

**Disposition: REJECT GUARD V1 for INR 20,000 trading with <=1% (INR 200 initial) cost-inclusive planned account risk.**
**Paper promotion:** NO. **Live deployment:** NO.

## Immutable historical references
- Source worktree: `D:\KrishivAI\worktrees\kats-india-swing-ridge-h3-guard-v1`
- Frozen source HEAD: `876ed1950699c6a5eb141592c9c47285bb99a154`
- Frozen result: `research/SWING_V1_RIDGE_H3_GUARD_V1_RESULTS.json`
- Result hash pinned in `tests/test_swing_ridge_h3_guard_v1.py` (full hash not provided here).
- Original independent reported result: BASE +INR 1,858.25; STRESS +INR 1,367.97; BASE max drawdown 5.06%. These were **exploratory historical simulation results**, not broker trades or prospectively validated profits.

## Independent audit findings (supplied)
1. GUARD retained underlying RIDGE_H3 signal/model, features, +150 bps threshold, selected symbol and 09:30 entry. Added 2.5% stop, breakeven, target and trailing rules, and **1.5%** planned risk (around INR 300 at starting capital), so it fails the explicitly required <=1% risk limit even before fill uncertainty.
2. Historical sample: 53 BASE trades spanning 24 symbols, 33 winners, 20 losers, 62.26% winning, profit factor 1.37; largest BASE loss INR 316.43. STRESS 30/53 winners, PF 1.26, largest realized loss INR 322.26. Max modeled stop-out loss including fees INR 324.57, approximately INR 294 average modeled stop-out loss.
3. Source rules were frozen before September/October 2026 paper losses but **after the original development RIDGE_H3 outcome was already inspected**. It is a post-result exploratory overlay. The reported 53 trades are not unseen independent validation.
4. The original paper experiment selected POLICYBZR for decisions on Sep 24, Sep 29, Oct 5; no demonstration that GUARD would avoid those signals. GUARD exits/sizing differ and could lead to different results, which are NOT AVAILABLE.
5. Historical execution relies on one-minute candle prices and modeled slippage. Minute candle open/high/low do not establish available order-book prices or fills. Zerodha historical cost assumptions differ from Upstox Plus paper costs.
6. No properly matched passive buy-and-hold after-cost benchmark comparison has been shown.
7. Five top stock contributions ~61.7% of BASE net profit; profitability exists only in the inspected development sample. Rounded displayed BASE trade nets differ by INR 0.02 from full precision aggregate, consistent with rounding (not independently resimulated here).

## Decision and safeguards
- `HISTORICAL_SIMULATION_POSITIVE=YES`
- `INDEPENDENT_VALIDATION=NO`
- `ONE_PERCENT_RISK_COMPLIANT=NO`
- `EXECUTION_VIABILITY_DEMONSTRATED=NO`
- `BENCHMARK_OUTPERFORMANCE_DEMONSTRATED=NO`
- `FINAL_VERDICT=REJECT`
- `DO_NOT_DEPLOY_OR_PAPER_TRADE=YES`
- `DO_NOT_REOPTIMIZE_OR_OPEN_SEALED_HOLDOUT=YES`
- `FROZEN_GUARD_WORKTREE_CHANGED=NO (this record lives in a different GitHub repository)`

### Research implication
Do not interpret positive exploratory simulation P&L as real evidence of profit. Any successor requires independent, uncontaminated data; realistic execution and broker costs; cost-inclusive risk <= INR 200 at INR 20,000 initial equity; meaningful sample size and concentration controls; and benchmarking. Preserve the original rejection, including the reasons it is invalid for account deployment.
