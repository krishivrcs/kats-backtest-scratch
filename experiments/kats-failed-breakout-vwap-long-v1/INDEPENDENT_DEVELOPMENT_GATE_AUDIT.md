# Independent Gate Audit — KATS-FAILED-BREAKOUT-VWAP-LONG-V1

**Independent verdict:** `ACCEPT_REJECTION`, `REJECT_DEVELOPMENT`.

## Immutable source and evidence
- Tested commit: `204f4677af8a99028d7bf3ff2bd044d101e29386`.
- Successful GitHub Actions run: https://github.com/krishivrcs/kats-backtest-scratch/actions/runs/38028435607
- Artifact ID: `11660639097`.
- Independently downloaded artifact ZIP SHA-256: `30476275cbd4c2082a570a2793940febbb29e0b1776c742bf7aba00bb030f040`.
- Public minute source archive SHA-256 (as stated by tested preregistration): `20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2`.
- All 12 tests PASS. GitHub Actions PASS; reconciliation PASS.

## Independent check — all recorded candidate decisions
An independent Decimal-arithmetic replay of the artifact's `development_candidates.csv` (57 records) against the frozen cash/risk, tick-rounded entry/exit, date-effective cost and prospective 1.50x net-reward rules reconstructed:
- `PROSPECTIVE_REWARD`: 40 rejected.
- `TARGET_NOT_ABOVE_ENTRY`: 16 rejected.
- `ELIGIBLE`: 1.
- Classification disagreements versus `development_rejections.csv` and `development_trades.csv`: **0**.
- All 57 recorded candidates have a recovery-completion timestamp followed by an entry-reference timestamp exactly 60 seconds later; recorded recovery follows the breakdown within 5, 10, or 15 minutes; no violations of the frozen latest-entry time.
- Candidate keys are unique.
- Best rejected prospective reward-to-all-in-stop-loss ratio: approximately **1.267**, below frozen 1.50 minimum; no rejected candidate passes the tested threshold.
- The only accepted signal is 2024-10-18 INFY, 10 whole shares. Recorded entry ₹1,886.25; observed modeled exit ₹1,882.00; gross −₹42.50; costs ₹20.013248745; net **−₹62.513248745**. Under adverse slippage, net **−₹81.511158745**.

## Result and boundaries
- Development: 57 candidates, 1 modeled trade. Zero wins, zero net profit, fails 30-trade minimum.
- `DEVELOPMENT_NET_PNL = -INR 62.51`.
- `DEVELOPMENT_ADVERSE_NET_PNL = -INR 81.51`.
- Validation: `NOT_ACCESSED` (sequential gate failed); sealed holdout untouched.
- No orders; paper engine not implemented.
- Historical assumptions rely on OHLCV, not broker-evidenced bid/ask and fills.

**Audit scope limitation:** This review independently verifies the economics, classification, and timestamps **as recorded in the artifact candidate ledger**. It does **not** independently regenerate the 57 candidate setups from the full original one-minute source, validate the upstream price/volume basis, or provide broker execution evidence.

## Decision
`REJECT_DEVELOPMENT` stands. Do not modify the strategy/threshold after outcomes, reopen validation, or label the strategy profitable. Preserve accepted tested code, results and sealed-holdout boundary. This independent audit lives on a separate review branch.
