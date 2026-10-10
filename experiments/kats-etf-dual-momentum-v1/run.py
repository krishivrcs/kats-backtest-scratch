"""KATS-ETF-DUAL-MOMENTUM-V1. Frozen rule implementation. Research only."""
import argparse
import csv
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

SYMS=("NIFTYBEES","GOLDBEES")
START,CUTOFF="2022-01-01","2025-10-31"
BASE=20000.0

def read_prices(path,spot_file):
    out={}
    for sym in SYMS:
        src=path/f"{sym}.csv"
        if not src.exists():raise ValueError("DATA_BLOCKED_SOURCE_MISSING:"+sym)
        rows=list(csv.DictReader(src.open(encoding="utf-8")))
        d={}
        for r in rows:
            day=r["date"][:10]
            if not START<=day<=CUTOFF:continue
            v={key:float(r[key]) for key in ("open","high","low","close","volume")}
            if day in d:raise ValueError("DATA_BLOCKED_DUPLICATE_DATE")
            if any(not math.isfinite(x) for x in v.values()):raise ValueError("DATA_BLOCKED_NAN")
            if v["volume"]<=0:continue  # Yahoo synthetic nontrading rows
            if min(v["open"],v["close"],v["high"],v["low"])<=0:raise ValueError("DATA_BLOCKED_PRICE")
            if v["high"]+1e-5<max(v["open"],v["close"],v["low"]):raise ValueError("DATA_BLOCKED_OHLC_HI")
            if v["low"]-1e-5>min(v["open"],v["close"],v["high"]):raise ValueError("DATA_BLOCKED_OHLC_LO")
            d[day]=v
        out[sym]=d
    common=sorted(set(out[SYMS[0]])&set(out[SYMS[1]]))
    if len(common)<750:raise ValueError(f"DATA_BLOCKED_TOO_FEW_COMMON:{len(common)}")
    checks=json.loads(Path(spot_file).read_text())["rows"]
    for r in checks:
        y=out[r["symbol"]].get(r["date"])
        if y is None:raise ValueError("DATA_BLOCKED_SPOT_MISSING:"+r["symbol"]+":"+r["date"])
        diffs={k:abs(float(y[k])-float(r[k])) for k in ("open","high","low","close")}
        vdiff=abs(y["volume"]-float(r["volume"]))/float(r["volume"])
        if max(diffs.values())>.15+1e-9 or vdiff>.05:
            raise ValueError("DATA_BLOCKED_NSE_SPOT_DISAGREEMENT:"+str((r["symbol"],r["date"],diffs,vdiff)))
    for sym in SYMS:
        previous=None
        for day in common:
            p=out[sym][day]["close"]
            if previous and abs(p/previous-1)>.15:
                raise ValueError("DATA_BLOCKED_DISCONTINUITY:"+sym+":"+day)
            previous=p
    return common,out

def signal(idx,dates,data):
    if idx<199:return None
    ranks=[]
    for sym in SYMS:
        prices=[data[sym][d]["close"] for d in dates[idx-199:idx+1]]
        mom=prices[-1]/prices[-127]-1
        avg=sum(prices)/200
        if prices[-1]>avg and mom>0:ranks.append((-mom,sym))
    return sorted(ranks)[0][1] if ranks else None

def price(raw,buy,bps):
    # Conservative 1-paisa rounding in direction of adverse execution.
    p=raw*(1+(1 if buy else -1)*bps/10000)
    return (math.ceil(p*100-1e-8) if buy else math.floor(p*100+1e-8))/100

def fees(symbol,p,q,buy):
    amount=p*q
    exchange=amount*.0000307
    sebi=amount*.000001
    gst=.18*(exchange+sebi)
    stamp=amount*.00015 if buy else 0
    stt=0 if buy or symbol=="GOLDBEES" else amount*.00001
    dp=0 if buy else 15.34
    return exchange+sebi+gst+stamp+stt+dp

def simulate(start,end,bps,dates,data):
    startidx=next(i for i,d in enumerate(dates) if d>=start)
    endidx=max(i for i,d in enumerate(dates) if d<=end)
    cash=BASE; held=None; quantity=0; entryprice=0; entryfees=0; entryday=""
    peak=BASE; dd=0; trades=[]; ledger=[]; curve=[]; chosen_intervals=0
    for i in range(startidx,endidx+1):
        day=dates[i]
        final=i==endidx
        monthly=i==startidx or (i>startidx and day[:7]!=dates[i-1][:7])
        if monthly and not final:chosen_intervals+=1
        if monthly or final:
            wanted=None if final else signal(i-1,dates,data)
            if held!=wanted:
                if held:
                    outprice=price(data[held][day]["open"],False,bps)
                    exitfees=fees(held,outprice,quantity,False)
                    gross=(outprice-entryprice)*quantity
                    net=gross-entryfees-exitfees
                    cash+=outprice*quantity-exitfees
                    trades.append({"symbol":held,"entry":entryday,"exit":day,
                      "qty":quantity,"entryprice":entryprice,"exitprice":outprice,
                      "gross":gross,"fees":entryfees+exitfees,"net":net})
                    ledger.append({"date":day,"action":"SELL","symbol":held,"qty":quantity,"price":outprice,
                                   "fees":exitfees,"cash":cash})
                    held=None;quantity=0;entryfees=0
                if wanted:
                    inprice=price(data[wanted][day]["open"],True,bps)
                    q=int(cash//inprice)
                    while q>0 and q*inprice+fees(wanted,inprice,q,True)>cash+1e-8:q-=1
                    if q>0:
                        entryfees=fees(wanted,inprice,q,True)
                        cash-=q*inprice+entryfees
                        entryprice=inprice;held=wanted;quantity=q;entryday=day
                        ledger.append({"date":day,"action":"BUY","symbol":held,"qty":quantity,"price":entryprice,
                                       "fees":entryfees,"cash":cash})
        if cash < -1e-6:raise AssertionError("NEGATIVE_CASH")
        equity=cash+quantity*data[held][day]["close"] if held else cash
        peak=max(peak,equity);dd=max(dd,1-equity/peak)
        curve.append((day,equity))
    if held:raise AssertionError("UNCLOSED_END")
    pnl=cash-BASE
    if abs(sum(t["net"] for t in trades)-pnl)>1e-6:raise AssertionError("TRADE_CASH_RECONCILIATION_FAIL")
    winners=sum(t["net"] for t in trades if t["net"]>0)
    losers=-sum(t["net"] for t in trades if t["net"]<0)
    years={}
    for d,e in curve: years[d[:4]]=e
    prev=BASE; year_returns={}
    for y,e in sorted(years.items()):year_returns[y]=e/prev-1;prev=e
    return {"start":start,"end":end,"bps_each_side":bps,
       "monthly_intervals":chosen_intervals,"completed_trades":len(trades),
       "gross_pnl":sum(t["gross"] for t in trades),
       "total_costs":sum(t["fees"] for t in trades),
       "net_pnl":pnl,"ending_equity":cash,"return_pct":100*pnl/BASE,
       "max_drawdown_pct":dd*100,"profit_factor":winners/losers if losers else (None if not winners else "INFINITE"),
       "yearly_net_returns_pct":{k:round(v*100,3) for k,v in year_returns.items()},
       "trades":trades,"ledger":ledger}

def benchmark(start,end,sym,bps,dates,data):
    a=next(d for d in dates if d>=start)
    b=next(d for d in reversed(dates) if d<=end)
    buy=price(data[sym][a]["open"],True,bps)
    n=int(BASE//buy)
    while n and buy*n+fees(sym,buy,n,True)>BASE:n-=1
    sell=price(data[sym][b]["open"],False,bps)
    ending=BASE-buy*n-fees(sym,buy,n,True)+sell*n-fees(sym,sell,n,False)
    return {"symbol":sym,"net_pnl":ending-BASE,"ending_equity":ending,"quantity":n}

def brief(v):
    return {k:value for k,value in v.items() if k not in ("trades","ledger")}

def write_rows(file,records):
    with file.open("w",newline="",encoding="utf-8") as f:
        if records:
            w=csv.DictWriter(f,fieldnames=list(records[0]))
            w.writeheader();w.writerows(records)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--data",type=Path,required=True)
    parser.add_argument("--spots",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    dates,data=read_prices(args.data,args.spots)
    manifest={"source":"Yahoo Finance daily unadjusted via yfinance; matched against independent NSE spot checks",
              "common_trading_dates":len(dates),"first":dates[0],"last":dates[-1],
              "spotted":len(json.loads(args.spots.read_text())["rows"]),
              "csv_hash_sha256":{s:hashlib.sha256((args.data/f"{s}.csv").read_bytes()).hexdigest() for s in SYMS}}
    (args.out/"source_manifest.json").write_text(json.dumps(manifest,indent=2))
    dev=simulate("2023-01-01","2023-12-31",5,dates,data)
    adverse=simulate("2023-01-01","2023-12-31",15,dates,data)
    write_rows(args.out/"dev_trades.csv",dev["trades"])
    dev_pass=dev["net_pnl"]>0 and adverse["net_pnl"]>0 and dev["max_drawdown_pct"]<=15
    result={"experiment_id":"KATS-ETF-DUAL-MOMENTUM-V1",
       "source":manifest,
       "development":brief(dev),"development_adverse":brief(adverse),
       "benchmark_dev":[benchmark("2023-01-01","2023-12-31",sym,5,dates,data) for sym in SYMS],
       "validation":"NOT_ACCESSED","verdict":"REJECT_DEVELOPMENT","live_orders":"NONE"}
    if dev_pass:
        val=simulate("2024-01-01","2025-10-31",5,dates,data)
        val_stress=simulate("2024-01-01","2025-10-31",15,dates,data)
        write_rows(args.out/"val_trades.csv",val["trades"])
        result["validation"]=brief(val)
        result["validation_adverse"]=brief(val_stress)
        result["benchmark_validation"]=[benchmark("2024-01-01","2025-10-31",sym,5,dates,data) for sym in SYMS]
        years=val["yearly_net_returns_pct"]
        ok=(val["monthly_intervals"]>=12 and val["net_pnl"]>0 and val_stress["net_pnl"]>0
            and val["max_drawdown_pct"]<=15 and bool(years)
            and sum(x>0 for x in years.values())>=len(years)/2)
        result["verdict"]="PROMISING_REQUIRES_INDEPENDENT_REVIEW" if ok else "REJECT_VALIDATION"
    (args.out/"results.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))
    print(json.dumps(result,sort_keys=True,allow_nan=False))
if __name__=="__main__":main()
