from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import re
import statistics
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
TICK = 0.05
STARTING_CAPITAL = 20_000.0
RISK_FRACTION = 0.01
ARCHIVE_SHA256 = "20024713c455cc16b5daae91e06991d57a1acfa6a30c77bb7d5a742ee1789ab2"
SYMBOLS = ("AXISBANK", "DLF", "HAL", "ICICIBANK", "INFY", "KOTAKBANK", "SBIN", "TCS")
LOAD_FROM = date(2024, 2, 1)
DEV_START, DEV_END = date(2024, 4, 1), date(2025, 2, 28)
VAL_START, VAL_END = date(2025, 3, 1), date(2025, 10, 31)


@dataclass(frozen=True)
class MinuteBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class FiveBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Candidate:
    day: date
    symbol: str
    rvol: float
    breakout_distance: float
    breakout_time: datetime
    pullback_time: datetime
    trigger_time: datetime
    entry_time: datetime
    entry_raw: float
    stop: float


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_timestamp(value: object) -> datetime:
    if isinstance(value, bool):
        raise ValueError("MALFORMED_TIMESTAMP")
    token = str(value).strip()
    if re.fullmatch(r"[+-]?\d+", token) is None:
        raise ValueError("TIMESTAMP_NOT_INTEGER_SECOND")
    stamp = datetime.fromtimestamp(int(token), timezone.utc).astimezone(IST)
    if stamp.second or stamp.microsecond:
        raise ValueError("OFF_GRID_TIMESTAMP")
    return stamp


def bar_issues(bar: MinuteBar) -> tuple[str, ...]:
    issues: list[str] = []
    prices = (bar.open, bar.high, bar.low, bar.close)
    if not all(math.isfinite(value) for value in prices):
        issues.append("NONFINITE_OHLC")
    elif any(value <= 0 for value in prices):
        issues.append("NONPOSITIVE_OHLC")
    elif not (bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high):
        issues.append("INVALID_OHLC_RELATIONSHIP")
    if not math.isfinite(bar.volume):
        issues.append("NONFINITE_VOLUME")
    elif bar.volume < 0:
        issues.append("NEGATIVE_VOLUME")
    if bar.timestamp.second or bar.timestamp.microsecond:
        issues.append("OFF_GRID_TIMESTAMP")
    return tuple(issues)


def row_to_bar(row: dict[str, str]) -> MinuteBar:
    return MinuteBar(
        parse_timestamp(row["time"]),
        float(row["open"]), float(row["high"]), float(row["low"]),
        float(row["close"]), float(row["Volume"]),
    )


def expected_minutes(day: date) -> tuple[datetime, ...]:
    start = datetime.combine(day, time(9, 15), IST)
    return tuple(start + timedelta(minutes=i) for i in range(375))


def session_issues(bars: list[MinuteBar], parse_errors: int = 0, out_of_order: int = 0) -> tuple[str, ...]:
    issues: list[str] = []
    if parse_errors:
        issues.append(f"MALFORMED_ROWS:{parse_errors}")
    stamps = [bar.timestamp for bar in bars]
    duplicates = len(stamps) - len(set(stamps))
    if duplicates:
        issues.append(f"DUPLICATE_TIMESTAMPS:{duplicates}")
    if out_of_order:
        issues.append(f"OUT_OF_ORDER:{out_of_order}")
    invalid = sum(bool(bar_issues(bar)) for bar in bars)
    if invalid:
        issues.append(f"INVALID_BARS:{invalid}")
    if bars:
        day = bars[0].timestamp.date()
        expected = expected_minutes(day)
        if tuple(stamps) != expected:
            missing = len(set(expected) - set(stamps))
            extra = len(set(stamps) - set(expected))
            issues.append(f"SESSION_GRID_MISMATCH:MISSING={missing}:EXTRA={extra}")
    else:
        issues.append("EMPTY_SESSION")
    return tuple(issues)


def aggregate_five(bars: list[MinuteBar]) -> list[FiveBar]:
    if session_issues(bars):
        raise ValueError("INELIGIBLE_SESSION")
    result: list[FiveBar] = []
    for offset in range(0, 375, 5):
        group = bars[offset:offset + 5]
        start = group[0].timestamp
        if tuple(bar.timestamp for bar in group) != tuple(start + timedelta(minutes=i) for i in range(5)):
            raise ValueError("INCOMPLETE_FIVE_MINUTE_BUCKET")
        result.append(FiveBar(start, group[0].open, max(b.high for b in group),
                              min(b.low for b in group), group[-1].close,
                              sum(b.volume for b in group)))
    return result


def load_archive(path: Path) -> tuple[dict[str, dict[date, list[MinuteBar]]], dict[str, object], list[dict[str, object]]]:
    archive_hash = sha256_file(path)
    if archive_hash != ARCHIVE_SHA256:
        raise SystemExit(f"archive SHA256 mismatch: {archive_hash}")
    admitted: dict[str, dict[date, list[MinuteBar]]] = {symbol: {} for symbol in SYMBOLS}
    exclusions: list[dict[str, object]] = []
    members: dict[str, object] = {}
    with zipfile.ZipFile(path) as zf:
        by_name = {Path(name).name.upper(): name for name in zf.namelist()}
        for symbol in SYMBOLS:
            member = by_name.get(f"{symbol}_1M.CSV.GZ")
            if not member:
                raise SystemExit(f"missing archive member for {symbol}")
            compressed = zf.read(member)
            members[symbol] = {"member": member, "compressed_bytes": len(compressed), "sha256": sha256_bytes(compressed)}
            grouped: dict[date, list[MinuteBar]] = defaultdict(list)
            parse_errors: Counter[date] = Counter()
            order_errors: Counter[date] = Counter()
            previous: datetime | None = None
            with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as text:
                for row in csv.DictReader(text):
                    try:
                        bar = row_to_bar(row)
                    except (KeyError, TypeError, ValueError, OverflowError):
                        continue
                    day = bar.timestamp.date()
                    if day < LOAD_FROM:
                        previous = bar.timestamp
                        continue
                    if day > VAL_END:
                        break
                    if previous is not None and bar.timestamp <= previous:
                        order_errors[day] += 1
                    previous = bar.timestamp
                    clock = bar.timestamp.time().replace(tzinfo=None)
                    if time(9, 15) <= clock <= time(15, 29):
                        grouped[day].append(bar)
            for day, bars in sorted(grouped.items()):
                issues = session_issues(bars, parse_errors[day], order_errors[day])
                if issues:
                    exclusions.append({"symbol": symbol, "date": day.isoformat(), "reasons": "|".join(issues)})
                else:
                    admitted[symbol][day] = bars
    manifest = {
        "source_url": "https://github.com/voletiramu/nse-fno-1min-data/releases/download/v1.0.0/stocks_1m_csvs.zip",
        "archive_sha256": archive_hash,
        "archive_bytes": path.stat().st_size,
        "timestamp_semantics": "exact Unix seconds UTC converted to Asia/Kolkata; one-minute interval start",
        "hard_max_date": VAL_END.isoformat(),
        "symbols": members,
        "discovery_grade_not_exchange_authoritative": True,
    }
    return admitted, manifest, exclusions


def ema5(bars: list[FiveBar]) -> list[float]:
    values: list[float] = []
    alpha = 2.0 / 6.0
    for bar in bars:
        values.append(bar.close if not values else alpha * bar.close + (1.0 - alpha) * values[-1])
    return values


def candidate_for_day(symbol: str, day: date, bars: list[MinuteBar], prior_opening_volumes: list[float]) -> Candidate | None:
    if len(prior_opening_volumes) < 20:
        return None
    five = aggregate_five(bars)
    emas = ema5(five)
    or_high = max(bar.high for bar in five[:3])
    or_low = min(bar.low for bar in five[:3])
    current_opening_volume = sum(bar.volume for bar in five[:3])
    average = sum(prior_opening_volumes[-20:]) / 20.0
    if average <= 0:
        return None
    rvol = current_opening_volume / average
    if rvol < 1.25:
        return None

    breakout: int | None = None
    for i, bar in enumerate(five):
        end = bar.timestamp + timedelta(minutes=5)
        if bar.timestamp.time() < time(9, 30) or end.time() > time(12, 0) or i < 6:
            continue
        previous_volume_median = statistics.median(item.volume for item in five[i - 6:i])
        if (bar.close > or_high * 1.001 and bar.close > emas[i]
                and emas[i] > emas[i - 2]
                and bar.volume >= 1.20 * previous_volume_median):
            breakout = i
            break
    if breakout is None:
        return None
    impulse_high = five[breakout].high
    pullback: int | None = None
    for i in range(breakout + 1, min(len(five), breakout + 7)):
        bar = five[i]
        if bar.close < emas[i] or bar.low < or_low:
            return None
        if bar.low <= emas[i] and bar.close >= emas[i] and bar.low >= or_high * 0.999 and bar.close < impulse_high:
            pullback = i
            break
    if pullback is None:
        return None
    trigger: int | None = None
    for i in range(pullback + 1, len(five) - 1):
        bar = five[i]
        if bar.timestamp + timedelta(minutes=5) > datetime.combine(day, time(13, 25), IST):
            break
        if bar.close < emas[i] or bar.low < or_low:
            return None
        if bar.close > five[i - 1].high and bar.close > emas[i] and bar.close > five[pullback].high:
            trigger = i
            break
    if trigger is None:
        return None
    entry_index = trigger + 1
    entry = five[entry_index]
    if entry.timestamp.time() > time(13, 30):
        return None
    stop = tick_down(min(item.low for item in five[pullback:trigger + 1]) - TICK)
    if stop <= 0 or stop >= entry.open:
        return None
    return Candidate(day, symbol, rvol, five[breakout].close / or_high - 1.0,
                     five[breakout].timestamp + timedelta(minutes=5),
                     five[pullback].timestamp + timedelta(minutes=5),
                     five[trigger].timestamp + timedelta(minutes=5),
                     entry.timestamp, entry.open, stop)


def generate_candidates(data: dict[str, dict[date, list[MinuteBar]]], start: date, end: date) -> list[Candidate]:
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
    return sorted(candidates, key=lambda item: (item.entry_time, -item.rvol, -item.breakout_distance, item.symbol))


def tick_up(value: float) -> float:
    return round(math.ceil((value - 1e-10) / TICK) * TICK, 2)


def tick_down(value: float) -> float:
    return round(math.floor((value + 1e-10) / TICK) * TICK, 2)


def side_costs(turnover: float, *, buy: bool, day: date) -> dict[str, float]:
    brokerage = min(20.0, 0.0003 * turnover)
    stt = 0.0 if buy else 0.00025 * turnover
    exchange_rate = 0.0000322 if day <= date(2024, 9, 30) else 0.0000297
    exchange = exchange_rate * turnover
    sebi = 0.000001 * turnover
    ipft = 0.000001 * turnover
    gst = 0.18 * (brokerage + exchange + sebi)
    stamp = 0.00003 * turnover if buy else 0.0
    return {"brokerage": brokerage, "stt": stt, "exchange": exchange,
            "sebi": sebi, "ipft": ipft, "gst": gst, "stamp": stamp,
            "total": brokerage + stt + exchange + sebi + ipft + gst + stamp}


def round_trip_costs(entry: float, exit_price: float, qty: int, day: date) -> dict[str, float]:
    buy = side_costs(entry * qty, buy=True, day=day)
    sell = side_costs(exit_price * qty, buy=False, day=day)
    return {key: buy[key] + sell[key] for key in buy}


def fill_entry(raw: float, slippage_bps: float) -> float:
    return tick_up(raw * (1.0 + slippage_bps / 10_000.0))


def fill_exit(raw: float, slippage_bps: float) -> float:
    return max(TICK, tick_down(raw * (1.0 - slippage_bps / 10_000.0)))


def size_position(equity: float, candidate: Candidate, slippage_bps: float) -> tuple[int, float, float, float]:
    entry = fill_entry(candidate.entry_raw, slippage_bps)
    stop_fill = fill_exit(candidate.stop, slippage_bps)
    affordable = int(equity // entry)
    for qty in range(affordable, 0, -1):
        costs = round_trip_costs(entry, stop_fill, qty, candidate.day)["total"]
        planned = (entry - stop_fill) * qty + costs
        buy_cost = side_costs(entry * qty, buy=True, day=candidate.day)["total"]
        if planned <= equity * RISK_FRACTION + 1e-9 and entry * qty + buy_cost <= equity + 1e-9:
            return qty, entry, stop_fill, planned
    return 0, entry, stop_fill, 0.0


def simulate_exit(candidate: Candidate, minutes: list[MinuteBar], entry: float, slippage_bps: float) -> tuple[datetime, float, str, float]:
    risk = entry - candidate.stop
    target = tick_down(entry + 2.0 * risk)
    for bar in minutes:
        if bar.timestamp < candidate.entry_time:
            continue
        if bar.timestamp.time() == time(15, 10):
            return bar.timestamp, fill_exit(bar.open, slippage_bps), "TIME_15_10", target
        if bar.open <= candidate.stop:
            return bar.timestamp, fill_exit(bar.open, slippage_bps), "STOP_GAP", target
        if bar.low <= candidate.stop and bar.high >= target:
            return bar.timestamp, fill_exit(candidate.stop, slippage_bps), "AMBIGUOUS_STOP_FIRST", target
        if bar.low <= candidate.stop:
            return bar.timestamp, fill_exit(candidate.stop, slippage_bps), "STOP", target
        if bar.high >= target:
            return bar.timestamp, fill_exit(target, slippage_bps), "TARGET", target
    raise ValueError("NO_CAUSAL_EXIT_EVIDENCE")


def run_portfolio(data: dict[str, dict[date, list[MinuteBar]]], candidates: list[Candidate], slippage_bps: float) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    equity = STARTING_CAPITAL
    trades: list[dict[str, object]] = []
    rejects: list[dict[str, object]] = []
    by_day: dict[date, list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        by_day[candidate.day].append(candidate)
    for day in sorted(by_day):
        executed = False
        for candidate in by_day[day]:
            if executed:
                rejects.append({"date": day.isoformat(), "symbol": candidate.symbol, "reason": "PORTFOLIO_OCCUPIED"})
                continue
            qty, entry, stop_fill, planned = size_position(equity, candidate, slippage_bps)
            if qty < 1:
                rejects.append({"date": day.isoformat(), "symbol": candidate.symbol, "reason": "CAPITAL_OR_RISK"})
                continue
            try:
                exit_time, exit_price, exit_reason, target = simulate_exit(candidate, data[candidate.symbol][day], entry, slippage_bps)
            except ValueError as exc:
                rejects.append({"date": day.isoformat(), "symbol": candidate.symbol, "reason": str(exc)})
                continue
            cost = round_trip_costs(entry, exit_price, qty, day)
            gross = (exit_price - entry) * qty
            net = gross - cost["total"]
            before = equity
            equity += net
            trades.append({
                "date": day.isoformat(), "symbol": candidate.symbol, "rvol": candidate.rvol,
                "breakout_distance": candidate.breakout_distance,
                "breakout_time": candidate.breakout_time.isoformat(), "pullback_time": candidate.pullback_time.isoformat(),
                "trigger_time": candidate.trigger_time.isoformat(), "entry_time": candidate.entry_time.isoformat(),
                "entry_price": entry, "quantity": qty, "stop": candidate.stop, "planned_stop_fill": stop_fill,
                "planned_risk": planned, "planned_risk_pct": planned / before,
                "target": target, "exit_time": exit_time.isoformat(), "exit_price": exit_price,
                "exit_reason": exit_reason, "gross_pnl": gross, "costs": cost["total"], "net_pnl": net,
                "equity_before": before, "equity_after": equity,
            })
            executed = True
    return trades, rejects


def metrics(trades: list[dict[str, object]]) -> dict[str, object]:
    nets = [float(t["net_pnl"]) for t in trades]
    gross = sum(float(t["gross_pnl"]) for t in trades)
    costs = sum(float(t["costs"]) for t in trades)
    wins = [x for x in nets if x > 0]
    losses = [x for x in nets if x < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    # Undefined (rather than JSON Infinity) when no losing trades exist.
    profit_factor: float | None = gross_profit / gross_loss if gross_loss else None
    equity = STARTING_CAPITAL
    peak = equity
    max_drawdown = 0.0
    monthly: dict[str, float] = defaultdict(float)
    symbols: dict[str, float] = defaultdict(float)
    for trade, net in zip(trades, nets):
        equity += net
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
        monthly[str(trade["date"])[:7]] += net
        symbols[str(trade["symbol"])] += net
    top = sorted(wins, reverse=True)[:3]
    positive_months = sum(value > 0 for value in monthly.values())
    return {
        "trades": len(trades), "gross_pnl": gross, "costs": costs, "net_pnl": sum(nets),
        "ending_equity": STARTING_CAPITAL + sum(nets), "profit_factor": profit_factor,
        "win_rate": len(wins) / len(nets) if nets else None,
        "expectancy": sum(nets) / len(nets) if nets else None,
        "max_drawdown": max_drawdown, "monthly": dict(sorted(monthly.items())),
        "positive_month_share": positive_months / len(monthly) if monthly else None,
        "symbol_net": dict(sorted(symbols.items())), "top_3_winners": top,
        "net_ex_top_3": sum(nets) - sum(top),
    }


def candidate_dict(candidate: Candidate) -> dict[str, object]:
    result = asdict(candidate)
    for key, value in list(result.items()):
        if isinstance(value, (date, datetime)):
            result[key] = value.isoformat()
    return result


def validation_pass(base: dict[str, object], adverse: dict[str, object]) -> bool:
    pf = base["profit_factor"]
    adverse_pf = adverse["profit_factor"]
    return bool(
        base["trades"] >= 50 and base["net_pnl"] > 0 and pf is not None and pf > 1.10
        and base["expectancy"] is not None and base["expectancy"] > 0
        and base["max_drawdown"] <= 0.15 * STARTING_CAPITAL
        and base["positive_month_share"] is not None and base["positive_month_share"] >= 0.50
        and base["net_ex_top_3"] > 0 and adverse["net_pnl"] > 0
        and adverse_pf is not None and adverse_pf > 1.0
    )

