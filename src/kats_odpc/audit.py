from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from .core import normalize_1m


EXPECTED_MINUTES = 375  # 09:15 through 15:29, minute-start convention
CORPORATE_GAP_THRESHOLD = 0.15


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _session_audit(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    work = frame.copy()
    work["session"] = work.index.normalize()
    duplicate_rows = int(work.index.duplicated(keep=False).sum())
    finite = np.isfinite(work[["open", "high", "low", "close", "volume"]]).all(axis=1)
    malformed = (
        (work["high"] < work[["open", "close", "low"]].max(axis=1))
        | (work["low"] > work[["open", "close", "high"]].min(axis=1))
        | (work[["open", "high", "low", "close"]] <= 0).any(axis=1)
        | (work["volume"] < 0)
        | ~finite
    )
    inside = (work.index.time >= pd.Timestamp("09:15").time()) & (
        work.index.time <= pd.Timestamp("15:29").time()
    )
    # Store row-quality flags positionally so duplicate timestamp labels can be
    # audited rather than causing an index re-alignment failure.
    work["_malformed"] = malformed.to_numpy()
    work["_inside_session"] = np.asarray(inside, dtype=bool)
    summaries = []
    prior_close = None
    corporate_events = []
    for date, day in work.groupby("session", sort=True):
        day = day.sort_index()
        unique = not day.index.duplicated().any()
        minute_count = len(day)
        expected = pd.date_range(date + pd.Timedelta(hours=9, minutes=15), periods=EXPECTED_MINUTES, freq="1min")
        complete_grid = minute_count == EXPECTED_MINUTES and day.index.equals(expected)
        bad = int(day["_malformed"].sum())
        outside = int((~day["_inside_session"]).sum())
        current_open = float(day.iloc[0].open) if len(day) else None
        overnight_gap = None if prior_close is None else current_open / prior_close - 1.0
        corporate_suspect = overnight_gap is not None and abs(overnight_gap) >= CORPORATE_GAP_THRESHOLD
        if corporate_suspect:
            corporate_events.append({"session": date.date().isoformat(), "overnight_gap_pct": overnight_gap})
        opening = day[(day.index.time >= pd.Timestamp("09:15").time()) & (day.index.time < pd.Timestamp("09:45").time())]
        opening_complete = len(opening) == 30
        valid = unique and complete_grid and bad == 0 and outside == 0 and opening_complete and not corporate_suspect
        summaries.append({
            "session": date,
            "valid": bool(valid),
            "minute_count": minute_count,
            "opening_volume": float(opening.volume.sum()) if opening_complete else None,
            "duplicate_timestamps": int(day.index.duplicated(keep=False).sum()),
            "malformed_rows": bad,
            "outside_session_rows": outside,
            "complete_minute_grid": bool(complete_grid),
            "corporate_action_suspect": bool(corporate_suspect),
            "overnight_gap_pct": overnight_gap,
        })
        if len(day):
            prior_close = float(day.iloc[-1].close)
    table = pd.DataFrame(summaries).set_index("session")
    stats = {
        "duplicate_rows": duplicate_rows,
        "malformed_rows": int(malformed.sum()),
        "rows_outside_regular_session": int((~np.asarray(inside, dtype=bool)).sum()),
        "session_count": len(table),
        "valid_session_count": int(table.valid.sum()),
        "invalid_session_count": int((~table.valid).sum()),
        "corporate_action_suspects": corporate_events,
    }
    return table, stats


def audit_symbol(path: Path, symbol: str) -> tuple[dict, pd.DataFrame]:
    parquet = pq.ParquetFile(path)
    raw = pd.read_parquet(path)
    normalized = normalize_1m(raw)
    sessions, stats = _session_audit(normalized)
    report = {
        "symbol": symbol,
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "schema": str(parquet.schema_arrow),
        "row_count": int(parquet.metadata.num_rows),
        "columns": list(raw.columns),
        "timestamp_column": "Date",
        "source_timezone": "NAIVE",
        "timestamp_interpretation": "Asia/Kolkata local exchange time",
        "earliest_timestamp": normalized.index.min().isoformat(),
        "latest_timestamp": normalized.index.max().isoformat(),
        **stats,
    }
    return report, sessions


def create_manifest(data_dir: Path, symbols: list[str], output: Path, source_commit: str) -> dict:
    reports = []
    session_dir = output.parent / "session_audits"
    session_dir.mkdir(parents=True, exist_ok=True)
    for symbol in symbols:
        report, sessions = audit_symbol(data_dir / f"{symbol}.parquet", symbol)
        reports.append(report)
        sessions.reset_index().to_csv(session_dir / f"{symbol}.csv", index=False)
    manifest = {
        "manifest_version": 1,
        "frozen_before_outcomes": True,
        "source_repository": "rahulkanadia/IndianMarkets_DataBackfill",
        "source_commit": source_commit,
        "valid_session_rule": {
            "required_minute_grid": "09:15..15:29 inclusive (375 minute-start bars)",
            "duplicates_allowed": False,
            "malformed_or_nonfinite_rows_allowed": False,
            "opening_volume_window": "09:15 inclusive to 09:45 exclusive",
            "corporate_action_gap_exclusion_abs_pct": CORPORATE_GAP_THRESHOLD,
        },
        "symbols": reports,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = sha256_file(output)
    (output.parent / "DATA_MANIFEST_SHA256.txt").write_text(digest + "\n", encoding="utf-8")
    return manifest
