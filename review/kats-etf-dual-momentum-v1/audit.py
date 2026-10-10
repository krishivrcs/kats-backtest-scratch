"""Second-implementation arithmetic and decision audit from frozen CI artifact.
Independent of the original experiment Python modules. Never imports them.
"""
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

p=Path(sys.argv[1])
original=json.loads((p/"results.json").read_text())
snap=json.loads((p/"source_manifest.json").read_text())
assert original["source"]==snap
symbols=("GOLDBEES","NIFTYBEES")
data={}
for symbol in symbols:
    fp=p/"prices"/f"{symbol}.csv"
    assert hashlib.sha256(fp.read_bytes()).hexdigest()==snap["csv_hash_sha256"][symbol]
    source=list(csv.DictReader(fp.open()))
    data[symbol]={r["date"]:r for r in source if float(r["volume"])>0 and "2022-01-01"<=r["date"]<="2025-10-31"}
dates=sorted(set(data[symbols[0]])&set(data[symbols[1]]))
assert len(dates)==snap["common_trading_dates"]==944

def selection(i):
    if i<199:return None
    choices=[]
    for sym in symbols:
        recent=[float(data[sym][day]["close"]) for day in dates[i-199:i+1]]
        m=recent[-1]/recent[-127]-1.
        avg=sum(recent)/len(recent)
        if recent[-1]>avg and m>0: choices.append((m,sym))
    return sorted(choices,key=lambda t:(-t[0],t[1]))[0][1] if choices else None

def cost(sym,px,n,buy):
    x=px*n
    a=x*(.0000307+.000001)*1.18
    if buy:return a+x*.00015
    return a+15.34+(x*.00001 if sym=="NIFTYBEES" else 0)

def px(sym,day,buy,bps):
    x=float(data[sym][day]["open"])*(1+bps/10000 if buy else 1-bps/10000)
    return (math.ceil(x*100-1e-8) if buy else math.floor(x*100+1e-8))/100

def inspect(start,end,bps):
    first=next(i for i,d in enumerate(dates) if d>=start)
    last=max(i for i,d in enumerate(dates) if d<=end)
    cash=20000.; held=None; shares=0; buyprice=0.; buyfees=0.; buyday=""
    trades=[];high=20000.;worst=0.
    for i in range(first,last+1):
        d=dates[i]
        turn=(i==first or d[:7]!=dates[i-1][:7] or i==last)
        if turn:
            target=None if i==last else selection(i-1)
            if target!=held:
                if held:
                    sale=px(held,d,False,bps)
                    f=cost(held,sale,shares,False)
                    cash+=sale*shares-f
                    gross=(sale-buyprice)*shares
                    trades.append(dict(symbol=held,entry=buyday,exit=d,qty=shares,
                                       entryprice=buyprice,exitprice=sale,gross=gross,
                                       fees=buyfees+f,net=gross-buyfees-f))
                    held=None;shares=0
                if target:
                    entry=px(target,d,True,bps)
                    q=int(cash//entry)
                    while q>0 and entry*q+cost(target,entry,q,True)>cash+1e-8:q-=1
                    if q:
                        held=target;shares=q;buyprice=entry;buyfees=cost(target,entry,q,True)
                        cash-=entry*q+buyfees;buyday=d
        if cash < -1e-8:raise AssertionError("OVERSPENT")
        value=cash+(shares*float(data[held][d]["close"]) if held else 0)
        high=max(high,value);worst=max(worst,1-value/high)
    assert held is None
    return {"trades":trades,"net":cash-20000,"ending":cash,
            "costs":sum(t["fees"] for t in trades),
            "gross":sum(t["gross"] for t in trades),
            "drawdown_pct":worst*100}

audit={}
for label,start,end in (("development","2023-01-01","2023-12-31"),
                       ("validation","2024-01-01","2025-10-31")):
    if label=="validation" and original["validation"]=="NOT_ACCESSED":
        audit[label]="NOT_ACCESSED";continue
    audit[label]={}
    for bps,key in ((5,label),(15,label+"_adverse")):
        result=inspect(start,end,bps)
        expected=original[key]
        for actual,target in (("net","net_pnl"),("ending","ending_equity"),
                              ("costs","total_costs"),("gross","gross_pnl"),
                              ("drawdown_pct","max_drawdown_pct")):
            assert math.isclose(result[actual],expected[target],abs_tol=1e-5), (key,actual,result[actual],expected[target])
        assert len(result["trades"])==expected["completed_trades"]
        audit[label]["bps_"+str(bps)]={"net":round(result["net"],2),"trades":len(result["trades"]),
                         "costs":round(result["costs"],2),"dd_pct":round(result["drawdown_pct"],3)}
        if bps==5:
            rows=list(csv.DictReader((p/("dev_trades.csv" if label=="development" else "val_trades.csv")).open()))
            assert len(rows)==len(result["trades"])
            for index,(expected_row,actual_row) in enumerate(zip(rows,result["trades"])):
                for field,value in actual_row.items():
                    observed=expected_row[field]
                    if isinstance(value,str):assert observed==value,(index,field)
                    else:assert math.isclose(float(observed),value,abs_tol=1e-5),(index,field,value,observed)
            audit[label]["trades"]=result["trades"]

comparison=original.get("benchmark_validation",[])
if comparison:
    g=next(x for x in comparison if x["symbol"]=="GOLDBEES")
    v=original["validation"]["net_pnl"]
    assert g["net_pnl"]>v
    audit["benchmark_message"]="GOLDBEES_buy_and_hold_outperformed_rotation_by_INR_"+str(round(g["net_pnl"]-v,2))
audit["original_commit"]=snap["csv_hash_sha256"]
audit["verdict"]="MECHANICAL_RECALCULATION_PASS_NOT_INDEPENDENT_FORWARD_PROOF"
(p/"audit_result.json").write_text(json.dumps(audit,indent=2,sort_keys=True))
print(json.dumps({k:v if k!="validation" and k!="development" else {m:x for m,x in v.items() if m!="trades"} for k,v in audit.items()},sort_keys=True))
