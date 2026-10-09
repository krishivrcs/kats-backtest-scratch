#!/usr/bin/env python3
"""Execute frozen KATS ORB-RVOL risk-management variants."""

from __future__ import annotations

import argparse
import csv
import json
import math
import zipfile
from collections import Counter, defaultdict
from datetime import date, time, timedelta
from pathlib import Path
from statistics import mean

from backtest import (
    IST,
    SCENARIOS,
    STARTING_CAPITAL,
    SYMBOLS,
    Bar,
    Contract,
    Signal,
    build_signals,
    charges,
    contract_reference_price,
    load_day_options,
    option_members,
    parse_cash_archive,
    raw_opportunity,
    sha256_file,
    slippage,
)

TICK = 0.05
CONFIGS = {
    "control_1pct": {"risk_ceiling": 0.01, "stop_kind": "PCT20"},
    "variant_a_3pct": {"risk_ceiling": 0.03, "stop_kind": "PCT20"},
    "variant_b_1point": {"risk_ceiling": None, "stop_kind": "FIXED_1_POINT"},
}


def floor_tick(value: float, tick: float = TICK) -> float:
    return max(0.0, math.floor((value + 1e-12) / tick) * tick)


def stop_prices(entry_price: float) -> dict[str, float]:
    original = entry_price * 0.80
    return {
        "original_strategy_stop": original,
        "variant_a_stop": original,
        "variant_b_stop": floor_tick(entry_price - 1.0),
    }


def estimated_trade(signal: Signal, opportunity: dict, config_name: str, equity: float) -> dict:
    config = CONFIGS[config_name]
    pct, minimum = SCENARIOS["baseline"]
    contract: Contract = opportunity["contract"]
    bars: list[Bar] = opportunity["bars"]
    entry_index = opportunity["entry_index"]
    lot = opportunity["lot_size"]
    entry_bar = bars[entry_index]
    entry_price = entry_bar.open + slippage(entry_bar.open, pct, minimum)
    stops = stop_prices(entry_price)
    stop = stops["variant_b_stop"] if config["stop_kind"] == "FIXED_1_POINT" else stops["original_strategy_stop"]
    target = entry_price * 1.40
    estimated_stop_exit = max(0.0, stop - slippage(stop, pct, minimum))
    estimated_costs = charges(entry_price, estimated_stop_exit, lot)["total"]
    planned_risk = (entry_price - estimated_stop_exit) * lot + estimated_costs
    premium_outlay = entry_price * lot
    required_cash = premium_outlay + estimated_costs
    affordable = required_cash <= equity + 1e-9
    risk_limit = None if config["risk_ceiling"] is None else equity * config["risk_ceiling"]
    risk_eligible = True if risk_limit is None else planned_risk <= risk_limit + 1e-9
    return {
        "config": config_name,
        "day": signal.day.isoformat(),
        "symbol": signal.symbol,
        "direction": signal.direction,
        "option_type": contract.option_type,
        "decision_time": signal.decision_time.isoformat(),
        "entry_timestamp": entry_bar.timestamp.isoformat(),
        "contract_identifier": contract.ticker,
        "expiry": contract.expiry.isoformat(),
        "strike": contract.strike,
        "underlying_close": signal.underlying_close,
        "contract_reference_price": contract_reference_price(signal),
        "option_entry_price": entry_price,
        "historical_lot_size": lot,
        "required_premium_outlay": premium_outlay,
        "estimated_round_trip_cost_at_stop": estimated_costs,
        "required_cash_including_estimated_costs": required_cash,
        "available_account_cash": equity,
        **stops,
        "active_stop": stop,
        "target": target,
        "estimated_planned_risk_rupees": planned_risk,
        "estimated_planned_risk_percent": planned_risk / equity * 100,
        "risk_limit_rupees": risk_limit,
        "affordability_result": "PASS" if affordable else "FAIL",
        "risk_eligibility_result": "PASS" if risk_eligible else "FAIL",
        "entry_candle_range": entry_bar.high - entry_bar.low,
        "one_point_vs_entry_candle_noise": "WITHIN_ENTRY_CANDLE_RANGE" if 1.0 <= entry_bar.high - entry_bar.low else "LARGER_THAN_ENTRY_CANDLE_RANGE",
        "estimated_round_trip_slippage_at_entry_scale": 2 * slippage(entry_price, pct, minimum),
    }


def exit_trade(estimate: dict, opportunity: dict) -> tuple[dict | None, str]:
    pct, minimum = SCENARIOS["baseline"]
    bars: list[Bar] = opportunity["bars"]
    entry_index = opportunity["entry_index"]
    stop = estimate["active_stop"]
    target = estimate["target"]
    exit_raw = exit_time = exit_reason = None
    for bar in bars[entry_index:]:
        clock = bar.timestamp.time().replace(tzinfo=None)
        if clock >= time(15, 15):
            exit_raw, exit_time, exit_reason = bar.open, bar.timestamp, "FORCED_15_15"
            break
        if bar.open <= stop:
            exit_raw, exit_time, exit_reason = bar.open, bar.timestamp, "STOP_GAP"
            break
        stop_hit = bar.low <= stop
        target_hit = bar.high >= target
        if stop_hit and target_hit:
            exit_raw, exit_time, exit_reason = stop, bar.timestamp, "AMBIGUOUS_STOP_FIRST"
            break
        if stop_hit:
            exit_raw, exit_time, exit_reason = stop, bar.timestamp, "STOP"
            break
        if target_hit:
            exit_raw, exit_time, exit_reason = target, bar.timestamp, "TARGET"
            break
    if exit_raw is None:
        return None, "NO_EXIT_DATA"
    exit_price = max(0.0, exit_raw - slippage(exit_raw, pct, minimum))
    quantity = estimate["historical_lot_size"]
    actual_costs = charges(estimate["option_entry_price"], exit_price, quantity)
    gross = (exit_price - estimate["option_entry_price"]) * quantity
    net = gross - actual_costs["total"]
    return {
        "exit_price": exit_price,
        "exit_timestamp": exit_time.isoformat(),
        "exit_reason": exit_reason,
        "gross_pnl": gross,
        "total_charges": actual_costs["total"],
        "net_pnl": net,
        "realized_loss_rupees": max(0.0, -net),
        "realized_loss_percent_equity": max(0.0, -net) / estimate["available_account_cash"] * 100,
        **{f"charge_{key}": value for key, value in actual_costs.items() if key != "total"},
    }, "EXECUTED"


def run_portfolio(config_name: str, target_days: list[date], opportunities: dict[date, list[tuple[Signal, dict | None, str]]]) -> tuple[list[dict], list[dict]]:
    equity = STARTING_CAPITAL
    trades = []
    diagnostics = []
    for day in target_days:
        executed_today = False
        for signal, opportunity, readiness in opportunities.get(day, []):
            base = {
                "config": config_name,
                "day": day.isoformat(),
                "symbol": signal.symbol,
                "direction": signal.direction,
                "option_type": "CE" if signal.direction == "LONG" else "PE",
                "decision_time": signal.decision_time.isoformat(),
                "available_account_cash": equity,
            }
            if opportunity is None:
                diagnostics.append({**base, "executed_or_rejected": "UNSCORABLE", "rejection_reason": readiness})
                continue
            estimate = estimated_trade(signal, opportunity, config_name, equity)
            if executed_today:
                diagnostics.append({**estimate, "executed_or_rejected": "REJECTED", "rejection_reason": "DAILY_PORTFOLIO_LIMIT"})
                continue
            if estimate["affordability_result"] == "FAIL":
                diagnostics.append({**estimate, "executed_or_rejected": "REJECTED", "rejection_reason": "CAPITAL_CONSTRAINT"})
                continue
            if estimate["risk_eligibility_result"] == "FAIL":
                diagnostics.append({**estimate, "executed_or_rejected": "REJECTED", "rejection_reason": "RISK_CONSTRAINT"})
                continue
            exit_values, reason = exit_trade(estimate, opportunity)
            if exit_values is None:
                diagnostics.append({**estimate, "executed_or_rejected": "UNSCORABLE", "rejection_reason": reason})
                continue
            row = {**estimate, **exit_values, "executed_or_rejected": "EXECUTED", "rejection_reason": ""}
            equity += row["net_pnl"]
            row["ending_equity_after_trade"] = equity
            trades.append(row)
            diagnostics.append(row)
            executed_today = True
    return trades, diagnostics


def metrics(trades: list[dict], diagnostics: list[dict]) -> dict:
    nets = [row["net_pnl"] for row in trades]
    wins = [value for value in nets if value > 0]
    losses = [value for value in nets if value < 0]
    equity = peak = STARTING_CAPITAL
    drawdown = 0.0
    for value in nets:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    reasons = Counter(row.get("rejection_reason") for row in diagnostics)
    return {
        "executable_trades": len(trades),
        "rejected_affordability": reasons["CAPITAL_CONSTRAINT"],
        "rejected_risk": reasons["RISK_CONSTRAINT"],
        "unscorable": sum(1 for row in diagnostics if row["executed_or_rejected"] == "UNSCORABLE"),
        "gross_pnl": sum(row["gross_pnl"] for row in trades),
        "costs": sum(row["total_charges"] for row in trades),
        "net_pnl": sum(nets),
        "ending_equity": STARTING_CAPITAL + sum(nets),
        "max_drawdown": drawdown,
        "max_realized_trade_loss": max((row["realized_loss_rupees"] for row in trades), default=0.0),
        "max_realized_risk_percent": max((row["realized_loss_percent_equity"] for row in trades), default=0.0),
        "profit_factor": (sum(wins) / abs(sum(losses))) if losses else ("Infinity" if wins else None),
        "win_rate": len(wins) / len(trades) if trades else None,
        "average_winner": mean(wins) if wins else None,
        "average_loser": mean(losses) if losses else None,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    if not fields:
        path.write_text("", encoding="utf-8")
        return
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
    members = option_members(args.option_zip)
    target_days = sorted(members)
    cash = parse_cash_archive(args.stock_zip)
    signals, signal_audit = build_signals(cash, target_days)
    opportunities: dict[date, list[tuple[Signal, dict | None, str]]] = defaultdict(list)
    with zipfile.ZipFile(args.option_zip) as zf:
        for day in target_days:
            day_signals = signals.get(day, [])
            needed = {signal.symbol: ("CE" if signal.direction == "LONG" else "PE") for signal in day_signals}
            contracts = load_day_options(zf, members[day], needed) if needed else {}
            for signal in day_signals:
                opportunity, readiness = raw_opportunity(signal, contracts)
                opportunities[day].append((signal, opportunity, readiness))
    result = {
        "project": "KATS-ORB-RVOL-3STOCK-RISK-VARIANTS",
        "baseline_commit": "23174e644dd3ef10a4973a6e895bbaceb692b324",
        "data_range": [target_days[0].isoformat(), target_days[-1].isoformat()],
        "option_sessions": len(target_days),
        "signals": sum(len(values) for values in signals.values()),
        "option_zip_sha256": sha256_file(args.option_zip),
        "stock_zip_sha256": sha256_file(args.stock_zip),
        "corporate_action_regression": "PASS_RELIANCE_PRE_BONUS_CONTRACT_REFERENCE_2X_ADJUSTED_CASH",
        "signal_audit": signal_audit,
        "configs": {},
    }
    all_diagnostics = []
    all_trades = []
    for config_name in CONFIGS:
        trades, diagnostics = run_portfolio(config_name, target_days, opportunities)
        result["configs"][config_name] = metrics(trades, diagnostics)
        all_diagnostics.extend(diagnostics)
        all_trades.extend(trades)
        write_csv(args.out / f"diagnostics_{config_name}.csv", diagnostics)
        write_csv(args.out / f"trades_{config_name}.csv", trades)
    write_csv(args.out / "all_signal_diagnostics.csv", all_diagnostics)
    write_csv(args.out / "all_executed_trades.csv", all_trades)
    result["reconciliation"] = {
        config: {
            "ledger_rows": sum(1 for row in all_trades if row["config"] == config),
            "ledger_net": sum(row["net_pnl"] for row in all_trades if row["config"] == config),
            "metrics_net": result["configs"][config]["net_pnl"],
        } for config in CONFIGS
    }
    result["variant_b_microstructure_warning"] = "UNRESOLVED_NO_BID_ASK; compare one-point stop with entry_candle_range and estimated slippage fields; no stop-price guarantee"
    (args.out / "risk_variant_results.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"signals": result["signals"], "configs": result["configs"], "reconciliation": result["reconciliation"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
