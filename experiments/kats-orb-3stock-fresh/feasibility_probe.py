#!/usr/bin/env python3
"""Audit cash-underlying data and official NSE contract masters.

This is a pre-outcome gate.  It does not calculate signals or P&L.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SYMBOLS = ("SBIN", "DLF", "RELIANCE")
REQUIRED_STOCK = {"time", "open", "high", "low", "close", "Volume"}
IST = ZoneInfo("Asia/Kolkata")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def symbol_from_member(member: str) -> str | None:
    name = Path(member).name.upper()
    for symbol in SYMBOLS:
        if name == f"{symbol}_1M.CSV.GZ":
            return symbol
    return None


def inspect_stock_member(zf: zipfile.ZipFile, member: str) -> dict:
    symbol = symbol_from_member(member)
    rows = 0
    malformed = 0
    bad_timestamp = 0
    duplicates = 0
    timestamps: set[int] = set()
    sessions = Counter()
    samples = []
    earliest = latest = None
    with zf.open(member) as compressed:
        with gzip.GzipFile(fileobj=compressed) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
            reader = csv.DictReader(text)
            columns = reader.fieldnames or []
            for row in reader:
                rows += 1
                if len(samples) < 3:
                    samples.append({key: row.get(key) for key in columns})
                try:
                    stamp = int(float(row["time"]))
                    instant = datetime.fromtimestamp(stamp, tz=timezone.utc).astimezone(IST)
                    if stamp in timestamps:
                        duplicates += 1
                    timestamps.add(stamp)
                    earliest = instant if earliest is None or instant < earliest else earliest
                    latest = instant if latest is None or instant > latest else latest
                    sessions[instant.date().isoformat()] += 1
                    o, h, low, c = (float(row[key]) for key in ("open", "high", "low", "close"))
                    volume = float(row["Volume"])
                    if min(o, h, low, c) <= 0 or low > min(o, c, h) or h < max(o, c, low) or volume < 0:
                        malformed += 1
                except (KeyError, TypeError, ValueError, OSError, OverflowError):
                    bad_timestamp += 1
                    malformed += 1
    return {
        "symbol": symbol,
        "member": member,
        "columns": columns,
        "required_present": REQUIRED_STOCK.issubset(columns),
        "rows": rows,
        "duplicates": duplicates,
        "bad_timestamps": bad_timestamp,
        "malformed_ohlcv": malformed,
        "earliest_ist": earliest.isoformat() if earliest else None,
        "latest_ist": latest.isoformat() if latest else None,
        "session_count": len(sessions),
        "session_bar_counts": dict(sorted(sessions.items())),
        "samples": samples,
    }


def inspect_stock_zip(path: Path) -> dict:
    output = {
        "source": "GitHub release voletiramu/nse-fno-1min-data v1.0.0",
        "source_claim": "Zerodha Kite API; research/educational use; as-is",
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "timestamp_rule": "Unix seconds interpreted as UTC then converted to Asia/Kolkata, per source README",
        "symbols": {},
    }
    with zipfile.ZipFile(path) as zf:
        matches = {symbol_from_member(name): name for name in zf.namelist() if symbol_from_member(name)}
        output["archive_members"] = len(zf.namelist())
        output["matched_members"] = matches
        for symbol in SYMBOLS:
            if symbol in matches:
                output["symbols"][symbol] = inspect_stock_member(zf, matches[symbol])
            else:
                output["symbols"][symbol] = {"symbol": symbol, "missing": True}
    return output


def normalized(row: dict[str, str]) -> dict[str, str]:
    return {re.sub(r"[^A-Z0-9]", "", key.upper()): (value or "").strip() for key, value in row.items()}


def inspect_master(path: Path) -> dict:
    result = {"file": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
    try:
        with gzip.open(path, "rt", encoding="utf-8-sig", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            result["columns"] = reader.fieldnames or []
            matches = []
            for source_row in reader:
                row = normalized(source_row)
                joined = "|".join(row.values()).upper()
                if any(symbol in joined for symbol in SYMBOLS) and ("OPTSTK" in joined or "CE" in joined or "PE" in joined):
                    matches.append(source_row)
                    if len(matches) >= 100:
                        break
            result["matching_rows"] = matches
            result["matching_row_count_capped"] = len(matches)
            result["readable"] = True
    except (OSError, csv.Error) as exc:
        result["readable"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stock_zip", type=Path)
    parser.add_argument("--masters", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    output = {
        "purpose": "pre-outcome feasibility gate; no strategy P&L calculated",
        "cash_underlying": inspect_stock_zip(args.stock_zip),
        "nse_contract_masters": [inspect_master(path) for path in sorted(args.masters.glob("*.csv.gz"))],
    }
    output["official_master_files_found"] = len(output["nse_contract_masters"])
    output["all_cash_symbols_present"] = all(
        not output["cash_underlying"]["symbols"][symbol].get("missing", False) for symbol in SYMBOLS
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({
        "stock_zip_sha256": output["cash_underlying"]["sha256"],
        "all_cash_symbols_present": output["all_cash_symbols_present"],
        "official_master_files_found": output["official_master_files_found"],
        "cash_ranges": {
            symbol: [
                output["cash_underlying"]["symbols"][symbol].get("earliest_ist"),
                output["cash_underlying"]["symbols"][symbol].get("latest_ist"),
            ] for symbol in SYMBOLS
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
