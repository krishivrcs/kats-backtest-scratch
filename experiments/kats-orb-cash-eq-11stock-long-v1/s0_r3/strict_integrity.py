#!/usr/bin/env python3
"""Strict, outcome-blind S0-R3 minute-bar integrity validator.

This module validates source structure only. It does not calculate ORB, RVOL,
signals, rankings, entries, exits, returns, or P&L.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
EXPECTED_ARCHIVE_SHA256 = "20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2"
QA_DATE = date(2024, 6, 25)
QA_SYMBOLS = ("HDFCBANK", "ICICIBANK", "HAL")
OPENING_MINUTES = tuple(time(9, 15 + i) for i in range(15))
NORMAL_SESSION_MINUTES = 375
EXPECTED_EXCEPTIONS = {
    "HDFCBANK": (835.6, 839.8, 837.4, 839.6, 370096.0),
    "ICICIBANK": (1170.25, 1174.35, 1171.0, 1171.75, 174373.0),
    "HAL": (5375.0, 5368.0, 5347.6, 5368.0, 72552.0),
}


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_timestamp(value: object) -> datetime:
    if isinstance(value, bool):
        raise ValueError("MALFORMED_TIMESTAMP")
    if isinstance(value, int):
        seconds = value
    else:
        token = str(value).strip()
        if re.fullmatch(r"[+-]?\d+", token) is None:
            raise ValueError("TIMESTAMP_NOT_EXACT_INTEGER_SECOND")
        seconds = int(token)
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc).astimezone(IST)
    if dt.second or dt.microsecond:
        raise ValueError("OFF_GRID_TIMESTAMP")
    return dt


def validate_bar(bar: Bar) -> tuple[str, ...]:
    issues: list[str] = []
    prices = (bar.open, bar.high, bar.low, bar.close)
    if not all(math.isfinite(value) for value in prices):
        issues.append("NONFINITE_OHLC")
    elif any(value <= 0 for value in prices):
        issues.append("NONPOSITIVE_OHLC")
    elif not (bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high):
        issues.append("INVALID_OHLC_RELATIONSHIP")
    if not math.isfinite(bar.volume):
        issues.append("NONFINITE_VOLUME")
    elif bar.volume < 0:
        issues.append("NEGATIVE_VOLUME")
    if bar.timestamp.tzinfo is None or bar.timestamp.utcoffset() != IST.utcoffset(bar.timestamp):
        issues.append("TIMESTAMP_NOT_IST")
    if bar.timestamp.second or bar.timestamp.microsecond:
        issues.append("OFF_GRID_TIMESTAMP")
    return tuple(issues)


def bar_from_row(row: Mapping[str, object]) -> Bar:
    return Bar(
        timestamp=parse_timestamp(row["time"]),
        open=float(row["open"]),
        high=float(row["high"]),
        low=float(row["low"]),
        close=float(row["close"]),
        volume=float(row["Volume"]),
    )


def expected_session_timestamps(day: date) -> tuple[datetime, ...]:
    start = datetime.combine(day, time(9, 15), IST)
    return tuple(start + timedelta(minutes=i) for i in range(NORMAL_SESSION_MINUTES))


def complete_five_minute_bucket(
    bars: Sequence[Bar], bucket_start: datetime, available_at: datetime
) -> bool:
    """Return true only after five unique, consecutive, valid bars are complete."""
    expected = tuple(bucket_start + timedelta(minutes=i) for i in range(5))
    by_timestamp: dict[datetime, list[Bar]] = defaultdict(list)
    for bar in bars:
        by_timestamp[bar.timestamp].append(bar)
    bucket_end = bucket_start + timedelta(minutes=5)
    return (
        available_at >= bucket_end
        and all(len(by_timestamp[stamp]) == 1 for stamp in expected)
        and all(not validate_bar(by_timestamp[stamp][0]) for stamp in expected)
    )


def audit_session(
    rows: Iterable[Mapping[str, object]], day: date, *, expected_session: bool = True
) -> dict[str, object]:
    """Audit one expected session while preserving every failed observation."""
    bars: list[Bar] = []
    issues = Counter()
    raw_timestamps: list[datetime] = []
    malformed = 0
    for row in rows:
        try:
            bar = bar_from_row(row)
        except (KeyError, TypeError, ValueError, OverflowError):
            malformed += 1
            issues["MALFORMED_ROW"] += 1
            continue
        raw_timestamps.append(bar.timestamp)
        bars.append(bar)
        issues.update(validate_bar(bar))

    counts = Counter(raw_timestamps)
    duplicate_count = sum(count - 1 for count in counts.values() if count > 1)
    out_of_order_count = sum(
        current <= previous for previous, current in zip(raw_timestamps, raw_timestamps[1:])
    )
    if duplicate_count:
        issues["DUPLICATE_TIMESTAMP"] += duplicate_count
    if out_of_order_count:
        issues["OUT_OF_ORDER_TIMESTAMP"] += out_of_order_count

    expected = expected_session_timestamps(day) if expected_session else ()
    observed = set(raw_timestamps)
    missing = tuple(stamp for stamp in expected if stamp not in observed)
    if expected_session and not rows and not bars:
        issues["MISSING_SESSION"] += 1
    if missing:
        issues["MISSING_MINUTE"] += len(missing)

    valid_unique = {
        bar.timestamp: bar
        for bar in bars
        if counts[bar.timestamp] == 1 and not validate_bar(bar)
    }
    opening_expected = expected[:15]
    opening_complete = bool(expected) and all(stamp in valid_unique for stamp in opening_expected)
    if expected and not opening_complete:
        issues["INCOMPLETE_OPENING_RANGE"] += 1

    incomplete_buckets = 0
    if expected:
        for offset in range(0, NORMAL_SESSION_MINUTES, 5):
            start = expected[offset]
            if not complete_five_minute_bucket(bars, start, start + timedelta(minutes=5)):
                incomplete_buckets += 1
        if incomplete_buckets:
            issues["INCOMPLETE_5M_BUCKET"] += incomplete_buckets

    return {
        "date": day.isoformat(),
        "expected_sessions": int(expected_session),
        "structural_session_denominator": 1,
        "observations": len(bars) + malformed,
        "valid_unique_observations": len(valid_unique),
        "issues": dict(sorted(issues.items())),
        "duplicate_timestamps": duplicate_count,
        "out_of_order_timestamps": out_of_order_count,
        "missing_minutes": len(missing),
        "opening_range_eligible": opening_complete,
        "incomplete_five_minute_buckets": incomplete_buckets,
        "structurally_eligible": not issues,
        "interpolation_used": False,
    }


def member_name(zf: zipfile.ZipFile, symbol: str) -> str:
    names = {Path(name).name.upper(): name for name in zf.namelist()}
    return names[f"{symbol}_1M.CSV.GZ"]


def qa_rows(zf: zipfile.ZipFile, symbol: str) -> list[dict[str, str]]:
    """Read only through the bounded QA day; never inspect validation/holdout rows."""
    compressed = zf.read(member_name(zf, symbol))
    selected: list[dict[str, str]] = []
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as raw, io.TextIOWrapper(
        raw, encoding="utf-8-sig", newline=""
    ) as text:
        for row in csv.DictReader(text):
            dt = parse_timestamp(row["time"])
            if dt.date() > QA_DATE:
                break
            if dt.date() == QA_DATE:
                selected.append(row)
    return selected


def run_qa(archive: Path, out: Path) -> dict[str, object]:
    archive_hash = sha256_file(archive)
    if archive_hash != EXPECTED_ARCHIVE_SHA256:
        raise SystemExit("archive SHA-256 mismatch")
    results: dict[str, object] = {}
    with zipfile.ZipFile(archive) as zf:
        for symbol in QA_SYMBOLS:
            rows = qa_rows(zf, symbol)
            report = audit_session(rows, QA_DATE)
            exception = next(
                bar_from_row(row)
                for row in rows
                if bar_from_row(row).timestamp.time() == time(9, 15)
            )
            actual = (exception.open, exception.high, exception.low, exception.close, exception.volume)
            if actual != EXPECTED_EXCEPTIONS[symbol]:
                raise AssertionError(f"{symbol} frozen QA exception mismatch")
            if "INVALID_OHLC_RELATIONSHIP" not in validate_bar(exception):
                raise AssertionError(f"{symbol} 09:15 exception was not rejected")
            if report["opening_range_eligible"]:
                raise AssertionError(f"{symbol} malformed opening range was admitted")
            results[symbol] = report
    evidence = {
        "scope": "S0_R3_QA_SOURCE_INTEGRITY_ONLY",
        "archive_sha256": archive_hash,
        "qa_date": QA_DATE.isoformat(),
        "symbols": results,
        "three_qa_exceptions_recorded": True,
        "upstox_corroboration_status": "MATCHED_PROVIDER_CANDLES_NOT_EXCHANGE_AUTHORITATIVE",
        "tatamotors_source_status": "UPSTOX_V3_AVAILABLE_NSE_EQ_INE155A01022",
        "tatamotors_special_session": "2025-10-14_STARTS_10:00_IST_330_CANDLES_OPENING_RANGE_INELIGIBLE",
        "tmpv_substitution": "PROHIBITED_PENDING_IDENTITY_AND_ECONOMIC_CONTINUITY",
        "corporate_action_basis_status": "UNRESOLVED",
        "signals_generated": False,
        "pnl_calculated": False,
        "holdout_accessed": False,
        "broker_orders": False,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "STRICT_QA_EVIDENCE.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    evidence = run_qa(args.archive, args.out)
    print(json.dumps({"scope": evidence["scope"], "three_qa_exceptions_recorded": True}))


if __name__ == "__main__":
    main()
