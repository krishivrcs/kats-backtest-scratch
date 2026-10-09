#!/usr/bin/env python3
"""S0-R1 outcome-blind source recovery and structural integrity audit."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, io, json, math, zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

IST=ZoneInfo("Asia/Kolkata")
HOLDOUT_START="2025-11-01"
TARGETS=("HDFCBANK","ICICIBANK","HAL")
EXPECTED_ARCHIVE_SHA="20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2"

def digest(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def strict_valid(o,h,l,c,v):
    values=(o,h,l,c,v)
    return (all(math.isfinite(x) for x in values) and all(x>0 for x in (o,h,l,c))
            and v>=0 and l<=min(o,c) and max(o,c)<=h)

def legacy_valid(o,h,l,c,v):
    return all(math.isfinite(x) for x in (o,h,l,c,v)) and l<=min(o,c)<=max(o,c)<=h and v>=0

def parse_member(zf:zipfile.ZipFile,name:str):
    raw=zf.read(name)
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz, io.TextIOWrapper(gz,encoding="utf-8-sig",newline="") as txt:
        yield from csv.DictReader(txt)

def inspect_member(zf,name):
    defects=[]; additional=defaultdict(int); previous=None; order_violations=0; malformed=0
    for rowno,row in enumerate(parse_member(zf,name),2):
        try:
            ts=int(float(row["time"])); dt=datetime.fromtimestamp(ts,tz=timezone.utc).astimezone(IST)
            o,h,l,c,v=(float(row[x]) for x in ("open","high","low","close","Volume"))
        except Exception:
            malformed+=1; continue
        part="sealed_holdout" if dt.date().isoformat()>=HOLDOUT_START else "pre_holdout"
        if previous is not None and ts<=previous: order_violations+=1
        previous=ts
        if not legacy_valid(o,h,l,c,v):
            if part=="pre_holdout":
                defects.append({"row":rowno,"timestamp_ist":dt.isoformat(),"structural_values":{"open":o,"high":h,"low":l,"close":c,"volume":v},"reason":reason(o,h,l,c,v)})
            else: additional["holdout_legacy_invalid"]+=1
        if legacy_valid(o,h,l,c,v) and not strict_valid(o,h,l,c,v):
            additional[f"{part}_nonpositive_ohlc"]+=1
    return {"legacy_defects_permitted":defects,"aggregate_additional_anomalies":dict(additional),"out_of_order_or_duplicate_steps":order_violations,"malformed_rows":malformed}

def structural_member(zf,name):
    raw=zf.read(name); first=last=None; rows=0
    for row in parse_member(zf,name):
        try: dt=datetime.fromtimestamp(int(float(row["time"])),tz=timezone.utc).astimezone(IST)
        except Exception: continue
        rows+=1; first=dt if first is None else min(first,dt); last=dt if last is None else max(last,dt)
    return {"member":name,"member_sha256":hashlib.sha256(raw).hexdigest(),"compressed_bytes":len(raw),"rows":rows,
            "earliest_ist":first.isoformat() if first else None,"latest_ist":last.isoformat() if last else None,
            "status":"STRUCTURAL_METADATA_ONLY_NOT_ADMITTED_AS_TATAMOTORS"}

def official_daily(path):
    if not path or not path.exists(): return {"status":"UNAVAILABLE"}
    with zipfile.ZipFile(path) as z:
        n=next(n for n in z.namelist() if n.lower().endswith(".csv"))
        with z.open(n) as f, io.TextIOWrapper(f,encoding="utf-8-sig") as txt:
            rows=list(csv.DictReader(txt))
    out={}
    for row in rows:
        sym=(row.get("SYMBOL") or row.get("TckrSymb") or "").strip()
        if sym in TARGETS and (row.get("SERIES") or row.get("SctySrs") or "EQ").strip()=="EQ":
            out[sym]={k:row.get(k) for k in ("OPEN","HIGH","LOW","CLOSE","TOTTRDQTY","TIMESTAMP") if k in row}
    return {"status":"OFFICIAL_DAILY_OBTAINED_NOT_MINUTE_CORROBORATION","date":"2024-06-25","records":out,
            "limitation":"Daily OHLCV cannot establish the disputed 09:15 minute values."}

def reason(o,h,l,c,v):
    r=[]
    if not all(math.isfinite(x) for x in (o,h,l,c,v)): r.append("NONFINITE")
    if any(x<=0 for x in (o,h,l,c)): r.append("NONPOSITIVE_OHLC")
    if v<0: r.append("NEGATIVE_VOLUME")
    if l>min(o,c) or max(o,c)>h: r.append("INVALID_HIGH_LOW_RELATIONSHIP")
    return r

def run(archive:Path,master:Path|None,bhavcopy:Path|None,out:Path):
    sha=digest(archive)
    if sha!=EXPECTED_ARCHIVE_SHA: raise SystemExit("archive hash mismatch")
    with zipfile.ZipFile(archive) as zf:
        basenames={Path(n).name.upper():n for n in zf.namelist()}
        exact_tata=basenames.get("TATAMOTORS_1M.CSV.GZ")
        near=sorted(k for k in basenames if "TATA" in k or "TMPV" in k)
        tmpv_meta=structural_member(zf,basenames["TMPV_1M.CSV.GZ"]) if "TMPV_1M.CSV.GZ" in basenames else None
        members={s:basenames[f"{s}_1M.CSV.GZ"] for s in TARGETS}
        defects={s:inspect_member(zf,n) for s,n in members.items()}
    instruments=[]
    if master and master.exists():
        with gzip.open(master,"rt",encoding="utf-8") as f: data=json.load(f)
        instruments=[{k:x.get(k) for k in ("trading_symbol","name","isin","instrument_key","instrument_type","segment","exchange_token")}
                     for x in data if x.get("segment")=="NSE_EQ" and x.get("trading_symbol") in {"TATAMOTORS","TMPV","TMCV"}]
    result={"scope":"S0_R1_SOURCE_RECOVERY_ONLY","archive_sha256":sha,"archive_verified":True,
            "tatamotors_exact_member":exact_tata,"archive_tata_near_names":near,"tmpv_archive_member":tmpv_meta,"upstox_current_instrument_records":instruments,
            "upstox_historical_probe":"AUTH_REQUIRED_NOT_EXECUTED","zerodha_historical_probe":"AUTH_REQUIRED_NOT_EXECUTED",
            "defects":defects,"official_nse_daily":official_daily(bhavcopy),"positive_ohlc_kernel":"LEGACY_GAP_CONFIRMED_STRICT_KERNEL_TESTED_SEPARATELY",
            "timestamp_ordering_kernel":"LEGACY_GAP_CONFIRMED_SOURCE_ORDER_COUNTS_RECORDED",
            "signals_generated":False,"pnl_calculated":False,"holdout_strategy_output_accessed":False}
    out.mkdir(parents=True,exist_ok=True)
    (out/"RECOVERY_EVIDENCE.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result

def main():
    p=argparse.ArgumentParser(); p.add_argument("archive",type=Path); p.add_argument("--master",type=Path); p.add_argument("--bhavcopy",type=Path); p.add_argument("--out",type=Path,required=True)
    r=run(**vars(p.parse_args())); print(json.dumps({"tatamotors_exact_member":r["tatamotors_exact_member"],"defect_counts":{s:len(x["legacy_defects_permitted"]) for s,x in r["defects"].items()}},sort_keys=True))
if __name__=="__main__": main()
