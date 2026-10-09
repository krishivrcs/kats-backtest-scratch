#!/usr/bin/env python3
"""Stream-probe a public Kaggle NSE F&O ZIP without retaining raw data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

REQUIRED = {"Ticker", "Date", "Time", "Open", "High", "Low", "Close", "Volume"}
SYMBOLS = ("SBIN", "DLF", "RELIANCE")
OPTION_RE = re.compile(r"(?:^|[^A-Z])(SBIN|DLF|RELIANCE).*?(\d+(?:\.\d+)?)(CE|PE)(?:\.|$)", re.I)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_timestamp(date_text: str, time_text: str) -> datetime | None:
    value = f"{date_text.strip()} {time_text.strip()}"
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def probe_csv(zf: zipfile.ZipFile, member: str) -> dict:
    rows = 0
    malformed = 0
    bad_timestamp = 0
    earliest = None
    latest = None
    dates = set()
    matching = {symbol: set() for symbol in SYMBOLS}
    samples = []
    option_types = Counter()
    with zf.open(member) as raw:
        import io
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
        reader = csv.DictReader(text)
        columns = reader.fieldnames or []
        for row in reader:
            rows += 1
            ticker = (row.get("Ticker") or "").strip().upper()
            if len(samples) < 3:
                samples.append({k: row.get(k) for k in columns})
            for symbol in SYMBOLS:
                if symbol in ticker and len(matching[symbol]) < 200:
                    matching[symbol].add(ticker)
            match = OPTION_RE.search(ticker)
            if match:
                option_types[match.group(3).upper()] += 1
            timestamp = parse_timestamp(row.get("Date", ""), row.get("Time", ""))
            if timestamp is None:
                bad_timestamp += 1
            else:
                earliest = timestamp if earliest is None or timestamp < earliest else earliest
                latest = timestamp if latest is None or timestamp > latest else latest
                dates.add(timestamp.date().isoformat())
            try:
                o, h, low, c = (float(row[name]) for name in ("Open", "High", "Low", "Close"))
                vol = float(row["Volume"])
                if min(o, h, low, c) < 0 or low > min(o, c, h) or h < max(o, c, low) or vol < 0:
                    malformed += 1
            except (KeyError, TypeError, ValueError):
                malformed += 1
    return {
        "member": member,
        "columns": columns,
        "required_present": REQUIRED.issubset(columns),
        "rows": rows,
        "earliest_naive": earliest.isoformat(sep=" ") if earliest else None,
        "latest_naive": latest.isoformat(sep=" ") if latest else None,
        "dates": sorted(dates),
        "bad_timestamps": bad_timestamp,
        "malformed_ohlcv": malformed,
        "matching_tickers": {k: sorted(v) for k, v in matching.items()},
        "option_like_rows": dict(option_types),
        "samples": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    output = {
        "source": "Kaggle kaalicharan9080/nse-future-and-options-data version 2",
        "license_claim": "CC0: Public Domain (as displayed by Kaggle)",
        "download_bytes": args.zip_path.stat().st_size,
        "download_sha256": sha256_file(args.zip_path),
        "timezone": "UNKNOWN_SOURCE_SEMANTICS; naive Date+Time observed",
        "members": [],
    }
    with zipfile.ZipFile(args.zip_path) as zf:
        members = sorted(n for n in zf.namelist() if n.lower().endswith(".csv"))
        output["zip_members"] = [{"name": n, "bytes": zf.getinfo(n).file_size, "crc32": f"{zf.getinfo(n).CRC:08x}"} for n in members]
        for member in members:
            output["members"].append(probe_csv(zf, member))
    output["required_symbols_have_matching_tickers"] = {
        symbol: any(m["matching_tickers"][symbol] for m in output["members"]) for symbol in SYMBOLS
    }
    output["actual_option_rows_detected"] = sum(
        sum(m["option_like_rows"].values()) for m in output["members"]
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "bytes": output["download_bytes"],
        "sha256": output["download_sha256"],
        "csv_members": len(output["members"]),
        "symbol_coverage": output["required_symbols_have_matching_tickers"],
        "actual_option_rows_detected": output["actual_option_rows_detected"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

