# KATS ORB three-stock fresh experiment

This directory is an isolated, outcome-independent investigation of a newly
specified three-stock opening-range-breakout and relative-volume strategy.
It does not reuse the old 78-trade ledger or target the previously reported
profit.

The first workflow stage is deliberately a data gate. It downloads the public
Kaggle dataset at runtime, records its checksum, inspects every CSV member, and
proves whether genuine SBIN, DLF and RELIANCE option contracts are present.
Raw market data is never committed or uploaded as an artifact.

See `SPEC.md` for the frozen fallback strategy and the conditions which must be
met before outcome generation may begin.

