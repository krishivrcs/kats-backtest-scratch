#!/usr/bin/env python3
"""Public-catalogue audit for untouched NSE stock-option minute data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

DEV_START = "2024-10-15"
DEV_END = "2024-10-31"
REQUIRED = ("SBIN", "DLF", "RELIANCE")


def get_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "KATS-research-source-audit/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def existing_archive(path: Path) -> dict:
    dates = []
    schemas = []
    with zipfile.ZipFile(path) as zf:
        csv_members = [name for name in zf.namelist() if name.lower().endswith(".csv")]
        for member in csv_members:
            with zf.open(member) as raw:
                text = raw.readline().decode("utf-8-sig", errors="replace").strip()
                first = raw.readline().decode("utf-8-sig", errors="replace").strip()
                schemas.append(text)
                if first:
                    row = next(csv.DictReader([text, first]))
                    value = row.get("Date", "").strip()
                    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                        try:
                            dates.append(datetime.strptime(value, fmt).date().isoformat()); break
                        except ValueError:
                            pass
    unique = sorted(set(dates))
    return {
        "sha256": sha256(path), "bytes": path.stat().st_size, "csv_members": len(csv_members),
        "session_dates": unique, "date_range": [unique[0], unique[-1]] if unique else None,
        "schema_headers": sorted(set(schemas)),
        "untouched_sessions": [day for day in unique if not (DEV_START <= day <= DEV_END)],
    }


def kaggle_search() -> list[dict]:
    queries = ["NSE options minute", "NSE F&O 1 minute", "Indian stock options intraday",
               "SBIN options historical", "NSE stock options"]
    refs = {}
    for query in queries:
        url = "https://www.kaggle.com/api/v1/datasets/list?" + urllib.parse.urlencode({"search": query, "page": 1})
        try:
            values = get_json(url)
        except Exception as error:
            refs[f"ERROR:{query}"] = {"error": repr(error), "query": query}
            continue
        for value in values:
            ref = value.get("ref") or f"UNKNOWN:{value.get('title')}"
            refs.setdefault(ref, value)
    rows = []
    for ref, value in refs.items():
        if ref.startswith("ERROR:"):
            rows.append({"catalogue": "KAGGLE", "reference": ref, "status": "QUERY_ERROR",
                         "details": value["error"]}); continue
        details = value
        try:
            details = get_json(f"https://www.kaggle.com/api/v1/datasets/view/{ref}")
        except Exception:
            pass
        files = details.get("resources") or details.get("files") or []
        file_text = " ".join(str(item.get("name") or item.get("path") or "") for item in files)
        text = " ".join(str(details.get(key, "")) for key in ("title", "subtitle", "description")) + " " + file_text
        lower = text.lower()
        symbols = [symbol for symbol in REQUIRED if symbol.lower() in lower]
        option_words = "option" in lower or "f&o" in lower or "fno" in lower
        minute_words = "minute" in lower or "1min" in lower or "1-min" in lower
        status = "POTENTIAL_FILE_PROBE_REQUIRED" if option_words and minute_words else "REJECT_METADATA_MISMATCH"
        rows.append({
            "catalogue": "KAGGLE", "reference": ref, "title": details.get("title"),
            "status": status, "matched_required_symbols": ",".join(symbols),
            "size_bytes": details.get("totalBytes") or details.get("size"),
            "last_updated": details.get("lastUpdated") or details.get("updated"),
            "license": details.get("licenseName"), "file_count": len(files),
            "file_names_sample": file_text[:2000],
        })
    return rows


def huggingface_search() -> list[dict]:
    rows = []
    try:
        values = get_json("https://huggingface.co/api/datasets?search=nse%20options&limit=100")
    except Exception as error:
        return [{"catalogue": "HUGGINGFACE", "reference": "QUERY", "status": "QUERY_ERROR",
                 "details": repr(error)}]
    for value in values:
        ref = value.get("id")
        card = ""
        siblings = []
        try:
            detail = get_json(f"https://huggingface.co/api/datasets/{ref}")
            card = str(detail.get("cardData") or "")
            siblings = [item.get("rfilename", "") for item in detail.get("siblings", [])]
        except Exception:
            detail = value
        text = (ref + " " + card + " " + " ".join(siblings)).lower()
        symbols = [symbol for symbol in REQUIRED if symbol.lower() in text]
        stock_scope = bool(symbols) or "stock option" in text
        option_scope = "option" in text
        minute_scope = "1m" in text or "minute" in text
        status = "POTENTIAL_FILE_PROBE_REQUIRED" if stock_scope and option_scope and minute_scope else "REJECT_INDEX_OR_NONOPTION_SCOPE"
        rows.append({"catalogue": "HUGGINGFACE", "reference": ref, "status": status,
                     "matched_required_symbols": ",".join(symbols), "file_count": len(siblings),
                     "file_names_sample": " ".join(siblings[:30])})
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("existing_option_zip", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    existing = existing_archive(args.existing_option_zip)
    candidates = kaggle_search() + huggingface_search()
    known = [
        {"source": "voletiramu/nse-fno-1min-data", "status": "REJECT_UNDERLYING_ONLY"},
        {"source": "rissin/nse-options-intraday", "status": "REJECT_INDEX_OPTIONS_ONLY"},
        {"source": "thetrademarkk/india-index-options-1m", "status": "REJECT_INDEX_OPTIONS_ONLY"},
        {"source": "QuantDev-stack/OptionVault", "status": "REJECT_FULL_DATA_LICENSED_PAID"},
        {"source": "djjain21/NSE-Futures-Options-F-O-Historical-Dataset-1minute-from-2015-2026", "status": "REJECT_FULL_DATA_PAID"},
        {"source": "Upstox expired-instruments historical candles", "status": "REJECT_PLUS_PLAN_REQUIRED"},
    ]
    potential = [row for row in candidates if row.get("status") == "POTENTIAL_FILE_PROBE_REQUIRED"]
    result = {
        "project": "KATS-ORB-CAPITAL-AWARE-UNTOUCHED-VALIDATION",
        "base_commit": "5e90960ebe858a5b2ccdaf93188f63af62363ad3",
        "required_symbols": REQUIRED, "required_granularity": "1_MINUTE_ACTUAL_OPTIONS",
        "development_exclusion": [DEV_START, DEV_END], "existing_archive": existing,
        "known_source_dispositions": known, "catalogue_candidates": len(candidates),
        "potential_file_probes": potential,
        "admission_status": "PENDING_CANDIDATE_FILE_PROBE" if potential else "BLOCKED_NO_ADMISSIBLE_FREE_SOURCE",
        "pnl_calculated": False,
    }
    write_csv(args.out / "catalogue_candidates.csv", candidates)
    (args.out / "source_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"existing_archive": existing, "catalogue_candidates": len(candidates),
                      "potential_file_probes": len(potential), "admission_status": result["admission_status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

