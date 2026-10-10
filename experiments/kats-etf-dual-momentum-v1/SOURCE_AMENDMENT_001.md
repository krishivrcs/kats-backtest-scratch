# Pre-outcome data-source amendment 001 — 2026-10-10

The registered NSE bhavcopy-history connector, queried for three-month intervals, returned no ETF OHLCV for most of 2023; e.g., both NIFTYBEES and GOLDBEES returned `Symbol not found` for 2023-06-30 and 2023-09-30. No development P&L was calculated. This makes a development evaluation using that connector **impossible**.

**Pre-outcome source substitution**: Acquire daily unadjusted NSE price candles (Open, High, Low, Close, Volume) for the already-frozen symbols/dates from Yahoo Finance via `yfinance`, stored in the CI evidence artifact with sha256 and provider metadata. Do not use `Adj Close` as executable price. Remove Yahoo's 0-volume synthetic holiday bars; strictly common positive-volume sessions only. Explicitly check zero/negative fields, intraday OHLC coherence, duplicate dates, and >15% close discontinuities (stop if seen) prior to P&L. Check corporate actions using separate NSE source; unusual ETF distributions may still make price-only benchmarking unreliable.

At least three actual common date spot checks in 2022, 2024 and 2025 against available NSE bhavcopy data required *before running the strategy*. Exact OHLC values can differ between data sources in a small number of corrections; if differences exceed ₹0.15 per OHLC price or material day-volume discrepancy >5%, **refuse scoring** and report. This check must be non-P&L.

**Unchanged**: universe, original preregistered signals, 2022 warmup, 2023 development, conditional 2024–Oct 2025 validation, all costs, 5/15bps slippage, month-end next-open execution, and gate. No lookahead. No strategy P&L known when written.

**Limitations**: Yahoo data is a secondary provider; ability to execute at its reported market open in actual order books remains unverified. If historical data is unavailable or integrity comparison fails, return DATA_BLOCKED; do not loosen the gate or silently synthesize missing records. No broker orders.
