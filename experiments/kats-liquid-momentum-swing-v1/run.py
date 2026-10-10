"""Frozen liquid-equity swing momentum experiment. Not a broker execution engine."""
from __future__ import annotations
import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "kats-failed-breakout-vwap-long-v1"))
import reversal
infra = reversal.infra

DEV_START, DEV_END = date(2024, 7, 1), date(2025, 2, 28)
VAL_START, VAL_END = date(2025, 3, 1), date(2025, 10, 31)
INITIAL = 20_000.
RISK = .01
TICK = .05
SYMBOLS = tuple(sorted(reversal.SYMBOLS))

@dataclass(frozen=True)
class Daily:
    day: date
    open: float
    high: float
    low: float
    close: float
    volume: float

def daily_market(raw):
    market = {}
    for symbol in SYMBOLS:
        out = []
        for day, bars in sorted(raw[symbol].items()):
            if len(bars) != 375:
                raise AssertionError("Invalid admitted session")
            b = Daily(day, bars[0].open, max(x.high for x in bars),
                      min(x.low for x in bars), bars[-1].close, sum(x.volume for x in bars))
            if out and abs(b.open / out[-1].close - 1) >= .15:
                # Do not bridge a large corporate-action/gap discontinuity.
                out = []
                continue
            out.append(b)
        market[symbol] = out
    return market

def mean(values):
    values=list(values)
    return sum(values)/len(values)

def atr(hist, idx, count=14):
    if idx < count: return None
    vals=[]
    for j in range(idx-count+1, idx+1):
        x,p=hist[j],hist[j-1]
        vals.append(max(x.high-x.low,abs(x.high-p.close),abs(x.low-p.close)))
    return mean(vals)

def choose(day, market, positions):
    ranks=[]
    for sym in SYMBOLS:
        i = positions[sym].get(day)
        if i is None or i < 63: continue
        h=market[sym]
        prior=h[i-63:i]
        x=h[i]
        ma20=mean(z.close for z in h[i-19:i+1])
        ma60=mean(z.close for z in h[i-59:i+1])
        roc63=x.close/h[i-63].close-1
        roc21=x.close/h[i-21].close-1
        turnover=mean(z.close*z.volume for z in h[i-19:i+1])
        a=atr(h,i)
        if (x.close>ma20>ma60 and roc63>=.05 and
            x.close>=.98*max(z.close for z in prior) and
            turnover>=20_000_000 and a is not None and a>0):
            stop=infra.tick_down(x.close-max(2*a,.02*x.close))
            if 0 < stop < x.close:
                ranks.append((-(roc63+.5*roc21),sym,stop,roc63,roc21))
    if not ranks: return None
    ranks.sort()
    _,sym,stop,m63,m21=ranks[0]
    return {"symbol":sym,"decision":day.isoformat(),"stop":stop,
            "momentum_63":m63,"momentum_21":m21}

def charges(price, qty, day, buy):
    turnover=price*qty
    ex=.0000322 if day<=date(2024,9,30) else .0000297
    stt=turnover*.001
    exchange=turnover*ex
    sebi=turnover*.000001
    ipft=turnover*.000001
    stamp=turnover*.00015 if buy else 0.
    gst=.18*(exchange+sebi+ipft)
    dp=0. if buy else 15.34
    return stt+exchange+sebi+ipft+stamp+gst+dp

def exec_buy(raw, bps):
    return infra.tick_up(raw*(1+bps/10000))

def exec_sell(raw,bps):
    return max(TICK,infra.tick_down(raw*(1-bps/10000)))

def quantity(equity,entry,stop,day,bps):
    if entry<=stop:return 0
    s=exec_sell(stop,bps)
    for n in range(int(equity//entry),0,-1):
        if (n*entry + charges(entry,n,day,True) <= equity and
            n*(entry-s)+charges(entry,n,day,True)+charges(s,n,day,False) <= equity*RISK):
            return n
    return 0

def signal_exit_on_close(history,i,held):
    if i < 9: return False
    ma10=mean(x.close for x in history[i-9:i+1])
    return held>=15 or history[i].close<ma10

def stats(trades,signals,start=INITIAL):
    nets=[t["net_pnl"] for t in trades]
    pos=sum(x for x in nets if x>0)
    neg=-sum(x for x in nets if x<0)
    eq=peak=start
    dd=0.
    months=defaultdict(float)
    for t in trades:
        eq+=t["net_pnl"]
        peak=max(peak,eq)
        dd=max(dd,peak-eq)
        months[t["exit_date"][:7]]+=t["net_pnl"]
    return {"trades":len(trades),"signals":signals,"gross_pnl":sum(t["gross_pnl"] for t in trades),
        "costs":sum(t["costs"] for t in trades),"net_pnl":sum(nets),
        "ending_equity":eq,"profit_factor":pos/neg if neg else (None if pos==0 else "INFINITE"),
        "win_rate":sum(n>0 for n in nets)/len(nets) if nets else None,
        "expectancy":mean(nets) if nets else None,"max_drawdown":dd,
        "positive_month_share":sum(n>0 for n in months.values())/len(months) if months else None,
        "net_without_largest_win":sum(nets)-(max(nets) if nets else 0),
        "months":dict(sorted(months.items()))}

def backtest(market,start,end,bps):
    sessions=sorted({d.day for hist in market.values() for d in hist if start<=d.day<=end})
    pos={sym:{x.day:i for i,x in enumerate(market[sym])} for sym in SYMBOLS}
    next_date={d:sessions[i+1] if i+1<len(sessions) else None for i,d in enumerate(sessions)}
    # Do not initiate positions in the last 20 observed sessions of this partition.
    decision_cutoff=sessions[-21] if len(sessions)>21 else start
    equity=INITIAL
    trades=[]
    rejected=[]
    order=None
    holding=None
    signals=0
    for day in sessions:
        nd=next_date[day]
        if order is not None:
            sym=order["symbol"]
            i=pos[sym].get(day)
            if holding is not None:raise AssertionError("Pending order overlaps holding")
            if i is None:
                rejected.append({"date":day.isoformat(),"symbol":sym,"reason":"ENTRY_SESSION_MISSING"})
            else:
                bar=market[sym][i]
                entry=exec_buy(bar.open,bps)
                stop=order["stop"]
                if entry<=stop:
                    rejected.append({"date":day.isoformat(),"symbol":sym,"reason":"ENTRY_BELOW_PRIOR_STOP"})
                else:
                    qty=quantity(equity,entry,stop,day,bps)
                    if qty<1:
                        rejected.append({"date":day.isoformat(),"symbol":sym,"reason":"NO_CASH_RISK_SIZE"})
                    else:
                        holding={"symbol":sym,"entry_date":day,"entry":entry,"qty":qty,"stop":stop,
                                 "buy_charge":charges(entry,qty,day,True),"held":0,
                                 "decision":order["decision"]}
            order=None
        if holding is not None:
            sym=holding["symbol"]
            i=pos[sym].get(day)
            if i is None:raise RuntimeError(f"OPEN_POSITION_MISSING_ADMITTED_BAR:{sym}:{day}")
            bar=market[sym][i]
            raw_exit=None
            reason=None
            if day>holding["entry_date"] and holding.get("exit_next_open"):
                raw_exit,reason=bar.open,"CLOSE_SIGNAL_NEXT_OPEN"
            elif bar.open<=holding["stop"]:
                raw_exit,reason=bar.open,"STOP_GAP"
            elif bar.low<=holding["stop"]:
                raw_exit,reason=holding["stop"],"STOP_TOUCHED_ASSUMED_FILL"
            if raw_exit is not None:
                sell=exec_sell(raw_exit,bps)
                qty=holding["qty"]
                gross=(sell-holding["entry"])*qty
                fee=holding["buy_charge"]+charges(sell,qty,day,False)
                net=gross-fee
                equity+=net
                trades.append({"symbol":sym,"decision_date":holding["decision"],
                    "entry_date":holding["entry_date"].isoformat(),"exit_date":day.isoformat(),
                    "entry":holding["entry"],"exit":sell,"qty":qty,"reason":reason,
                    "gross_pnl":gross,"costs":fee,"net_pnl":net,
                    "equity_after":equity})
                holding=None
            else:
                holding["held"]+=1
                if signal_exit_on_close(market[sym],i,holding["held"]):
                    holding["exit_next_open"]=True
                a=atr(market[sym],i)
                if a is not None:
                    holding["stop"]=max(holding["stop"],infra.tick_down(bar.close-2*a))
        if holding is None and order is None and day<=decision_cutoff and nd is not None:
            found=choose(day,market,pos)
            if found:
                signals+=1
                order=found
    if holding is not None or order is not None:
        raise RuntimeError("PARTITION_HAS_UNCLOSED_POSITION_OR_ORDER")
    return trades,rejected,stats(trades,signals)

def passed_dev(b,a):
    pf=b["profit_factor"]
    return bool(b["trades"]>=12 and b["net_pnl"]>0 and isinstance(pf,(int,float))
        and pf>1.10 and b["positive_month_share"]>=.5
        and b["max_drawdown"]<=3000 and b["net_without_largest_win"]>0 and a["net_pnl"]>0)

def passed_val(b,a):
    pf=b["profit_factor"]
    return bool(b["trades"]>=8 and b["net_pnl"]>0 and isinstance(pf,(int,float))
        and pf>1.10 and b["positive_month_share"]>=.5
        and b["max_drawdown"]<=3000 and b["net_without_largest_win"]>0 and a["net_pnl"]>0)

def write_csv(path,rows):
    with path.open("w",newline="",encoding="utf-8") as f:
        if rows:
            w=csv.DictWriter(f,fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        else:f.write("")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("archive",type=Path)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    raw,manifest,source_exclusions=reversal.load_until(args.archive,DEV_END)
    daily=daily_market(raw)
    dev,ex,met=backtest(daily,DEV_START,DEV_END,5.)
    d_adv,ex_adv,adv=backtest(daily,DEV_START,DEV_END,10.)
    report={"id":"KATS-LIQUID-MOMENTUM-SWING-V1",
        "archive_sha256":manifest["archive_sha256"],
        "development":met,"development_adverse":adv,
        "validation":"NOT_ACCESSED","verdict":"REJECT_DEVELOPMENT",
        "real_orders":"NONE","candle_fills_not_broker_evidence":True}
    write_csv(args.out/"dev_trades.csv",dev)
    write_csv(args.out/"dev_rejections.csv",ex)
    (args.out/"source_manifest_dev.json").write_text(json.dumps(manifest,indent=2))
    if passed_dev(met,adv):
        raw_val,vm,vex=reversal.load_until(args.archive,VAL_END)
        daily_val=daily_market(raw_val)
        val,vr,vmets=backtest(daily_val,VAL_START,VAL_END,5.)
        va,var,vadv=backtest(daily_val,VAL_START,VAL_END,10.)
        report["validation"]=vmets
        report["validation_adverse"]=vadv
        report["verdict"]="PROMISING_REQUIRES_INDEPENDENT_REVIEW" if passed_val(vmets,vadv) else "REJECT_VALIDATION"
        write_csv(args.out/"validation_trades.csv",val)
        write_csv(args.out/"validation_rejections.csv",vr)
        (args.out/"source_manifest_validation.json").write_text(json.dumps(vm,indent=2))
    (args.out/"results.json").write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False))
    print(json.dumps(report,sort_keys=True,allow_nan=False))
if __name__=="__main__":
    main()
