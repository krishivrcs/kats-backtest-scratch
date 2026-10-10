from __future__ import annotations

import csv
import gzip
import io
import json
import statistics
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parents[1] / "kats-profit-sprint-20261010"
sys.path.insert(0, str(INFRA_DIR))
import engine as infra

SYMBOLS = infra.SYMBOLS
DEV_START, DEV_END = infra.DEV_START, infra.DEV_END
VAL_START, VAL_END = infra.VAL_START, infra.VAL_END
LOAD_FROM = infra.LOAD_FROM
STARTING_CAPITAL = infra.STARTING_CAPITAL
RISK_FRACTION = infra.RISK_FRACTION
TICK = infra.TICK


@dataclass(frozen=True)
class Candidate:
    day: date
    symbol: str
    rvol: float
    breakdown_depth: float
    breakdown_time: datetime
    recovery_time: datetime
    entry_time: datetime
    entry_raw: float
    stop: float
    target: float


def load_until(path: Path, maximum_date: date) -> tuple[dict[str, dict[date, list[infra.MinuteBar]]], dict[str, object], list[dict[str, object]]]:
    archive_hash = infra.sha256_file(path)
    if archive_hash != infra.ARCHIVE_SHA256:
        raise SystemExit(f"archive SHA256 mismatch: {archive_hash}")
    admitted: dict[str, dict[date, list[infra.MinuteBar]]] = {symbol: {} for symbol in SYMBOLS}
    exclusions: list[dict[str, object]] = []
    members: dict[str, object] = {}
    with zipfile.ZipFile(path) as zf:
        names = {Path(name).name.upper(): name for name in zf.namelist()}
        for symbol in SYMBOLS:
            member = names.get(f"{symbol}_1M.CSV.GZ")
            if member is None:
                raise SystemExit(f"missing archive member: {symbol}")
            info = zf.getinfo(member)
            members[symbol] = {"member": member, "compressed_bytes": info.compress_size, "uncompressed_bytes": info.file_size}
            grouped: dict[date, list[infra.MinuteBar]] = defaultdict(list)
            order_errors: Counter[date] = Counter()
            previous: datetime | None = None
            with zf.open(member) as compressed, gzip.GzipFile(fileobj=compressed) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as text:
                for row in csv.DictReader(text):
                    try:
                        bar = infra.row_to_bar(row)
                    except (KeyError, TypeError, ValueError, OverflowError):
                        continue
                    day = bar.timestamp.date()
                    if day < LOAD_FROM:
                        previous = bar.timestamp
                        continue
                    if day > maximum_date:
                        break
                    if previous is not None and bar.timestamp <= previous:
                        order_errors[day] += 1
                    previous = bar.timestamp
                    clock = bar.timestamp.time().replace(tzinfo=None)
                    if time(9, 15) <= clock <= time(15, 29):
                        grouped[day].append(bar)
            for day, bars in sorted(grouped.items()):
                issues = infra.session_issues(bars, out_of_order=order_errors[day])
                if issues:
                    exclusions.append({"symbol": symbol, "date": day.isoformat(), "reasons": "|".join(issues)})
                else:
                    admitted[symbol][day] = bars
    manifest = {
        "source_url": "https://github.com/voletiramu/nse-fno-1min-data/releases/download/v1.0.0/stocks_1m_csvs.zip",
        "archive_sha256": archive_hash,
        "maximum_strategy_date_parsed": maximum_date.isoformat(),
        "timestamp_semantics": "integer Unix UTC converted to Asia/Kolkata interval starts",
        "members": members,
        "discovery_grade_not_exchange_authoritative": True,
    }
    return admitted, manifest, exclusions


def cumulative_vwap(five: list[infra.FiveBar]) -> list[float | None]:
    cumulative_pv = 0.0
    cumulative_volume = 0.0
    result: list[float | None] = []
    for bar in five:
        typical = (bar.high + bar.low + bar.close) / 3.0
        cumulative_pv += typical * bar.volume
        cumulative_volume += bar.volume
        result.append(cumulative_pv / cumulative_volume if cumulative_volume > 0 else None)
    return result


def candidate_from_five(symbol: str, day: date, five: list[infra.FiveBar],
                        prior_opening_volumes: list[float],
                        minute_by_time: dict[datetime, infra.MinuteBar]) -> Candidate | None:
    if len(prior_opening_volumes) < 20:
        return None
    average = sum(prior_opening_volumes[-20:]) / 20.0
    if average <= 0:
        return None
    opening_volume = sum(bar.volume for bar in five[:3])
    rvol = opening_volume / average
    if rvol < 1.0:
        return None
    or_low = min(bar.low for bar in five[:3])
    vwaps = cumulative_vwap(five)
    breakdown: int | None = None
    for i, bar in enumerate(five):
        end = bar.timestamp + timedelta(minutes=5)
        if bar.timestamp.time() < time(9, 30) or end.time() > time(12, 30) or i < 6:
            continue
        previous_median = statistics.median(item.volume for item in five[i - 6:i])
        if bar.close < or_low and bar.low < or_low * 0.999 and bar.volume >= 1.20 * previous_median:
            breakdown = i
            break
    if breakdown is None:
        return None
    recovery: int | None = None
    for i in range(breakdown + 1, min(len(five), breakdown + 4)):
        bar = five[i]
        if bar.close > or_low and bar.close > bar.open and bar.close > five[i - 1].close:
            recovery = i
            break
    if recovery is None or vwaps[recovery] is None:
        return None
    decision_time = five[recovery].timestamp + timedelta(minutes=5)
    # A completed bar and the next bar's boundary share a timestamp. Waiting one
    # full source minute makes the historical order sequence explicitly causal.
    entry_time = decision_time + timedelta(minutes=1)
    entry_bar = minute_by_time.get(entry_time)
    if entry_bar is None or entry_time.time() > time(12, 45):
        return None
    extreme = min(bar.low for bar in five[breakdown:recovery + 1])
    stop = infra.tick_down(extreme - TICK)
    target = infra.tick_down(float(vwaps[recovery]))
    if stop <= 0 or stop >= entry_bar.open:
        return None
    return Candidate(
        day, symbol, rvol, or_low / extreme - 1.0,
        five[breakdown].timestamp + timedelta(minutes=5),
        decision_time,
        entry_time, entry_bar.open, stop, target,
    )


def candidate_for_day(symbol: str, day: date, bars: list[infra.MinuteBar], prior_opening_volumes: list[float]) -> Candidate | None:
    return candidate_from_five(symbol, day, infra.aggregate_five(bars), prior_opening_volumes,
                               {bar.timestamp: bar for bar in bars})


def generate_candidates(data: dict[str, dict[date, list[infra.MinuteBar]]], start: date, end: date) -> list[Candidate]:
    candidates: list[Candidate] = []
    for symbol in SYMBOLS:
        history: list[float] = []
        for day, bars in sorted(data[symbol].items()):
            opening_volume = sum(bar.volume for bar in bars if bar.timestamp.time() < time(9, 30))
            if start <= day <= end:
                candidate = candidate_for_day(symbol, day, bars, history)
                if candidate is not None:
                    candidates.append(candidate)
            history.append(opening_volume)
    return sorted(candidates, key=lambda item: (item.entry_time, -item.rvol, -item.breakdown_depth, item.symbol))


def size_and_reward(equity: float, candidate: Candidate, slippage_bps: float) -> dict[str, float | int | str]:
    entry = infra.fill_entry(candidate.entry_raw, slippage_bps)
    stop_fill = infra.fill_exit(candidate.stop, slippage_bps)
    target_fill = infra.fill_exit(candidate.target, slippage_bps)
    if target_fill <= entry:
        return {"quantity": 0, "reason": "TARGET_NOT_ABOVE_ENTRY", "entry": entry, "stop_fill": stop_fill, "target_fill": target_fill}
    affordable = int(equity // entry)
    for qty in range(affordable, 0, -1):
        stop_cost = infra.round_trip_costs(entry, stop_fill, qty, candidate.day)["total"]
        planned_loss = (entry - stop_fill) * qty + stop_cost
        buy_cost = infra.side_costs(entry * qty, buy=True, day=candidate.day)["total"]
        if planned_loss > equity * RISK_FRACTION + 1e-9 or entry * qty + buy_cost > equity + 1e-9:
            continue
        target_cost = infra.round_trip_costs(entry, target_fill, qty, candidate.day)["total"]
        planned_profit = (target_fill - entry) * qty - target_cost
        if planned_profit < 1.50 * planned_loss:
            return {"quantity": 0, "reason": "PROSPECTIVE_REWARD", "entry": entry, "stop_fill": stop_fill,
                    "target_fill": target_fill, "planned_loss": planned_loss, "planned_profit": planned_profit}
        return {"quantity": qty, "reason": "ELIGIBLE", "entry": entry, "stop_fill": stop_fill,
                "target_fill": target_fill, "planned_loss": planned_loss, "planned_profit": planned_profit}
    return {"quantity": 0, "reason": "CAPITAL_OR_RISK", "entry": entry, "stop_fill": stop_fill, "target_fill": target_fill}


def simulate_exit(candidate: Candidate, minutes: list[infra.MinuteBar], slippage_bps: float) -> tuple[datetime, float, str]:
    for bar in minutes:
        if bar.timestamp < candidate.entry_time:
            continue
        if bar.timestamp.time() == time(15, 10):
            return bar.timestamp, infra.fill_exit(bar.open, slippage_bps), "TIME_15_10"
        if bar.open <= candidate.stop:
            return bar.timestamp, infra.fill_exit(bar.open, slippage_bps), "STOP_GAP"
        if bar.low <= candidate.stop and bar.high >= candidate.target:
            return bar.timestamp, infra.fill_exit(candidate.stop, slippage_bps), "AMBIGUOUS_STOP_FIRST"
        if bar.low <= candidate.stop:
            return bar.timestamp, infra.fill_exit(candidate.stop, slippage_bps), "STOP"
        if bar.high >= candidate.target:
            return bar.timestamp, infra.fill_exit(candidate.target, slippage_bps), "VWAP_TARGET"
    raise ValueError("NO_CAUSAL_EXIT_EVIDENCE")


def run_portfolio(data: dict[str, dict[date, list[infra.MinuteBar]]], candidates: list[Candidate], slippage_bps: float) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    equity = STARTING_CAPITAL
    trades: list[dict[str, object]] = []
    rejects: list[dict[str, object]] = []
    grouped: dict[date, list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate.day].append(candidate)
    for day in sorted(grouped):
        occupied = False
        for candidate in grouped[day]:
            if occupied:
                rejects.append({"date": day.isoformat(), "symbol": candidate.symbol, "reason": "PORTFOLIO_OCCUPIED"})
                continue
            sizing = size_and_reward(equity, candidate, slippage_bps)
            qty = int(sizing["quantity"])
            if qty < 1:
                rejects.append({"date": day.isoformat(), "symbol": candidate.symbol, "reason": sizing["reason"]})
                continue
            try:
                exit_time, exit_price, exit_reason = simulate_exit(candidate, data[candidate.symbol][day], slippage_bps)
            except ValueError as exc:
                rejects.append({"date": day.isoformat(), "symbol": candidate.symbol, "reason": str(exc)})
                continue
            entry = float(sizing["entry"])
            costs = infra.round_trip_costs(entry, exit_price, qty, day)
            gross = (exit_price - entry) * qty
            net = gross - costs["total"]
            before = equity
            equity += net
            trades.append({
                "date": day.isoformat(), "symbol": candidate.symbol, "rvol": candidate.rvol,
                "breakdown_depth": candidate.breakdown_depth, "breakdown_time": candidate.breakdown_time.isoformat(),
                "recovery_time": candidate.recovery_time.isoformat(), "entry_time": candidate.entry_time.isoformat(),
                "entry_price": entry, "quantity": qty, "stop": candidate.stop, "target": candidate.target,
                "planned_stop_fill": sizing["stop_fill"], "planned_target_fill": sizing["target_fill"],
                "planned_risk": sizing["planned_loss"], "planned_risk_pct": float(sizing["planned_loss"]) / before,
                "planned_profit": sizing["planned_profit"], "exit_time": exit_time.isoformat(),
                "exit_price": exit_price, "exit_reason": exit_reason, "gross_pnl": gross,
                "costs": costs["total"], "net_pnl": net, "equity_before": before, "equity_after": equity,
            })
            occupied = True
    return trades, rejects


def development_pass(base: dict[str, object], adverse: dict[str, object]) -> bool:
    return bool(
        base["trades"] >= 30 and base["net_pnl"] > 0 and base["profit_factor"] is not None and base["profit_factor"] > 1.15
        and base["expectancy"] is not None and base["expectancy"] > 0
        and base["max_drawdown"] <= 0.15 * STARTING_CAPITAL
        and base["positive_month_share"] is not None and base["positive_month_share"] >= 0.50
        and base["net_ex_top_3"] > 0 and adverse["net_pnl"] > 0
        and adverse["profit_factor"] is not None and adverse["profit_factor"] > 1.0
    )


def validation_pass(base: dict[str, object], adverse: dict[str, object], development_trades: int) -> bool:
    return bool(
        base["trades"] >= 20 and development_trades + base["trades"] >= 50
        and base["net_pnl"] > 0 and base["profit_factor"] is not None and base["profit_factor"] > 1.10
        and base["expectancy"] is not None and base["expectancy"] > 0
        and base["max_drawdown"] <= 0.15 * STARTING_CAPITAL
        and base["positive_month_share"] is not None and base["positive_month_share"] >= 0.50
        and base["net_ex_top_3"] > 0 and adverse["net_pnl"] > 0
        and adverse["profit_factor"] is not None and adverse["profit_factor"] > 1.0
    )


def candidate_dict(candidate: Candidate) -> dict[str, object]:
    result = asdict(candidate)
    for key, value in list(result.items()):
        if isinstance(value, (date, datetime)):
            result[key] = value.isoformat()
    return result

