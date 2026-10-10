"""KATS-INTRADAY-300NET-V1: research-only causal setup + cash/risk/fee simulation.

It does NOT connect to a broker, guarantee profits, or execute real orders.
"""
from __future__ import annotations

import math
import statistics
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"kats-failed-breakout-vwap-long-v1"))
import reversal
infra=reversal.infra
TICK=.05
MAX_NET_LOSS=200.
NET_WIN_TARGET=300.
START_CAPITAL=20000.
SYMBOLS=tuple(infra.SYMBOLS)
DEV_START, DEV_END=infra.DEV_START,infra.DEV_END
VAL_START, VAL_END=infra.VAL_START,infra.VAL_END

@dataclass(frozen=True)
class Setup:
    day: date
    symbol: str
    direction: int # +1 long, -1 short
    entry_time: datetime
    observed_entry_open: float # simulation only, not a predictive signal
    stop: float
    rvol: float
    median_daily_range: float
    signal_time: datetime

def fee_side(price:float, qty:int, day:date, buy:bool)->float:
    """Upstox Plus MIS charges, conservative historical fee approximation."""
    amount=price*qty
    brokerage=min(30.,.001*amount)
    stt=0. if buy else .00025*amount
    exchange=.0000322*amount if day<date(2024,10,1) else .0000297*amount
    sebi=.000001*amount
    ipft=.000001*amount
    stamp=.00003*amount if buy else 0.
    gst=.18*(brokerage+exchange+sebi+ipft)
    return brokerage+stt+exchange+sebi+ipft+stamp+gst

def tick_up(v:float)->float:
    return round(math.ceil((v-1e-9)/TICK)*TICK,2)

def tick_down(v:float)->float:
    return round(math.floor((v+1e-9)/TICK)*TICK,2)

def execute(raw:float, action:str, slip_bps:float)->float:
    assert action in ("BUY","SELL")
    return tick_up(raw*(1+slip_bps/10000)) if action=="BUY" else max(TICK,tick_down(raw*(1-slip_bps/10000)))

def open_action(direction:int)->str:
    return "BUY" if direction==1 else "SELL"

def close_action(direction:int)->str:
    return "SELL" if direction==1 else "BUY"

def trade_cost(entry:float, out:float, qty:int, day:date, direction:int)->float:
    return fee_side(entry,qty,day,direction==1)+fee_side(out,qty,day,direction==-1)

def net_profit(entry:float, out:float, qty:int, day:date, direction:int)->float:
    return direction*(out-entry)*qty-trade_cost(entry,out,qty,day,direction)

def size_and_target(setup:Setup,equity:float,slip_bps:float):
    """Compute *before reading future price outcomes*; no entry when net 300 implausible."""
    entry=execute(setup.observed_entry_open,open_action(setup.direction),slip_bps)
    stop_out=execute(setup.stop,close_action(setup.direction),slip_bps)
    if setup.direction*(entry-stop_out)<=0 or entry<=0:
        return None,"INVALID_STOP"
    risk_cap=min(MAX_NET_LOSS,.01*equity)
    chosen=0;loss=0.
    for q in range(int(min(equity,START_CAPITAL)//entry),0,-1):
        entry_fees=fee_side(entry,q,setup.day,setup.direction==1)
        stop_loss=-net_profit(entry,stop_out,q,setup.day,setup.direction)
        if q*entry+entry_fees<=min(equity,START_CAPITAL)+1e-9 and stop_loss<=risk_cap+1e-9:
            chosen=q;loss=stop_loss;break
    if chosen==0:return None,"INSUFFICIENT_CAPITAL_OR_RISK"
    # Work out a raw stop-order/limit target that nets 300 after slippage and fees.
    # The target's raw price must be above entry for longs and below for shorts.
    expected_exitcharge=fee_side(entry,chosen,setup.day,setup.direction==-1)
    entrycharge=fee_side(entry,chosen,setup.day,setup.direction==1)
    approx_delta=(NET_WIN_TARGET+entrycharge+expected_exitcharge)/chosen
    raw=(tick_up(entry+approx_delta+entry*slip_bps/10000+TICK)
          if setup.direction==1 else tick_down(entry-approx_delta-entry*slip_bps/10000-TICK))
    if raw<=0:return None,"TARGET_BELOW_ZERO"
    limit=1.5*setup.median_daily_range
    target=None;target_fill=None;reward=None
    for _ in range(80):
        if setup.direction*(raw-entry)<=0 or abs(raw-entry)>limit+1e-9:
            return None,"TARGET_BEYOND_PRECOMMITTED_RANGE"
        projected=execute(raw,close_action(setup.direction),slip_bps)
        earned=net_profit(entry,projected,chosen,setup.day,setup.direction)
        if earned>=NET_WIN_TARGET-1e-8:
            target,target_fill,reward=raw,projected,earned
            break
        raw=round(raw+setup.direction*TICK,2)
    if target is None:return None,"TARGET_NOT_SOLVABLE"
    return {"entry":entry,"quantity":chosen,"stop":setup.stop,"stop_out":stop_out,
            "planned_risk":loss,"target_raw":target,"target_fill":target_fill,
            "planned_reward":reward,"cash_before":equity}, "ELIGIBLE"

def generate_setups(data,start:date,end:date)->list[Setup]:
    setups=[]
    for sym in SYMBOLS:
        history_open15=[]
        history_range=[]
        for day,bars in sorted(data[sym].items()):
            five=infra.aggregate_five(bars)
            avg15=sum(b.volume for b in five[:3])
            if start<=day<=end and len(history_open15)>=20 and len(history_range)>=20:
                baseline=statistics.mean(history_open15[-20:])
                if baseline>0:
                    rvol=avg15/baseline
                    if rvol>=1.15:
                        median_range=statistics.median(history_range[-20:])
                        cum_pv=0.;cum_v=0.
                        minute_by_time={b.timestamp:b for b in bars}
                        for j,bar in enumerate(five):
                            typical=(bar.high+bar.low+bar.close)/3
                            cum_pv+=typical*bar.volume
                            cum_v+=bar.volume
                            if j<9 or cum_v<=0:continue
                            # Signal uses only a fully completed 5m bar.
                            endtime=(bar.timestamp+timedelta(minutes=5)).time()
                            if endtime<time(10,0) or endtime>time(12,30):continue
                            vwap=cum_pv/cum_v
                            prev=five[j-9:j]
                            med_vol=statistics.median(x.volume for x in prev)
                            if bar.volume<1.30*med_vol or med_vol<=0:continue
                            hi=max(x.high for x in prev)
                            lo=min(x.low for x in prev)
                            long=bar.close>=1.0005*hi and bar.close>bar.open and bar.close>vwap
                            short=bar.close<=.9995*lo and bar.close<bar.open and bar.close<vwap
                            if not (long or short):continue
                            direction=1 if long else -1
                            # Avoid reading/using the current trade outcome to select a symbol.
                            entrytime=bar.timestamp+timedelta(minutes=6)
                            entrybar=minute_by_time.get(entrytime)
                            if entrybar is None or entrybar.volume<=0:continue
                            last3=five[j-2:j+1]
                            stop=(tick_down(min(x.low for x in last3)-TICK) if long
                                  else tick_up(max(x.high for x in last3)+TICK))
                            if stop<=0:continue
                            setups.append(Setup(day,sym,direction,entrytime,entrybar.open,stop,
                                                rvol,median_range,bar.timestamp+timedelta(minutes=5)))
            history_open15.append(avg15)
            history_range.append(max(x.high for x in bars)-min(x.low for x in bars))
    return sorted(setups,key=lambda x:(x.day,x.entry_time,-x.rvol,x.symbol,-x.direction))

def exit_trade(setup:Setup,plan:dict,bars,slip_bps:float):
    symbol_time=setup.entry_time
    for bar in bars:
        if bar.timestamp<symbol_time:continue
        if bar.timestamp.time()>time(15,10):break
        if bar.timestamp.time()==time(15,10):
            if bar.volume<=0:raise RuntimeError("DATA_UNSCORABLE_MANDATORY_EXIT")
            return bar.timestamp,execute(bar.open,close_action(setup.direction),slip_bps),"TIME_15_10"
        if setup.direction==1:
            stop_open=bar.open<=setup.stop
            stop_touch=bar.low<=setup.stop
            take_touch=bar.high>=plan["target_raw"]
        else:
            stop_open=bar.open>=setup.stop
            stop_touch=bar.high>=setup.stop
            take_touch=bar.low<=plan["target_raw"]
        if stop_open or stop_touch or take_touch:
            if bar.volume<=0:raise RuntimeError("DATA_UNSCORABLE_EXIT_ZERO_VOLUME")
            if stop_open:
                return bar.timestamp,execute(bar.open,close_action(setup.direction),slip_bps),"GAP_STOP"
            if stop_touch:
                return bar.timestamp,execute(setup.stop,close_action(setup.direction),slip_bps),("AMBIGUOUS_STOP_FIRST" if take_touch else "STOP")
            return bar.timestamp,execute(plan["target_raw"],close_action(setup.direction),slip_bps),"NET300_TARGET"
    raise RuntimeError("DATA_UNSCORABLE_NO_EXIT_CANDLE")

def run_portfolio(data,setups,slip_bps:float):
    grouped=defaultdict(list)
    for setup in setups: grouped[setup.day].append(setup)
    equity=START_CAPITAL
    trades=[];rejects=[];sessions=sorted({d for sym in SYMBOLS for d in data[sym] if DEV_START<=d<=VAL_END})
    for day in sorted(grouped):
        if not grouped[day]:continue
        chosen=None;plan=None
        for setup in grouped[day]:
            plan,reason=size_and_target(setup,equity,slip_bps)
            if plan is None:
                rejects.append({"date":day.isoformat(),"symbol":setup.symbol,"reason":reason})
                continue
            chosen=setup;break
        if chosen is None:continue
        for setup in grouped[day]:
            if setup is chosen:continue
            rejects.append({"date":day.isoformat(),"symbol":setup.symbol,"reason":"ONE_TRADE_SESSION"})
        t,exitprice,why=exit_trade(chosen,plan,data[chosen.symbol][day],slip_bps)
        net=net_profit(plan["entry"],exitprice,plan["quantity"],day,chosen.direction)
        cost=trade_cost(plan["entry"],exitprice,plan["quantity"],day,chosen.direction)
        gross=chosen.direction*(exitprice-plan["entry"])*plan["quantity"]
        before=equity;equity+=net
        trades.append({
            "date":day.isoformat(),"symbol":chosen.symbol,"direction":"LONG" if chosen.direction==1 else "SHORT",
            "signal_time":chosen.signal_time.isoformat(),"entry_time":chosen.entry_time.isoformat(),
            "entry":plan["entry"],"quantity":plan["quantity"],"stop":chosen.stop,
            "target":plan["target_raw"],"planned_reward_net":plan["planned_reward"],
            "planned_risk_net":plan["planned_risk"],"risk_pct":plan["planned_risk"]/before,
            "exit_time":t.isoformat(),"exit_price":exitprice,"exit_reason":why,
            "gross_pnl":gross,"costs":cost,"net_pnl":net,"equity_before":before,"equity_after":equity,
        })
    return trades,rejects

def metrics(trades):
    if not trades:return {"trades":0,"net_pnl":0.,"costs":0.,"profit_factor":None,
      "max_drawdown":0.,"positive_month_share":None,"net_ex_top_3":None,
      "target_wins":0,"profitable_days":0,"losing_days":0,"no_trade_days":None}
    total=START_CAPITAL;peak=START_CAPITAL;dd=0.;months=defaultdict(float)
    for t in trades:
        total+=t["net_pnl"]
        peak=max(peak,total);dd=max(dd,peak-total)
        months[t["date"][:7]]+=t["net_pnl"]
    profits=sum(t["net_pnl"] for t in trades if t["net_pnl"]>0)
    losses=-sum(t["net_pnl"] for t in trades if t["net_pnl"]<0)
    return {"trades":len(trades),"gross_pnl":sum(t["gross_pnl"] for t in trades),
       "net_pnl":total-START_CAPITAL,"ending_equity":total,"costs":sum(t["costs"] for t in trades),
       "profit_factor":profits/losses if losses else ("INFINITE" if profits else None),
       "win_rate":sum(t["net_pnl"]>0 for t in trades)/len(trades),
       "max_drawdown":dd,"positive_month_share":sum(v>0 for v in months.values())/len(months),
       "net_ex_top_3":total-START_CAPITAL-sum(sorted((t["net_pnl"] for t in trades),reverse=True)[:3]),
       "target_wins":sum(t["exit_reason"]=="NET300_TARGET" and t["net_pnl"]>=299.999 for t in trades),
       "profitable_days":sum(t["net_pnl"]>0 for t in trades),
       "losing_days":sum(t["net_pnl"]<0 for t in trades)}

def dev_pass(b,a):
    return (b["trades"]>=35 and b["net_pnl"]>0 and a["net_pnl"]>0 and
      isinstance(b["profit_factor"],(int,float)) and b["profit_factor"]>1.15 and
      b["max_drawdown"]<=3000 and b["positive_month_share"]>=.5 and
      b["net_ex_top_3"]>0 and b["target_wins"]>=12)

def val_pass(b,a):
    return (b["trades"]>=25 and b["net_pnl"]>0 and a["net_pnl"]>0 and
      isinstance(b["profit_factor"],(int,float)) and b["profit_factor"]>1.10 and
      b["max_drawdown"]<=3000 and b["positive_month_share"]>=.5 and
      b["net_ex_top_3"]>0 and b["target_wins"]>=8)
