# KATS failed-breakout VWAP long V1

Read `PREREGISTRATION.md` first. This experiment sequentially gates validation: validation data is not parsed or scored if development fails.

```bash
python -m unittest discover -s experiments/kats-failed-breakout-vwap-long-v1/tests -v
python experiments/kats-failed-breakout-vwap-long-v1/run.py /tmp/stocks_1m_csvs.zip --out /tmp/failed-breakout-results
```

The source archive is discovery-grade OHLCV, not historical executable quotes. No live-order path exists.
