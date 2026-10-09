#!/usr/bin/env python3
"""S0 structural data admission only. No strategy or return calculations."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, io, json, math, zipfile
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
EXPECTED_COLUMNS = ["time", "open", "high", "low", "close", "CE Breakout Level", "PE Breakout Level", "Volume"]
PRICE_FIELDS = ("open", "high", "low", "close")
PROHIBITED_HOLDOUT_KEYS = {"signal", "direction", "rank", "entry", "exit", "return", "pnl", "price"}

class HoldoutAccessError(RuntimeError): pass

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()

def to_ist(value: str) -> datetime:
    return datetime.fromtimestamp(int(float(value)), tz=timezone.utc).astimezone(IST)

def partition(d: date, parts: dict) -> str:
    for name, (start, end) in parts.items():
        if date.fromisoformat(start) <= d <= date.fromisoformat(end): return name
    return "outside"

def assert_strategy_access_allowed(d: date, parts: dict) -> None:
    if partition(d, parts) == "sealed_holdout":
        raise HoldoutAccessError("sealed holdout strategy access denied")

def valid_ohlcv(o: float, h: float, l: float, c: float, v: float) -> bool:
    return all(math.isfinite(x) for x in (o,h,l,c,v)) and l <= min(o,c) <= max(o,c) <= h and v >= 0

def expected_session_minutes(d: date) -> set[int]:
    start = datetime.combine(d, time(9,15), IST)
    return {int((start + timedelta(minutes=i)).timestamp()) for i in range(375)}

def locate_members(zf: zipfile.ZipFile, symbols: list[str]) -> dict[str,str|None]:
    by_base = {Path(n).name.upper(): n for n in zf.namelist() if not n.endswith("/")}
    return {s: next((by_base[x] for x in (f"{s}_1M.CSV.GZ", f"{s}.CSV.GZ", f"{s}_1M.CSV") if x in by_base), None) for s in symbols}

def audit_member(zf: zipfile.ZipFile, member: str, parts: dict) -> dict:
    compressed = zf.read(member)
    result = {"member": member, "member_sha256": hashlib.sha256(compressed).hexdigest(),
              "compressed_bytes": len(compressed), "rows": 0, "schema": [], "schema_ok": False,
              "timestamp_unit": "unix_seconds", "timezone_interpretation": "UTC epoch converted to Asia/Kolkata",
              "earliest_ist": None, "latest_ist": None, "duplicates": 0, "nonfinite_or_parse_errors": 0,
              "invalid_ohlcv": 0, "off_grid": 0, "outside_session": 0,
              "partitions": {p:{"rows":0,"sessions":0,"incomplete_sessions":0,"missing_minutes":0} for p in parts}}
    seen, sessions = set(), defaultdict(set)
    raw = gzip.GzipFile(fileobj=io.BytesIO(compressed)) if member.lower().endswith(".gz") else io.BytesIO(compressed)
    with raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as txt:
        reader = csv.DictReader(txt)
        result["schema"] = reader.fieldnames or []
        result["schema_ok"] = result["schema"] == EXPECTED_COLUMNS
        if not result["schema_ok"]: return result
        first = last = None
        for row in reader:
            result["rows"] += 1
            try:
                dt = to_ist(row["time"]); ts = int(dt.timestamp())
                vals = [float(row[k]) for k in PRICE_FIELDS] + [float(row["Volume"])]
            except (ValueError, TypeError, OverflowError):
                result["nonfinite_or_parse_errors"] += 1; continue
            first = dt if first is None or dt < first else first
            last = dt if last is None or dt > last else last
            if ts in seen: result["duplicates"] += 1
            seen.add(ts)
            if dt.second or dt.microsecond: result["off_grid"] += 1
            if not valid_ohlcv(*vals): result["invalid_ohlcv"] += 1
            p = partition(dt.date(), parts)
            if p in parts:
                result["partitions"][p]["rows"] += 1
                sessions[(p, dt.date())].add(ts)
            if not (time(9,15) <= dt.time().replace(tzinfo=None) <= time(15,29)):
                result["outside_session"] += 1
        result["earliest_ist"] = first.isoformat() if first else None
        result["latest_ist"] = last.isoformat() if last else None
    for (p,d), stamps in sessions.items():
        miss = len(expected_session_minutes(d) - stamps)
        result["partitions"][p]["sessions"] += 1
        result["partitions"][p]["missing_minutes"] += miss
        result["partitions"][p]["incomplete_sessions"] += int(miss != 0)
    return result

def ensure_holdout_safe(obj) -> None:
    def walk(x, path=""):
        if isinstance(x, dict):
            for k,v in x.items():
                if "sealed_holdout" in path and any(t in k.lower() for t in PROHIBITED_HOLDOUT_KEYS):
                    raise AssertionError(f"prohibited holdout field: {path}/{k}")
                walk(v, path+"/"+k)
        elif isinstance(x, list):
            for v in x: walk(v,path)
    walk(obj)

def render_report(m: dict) -> str:
    lines = ["# S0 11-stock source-data admission report", "", "This report contains structural integrity metadata only. No ORB, RVOL, signals, rankings, entries, exits, returns or P&L were calculated.", "",
             f"- Archive SHA-256 verified: **{m['archive_hash_verified']}**", f"- Members found: **{m['members_found']}/11**", f"- Timestamp interpretation: **{m['timestamp_provenance']}**", "",
             "| Symbol | Member | Rows | Schema | Duplicates | Invalid/parse | Off-grid | Missing minutes (QA/DEV/VAL/HOLDOUT) | Admission |",
             "|---|---:|---:|---|---:|---:|---:|---|---|"]
    for s,x in m["symbols"].items():
        if not x: lines.append(f"| {s} | NO | 0 | FAIL | - | - | - | - | BLOCKED | "); continue
        pm = "/".join(str(x["partitions"][p]["missing_minutes"]) for p in ("qa","development","validation","sealed_holdout"))
        bad=x["nonfinite_or_parse_errors"]+x["invalid_ohlcv"]
        admission="ADMITTED_WITH_RECORDED_GAPS" if x["schema_ok"] and not bad and not x["off_grid"] else "BLOCKED"
        lines.append(f"| {s} | YES | {x['rows']} | {'PASS' if x['schema_ok'] else 'FAIL'} | {x['duplicates']} | {bad} | {x['off_grid']} | {pm} | {admission} |")
    lines += ["", "## Membership and corporate-action status", "", "- RELIANCE: official 1:1 bonus evidence identified; archive price-basis reconciliation remains required before scoring.", "- TATAMOTORS: no exact TATAMOTORS archive member was found; the 2025 demerger and TATAMOTORS→TMPV identity/price-basis continuity also remains unresolved. No substitute was used.", "- Other candidates: date-effective official eligibility and exhaustive corporate-action reconciliation remain required.", "", "## Official daily cross-check", "", "UNRESOLVED: no exchange daily files are embedded in this data-only artifact. Primary daily reconciliation must pass before scoring.", "", "## Separate execution blocker", "", "ENTRY_TIMING_CLARIFICATION=REQUIRED_BEFORE_SIMULATION. The diagnostic reference must occur after S_c = E_c + delta_order; submission cutoff and later diagnostic-price timestamp remain unresolved. S0 does not simulate entries.", "", f"FINAL_VERDICT={m['verdict']}", ""]
    return "\n".join(lines)

def run(archive: Path, expected: Path, out: Path) -> dict:
    cfg=json.loads(expected.read_text()); digest=sha256_file(archive)
    if digest != cfg["archive_sha256"]: raise SystemExit(f"archive SHA mismatch: {digest}")
    with zipfile.ZipFile(archive) as zf:
        found=locate_members(zf,cfg["symbols"])
        symbols={s:(audit_member(zf,n,cfg["partitions"]) if n else None) for s,n in found.items()}
    blocked=[s for s,x in symbols.items() if x is None or not x["schema_ok"] or x["nonfinite_or_parse_errors"] or x["invalid_ohlcv"] or x["off_grid"]]
    manifest={"hypothesis":"KATS-ORB-CASH-EQ-11STOCK-LONG-V1","scope":"S0_DATA_ONLY","archive_url":cfg["archive_url"],"archive_sha256":digest,
              "archive_hash_verified":True,"archive_bytes":archive.stat().st_size,"members_found":sum(x is not None for x in symbols.values()),
              "timestamp_provenance":"Unix-second epoch interpreted UTC then converted to Asia/Kolkata; interval-label semantics require independent source confirmation",
              "symbols":symbols,"partitions":cfg["partitions"],"corporate_actions":cfg["corporate_actions"],
              "nse_daily_crosscheck_status":"UNRESOLVED_PRIMARY_DAILY_RECONCILIATION_NOT_EXECUTED",
              "entry_timing_clarification":"REQUIRED_BEFORE_SIMULATION","signals_generated":False,"pnl_calculated":False,
              "holdout_strategy_data_accessed":False,"verdict":"S0_BLOCKED_DATA_INTEGRITY" if blocked else "S0_DATA_ADMISSION_PARTIAL"}
    ensure_holdout_safe(manifest); out.mkdir(parents=True,exist_ok=True)
    (out/"SOURCE_MANIFEST.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    (out/"DATA_ADMISSION_REPORT.md").write_text(render_report(manifest))
    return manifest

def main():
    p=argparse.ArgumentParser(); p.add_argument("archive",type=Path); p.add_argument("--expected",type=Path,required=True); p.add_argument("--out",type=Path,required=True)
    m=run(**vars(p.parse_args())); print(json.dumps({"members_found":m["members_found"],"verdict":m["verdict"]},sort_keys=True))
if __name__=="__main__": main()
