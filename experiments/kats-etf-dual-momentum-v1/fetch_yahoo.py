"""Fetch public ETF daily OHLCV. All pricing evidence is preserved in CI artifact."""
import argparse
import csv
from pathlib import Path
import yfinance as yf

p=argparse.ArgumentParser()
p.add_argument("--out",type=Path,required=True)
args=p.parse_args()
args.out.mkdir(parents=True,exist_ok=True)
for sym in ("NIFTYBEES","GOLDBEES"):
    f=yf.Ticker(sym+".NS").history(start="2022-01-01",end="2025-11-01",
       interval="1d",auto_adjust=False,actions=False,repair=False,raise_errors=True)
    if f is None or len(f)<750:
        raise RuntimeError(f"DATA_BLOCKED_YAHOO_INCOMPLETE: {sym}: {len(f) if f is not None else 0}")
    dst=args.out/(sym+".csv")
    with dst.open("w",newline="",encoding="utf-8") as dest:
        w=csv.writer(dest)
        w.writerow(["date","open","high","low","close","volume"])
        for date,row in f.iterrows():
            w.writerow([date.date().isoformat(),row["Open"],row["High"],row["Low"],row["Close"],row["Volume"]])
    print(f"DATA_FETCHED {sym}: {len(f)} rows")
