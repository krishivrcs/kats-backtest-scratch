# KATS profit sprint 2026-10-10

This directory is an isolated exploratory, long-only NSE cash-equity experiment. Read `PREREGISTRATION.md` before interpreting any result.

Reproduce with Python 3.11:

```bash
python -m unittest discover -s experiments/kats-profit-sprint-20261010/tests -v
sha256sum /tmp/stocks_1m_csvs.zip
python experiments/kats-profit-sprint-20261010/run.py /tmp/stocks_1m_csvs.zip --out /tmp/kats-profit-sprint-results
```

The archive hash must equal `20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2`. No date after 2025-10-31 is scored. Historical candles are discovery-grade and are not evidence of executable quotes.
