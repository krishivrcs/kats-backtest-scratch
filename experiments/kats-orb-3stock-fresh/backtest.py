#!/usr/bin/env python3
"""Frozen KATS ORB/RVOL three-stock option-candle backtest."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
import zipfile
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from statistics import mean
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
SYMBOLS = ("SBIN", "DLF", "RELIANCE")
OPTION_RE = re.compile(r"^(SBIN|DLF|RELIANCE)(\d{2}[A-Z]{3}\d{2})(\d+(?:\.\d+)?)(CE|PE)\.NFO$")
STARTING_CAPITAL = 20_000.0
SCENARIOS = {
    "baseline": (0.005, 0.05),
    "adverse": (0.010, 0.10),
    "severe": (0.020, 0.20),
}


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    symbol: str
    day: date
    direction: str
    decision_time: datetime
    underlying_close: float
    rvol: float
    breakout_distance: float


@dataclass(frozen=True)
class Contract:
    ticker: str
    symbol: str
    expiry: date
    strike: float
    option_type: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_option_ticker(ticker: str) -> Contract | None:
    match = OPTION_RE.fullmatch(ticker.strip().upper())
    if not match:
        return None
    symbol, expiry_text, strike, option_type = match.groups()
    return Contract(ticker.strip().upper(), symbol, datetime.strptime(expiry_text, "%d%b%y").date(), float(strike), option_type)


def lot_size(symbol: str, day: date) -> int:
    if symbol == "SBIN":
        return 750
    if symbol == "DLF":
        return 825
    if symbol == "RELIANCE":
        return 250 if day <= date(2024, 10, 25) else 500
    raise ValueError(symbol)


def slippage(price: float, pct: float, minimum: float) -> float:
    return max(price * pct, minimum)


def charges(buy_price: float, sell_price: float, quantity: int) -> dict[str, float]:
    buy_value = buy_price * quantity
    sell_value = sell_price * quantity
    brokerage = 40.0
    stt = sell_value * 0.001
    exchange = (buy_value + sell_value) * 0.0003503
    sebi = (buy_value + sell_value) * 0.000001
    gst = (brokerage + exchange + sebi) * 0.18
    stamp = buy_value * 0.00003
    total = brokerage + stt + exchange + sebi + gst + stamp
    return {"brokerage": brokerage, "stt": stt, "exchange": exchange, "sebi": sebi, "gst": gst, "stamp": stamp, "total": total}


def aggregate_5m(bars: list[Bar]) -> list[Bar]:
    buckets: dict[datetime, list[Bar]] = defaultdict(list)
    for bar in bars:
        minute = bar.timestamp.minute - bar.timestamp.minute % 5
        key = bar.timestamp.replace(minute=minute, second=0, microsecond=0)
        buckets[key].append(bar)
    result = []
    for key in sorted(buckets):
        group = sorted(buckets[key], key=lambda b: b.timestamp)
        result.append(Bar(key, group[0].open, max(b.high for b in group), min(b.low for b in group), group[-1].close, sum(b.volume for b in group)))
    return result


def valid_opening(bars: list[Bar]) -> bool:
    expected = {time(9, minute) for minute in range(15, 30)}
    opening = [bar for bar in bars if time(9, 15) <= bar.timestamp.time().replace(tzinfo=None) <= time(9, 29)]
    observed = {bar.timestamp.time().replace(tzinfo=None) for bar in opening}
    sound = all(
        min(bar.open, bar.high, bar.low, bar.close) > 0
        and bar.low <= min(bar.open, bar.close, bar.high)
        and bar.high >= max(bar.open, bar.close, bar.low)
        and bar.volume >= 0
        for bar in opening
    )
    return observed == expected and len(opening) == 15 and sound


def signal_for_day(symbol: str, day: date, bars: list[Bar], prior_open_volumes: list[float]) -> tuple[Signal | None, str]:
    opening = [b for b in bars if time(9, 15) <= b.timestamp.time().replace(tzinfo=None) <= time(9, 29)]
    if not valid_opening(bars):
        return None, "INVALID_CURRENT_OPENING_SESSION"
    if len(prior_open_volumes) < 20:
        return None, "INSUFFICIENT_20_SESSION_HISTORY"
    current_volume = sum(b.volume for b in opening)
    average_volume = mean(prior_open_volumes[-20:])
    if average_volume <= 0:
        return None, "NONPOSITIVE_VOLUME_HISTORY"
    rvol = current_volume / average_volume
    if rvol < 1.50:
        return None, "RVOL_BELOW_1_50"
    opening_high = max(b.high for b in opening)
    opening_low = min(b.low for b in opening)
    for bar in aggregate_5m(bars):
        decision = bar.timestamp + timedelta(minutes=5)
        if decision <= datetime.combine(day, time(9, 30), IST) or decision > datetime.combine(day, time(12, 0), IST):
            continue
        if bar.close > opening_high:
            return Signal(symbol, day, "LONG", decision, bar.close, rvol, (bar.close / opening_high) - 1.0), "SIGNAL"
        if bar.close < opening_low:
            return Signal(symbol, day, "SHORT", decision, bar.close, rvol, (opening_low / bar.close) - 1.0), "SIGNAL"
    return None, "NO_BREAKOUT"


def parse_cash_archive(path: Path) -> dict[str, dict[date, list[Bar]]]:
    result: dict[str, dict[date, list[Bar]]] = {symbol: defaultdict(list) for symbol in SYMBOLS}
    with zipfile.ZipFile(path) as zf:
        names = {Path(name).name.upper(): name for name in zf.namelist()}
        for symbol in SYMBOLS:
            member = names[f"{symbol}_1M.CSV.GZ"]
            with zf.open(member) as compressed, gzip.GzipFile(fileobj=compressed) as raw:
                reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
                for row in reader:
                    stamp = datetime.fromtimestamp(int(float(row["time"])), tz=timezone.utc).astimezone(IST)
                    bar = Bar(stamp, *(float(row[key]) for key in ("open", "high", "low", "close")), float(row["Volume"]))
                    result[symbol][stamp.date()].append(bar)
    return result


def option_members(path: Path) -> dict[date, str]:
    members = {}
    with zipfile.ZipFile(path) as zf:
        for member in zf.namelist():
            if not member.lower().endswith(".csv"):
                continue
            with zf.open(member) as raw:
                reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline=""))
                first = next(reader, None)
                if first:
                    members[datetime.strptime(first["Date"], "%Y-%m-%d").date()] = member
    return members


def build_signals(cash: dict[str, dict[date, list[Bar]]], target_days: list[date]) -> tuple[dict[date, list[Signal]], list[dict]]:
    signals: dict[date, list[Signal]] = defaultdict(list)
    audit = []
    for symbol in SYMBOLS:
        valid_days = []
        opening_volumes = {}
        for day in sorted(cash[symbol]):
            bars = cash[symbol][day]
            if valid_opening(bars):
                valid_days.append(day)
                opening_volumes[day] = sum(b.volume for b in bars if time(9, 15) <= b.timestamp.time().replace(tzinfo=None) <= time(9, 29))
        for day in target_days:
            prior = [opening_volumes[d] for d in valid_days if d < day][-20:]
            signal, reason = signal_for_day(symbol, day, cash[symbol].get(day, []), prior)
            audit.append({"day": day.isoformat(), "symbol": symbol, "reason": reason, "prior_valid_sessions": len(prior)})
            if signal:
                signals[day].append(signal)
    for day in signals:
        signals[day].sort(key=lambda s: (s.decision_time, -s.rvol, -s.breakout_distance, s.symbol))
    return signals, audit


def parse_option_time(row: dict[str, str]) -> datetime:
    naive = datetime.strptime(f"{row['Date']} {row['Time']}", "%Y-%m-%d %H:%M:%S")
    return naive.replace(tzinfo=IST)


def load_day_options(zf: zipfile.ZipFile, member: str, needed: dict[str, str]) -> dict[str, tuple[Contract, list[Bar]]]:
    contracts: dict[str, Contract] = {}
    bars: dict[str, list[Bar]] = defaultdict(list)
    with zf.open(member) as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline=""))
        for row in reader:
            ticker = row["Ticker"].strip().upper()
            contract = parse_option_ticker(ticker)
            if not contract or needed.get(contract.symbol) != contract.option_type:
                continue
            stamp = parse_option_time(row)
            contracts[ticker] = contract
            bars[ticker].append(Bar(stamp, *(float(row[key]) for key in ("Open", "High", "Low", "Close")), float(row["Volume"])))
    return {ticker: (contracts[ticker], sorted(values, key=lambda b: b.timestamp)) for ticker, values in bars.items()}


def select_contract(signal: Signal, day_contracts: dict[str, tuple[Contract, list[Bar]]]) -> tuple[Contract | None, list[Bar]]:
    option_type = "CE" if signal.direction == "LONG" else "PE"
    available = [contract for contract, _ in day_contracts.values() if contract.symbol == signal.symbol and contract.option_type == option_type and (contract.expiry - signal.day).days >= 5]
    if not available:
        return None, []
    expiry = min(contract.expiry for contract in available)
    expiry_contracts = [contract for contract in available if contract.expiry == expiry]
    def strike_key(contract: Contract):
        tie = contract.strike if option_type == "CE" else -contract.strike
        return (abs(contract.strike - signal.underlying_close), tie)
    chosen = min(expiry_contracts, key=strike_key)
    return chosen, day_contracts[chosen.ticker][1]


def raw_opportunity(signal: Signal, day_contracts: dict[str, tuple[Contract, list[Bar]]]) -> tuple[dict | None, str]:
    contract, bars = select_contract(signal, day_contracts)
    if not contract:
        return None, "NO_ELIGIBLE_CONTRACT"
    latest = signal.decision_time + timedelta(minutes=2)
    entry_index = next((i for i, bar in enumerate(bars) if signal.decision_time <= bar.timestamp.replace(second=0) <= latest and bar.volume > 0), None)
    if entry_index is None:
        return None, "NO_POSITIVE_VOLUME_ENTRY_WITHIN_2_MIN"
    if not any(bar.timestamp.time().replace(tzinfo=None) >= time(15, 15) for bar in bars[entry_index:]):
        return None, "NO_FORCED_EXIT_BAR"
    return {"signal": signal, "contract": contract, "bars": bars, "entry_index": entry_index, "lot_size": lot_size(signal.symbol, signal.day)}, "READY"


def simulate(opportunity: dict, scenario: str, equity: float) -> tuple[dict | None, str]:
    pct, minimum = SCENARIOS[scenario]
    signal: Signal = opportunity["signal"]
    contract: Contract = opportunity["contract"]
    bars: list[Bar] = opportunity["bars"]
    entry_index = opportunity["entry_index"]
    quantity = opportunity["lot_size"]
    entry_bar = bars[entry_index]
    entry_price = entry_bar.open + slippage(entry_bar.open, pct, minimum)
    stop = entry_price * 0.80
    target = entry_price * 1.40
    estimated_stop_exit = max(0.0, stop - slippage(stop, pct, minimum))
    estimate_cost = charges(entry_price, estimated_stop_exit, quantity)["total"]
    planned_loss = (entry_price - estimated_stop_exit) * quantity + estimate_cost
    if entry_price * quantity > equity:
        return None, "CAPITAL_CONSTRAINT"
    if planned_loss > equity * 0.01 + 1e-9:
        return None, "RISK_CONSTRAINT"
    exit_raw = None
    exit_reason = None
    exit_time = None
    for bar in bars[entry_index:]:
        clock = bar.timestamp.time().replace(tzinfo=None)
        if clock >= time(15, 15):
            exit_raw, exit_reason, exit_time = bar.open, "FORCED_15_15", bar.timestamp
            break
        stop_hit = bar.low <= stop
        target_hit = bar.high >= target
        if bar.open <= stop:
            exit_raw, exit_reason, exit_time = bar.open, "STOP_GAP", bar.timestamp
            break
        if stop_hit and target_hit:
            exit_raw, exit_reason, exit_time = stop, "AMBIGUOUS_STOP_FIRST", bar.timestamp
            break
        if stop_hit:
            exit_raw, exit_reason, exit_time = stop, "STOP", bar.timestamp
            break
        if target_hit:
            exit_raw, exit_reason, exit_time = target, "TARGET", bar.timestamp
            break
    if exit_raw is None:
        return None, "NO_EXIT"
    exit_price = max(0.0, exit_raw - slippage(exit_raw, pct, minimum))
    cost = charges(entry_price, exit_price, quantity)
    gross = (exit_price - entry_price) * quantity
    net = gross - cost["total"]
    return {
        "day": signal.day.isoformat(), "symbol": signal.symbol, "direction": signal.direction,
        "decision_time": signal.decision_time.isoformat(), "rvol": signal.rvol,
        "underlying_close": signal.underlying_close, "ticker": contract.ticker,
        "expiry": contract.expiry.isoformat(), "strike": contract.strike, "option_type": contract.option_type,
        "lot_size": quantity, "entry_time": entry_bar.timestamp.isoformat(), "entry_price": entry_price,
        "stop": stop, "target": target, "planned_loss": planned_loss,
        "exit_time": exit_time.isoformat(), "exit_price": exit_price, "exit_reason": exit_reason,
        "gross_pnl": gross, "costs": cost["total"], "net_pnl": net, **{f"cost_{k}": v for k, v in cost.items() if k != "total"},
    }, "EXECUTED"


def portfolio(scenario: str, target_days: list[date], opportunities: dict[date, list[tuple[Signal, dict | None, str]]]) -> tuple[list[dict], list[dict]]:
    equity = STARTING_CAPITAL
    trades = []
    exclusions = []
    for day in target_days:
        executed = False
        for signal, opportunity, readiness in opportunities.get(day, []):
            if executed:
                exclusions.append({"scenario": scenario, "day": day.isoformat(), "symbol": signal.symbol, "reason": "DAILY_PORTFOLIO_LIMIT"})
                continue
            if opportunity is None:
                exclusions.append({"scenario": scenario, "day": day.isoformat(), "symbol": signal.symbol, "reason": readiness})
                continue
            trade, reason = simulate(opportunity, scenario, equity)
            if trade is None:
                exclusions.append({"scenario": scenario, "day": day.isoformat(), "symbol": signal.symbol, "reason": reason})
                continue
            trade["equity_before"] = equity
            equity += trade["net_pnl"]
            trade["equity_after"] = equity
            trades.append(trade)
            executed = True
    return trades, exclusions


def metrics(trades: list[dict], target_days: list[date]) -> dict:
    nets = [trade["net_pnl"] for trade in trades]
    gross = sum(trade["gross_pnl"] for trade in trades)
    costs_total = sum(trade["costs"] for trade in trades)
    wins = [value for value in nets if value > 0]
    losses = [value for value in nets if value < 0]
    equity = STARTING_CAPITAL
    peak = equity
    max_dd = 0.0
    consecutive = maximum_consecutive = 0
    for value in nets:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
        consecutive = consecutive + 1 if value < 0 else 0
        maximum_consecutive = max(maximum_consecutive, consecutive)
    n = len(target_days)
    dev_end, val_end = math.floor(0.60 * n), math.floor(0.80 * n)
    validation_days = {d.isoformat() for d in target_days[dev_end:val_end]}
    holdout_days = {d.isoformat() for d in target_days[val_end:]}
    top_winners = sorted(wins, reverse=True)[:5]
    return {
        "trades": len(trades), "gross_pnl": gross, "total_costs": costs_total,
        "net_pnl": sum(nets), "ending_equity": STARTING_CAPITAL + sum(nets),
        "net_return_percent": sum(nets) / STARTING_CAPITAL * 100,
        "profit_factor": (sum(wins) / abs(sum(losses))) if losses else (None if not wins else "Infinity"),
        "win_rate": len(wins) / len(trades) if trades else None,
        "average_winner": mean(wins) if wins else None, "average_loser": mean(losses) if losses else None,
        "net_expectancy_per_trade": mean(nets) if nets else None, "max_drawdown": max_dd,
        "max_consecutive_losses": maximum_consecutive,
        "symbol_net": {symbol: sum(t["net_pnl"] for t in trades if t["symbol"] == symbol) for symbol in SYMBOLS},
        "validation_net": sum(t["net_pnl"] for t in trades if t["day"] in validation_days),
        "holdout_net": sum(t["net_pnl"] for t in trades if t["day"] in holdout_days),
        "validation_trades": sum(1 for t in trades if t["day"] in validation_days),
        "holdout_trades": sum(1 for t in trades if t["day"] in holdout_days),
        "excluding_top_5_winners_net": sum(nets) - sum(top_winners),
        "partition_days": {"development": [d.isoformat() for d in target_days[:dev_end]], "validation": sorted(validation_days), "holdout": sorted(holdout_days)},
        "monthly_net": {month: sum(t["net_pnl"] for t in trades if t["day"].startswith(month)) for month in sorted({t["day"][:7] for t in trades})},
        "annual_net": {year: sum(t["net_pnl"] for t in trades if t["day"].startswith(year)) for year in sorted({t["day"][:4] for t in trades})},
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("option_zip", type=Path)
    parser.add_argument("stock_zip", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    option_days = option_members(args.option_zip)
    target_days = sorted(option_days)
    cash = parse_cash_archive(args.stock_zip)
    signals, signal_audit = build_signals(cash, target_days)
    opportunities: dict[date, list[tuple[Signal, dict | None, str]]] = defaultdict(list)
    with zipfile.ZipFile(args.option_zip) as zf:
        for day in target_days:
            day_signals = signals.get(day, [])
            needed = {s.symbol: ("CE" if s.direction == "LONG" else "PE") for s in day_signals}
            day_contracts = load_day_options(zf, option_days[day], needed) if needed else {}
            for signal in day_signals:
                opportunity, reason = raw_opportunity(signal, day_contracts)
                opportunities[day].append((signal, opportunity, reason))
    result = {
        "project": "KATS-ORB-3STOCK-FRESH", "strategy_spec": "NEW_PREREGISTERED",
        "data_type": "OPTION_1MIN_PLUS_CASH_UNDERLYING_1MIN", "starting_capital": STARTING_CAPITAL,
        "option_data": {"sha256": sha256_file(args.option_zip), "days": [d.isoformat() for d in target_days], "timezone": "naive 09:15:59-15:30:59 interpreted as IST; source semantics not documented"},
        "cash_data": {"sha256": sha256_file(args.stock_zip), "timestamp": "Unix UTC converted to Asia/Kolkata per source README"},
        "lot_size_provenance": {"SBIN": "NSE/FAOP/61369: 1500 to 750", "DLF": "NSE/FAOP/61369: 1650 to 825", "RELIANCE": "250 through 2024-10-25; NSE/CMPT/64652 bonus adjustment to 500 from 2024-10-28"},
        "signals": sum(len(values) for values in signals.values()),
        "signal_rows": [{**asdict(signal), "day": signal.day.isoformat(), "decision_time": signal.decision_time.isoformat()} for values in signals.values() for signal in values],
        "signal_audit": signal_audit, "scenarios": {},
    }
    all_exclusions = []
    for scenario in SCENARIOS:
        trades, exclusions = portfolio(scenario, target_days, opportunities)
        result["scenarios"][scenario] = metrics(trades, target_days)
        write_csv(args.out / f"trades_{scenario}.csv", trades)
        all_exclusions.extend(exclusions)
    write_csv(args.out / "exclusions.csv", all_exclusions)
    result["classification"] = "UNDERPOWERED" if result["scenarios"]["baseline"]["trades"] < 100 or result["scenarios"]["baseline"]["holdout_trades"] < 30 else "SCORED"
    result["realistic_execution_status"] = "UNVERIFIED_NO_BID_ASK_AND_OPTION_TIMEZONE_SOURCE_UNDOCUMENTED"
    (args.out / "results.json").write_text(json.dumps(result, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"signals": result["signals"], "baseline": result["scenarios"]["baseline"], "classification": result["classification"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
