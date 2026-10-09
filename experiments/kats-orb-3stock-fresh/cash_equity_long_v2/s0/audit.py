#!/usr/bin/env python3
"""Outcome-blind KATS ORB cash-equity V2 source and signal-identity audit.

No entry, exit, cost, return, or P&L calculation exists in this module.
Holdout rows are reduced to aggregate integrity metadata at ingestion and can
never enter a signal function.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import io
import json
import math
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Iterable
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
SYMBOLS = ("SBIN", "DLF", "RELIANCE")
EXPECTED_SHA256 = "20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2"
EXPECTED_BYTES = 485_923_642
SOURCE_URL = "https://github.com/voletiramu/nse-fno-1min-data/releases/download/v1.0.0/stocks_1m_csvs.zip"
QA_START = date(2024, 4, 1)
QA_END = date(2024, 10, 14)
DEV_START = date(2024, 10, 15)
DEV_END = date(2024, 10, 31)
VALIDATION_START = date(2024, 11, 1)
VALIDATION_END = date(2025, 10, 31)
HOLDOUT_START = date(2025, 11, 1)
HOLDOUT_END = date(2026, 4, 30)
PERMITTED_END = VALIDATION_END
EXPECTED_COLUMNS = ("time", "open", "high", "low", "close", "CE Breakout Level", "PE Breakout Level", "Volume")


@dataclass(frozen=True)
class AuditBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class AuditSignal:
    symbol: str
    day: date
    direction: str
    decision_time: datetime
    rvol: float
    breakout_distance: float


class HoldoutAccessError(RuntimeError):
    pass


def assert_signal_access_allowed(day: date) -> None:
    if HOLDOUT_START <= day <= HOLDOUT_END:
        raise HoldoutAccessError(f"sealed holdout signal access denied: {day.isoformat()}")
    if day > PERMITTED_END:
        raise HoldoutAccessError(f"post-validation signal access denied: {day.isoformat()}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sound_bar(bar: AuditBar) -> bool:
    values = (bar.open, bar.high, bar.low, bar.close, bar.volume)
    return (
        all(math.isfinite(value) for value in values)
        and min(bar.open, bar.high, bar.low, bar.close) > 0
        and bar.low <= min(bar.open, bar.close, bar.high)
        and bar.high >= max(bar.open, bar.close, bar.low)
        and bar.volume >= 0
        and bar.timestamp.second == 0
        and bar.timestamp.microsecond == 0
    )


def expected_minutes(start: datetime) -> tuple[datetime, ...]:
    return tuple(start + timedelta(minutes=i) for i in range(5))


def complete_5m_bucket(group: Iterable[AuditBar], start: datetime) -> AuditBar | None:
    bars = sorted(group, key=lambda item: item.timestamp)
    stamps = tuple(item.timestamp for item in bars)
    if len(bars) != 5 or len(set(stamps)) != 5 or stamps != expected_minutes(start):
        return None
    if not all(sound_bar(item) for item in bars):
        return None
    return AuditBar(
        timestamp=start,
        open=bars[0].open,
        high=max(item.high for item in bars),
        low=min(item.low for item in bars),
        close=bars[-1].close,
        volume=sum(item.volume for item in bars),
    )


def aggregate_v2(bars: list[AuditBar]) -> tuple[list[AuditBar], list[datetime]]:
    buckets: dict[datetime, list[AuditBar]] = defaultdict(list)
    for bar in bars:
        minute = bar.timestamp.minute - bar.timestamp.minute % 5
        key = bar.timestamp.replace(minute=minute, second=0, microsecond=0)
        buckets[key].append(bar)
    complete: list[AuditBar] = []
    incomplete: list[datetime] = []
    for key in sorted(buckets):
        result = complete_5m_bucket(buckets[key], key)
        if result is None:
            incomplete.append(key)
        else:
            complete.append(result)
    return complete, incomplete


def valid_opening_v2(bars: list[AuditBar]) -> bool:
    opening = [bar for bar in bars if time(9, 15) <= bar.timestamp.timetz().replace(tzinfo=None) <= time(9, 29)]
    expected = {
        datetime.combine(opening[0].timestamp.date(), time(9, 15), IST) + timedelta(minutes=i)
        for i in range(15)
    } if opening else set()
    stamps = [bar.timestamp for bar in opening]
    return len(opening) == 15 and len(set(stamps)) == 15 and set(stamps) == expected and all(sound_bar(bar) for bar in opening)


def v2_signal_for_day(symbol: str, day: date, bars: list[AuditBar], prior_open_volumes: list[float]) -> tuple[AuditSignal | None, str]:
    assert_signal_access_allowed(day)
    opening = [bar for bar in bars if time(9, 15) <= bar.timestamp.timetz().replace(tzinfo=None) <= time(9, 29)]
    if not valid_opening_v2(bars):
        return None, "INVALID_CURRENT_OPENING_SESSION"
    if len(prior_open_volumes) < 20:
        return None, "INSUFFICIENT_20_SESSION_HISTORY"
    average_volume = mean(prior_open_volumes[-20:])
    if average_volume <= 0:
        return None, "NONPOSITIVE_VOLUME_HISTORY"
    rvol = sum(bar.volume for bar in opening) / average_volume
    if rvol < 1.50:
        return None, "RVOL_BELOW_1_50"
    opening_high = max(bar.high for bar in opening)
    opening_low = min(bar.low for bar in opening)
    complete, _ = aggregate_v2(bars)
    for bar in complete:
        decision = bar.timestamp + timedelta(minutes=5)
        if decision <= datetime.combine(day, time(9, 30), IST) or decision > datetime.combine(day, time(12, 0), IST):
            continue
        if bar.close > opening_high:
            return AuditSignal(symbol, day, "LONG", decision, rvol, (bar.close / opening_high) - 1.0), "SIGNAL"
        if bar.close < opening_low:
            return AuditSignal(symbol, day, "SHORT", decision, rvol, (opening_low / bar.close) - 1.0), "SIGNAL"
    return None, "NO_BREAKOUT"


def load_legacy_module(path: Path):
    spec = importlib.util.spec_from_file_location("frozen_legacy_backtest", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen legacy module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def partition(day: date) -> str | None:
    if QA_START <= day <= QA_END:
        return "QA"
    if DEV_START <= day <= DEV_END:
        return "DEVELOPMENT"
    if VALIDATION_START <= day <= VALIDATION_END:
        return "VALIDATION"
    return None


def parse_archive(archive: Path) -> tuple[dict[str, dict[date, list[AuditBar]]], dict]:
    retained: dict[str, dict[date, list[AuditBar]]] = {symbol: defaultdict(list) for symbol in SYMBOLS}
    source = {
        "schema": {},
        "symbols": {},
        "totals": Counter(),
        "holdout_integrity_only": Counter(),
        "holdout_signal_fields_generated": False,
    }
    with zipfile.ZipFile(archive) as zf:
        members = {Path(name).name.upper(): name for name in zf.namelist()}
        for symbol in SYMBOLS:
            expected_name = f"{symbol}_1M.CSV.GZ"
            if expected_name not in members:
                raise RuntimeError(f"missing member {expected_name}")
            member = members[expected_name]
            stats = Counter()
            seen: set[datetime] = set()
            session_stamps: dict[date, set[datetime]] = defaultdict(set)
            holdout_session_stamps: dict[date, set[datetime]] = defaultdict(set)
            earliest: datetime | None = None
            latest: datetime | None = None
            with zf.open(member) as compressed, gzip.GzipFile(fileobj=compressed) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
                reader = csv.DictReader(text)
                if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
                    raise RuntimeError(f"schema mismatch for {symbol}: {reader.fieldnames}")
                source["schema"][symbol] = reader.fieldnames
                for row in reader:
                    stats["rows"] += 1
                    source["totals"]["rows"] += 1
                    try:
                        epoch = int(float(row["time"]))
                        stamp = datetime.fromtimestamp(epoch, tz=timezone.utc).astimezone(IST)
                    except Exception:
                        stats["malformed_timestamp"] += 1
                        source["totals"]["malformed_timestamp"] += 1
                        continue
                    earliest = stamp if earliest is None else min(earliest, stamp)
                    latest = stamp if latest is None else max(latest, stamp)
                    is_duplicate = stamp in seen
                    if is_duplicate:
                        stats["duplicates"] += 1
                        source["totals"]["duplicates"] += 1
                    seen.add(stamp)
                    if stamp.second != 0 or stamp.microsecond != 0:
                        stats["off_grid"] += 1
                        source["totals"]["off_grid"] += 1
                    try:
                        bar = AuditBar(stamp, *(float(row[key]) for key in ("open", "high", "low", "close")), float(row["Volume"]))
                    except Exception:
                        stats["malformed_numeric"] += 1
                        source["totals"]["malformed_numeric"] += 1
                        if HOLDOUT_START <= stamp.date() <= HOLDOUT_END:
                            source["holdout_integrity_only"]["malformed_numeric"] += 1
                        continue
                    if not sound_bar(bar):
                        stats["invalid_ohlcv"] += 1
                        source["totals"]["invalid_ohlcv"] += 1
                    local_time = stamp.timetz().replace(tzinfo=None)
                    if not (time(9, 15) <= local_time <= time(15, 29)):
                        stats["outside_expected_session"] += 1
                        source["totals"]["outside_expected_session"] += 1
                    if HOLDOUT_START <= stamp.date() <= HOLDOUT_END:
                        source["holdout_integrity_only"]["rows"] += 1
                        if is_duplicate:
                            source["holdout_integrity_only"]["duplicates"] += 1
                        if not sound_bar(bar):
                            source["holdout_integrity_only"]["invalid_ohlcv"] += 1
                        if stamp.second != 0 or stamp.microsecond != 0:
                            source["holdout_integrity_only"]["off_grid"] += 1
                        if time(9, 15) <= local_time <= time(15, 29):
                            holdout_session_stamps[stamp.date()].add(stamp)
                        continue
                    if stamp.date() <= PERMITTED_END:
                        retained[symbol][stamp.date()].append(bar)
                        if time(9, 15) <= local_time <= time(15, 29):
                            session_stamps[stamp.date()].add(stamp)
            for session_day, stamps in session_stamps.items():
                expected = {
                    datetime.combine(session_day, time(9, 15), IST) + timedelta(minutes=i)
                    for i in range(375)
                }
                stats["missing_expected_session_minutes"] += len(expected - stamps)
                source["totals"]["missing_expected_session_minutes"] += len(expected - stamps)
                stats[f"session_first_{min(stamps).strftime('%H:%M:%S')}"] += 1
                stats[f"session_last_{max(stamps).strftime('%H:%M:%S')}"] += 1
            for session_day, stamps in holdout_session_stamps.items():
                expected = {
                    datetime.combine(session_day, time(9, 15), IST) + timedelta(minutes=i)
                    for i in range(375)
                }
                source["holdout_integrity_only"]["missing_expected_session_minutes"] += len(expected - stamps)
                source["holdout_integrity_only"][f"session_first_{min(stamps).strftime('%H:%M:%S')}"] += 1
                source["holdout_integrity_only"][f"session_last_{max(stamps).strftime('%H:%M:%S')}"] += 1
            source["symbols"][symbol] = {
                **dict(stats),
                "earliest_ist": earliest.isoformat() if earliest else None,
                "latest_ist": latest.isoformat() if latest else None,
                "member": member,
            }
    source["totals"] = dict(source["totals"])
    source["holdout_integrity_only"] = dict(source["holdout_integrity_only"])
    return retained, source


def target_days(data: dict[str, dict[date, list[AuditBar]]]) -> list[date]:
    return sorted({day for symbol in SYMBOLS for day in data[symbol] if QA_START <= day <= VALIDATION_END})


def build_legacy(legacy, data: dict[str, dict[date, list[AuditBar]]], days: list[date]) -> dict[date, list]:
    converted = {
        symbol: {
            day: [legacy.Bar(bar.timestamp, bar.open, bar.high, bar.low, bar.close, bar.volume) for bar in bars]
            for day, bars in sessions.items()
        }
        for symbol, sessions in data.items()
    }
    signals, _ = legacy.build_signals(converted, days)
    return signals


def build_v2(data: dict[str, dict[date, list[AuditBar]]], days: list[date]) -> dict[date, list[AuditSignal]]:
    signals: dict[date, list[AuditSignal]] = defaultdict(list)
    for symbol in SYMBOLS:
        valid_days: list[date] = []
        opening_volumes: dict[date, float] = {}
        for day in sorted(data[symbol]):
            bars = data[symbol][day]
            if valid_opening_v2(bars):
                valid_days.append(day)
                opening_volumes[day] = sum(bar.volume for bar in bars if time(9, 15) <= bar.timestamp.timetz().replace(tzinfo=None) <= time(9, 29))
        for day in days:
            assert_signal_access_allowed(day)
            prior = [opening_volumes[item] for item in valid_days if item < day][-20:]
            signal, _ = v2_signal_for_day(symbol, day, data[symbol].get(day, []), prior)
            if signal:
                signals[day].append(signal)
    for day in signals:
        signals[day].sort(key=lambda item: (item.decision_time, -item.rvol, -item.breakout_distance, item.symbol))
    return signals


def signal_rows(signals: dict[date, list], model: str) -> list[dict]:
    rows = []
    for day in sorted(signals):
        assert_signal_access_allowed(day)
        for rank, signal in enumerate(signals[day], start=1):
            rows.append({
                "model": model,
                "partition": partition(day),
                "date": day.isoformat(),
                "symbol": signal.symbol,
                "direction": signal.direction,
                "decision_timestamp_ist": signal.decision_time.isoformat(),
                "chronological_rank": rank,
            })
    return rows


def compare_rows(legacy_rows: list[dict], v2_rows: list[dict]) -> tuple[list[dict], Counter]:
    legacy = {(row["date"], row["symbol"]): row for row in legacy_rows}
    v2 = {(row["date"], row["symbol"]): row for row in v2_rows}
    differences = []
    counts = Counter({key: 0 for key in ("ADDED_SIGNAL", "REMOVED_SIGNAL", "SHIFTED_SIGNAL", "DIRECTION_CHANGED", "RANK_CHANGED")})
    for key in sorted(set(legacy) | set(v2)):
        left, right = legacy.get(key), v2.get(key)
        kinds = []
        if left is None:
            kinds.append("ADDED_SIGNAL")
        elif right is None:
            kinds.append("REMOVED_SIGNAL")
        else:
            if left["direction"] != right["direction"]:
                kinds.append("DIRECTION_CHANGED")
            if left["decision_timestamp_ist"] != right["decision_timestamp_ist"]:
                kinds.append("SHIFTED_SIGNAL")
            if left["chronological_rank"] != right["chronological_rank"]:
                kinds.append("RANK_CHANGED")
        for kind in kinds:
            counts[kind] += 1
            differences.append({"classification": kind, "date": key[0], "symbol": key[1], "legacy": left, "v2": right})
    return differences, counts


def incomplete_counts(data: dict[str, dict[date, list[AuditBar]]]) -> dict:
    result = Counter()
    for symbol in SYMBOLS:
        for day, bars in data[symbol].items():
            part = partition(day)
            if part is None:
                continue
            _, incomplete = aggregate_v2(bars)
            for start in incomplete:
                result["session_total"] += 1
                if time(9, 15) <= start.timetz().replace(tzinfo=None) <= time(11, 55):
                    result["strategy_window_total"] += 1
                    result[f"{part}_strategy_window"] += 1
    return dict(result)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def count_by_partition(rows: list[dict]) -> dict[str, int]:
    counts = Counter(row["partition"] for row in rows)
    return {name: counts[name] for name in ("QA", "DEVELOPMENT", "VALIDATION")}


def audit(archive: Path, legacy_path: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    archive_sha = sha256_file(archive)
    archive_bytes = archive.stat().st_size
    if archive_sha != EXPECTED_SHA256 or archive_bytes != EXPECTED_BYTES:
        raise RuntimeError(f"source identity mismatch sha={archive_sha} bytes={archive_bytes}")
    data, integrity = parse_archive(archive)
    if integrity["holdout_signal_fields_generated"]:
        raise RuntimeError("holdout isolation invariant violated")
    fatal = sum(integrity["totals"].get(key, 0) for key in ("malformed_timestamp", "malformed_numeric", "invalid_ohlcv", "off_grid"))
    legacy = load_legacy_module(legacy_path)
    days = target_days(data)
    legacy_signals = build_legacy(legacy, data, days)
    v2_signals = build_v2(data, days)
    legacy_rows = signal_rows(legacy_signals, "LEGACY")
    v2_rows = signal_rows(v2_signals, "V2_COMPLETE_BUCKET")
    differences, diff_counts = compare_rows(legacy_rows, v2_rows)
    incomplete = incomplete_counts(data)
    compatibility = "PASS" if sum(diff_counts.values()) == 0 else "FAILED"
    data_integrity = "PASS" if fatal == 0 else "FAILED"
    final_verdict = "COMPATIBILITY_PASS" if compatibility == "PASS" and data_integrity == "PASS" else ("BLOCKED_DATA_INTEGRITY" if data_integrity != "PASS" else "COMPATIBILITY_FAILED")
    manifest = {
        "source_url": SOURCE_URL,
        "release_tag": "v1.0.0",
        "release_asset_id": 410673470,
        "expected_bytes": EXPECTED_BYTES,
        "observed_bytes": archive_bytes,
        "expected_sha256": EXPECTED_SHA256,
        "observed_sha256": archive_sha,
        "sha256_verified": True,
        "documented_source": "Zerodha Kite API via public research archive; not exchange-authoritative",
        "schema_expected": list(EXPECTED_COLUMNS),
        "timestamp_provenance": "Unix seconds interpreted UTC then converted to Asia/Kolkata; interval-start labels supported by README loading example and observed 09:15-15:29 IST session alignment; not exchange-authoritative",
        "permitted_signal_range": [QA_START.isoformat(), VALIDATION_END.isoformat()],
        "sealed_holdout_range": [HOLDOUT_START.isoformat(), HOLDOUT_END.isoformat()],
        "holdout_isolation": "RAW_ROWS_REDUCED_TO_AGGREGATE_INTEGRITY_METADATA; NO_BAR_RETENTION; SIGNAL_ACCESS_GUARD",
        "integrity": integrity,
        "data_integrity_status": data_integrity,
    }
    counts_legacy = count_by_partition(legacy_rows)
    counts_v2 = count_by_partition(v2_rows)
    report = {
        "qa_legacy_signals": counts_legacy["QA"],
        "qa_v2_signals": counts_v2["QA"],
        "development_legacy_signals": counts_legacy["DEVELOPMENT"],
        "development_v2_signals": counts_v2["DEVELOPMENT"],
        "validation_legacy_signals": counts_legacy["VALIDATION"],
        "validation_v2_signals": counts_v2["VALIDATION"],
        "added_signals": diff_counts["ADDED_SIGNAL"],
        "removed_signals": diff_counts["REMOVED_SIGNAL"],
        "shifted_signals": diff_counts["SHIFTED_SIGNAL"],
        "direction_changed": diff_counts["DIRECTION_CHANGED"],
        "rank_changed": diff_counts["RANK_CHANGED"],
        "incomplete_5m_buckets": incomplete,
        "malformed_input_records": fatal,
        "frozen_signal_compatibility": compatibility,
        "holdout_signal_accessed": False,
        "backtest_run": False,
        "pnl_calculated": False,
        "broker_orders": False,
        "final_verdict": final_verdict,
    }
    (out / "source_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (out / "compatibility_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    (out / "differences.json").write_text(json.dumps(differences, indent=2, sort_keys=True), encoding="utf-8")
    fields = ["model", "partition", "date", "symbol", "direction", "decision_timestamp_ist", "chronological_rank"]
    write_csv(out / "legacy_signal_identities.csv", legacy_rows, fields)
    write_csv(out / "v2_signal_identities.csv", v2_rows, fields)
    summary = [
        "PROJECT=KATS-ORB-CASH-EQ-LONG-V2-S0",
        f"SOURCE_SHA256_VERIFIED={str(manifest['sha256_verified']).upper()}",
        f"TIMESTAMP_PROVENANCE={manifest['timestamp_provenance']}",
        "HOLDOUT_ISOLATION=PASS_NO_HOLDOUT_SIGNAL_FIELDS_GENERATED",
        f"QA_LEGACY_SIGNALS={report['qa_legacy_signals']}",
        f"QA_V2_SIGNALS={report['qa_v2_signals']}",
        f"DEVELOPMENT_LEGACY_SIGNALS={report['development_legacy_signals']}",
        f"DEVELOPMENT_V2_SIGNALS={report['development_v2_signals']}",
        f"VALIDATION_LEGACY_SIGNALS={report['validation_legacy_signals']}",
        f"VALIDATION_V2_SIGNALS={report['validation_v2_signals']}",
        f"ADDED_SIGNALS={report['added_signals']}",
        f"REMOVED_SIGNALS={report['removed_signals']}",
        f"SHIFTED_SIGNALS={report['shifted_signals']}",
        f"DIRECTION_CHANGED={report['direction_changed']}",
        f"RANK_CHANGED={report['rank_changed']}",
        f"INCOMPLETE_5M_BUCKETS={incomplete.get('strategy_window_total', 0)}",
        f"FROZEN_SIGNAL_COMPATIBILITY={compatibility}",
        "HOLDOUT_SIGNAL_ACCESSED=NO",
        "BACKTEST_RUN=NO",
        "PNL_CALCULATED=NO",
        "BROKER_ORDERS=NO",
        f"FINAL_VERDICT={final_verdict}",
    ]
    (out / "SUMMARY.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--legacy", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.archive, args.legacy, args.out)
    print((args.out / "SUMMARY.txt").read_text(encoding="utf-8"), end="")
    return 0 if report["final_verdict"] in {"COMPATIBILITY_PASS", "COMPATIBILITY_FAILED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
