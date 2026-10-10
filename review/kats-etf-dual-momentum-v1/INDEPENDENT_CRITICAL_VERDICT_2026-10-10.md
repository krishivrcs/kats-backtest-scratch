# KATS ETF Dual Momentum V1 — Independent critical audit disposition

Date: 2026-10-10. **Disposition: REJECT for paper promotion / live trading.**

This is a faithful record of the separate human-supplied independent critical audit delivered after the GitHub experiment and initial mechanical recalculation; it **does not claim that this GitHub commit independently executed that auditor's script**. The original preregistered development and validation code/data/CI artifacts are unmodified.

## Prior machine-generated evidence
- Backtest run: https://github.com/krishivrcs/kats-backtest-scratch/actions/runs/38041332940
- Mechanical second-implementation arithmetic audit: https://github.com/krishivrcs/kats-backtest-scratch/actions/runs/38041462911
- Development, 2023: +INR 3,393.52 net, 3 completed trades (5bps each side).
- Validation, 2024-01 through 2025-10: +INR 9,552.90 net, 8 completed trades, 13.01% modeled maximum drawdown; adverse slippage validation +INR 9,110.27.
- Gold ETF validation buy-and-hold +INR 17,019.57, exceeding rotation by INR 7,466.67 in the same simulation.

## Independent critical audit findings (as supplied)
- Eleven completed trades across two partitions, only eight validation trades. Seven non-leading validation trades together lose INR 662.72; one GOLDBEES trade gains INR 10,215.62, exceeding total validation profit.
- Time ordering and historical cash/fee arithmetic substantively reproduced.
- Seven historical NSE bhavcopy files checked; 13 symbol-date OHLC records matched Yahoo price values at paise precision (12 of 22 fill bars covered). Four special exchange sessions absent from Yahoo; none are the trade dates, but missing sessions limit source completeness.
- Actual open-print fill assumptions are not established as achievable trades. Daily bar open alone lacks spread, queue or depth. Costs in the simulation do not represent the user's audited Upstox Plus pricing.
- 100%-invested single ETF exposures with no protective stop breach stated <=1% planned trade-risk mandate; losses and adverse excursion exceed INR 200 reference loss budget.
- Untimed 50/50 NIFTYBEES/GOLDBEES buy-and-hold reportedly outperformed the rotation in both partitions with materially lower drawdown (the auditor's exact benchmark net values were truncated in the supplied textual table; treat detailed values as NOT AVAILABLE, rather than inventing them).
- Positive validation is materially concentrated in a gold bullish period, and an already known market regime undermines confident independent-alpha inference.
- Earlier second-implementation audit proves *mechanical reproduction* of the same rules; it is not independent proof of investment alpha, broker fill feasibility or future profits.

## Binding decision
- FINAL_VERDICT: REJECT_CURRENT_IMPLEMENTATION.
- PAPER_TRADING_AUTHORIZED: NO.
- LIVE_ORDERS_AUTHORIZED: NO.
- REVIEW_ONLY_AND_FROZEN: YES.
- REOPTIMIZE_ON_THE_SAME_2023_2025_SAMPLE: PROHIBITED.
- STRATEGY_SUCCESSOR: must originate in independently motivated market mechanism and fresh evidence, have risk-capped deterministic exits and execution-calibrated broker charges, outperform appropriately matched passive baseline after costs, then independently pass unseen validation and prospective paper execution.
- No source, production ledgers, strategies, real-account settings, or scheduled tasks were altered by recording this review.
