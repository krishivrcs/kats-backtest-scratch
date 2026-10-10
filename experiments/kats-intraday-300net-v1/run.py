"""Execute fixed KATS INR 300 net intraday experiment; no broker operations."""
import argparse
import csv
import json
from pathlib import Path
import system

def save_csv(path,records):
    if not records:
        path.write_text("",encoding="utf-8")
        return
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

def report(out,partition,setups,base,base_rej,adverse,adverse_rej):
    save_csv(out/f"{partition}_trades.csv",base)
    save_csv(out/f"{partition}_adverse_trades.csv",adverse)
    save_csv(out/f"{partition}_rejects.csv",base_rej)
    save_csv(out/f"{partition}_adverse_rejects.csv",adverse_rej)
    return {"signals":len(setups),"base":system.metrics(base),"adverse":system.metrics(adverse)}

def execute_partition(raw,start,end,out,name):
    setups=system.generate_setups(raw,start,end)
    base,rej=system.run_portfolio(raw,setups,5.)
    stress,rej_stress=system.run_portfolio(raw,setups,15.)
    return report(out,name,setups,base,rej,stress,rej_stress)

def main():
    a=argparse.ArgumentParser()
    a.add_argument("archive",type=Path)
    a.add_argument("--out",required=True,type=Path)
    args=a.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    raw,dev_manifest,exclude=system.reversal.load_until(args.archive,system.DEV_END)
    d=execute_partition(raw,system.DEV_START,system.DEV_END,args.out,"development")
    (args.out/"development_manifest.json").write_text(json.dumps(dev_manifest,indent=2)+"\n")
    save_csv(args.out/"development_source_exclusions.csv",exclude)
    result={"id":"KATS-INTRADAY-300NET-V1","date":"2026-10-10",
       "capital":system.START_CAPITAL,"planned_risk_cap":200.,
       "net_winning_trade_target":300.,"real_orders":"NONE",
       "source_archive_sha256":system.infra.ARCHIVE_SHA256,
       "development":d,"validation":"NOT_ACCESSED",
       "verdict":"REJECT_DEVELOPMENT","reason":None}
    if system.dev_pass(d["base"],d["adverse"]):
        val_data,val_manifest,val_exclusion=system.reversal.load_until(args.archive,system.VAL_END)
        v=execute_partition(val_data,system.VAL_START,system.VAL_END,args.out,"validation")
        (args.out/"validation_manifest.json").write_text(json.dumps(val_manifest,indent=2)+"\n")
        save_csv(args.out/"validation_source_exclusions.csv",val_exclusion)
        result["validation"]=v
        result["verdict"]=("PROMISING_REQUIRES_INDEPENDENT_EXECUTION_REVIEW"
                           if system.val_pass(v["base"],v["adverse"]) else "REJECT_VALIDATION")
    else:
        result["reason"]="DEVELOPMENT_GATE_FAILED_NO_VALIDATION_ACCESS"
    # Days with zero trades must be visible and must NOT count toward daily income.
    for name in ("development","validation"):
        if name not in result or not isinstance(result[name],dict):continue
        start,end=((system.DEV_START,system.DEV_END) if name=="development"
                   else (system.VAL_START,system.VAL_END))
        n=len({day for sym in system.SYMBOLS for day in
            (raw if name=="development" else val_data)[sym] if start<=day<=end})
        for case in ("base","adverse"):
            result[name][case]["admitted_trading_sessions"]=n
            result[name][case]["no_trade_days"]=n-result[name][case]["trades"]
            result[name][case]["realized_average_net_per_trading_session"]=(result[name][case]["net_pnl"]/n if n else None)
    (args.out/"results.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps(result,sort_keys=True,allow_nan=False))

if __name__=="__main__":
    main()
