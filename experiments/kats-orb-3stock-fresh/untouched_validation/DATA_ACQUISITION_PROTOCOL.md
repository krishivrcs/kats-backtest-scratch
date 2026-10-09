# Untouched validation data-acquisition protocol

Frozen at base commit `5e90960ebe858a5b2ccdaf93188f63af62363ad3` before any
untouched P&L is calculated.

Required admission gates:

1. Actual NSE stock-option candles for SBIN, DLF and RELIANCE; underlying cash,
   stock futures, index options, EOD data and synthetic premiums are rejected.
2. One-minute OHLC with timestamp, contract, expiry, strike and CE/PE. Volume is
   required; OI is recorded when present.
3. At least twelve months outside 2024-10-15 through 2024-10-31.
4. Lawful free research access. Paid/licensed-only datasets, prohibited scraping
   and access-control bypasses are rejected.
5. Exact files, byte sizes, hashes, timestamp interpretation, session dates and
   corporate-action basis must be frozen before strategy execution.
6. The frozen strategy at `5e90960` will run unchanged only after all gates pass.

The source-audit workflow queries public catalogues and records metadata only.
It does not calculate strategy signals or P&L.

